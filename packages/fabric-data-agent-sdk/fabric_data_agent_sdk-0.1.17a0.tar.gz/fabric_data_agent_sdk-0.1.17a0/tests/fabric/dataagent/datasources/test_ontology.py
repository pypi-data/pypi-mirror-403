"""
Unit tests for the Fabric Ontology datasource.
"""

import requests
from typing import Any, Optional
from uuid import UUID

import pandas as pd
import pytest

from fabric.dataagent.datasources.factory import make_source
from fabric.dataagent.datasources.ontology import OntologySource
from sempy.fabric.exceptions import FabricHTTPException


def _build_cfg() -> dict:
	"""
	Builds a dummy configuration dictionary for an Ontology source.
	"""
	return {
		"type": "ontology",
		"display_name": "MyOntology",
		"workspace_name": "MyWorkspace",
	}


def _list_dummy_items(type: str, workspace: str) -> pd.DataFrame:
    """
	Dummy list_items function for ontology tests.
	"""
    assert type == "ontology"
    assert workspace in ("MyWorkspace", "ws123")
    return pd.DataFrame(
        [{"Id": "ont456", "Display Name": "MyOntology"}],
        columns=["Id", "Display Name"],
    )


class _DummyResponse:
	"""
	Stub response object mimicking the minimal requests.Response surface used.
	"""

	def __init__(
		self,
		payload: list[dict] | None = None,
		status_code: int = 200,
		message: str | None = None,
		url: str = "https://dummy"
	):
		self._payload = payload or []
		self.status_code = status_code
		self._message = message
		self.text = message or ""
		self.reason = message or ""
		self.url = url
		self.headers = {}

	def json(self) -> list[dict] | None:  # noqa: D401
		return self._payload

	def get(self, key: str, default: str = "") -> str:
		if key == "Message" and self._message:
			return self._message
		return default


class DummyRequests:
    """
    DummyRequests with a fake requests.post for ontology tests with 
	success responses. Records every call and returns a 
	preconfigured _DummyResponse.
    """

    def __init__(self, payload: list[dict] | None = None):
        self.calls: list[dict] = []
        self._payload = payload

    def post(
		self,
		url: str,
		json: Any,
		headers: dict,
		timeout: Optional[int] = None
	) -> _DummyResponse:
        self.calls.append({"url": url, "json": json, "headers": headers})
        return _DummyResponse(payload=self._payload, status_code=200, url=url)


class DummyRequestsWithError(DummyRequests):
	"""
	DummyRequests with a fake requests.post for ontology tests with 
	an internal error response.Records every call and returns a 
	preconfigured _DummyResponse.
	"""
	
	def post(
		self,
		url: str,
		json,
		headers: dict,
		timeout: Optional[int] = None
	) -> _DummyResponse:
		self.calls.append({"url": url, "json": json, "headers": headers})
		return _DummyResponse(
            payload=[],
			status_code=500,
			message="Internal Server Error",
			url=url
        )

class _DummyEnvConfig:
	"""
	Dummy environment configuration for ontology tests.
	"""
	
	class fabric_env_config:
		wl_host = "https://host.example.com"


class _DummyToken:
	"""
	Dummy token object for ontology tests.
	"""

	def __init__(self, token: str):
		self.Token = token


class _DummyTokenSvc:
	"""
	Dummy TokenServiceClient for ontology tests.
	"""
	def get_mwc_token(self, workspace_id: str, artifact_id: str) -> str:
		assert workspace_id == "ws123"
		assert artifact_id == "ont456"
		return _DummyToken("DUMMY_MWC")


@pytest.fixture()
def monkeypatched_env(monkeypatch):
	"""
	Common monkeypatch for environment/service discovery helpers 
	and token acquisition.
	"""
	import fabric.dataagent.datasources.ontology as ontology_mod

	monkeypatch.setattr(
		ontology_mod, "resolve_workspace_id", lambda _: "ws123"
	)
	monkeypatch.setattr(
		ontology_mod,
		"resolve_workspace_capacity",
		lambda _: (UUID("12345678-1234-5678-1234-567812345678"), "111")
	)
	monkeypatch.setattr(
		ontology_mod, "get_fabric_env_config", lambda: _DummyEnvConfig()
	)
	monkeypatch.setattr(ontology_mod, "list_items", _list_dummy_items)
	monkeypatch.setattr(ontology_mod, "TokenServiceClient", _DummyTokenSvc)

	return ontology_mod


def test_make_source_creates_ontology_source(
		monkeypatched_env: _DummyEnvConfig
	):
	src = make_source(_build_cfg())
	assert isinstance(src, OntologySource)
	assert src.artifact_id_or_name == "MyOntology"


def test_ontology_query_success(
		monkeypatch: Any,
		monkeypatched_env: _DummyEnvConfig
	):
	payload = {
        "fields": ["col1", "col2"],
        "value": [[1, "a"], [2, "b"]],
    }
	dummy_client = DummyRequests(payload=payload)
	monkeypatch.setattr(requests, "post", dummy_client.post)

	src = make_source(_build_cfg())
	df = src.execute(
		(
			"{'entitySelector':{'query':'MATCH (g:B) "
			"RETURN g.x','queryType':'GQL'}}"
        )
    )

	# Assertions on DataFrame content
	assert isinstance(df, pd.DataFrame)
	pd.testing.assert_frame_equal(
		df,
		pd.DataFrame([[1, "a"], [2, "b"]], columns=["col1", "col2"])
	)

	# Verify single POST call and header details
	assert len(dummy_client.calls) == 1
	call = dummy_client.calls[0]
	expected_url = (
		"https://host.example.com/webapi/capacities/"
		"12345678-1234-5678-1234-567812345678/workloads/DO/"
		"DigitalOperationsService/direct/v3/workspaces/ws123/"
        "digitalTwinBuilders/ont456/query"
	)
	assert call["url"] == expected_url
	assert call["json"] == (
		"{'entitySelector':{'query':'MATCH (g:B) "
		"RETURN g.x','queryType':'GQL'}}"
    )
	# Authorization header should carry the dummy bearer token
	assert call["headers"].get("Authorization") == "MwcToken DUMMY_MWC"


def test_ontology_query_http_error(monkeypatch, monkeypatched_env):
	# Error response (non-200) should raise FabricHTTPException
	dummy_client = DummyRequestsWithError()
	monkeypatch.setattr(requests, "post", dummy_client.post)

	src = make_source(_build_cfg())
	with pytest.raises(FabricHTTPException) as exc:
		src.execute("SELECT * FROM Ontology")

	assert exc.value.status_code == 500
	assert "Internal Server Error" in str(exc.value)
	# Ensure the failing call was attempted
	assert len(dummy_client.calls) == 1

"""
This script defines the interface for interacting with the Fabric ontology 
data source.
"""

import requests
from typing import Any, Union
from uuid import UUID

import pandas as pd
from sempy.fabric import (
    list_items,
    resolve_workspace_id
)
from sempy.fabric.exceptions import FabricHTTPException
from sempy_labs import resolve_workspace_capacity
from synapse.ml.fabric.service_discovery import get_fabric_env_config
from synapse.ml.fabric.token_utils import TokenServiceClient

from .base import BaseSource


class _OntologyConnection:
    """
    This class defines the interface for execution of interactions with 
    the Fabric ontology.
    """

    def __init__(
        self,
        artifact_id_or_name: Union[str, UUID],
        workspace_id_or_name: str | None = None
    ):
        self._workspace_id = resolve_workspace_id(
            workspace_id_or_name
        )
        self._artifact_id = _OntologyConnection._get_ontology_artifact_id(
            artifact_id_or_name,
            workspace_id_or_name
        )
        self._capacity_id, _ = resolve_workspace_capacity(
            workspace_id_or_name
        )

        self._token_service_client = TokenServiceClient()
        self._host = get_fabric_env_config().fabric_env_config.wl_host
        self._url = (
            f"{self._host}/webapi/capacities/{self._capacity_id}/"
            f"workloads/DO/DigitalOperationsService/direct/v3/workspaces/"
            f"{self._workspace_id}/digitalTwinBuilders/"
            f"{self._artifact_id}/query"
        )
    
    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type: Any,
        exc: Any,
        tb: Any
    ) -> bool:
        return False

    def query(
        self,
        ontology_query_code: str,
        *_: Any,
        **__: Any
    ) -> pd.DataFrame:
        """
        Execute an ontology query and return the results as a DataFrame.

        Parameters
        ----------
        ontology_query_code : str
            The ontology query code to execute.

        Returns
        -------
        pd.DataFrame
            The results of the query as a pandas DataFrame.
        """
        mwc_token = self._token_service_client.get_mwc_token(
            self._workspace_id, self._artifact_id
        ).Token
        headers: dict[str, str] = {
            "Authorization": f"MwcToken {mwc_token}"
        }

        try:
            response = requests.post(
                self._url,
                json=ontology_query_code,
                headers=headers,
                timeout=300
            )
        except Exception as exc:
            raise RuntimeError(
                f"Ontology query failed due to an exception: {exc}"
            ) from exc
        
        if response.status_code != 200:
            raise FabricHTTPException(response)

        response_json = response.json()
        return pd.DataFrame(
            response_json["value"],
            columns=response_json["fields"]
        )
    
    @staticmethod
    def _get_ontology_artifact_id(
        identifier: Union[str, UUID],
        workspace: Union[str, UUID],
    ) -> str:
        """
        Retrieve the ID of an Ontology artifact 
        in the given workspace by name or ID.

        Parameters
        ----------
        identifier : str | UUID
            The Ontology artifact display name or its UUID.
        workspace : str | UUID
            The workspace name or ID containing the artifact.

        Returns
        -------
        str
            The string ID of the Ontology artifact.
        """
        df: pd.DataFrame = list_items(type="ontology", workspace=workspace)

        if df.empty:
            raise ValueError(f"No Ontology artifact found in workspace '{workspace}'.")

        if not {"Id", "Display Name"}.issubset(df.columns):
            raise ValueError("Expected columns 'Id' and 'Display Name' not found.")

        # Match by UUID first, otherwise by display name
        try:
            uuid_val = UUID(str(identifier))
            matched_item = df.loc[df["Id"] == str(uuid_val)]
        except ValueError:
            matched_item = df.loc[df["Display Name"] == str(identifier)]

        if matched_item.empty:
            raise ValueError(
                f"Ontology artifact '{identifier}' not "
                f"found in workspace '{workspace}'."
            )

        return matched_item.iloc[0]["Id"]


class OntologySource(BaseSource):
    """
    Fabric ontology datasource.
    connect(): Run ontology queries (read-only)
    """

    def connect(self) -> _OntologyConnection:
        return _OntologyConnection(
            artifact_id_or_name=self.artifact_id_or_name,
            workspace_id_or_name=self.workspace_id_or_name,
        )

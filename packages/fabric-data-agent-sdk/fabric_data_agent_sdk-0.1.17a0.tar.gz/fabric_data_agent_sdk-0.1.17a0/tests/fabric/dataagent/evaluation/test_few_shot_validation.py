
import pytest
from fabric.dataagent.evaluation._few_shot_validation import (
    _evaluate_few_shot_examples,
    FewShotEvalResult,
    _cases_to_dataframe,
    _filter_conflicts,
    _validate_confidence,
    safe_parse_json,
    _detect_conflicts_between_examples,
    _get_conflict_details,
)

# Module-level dummy LLM classes for mocking
class DummyChoices:
    def __init__(self, content):
        self.message = type("msg", (), {"content": content})
class DummyResponse:
    def __init__(self, content):
        self.choices = [DummyChoices(content)]
class DummyChat:
    def __init__(self, content):
        self.completions = type("comp", (), {"create": lambda *args, **kwargs: DummyResponse(content)})
class DummyLLM:
    def __init__(self, content):
        self.chat = DummyChat(content)


def test_evaluate_few_shot_examples_validation():
    dummy_examples = [
        {"natural language": "What is the sum of sales?", "sql": "SELECT SUM(sales) FROM table;"},
        {"natural language": "How many users?", "sql": "SELECT COUNT(*) FROM users;"}
    ]
    # Should raise error if examples is empty
    with pytest.raises(ValueError):
        _evaluate_few_shot_examples([], "lakehouse")
    # Should raise error if example is missing keys
    with pytest.raises(ValueError):
        _evaluate_few_shot_examples([{"foo": "bar"}], "lakehouse")
    # Note: For real LLM test, mock llm_client or use use_fabric_llm=True in a Fabric environment
    # This test only checks input validation
    # Should raise error if examples is not a list
    with pytest.raises(ValueError):
        _evaluate_few_shot_examples("not a list", "lakehouse")
    with pytest.raises(ValueError):
        _evaluate_few_shot_examples({"natural language": "foo", "sql": "bar"}, "lakehouse")
    # Should raise error for unsupported datasource types
    with pytest.raises(ValueError, match="Few-shot evaluation is only supported for SQL datasources"):
        _evaluate_few_shot_examples(dummy_examples, "kusto")
    with pytest.raises(ValueError, match="Few-shot evaluation is only supported for SQL datasources"):
        _evaluate_few_shot_examples(dummy_examples, "ontology")


def test_evaluate_few_shot_examples_valid(monkeypatch):
    # Simulate a valid LLM JSON response
    llm_content = '{"evaluations": [{"example_id": 1, "reasoning": "Good mapping.", "quality": "yes", "reasoning_details": {"clarity": "yes", "mapping": "yes", "relatedness": "yes"}}, {"example_id": 2, "reasoning": "Clear question.", "quality": "no", "reasoning_details": {"clarity": "yes", "mapping": "no", "relatedness": "yes"}}]}'
    dummy_llm = DummyLLM(llm_content)
    examples = [
        {"natural language": "What is the sum of sales?", "sql": "SELECT SUM(sales) FROM table;"},
        {"natural language": "How many users?", "sql": "SELECT COUNT(*) FROM users;"}
    ]
    # Mock openai module used by the function
    monkeypatch.setattr("fabric.dataagent.evaluation._few_shot_validation.openai", dummy_llm)
    result = _evaluate_few_shot_examples(examples, "lakehouse")
    assert isinstance(result, FewShotEvalResult)
    assert result.total == 2
    assert result.success_count == 1
    assert result.success_rate == 50.0
    assert len(result.success_cases) == 1
    assert len(result.failure_cases) == 1


def test_evaluate_few_shot_examples_duplicates(monkeypatch):
    # Simulate LLM response for duplicates
    llm_content = '{"evaluations": [{"example_id": 1, "reasoning": "Duplicate example.", "quality": "yes", "reasoning_details": {"clarity": "yes", "mapping": "yes", "relatedness": "yes"}}, {"example_id": 2, "reasoning": "Duplicate example.", "quality": "yes", "reasoning_details": {"clarity": "yes", "mapping": "yes", "relatedness": "yes"}}]}'
    dummy_llm = DummyLLM(llm_content)
    examples = [
        {"natural language": "What is the sum of sales?", "sql": "SELECT SUM(sales) FROM table;"},
        {"natural language": "What is the sum of sales?", "sql": "SELECT SUM(sales) FROM table;"}
    ]
    monkeypatch.setattr("fabric.dataagent.evaluation._few_shot_validation.openai", dummy_llm)
    result = _evaluate_few_shot_examples(examples, "lakehouse")
    assert result.success_count == 2


def test_evaluate_few_shot_examples_empty_strings(monkeypatch):
    llm_content = '{"evaluations": [{"example_id": 1, "reasoning": "Empty question.", "quality": "no", "reasoning_details": {"clarity": "no", "mapping": "no", "relatedness": "no"}}]}'
    dummy_llm = DummyLLM(llm_content)
    examples = [
        {"natural language": "", "sql": ""}
    ]
    monkeypatch.setattr("fabric.dataagent.evaluation._few_shot_validation.openai", dummy_llm)
    result = _evaluate_few_shot_examples(examples, "lakehouse")
    assert result.success_count == 0
    assert result.success_rate == 0.0


def test_evaluate_few_shot_examples_missing_nl_or_sql():
    # Missing 'natural language' key
    with pytest.raises(ValueError):
        _evaluate_few_shot_examples([{"sql": "SELECT 1;"}], "lakehouse")
    # Missing 'sql' key
    with pytest.raises(ValueError):
        _evaluate_few_shot_examples([{"natural language": "foo"}], "lakehouse")


def test_evaluate_few_shot_examples_large_batch(monkeypatch):
    # Simulate LLM response for large batch
    batch_size = 50
    llm_content = '{"evaluations": [' + ','.join([
        '{"example_id": %d, "reasoning": "ok", "quality": "yes", "reasoning_details": {"clarity": "yes", "mapping": "yes", "relatedness": "yes"}}' % (i+1)
        for i in range(batch_size)
    ]) + ']}'
    dummy_llm = DummyLLM(llm_content)
    examples = [
        {"natural language": f"Q{i}", "sql": f"SELECT {i};"} for i in range(batch_size)
    ]
    monkeypatch.setattr("fabric.dataagent.evaluation._few_shot_validation.openai", dummy_llm)
    result = _evaluate_few_shot_examples(examples, "lakehouse")
    assert result.success_count == batch_size
    assert result.success_rate == 100.0

def test__cases_to_dataframe_basic():
    cases = [
        {
            "example": {"natural language": "Q1", "sql": "SELECT 1;"},
            "quality": "yes",
            "reasoning": "Good",
            "reasoning_details": {"clarity": "yes", "mapping": "yes", "relatedness": "yes"}
        },
        {
            "example": {"natural language": "Q2", "sql": "SELECT 2;"},
            "quality": "no",
            "reasoning": "Bad",
            "reasoning_details": {"clarity": "no", "mapping": "no", "relatedness": "no"}
        }
    ]
    df = _cases_to_dataframe(cases)
    assert df.shape == (2, 7)
    assert df.iloc[0]["Few-shot question"] == "Q1"
    assert df.iloc[1]["Quality score"] == "no"
    assert df.iloc[1]["Clarity"] == "no"


def test__cases_to_dataframe_empty():
    df = _cases_to_dataframe([])
    assert df.empty


def test__cases_to_dataframe_missing_fields():
    cases = [
        {
            "example": {"natural language": "Q1", "sql": "SELECT 1;"},
            # missing quality, reasoning, reasoning_details
        }
    ]
    df = _cases_to_dataframe(cases)
    assert df.iloc[0]["Few-shot question"] == "Q1"
    assert df.iloc[0]["Quality score"] == ""


# ============= Conflict Detection Tests =============

def test__validate_confidence_valid_range():
    """Test confidence validation with valid 1-5 integer values."""
    assert _validate_confidence(1) == 1
    assert _validate_confidence(3) == 3
    assert _validate_confidence(5) == 5


def test__validate_confidence_out_of_range():
    """Test confidence validation with out-of-range values."""
    assert _validate_confidence(0) == 0  # Below range
    assert _validate_confidence(-1) == 0
    assert _validate_confidence(6) == 5  # Above range, capped
    assert _validate_confidence(10) == 5


def test__validate_confidence_string_input():
    """Test confidence validation with string inputs."""
    assert _validate_confidence("3") == 3
    assert _validate_confidence("5.0") == 5
    assert _validate_confidence("invalid") == 0


def test__validate_confidence_invalid_types():
    """Test confidence validation with invalid types."""
    assert _validate_confidence(None) == 0
    assert _validate_confidence([]) == 0
    assert _validate_confidence({}) == 0


def test_safe_parse_json_valid():
    """Test JSON parsing with valid JSON strings."""
    result = safe_parse_json('{"conflicts": []}', {})
    assert result == {"conflicts": []}
    
    result = safe_parse_json('{"key": "value"}', {})
    assert result == {"key": "value"}


def test_safe_parse_json_with_code_fences():
    """Test JSON parsing with markdown code fences."""
    result = safe_parse_json('```json\n{"conflicts": []}\n```', {})
    assert result == {"conflicts": []}
    
    result = safe_parse_json('```\n{"conflicts": []}\n```', {})
    assert result == {"conflicts": []}


def test_safe_parse_json_invalid():
    """Test JSON parsing with invalid JSON."""
    fallback = {"error": "fallback"}
    result = safe_parse_json('not valid json', fallback)
    assert result == fallback
    
    result = safe_parse_json('{incomplete', fallback)
    assert result == fallback


def test_safe_parse_json_non_string():
    """Test JSON parsing with non-string input."""
    fallback = {"error": "fallback"}
    result = safe_parse_json(None, fallback)
    assert result == fallback
    
    result = safe_parse_json(123, fallback)
    assert result == fallback


def test__filter_conflicts_basic():
    """Test basic conflict filtering with valid conflicts."""
    conflicts = [
        {"examples": [1, 2], "description": "Conflict A", "confidence": 3},
        {"examples": [3, 4], "description": "Conflict B", "confidence": 5},
    ]
    result = _filter_conflicts(conflicts, min_confidence=0)
    assert len(result) == 2
    assert result[0]["examples"] == [1, 2]
    assert result[1]["examples"] == [3, 4]


def test__filter_conflicts_confidence_threshold():
    """Test conflict filtering with confidence threshold."""
    conflicts = [
        {"examples": [1, 2], "description": "Low confidence", "confidence": 2},
        {"examples": [3, 4], "description": "High confidence", "confidence": 5},
        {"examples": [5, 6], "description": "Medium confidence", "confidence": 3},
    ]
    result = _filter_conflicts(conflicts, min_confidence=3)
    assert len(result) == 2
    assert result[0]["confidence"] == 5
    assert result[1]["confidence"] == 3


def test__filter_conflicts_removes_single_example():
    """Test that conflicts with single example are filtered out."""
    conflicts = [
        {"examples": [1], "description": "Single example", "confidence": 5},
        {"examples": [1, 2], "description": "Valid conflict", "confidence": 5},
    ]
    result = _filter_conflicts(conflicts, min_confidence=0)
    assert len(result) == 1
    assert result[0]["examples"] == [1, 2]


def test__filter_conflicts_deduplicates_indices():
    """Test that duplicate indices in conflicts are removed."""
    conflicts = [
        {"examples": [1, 2, 2, 1], "description": "Duplicates", "confidence": 3},
    ]
    result = _filter_conflicts(conflicts, min_confidence=0)
    assert len(result) == 1
    assert result[0]["examples"] == [1, 2]


def test__filter_conflicts_invalid_input():
    """Test conflict filtering with invalid inputs."""
    assert _filter_conflicts(None) == []
    assert _filter_conflicts("not a list") == []
    assert _filter_conflicts([]) == []


def test__filter_conflicts_invalid_structure():
    """Test conflict filtering with malformed conflict structures."""
    conflicts = [
        "not a dict",
        {"no_examples_key": [1, 2]},
        {"examples": "not a list", "confidence": 3},
        {"examples": [], "confidence": 3},  # Empty examples list
    ]
    result = _filter_conflicts(conflicts, min_confidence=0)
    assert len(result) == 0


def test_detect_conflicts_no_conflicts(monkeypatch):
    """Test conflict detection when no conflicts exist."""
    llm_content = '{"conflicts": []}'
    dummy_llm = DummyLLM(llm_content)
    
    examples = [
        {"natural language": "Q1", "sql": "SELECT 1;", "_original_index": 1},
        {"natural language": "Q2", "sql": "SELECT 2;", "_original_index": 2},
    ]
    
    result, completion_tokens = _detect_conflicts_between_examples(examples, dummy_llm, "dummy")
    parsed = safe_parse_json(result, {"conflicts": []})
    assert parsed["conflicts"] == []
    assert completion_tokens is None  # DummyLLM doesn't provide usage info


def test_detect_conflicts_with_conflicts(monkeypatch):
    """Test conflict detection when conflicts are found."""
    llm_content = '{"conflicts": [{"examples": [1, 2], "description": "Same intent, different SQL", "confidence": 5}]}'
    dummy_llm = DummyLLM(llm_content)
    
    examples = [
        {"natural language": "Q1", "sql": "SELECT SUM(x);", "_original_index": 1},
        {"natural language": "Q1", "sql": "SELECT COUNT(x);", "_original_index": 2},
    ]
    
    result, completion_tokens = _detect_conflicts_between_examples(examples, dummy_llm, "dummy")
    parsed = safe_parse_json(result, {"conflicts": []})
    assert len(parsed["conflicts"]) == 1
    assert parsed["conflicts"][0]["examples"] == [1, 2]
    assert parsed["conflicts"][0]["confidence"] == 5
    assert completion_tokens is None  # DummyLLM doesn't provide usage info


def test__get_conflict_details_basic():
    """Test expanding conflicts into detailed per-example rows."""
    conflict_analysis = {
        "conflicts": [
            {
                "examples": [1, 2],
                "description": "Test conflict",
                "confidence": 4
            }
        ]
    }
    examples = [
        {"natural language": "Q1", "sql": "SELECT 1;"},
        {"natural language": "Q2", "sql": "SELECT 2;"},
    ]
    
    details = _get_conflict_details(conflict_analysis, examples, "Test Dataset")
    assert len(details) == 2
    assert details[0]["Dataset"] == "Test Dataset"
    assert details[0]["Example Number"] == 1
    assert details[0]["Question"] == "Q1"
    assert details[1]["Example Number"] == 2
    assert details[1]["Confidence"] == 4
    assert details[1]["Confidence Level"] == "Medium"


def test__get_conflict_details_confidence_levels():
    """Test that confidence levels are correctly assigned."""
    conflict_analysis = {
        "conflicts": [
            {"examples": [1], "description": "High", "confidence": 5},
            {"examples": [2], "description": "Medium", "confidence": 4},
            {"examples": [3], "description": "Low", "confidence": 3},
            {"examples": [4], "description": "Very Low", "confidence": 2},
            {"examples": [5], "description": "Speculative", "confidence": 1},
        ]
    }
    examples = [
        {"natural language": f"Q{i}", "sql": f"SELECT {i};"} for i in range(1, 6)
    ]
    
    details = _get_conflict_details(conflict_analysis, examples, "Test")
    assert details[0]["Confidence Level"] == "High"
    assert details[1]["Confidence Level"] == "Medium"
    assert details[2]["Confidence Level"] == "Low"
    assert details[3]["Confidence Level"] == "Very Low"
    assert details[4]["Confidence Level"] == "Speculative"


def test__get_conflict_details_invalid_indices():
    """Test that invalid or out-of-range indices are skipped."""
    conflict_analysis = {
        "conflicts": [
            {
                "examples": [1, 99],  # 99 is out of range
                "description": "Invalid index",
                "confidence": 3
            }
        ]
    }
    examples = [
        {"natural language": "Q1", "sql": "SELECT 1;"},
    ]
    
    details = _get_conflict_details(conflict_analysis, examples, "Test")
    assert len(details) == 1
    assert details[0]["Example Number"] == 1


def test__get_conflict_details_empty_conflicts():
    """Test conflict details with no conflicts."""
    conflict_analysis = {"conflicts": []}
    examples = [{"natural language": "Q1", "sql": "SELECT 1;"}]
    
    details = _get_conflict_details(conflict_analysis, examples, "Test")
    assert details == []


def test_evaluate_few_shot_examples_with_conflicts(monkeypatch):
    """Test that evaluate_few_shot_examples includes conflict analysis."""
    quality_response = '{"evaluations": [{"example_id": 1, "reasoning": "Good", "quality": "yes", "reasoning_details": {"clarity": "yes", "mapping": "yes", "relatedness": "yes"}}, {"example_id": 2, "reasoning": "Good", "quality": "yes", "reasoning_details": {"clarity": "yes", "mapping": "yes", "relatedness": "yes"}}]}'
    conflict_response = '{"conflicts": [{"examples": [1, 2], "description": "Conflict", "confidence": 4}]}'
    
    # Create a mock that returns different responses based on call order
    call_count = [0]
    def create_mock(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            return DummyResponse(quality_response)
        else:
            return DummyResponse(conflict_response)
    
    dummy_llm = type("DummyLLM", (), {
        "chat": type("Chat", (), {
            "completions": type("Comp", (), {
                "create": create_mock
            })()
        })()
    })()
    
    examples = [
        {"natural language": "Q1", "sql": "SELECT SUM(x);"},
        {"natural language": "Q1 rephrased", "sql": "SELECT COUNT(x);"},
    ]
    
    monkeypatch.setattr("fabric.dataagent.evaluation._few_shot_validation.openai", dummy_llm)
    result = _evaluate_few_shot_examples(examples, "lakehouse")
    assert result.success_count == 2
    assert "conflict_analysis" in result._asdict()
    assert "conflicts" in result.conflict_analysis
    assert len(result.conflict_analysis["conflicts"]) == 1


def test_conflict_filtering_in_evaluate(monkeypatch):
    """Test that invalid conflict indices are filtered during evaluation."""
    quality_response = '{"evaluations": [{"example_id": 1, "reasoning": "Good", "quality": "yes", "reasoning_details": {"clarity": "yes", "mapping": "yes", "relatedness": "yes"}}, {"example_id": 2, "reasoning": "Bad", "quality": "no", "reasoning_details": {"clarity": "no", "mapping": "no", "relatedness": "no"}}]}'
    # Conflict references example 2, which was rejected
    conflict_response = '{"conflicts": [{"examples": [1, 2], "description": "Invalid", "confidence": 3}]}'
    
    call_count = [0]
    def create_mock(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            return DummyResponse(quality_response)
        else:
            return DummyResponse(conflict_response)
    
    dummy_llm = type("DummyLLM", (), {
        "chat": type("Chat", (), {
            "completions": type("Comp", (), {
                "create": create_mock
            })()
        })()
    })()
    
    examples = [
        {"natural language": "Q1", "sql": "SELECT 1;"},
        {"natural language": "Q2", "sql": "SELECT 2;"},
    ]
    
    monkeypatch.setattr("fabric.dataagent.evaluation._few_shot_validation.openai", dummy_llm)
    result = _evaluate_few_shot_examples(examples, "lakehouse")
    # Example 2 was rejected, so it shouldn't be in approved set
    # The conflict should be filtered out because example 2 is not approved
    assert result.success_count == 1
    assert len(result.conflict_analysis["conflicts"]) == 0


def test_datasource_evaluate_few_shots_type_mapping():
    """Test that Datasource.evaluate_few_shots correctly maps internal types to external types."""
    from unittest.mock import MagicMock, patch
    from fabric.dataagent.client._fabric_data_agent_mgmt import Datasource
    from fabric.dataagent.client._fabric_data_agent_api import FabricDataAgentAPI
    from fabric.dataagent.client._tagged_value import TaggedValue
    
    # Create mock client and datasource
    mock_client = MagicMock(spec=FabricDataAgentAPI)
    datasource = Datasource(mock_client, "test_datasource_id")
    
    # Mock the datasource configuration with internal type "lakehouse_tables"
    mock_client.get_datasource.return_value = TaggedValue(
        {"type": "lakehouse_tables"}, "etag"
    )
    
    # Mock the few-shots
    mock_client.get_datasource_fewshots.return_value = TaggedValue(
        {
            "fewShots": [
                {
                    "id": "1",
                    "question": "What is the sum of sales?",
                    "query": "SELECT SUM(sales) FROM table;",
                    "state": "Approved",
                    "embedding": None,
                }
            ]
        },
        "etag",
    )
    
    # Mock the _evaluate_few_shot_examples function to verify correct type is passed
    with patch('fabric.dataagent.evaluation._few_shot_validation._evaluate_few_shot_examples') as mock_eval:
        mock_eval.return_value = MagicMock(
            success_cases=[],
            failure_cases=[],
            conflict_analysis=MagicMock(conflicted_indices=[])
        )
        
        datasource.evaluate_few_shots()
        
        # Verify that the external type "lakehouse" was passed, not "lakehouse_tables"
        call_args = mock_eval.call_args
        assert call_args[1]['datasource_type'] == "lakehouse"


def test_datasource_evaluate_few_shots_warehouse_type_mapping():
    """Test that Datasource.evaluate_few_shots correctly maps data_warehouse to warehouse."""
    from unittest.mock import MagicMock, patch
    from fabric.dataagent.client._fabric_data_agent_mgmt import Datasource
    from fabric.dataagent.client._fabric_data_agent_api import FabricDataAgentAPI
    from fabric.dataagent.client._tagged_value import TaggedValue
    
    # Create mock client and datasource
    mock_client = MagicMock(spec=FabricDataAgentAPI)
    datasource = Datasource(mock_client, "test_datasource_id")
    
    # Mock the datasource configuration with internal warehouse type "data_warehouse"
    mock_client.get_datasource.return_value = TaggedValue(
        {"type": "data_warehouse"}, "etag"
    )
    
    # Mock the few-shots
    mock_client.get_datasource_fewshots.return_value = TaggedValue(
        {
            "fewShots": [
                {
                    "id": "1",
                    "question": "How many users?",
                    "query": "SELECT COUNT(*) FROM users;",
                    "state": "Approved",
                    "embedding": None,
                }
            ]
        },
        "etag",
    )
    
    # Mock the _evaluate_few_shot_examples function
    with patch('fabric.dataagent.evaluation._few_shot_validation._evaluate_few_shot_examples') as mock_eval:
        mock_eval.return_value = MagicMock(
            success_cases=[],
            failure_cases=[],
            conflict_analysis=MagicMock(conflicted_indices=[])
        )
        
        datasource.evaluate_few_shots()
        
        # Verify that the external type "warehouse" was passed, not "data_warehouse"
        call_args = mock_eval.call_args
        assert call_args[1]['datasource_type'] == "warehouse"


def test_datasource_evaluate_few_shots_unsupported_type():
    """Test that evaluate_few_shots raises error for unsupported datasource types."""
    from unittest.mock import MagicMock
    from fabric.dataagent.client._fabric_data_agent_mgmt import Datasource
    from fabric.dataagent.client._fabric_data_agent_api import FabricDataAgentAPI
    from fabric.dataagent.client._tagged_value import TaggedValue
    
    # Create mock client and datasource
    mock_client = MagicMock(spec=FabricDataAgentAPI)
    datasource = Datasource(mock_client, "test_datasource_id")
    
    # Mock the datasource configuration with unsupported type
    mock_client.get_datasource.return_value = TaggedValue(
        {"type": "semantic_model"}, "etag"
    )
    
    # Mock the few-shots
    mock_client.get_datasource_fewshots.return_value = TaggedValue(
        {
            "fewShots": [
                {
                    "id": "1",
                    "question": "Test question",
                    "query": "Test query",
                    "state": "Approved",
                    "embedding": None,
                }
            ]
        },
        "etag",
    )
    
    # Should raise ValueError for unsupported type
    with pytest.raises(ValueError, match="Few-shot evaluation is only supported for SQL datasources"):
        datasource.evaluate_few_shots()


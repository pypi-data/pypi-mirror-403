from ._fabric_data_agent_api import FabricDataAgentAPI
from ._tagged_value import TaggedValue
from sempy.fabric.exceptions import FabricHTTPException

from uuid import uuid4

import logging
import pandas as pd
import time
import typing as t
import warnings


# The list of selectable element types (e.g. columns, measures are not selectable since the UX doesn't support it)
SELECTABLE_ELEMENT_TYPES = [
    "semantic_model.table",
    "lakehouse_tables.table",
    "warehouse_tables.table",
    "kusto.table",
]

# The list of datasource types that allow configuration updates
CONFIGURABLE_DATASOURCE_TYPES = [
    "lakehouse_tables",
    "data_warehouse",
    "kusto",
]

# The list of datasource types that allow table/column description
DESCRIPTION_ENABLED_DATASOURCE_TYPES = [
    "lakehouse_tables",
    "data_warehouse",
]

# The list of element types that allow table/column description
DESCRIPTION_ENABLED_ELEMENT_TYPES = [
    "lakehouse_tables.table",
    "warehouse_tables.table",
    "lakehouse_tables.column",
    "warehouse_tables.column",
]


class Datasource:
    """
    Represents a datasource within an DataAgent.

    Attributes
    ----------
    _client : FabricDataAgentAPI
        The FabricDataAgentAPI client instance.
    _id : str
        The unique identifier of the datasource.
    """

    _client: FabricDataAgentAPI
    _id: str

    def __init__(self, client: FabricDataAgentAPI, id: str) -> None:
        """
        Initialize a Datasource instance.

        Parameters
        ----------
        client : FabricDataAgentAPI
            The FabricDataAgentAPI client to interact with the datasource.
        id : str
            The unique identifier of the datasource.
        """
        self._client = client
        self._id = id

    def __repr__(self):
        """
        Return a string representation of the Datasource.

        Returns
        -------
        str
            The string representation including the datasource ID.
        """
        return f"Datasource({self._id})"

    def pretty_print(self, include_type: t.Optional[bool] = False) -> None:
        """
        Pretty print the datasource configuration.

        Parameters
        ----------
        include_type : bool, optional
            Whether to include the type of the element in the output. Defaults to False.
        """
        config = self._client.get_datasource(self._id)

        def render_children(elements, level):
            if elements is None or len(elements) == 0:
                return

            indent = ' ' * 2

            for elem in elements:
                msg = f"{indent}|" * level + f' {elem["display_name"]}'

                if include_type:
                    msg += f' ({elem["type"]})'

                if elem.get("type") in SELECTABLE_ELEMENT_TYPES and elem["is_selected"]:
                    msg += " *"

                print(msg)
                render_children(elem["children"], level + 1)

        render_children(config.value.get("elements", []), 0)
        return config.value['display_name']

    def get_fewshots(self) -> pd.DataFrame:
        """
        Get the fewshots for the datasource.

        Returns
        -------
        pd.DataFrame
            A DataFrame containing the fewshots (Id, Question, Query, State, Embedding).
        """
        data = self._client.get_datasource_fewshots(self._id)

        return pd.DataFrame(
            [
                {
                    "Id": f["id"],
                    "Question": f["question"],
                    "Query": f["query"],
                    "State": f["state"],
                    "Embedding": f["embedding"],
                }
                for f in data.value.get("fewShots", [])
            ],
            columns=["Id", "Question", "Query", "State", "Embedding"],
        )

    def _get_normalized_fewshots(self) -> list[dict[str, str]]:
        """
        Internal utility to fetch few-shots and normalize them to NL/SQL pairs for evaluators.

        Returns
        -------
        list[dict[str, str]]
            Each item has keys: "natural language" and "sql".
        """
        # NOTE: Compatibility adapter
        # This method intentionally aligns with current product UI outputs
        # (legacy "fewShots" with "Question"/"Query" entries and dict exports).
        # If/when the API standardizes on a single schema (e.g., "fewshots" with
        # "natural_language"/"sql"), we can simplify this method to pass-through
        # or adjust mapping accordingly.
        data = self._client.get_datasource_fewshots(self._id)
        payload = data.value or {}

        # Adapter aligned to current product UI outputs:
        # - Primary: payload["fewShots"] list of dicts with "Question"/"Query"
        # - Fallback: dict mapping Question -> Query (export/import)
        items = []
        if isinstance(payload, dict):
            items = payload.get("fewShots") or []

        normalized: list[dict[str, str]] = []
        for item in items if isinstance(items, list) else []:
            if not isinstance(item, dict):
                continue
            nl = item.get("Question") or item.get("question")
            sql = item.get("Query") or item.get("query")
            if isinstance(nl, str) and isinstance(sql, str):
                normalized.append({"natural language": nl, "sql": sql})

        # Fallback: dict mapping NL->SQL
        if not normalized and isinstance(payload, dict):
            for k, v in payload.items():
                if isinstance(k, str) and isinstance(v, str):
                    normalized.append({"natural language": k, "sql": v})

        return normalized

    def evaluate_few_shots(self, batch_size: int = 10):
        """
        Evaluate the quality and detect conflicts in few-shot examples for this datasource.
        
        This method uses an LLM to assess example quality and detect potential conflicts
        between examples. It is only supported for SQL datasources (lakehouse, warehouse).
        
        All results are returned as pandas DataFrames for easy analysis and visualization.
        
        NOTE: The datasource must have few-shot examples added to it (via add_fewshots() or
        through the Fabric UI) before calling this method.
        
        Parameters
        ----------
        batch_size : int, optional
            Number of examples to evaluate per batch. Default is 10.
        
        Returns
        -------
        FewShotEvaluation
            Dataclass containing:
            - quality_results: DataFrame with all examples and quality scores
            - success_cases: DataFrame with only successful examples
            - failure_cases: DataFrame with only failed examples
            - conflict_details: DataFrame with detailed conflict analysis
            - success_rate: Percentage of successful examples (0.0-100.0)
            - total_examples: Total number of examples evaluated
            - success_count: Number of successful examples
            - conflict_count: Number of conflicts detected
        
        Raises
        ------
        ValueError
            If the datasource type is not supported for few-shot evaluation, or if
            no examples are found in the datasource.
        
        Example
        -------
        >>> datasource = agent.get_datasource(datasource_id)
        >>> result = datasource.evaluate_few_shots()
        >>> 
        >>> # Display quality results
        >>> display(result.quality_results)
        >>> print(f"Success rate: {result.success_rate:.1%}")
        >>> 
        >>> # Display conflicts
        >>> display(result.conflict_details)
        >>> print(f"Found {result.conflict_count} conflicts")
        >>> 
        >>> # Analyze failures
        >>> display(result.failure_cases)
        """
        from ..evaluation._few_shot_validation import _evaluate_few_shot_examples, _cases_to_dataframe, _get_conflict_details
        from ..evaluation._models import FewShotEvaluation
        
        # Get datasource configuration and examples
        config = self.get_configuration()
        internal_type = config.get("type")
        examples = self._get_normalized_fewshots()
        
        if not examples:
            raise ValueError("No few-shot examples found in datasource. Add examples using add_fewshots() or through the Fabric UI.")
        
        # Map internal type to external Fabric API type for validation
        # This mapping aligns with what users specify in add_datasource()
        # Unmapped types will be passed through and caught by validation in _evaluate_few_shot_examples
        type_mapping = {
            "lakehouse_tables": "lakehouse",
            "data_warehouse": "warehouse",
        }
        datasource_type = type_mapping.get(internal_type, internal_type)
        
        # Call the internal utility function with primitives
        result = _evaluate_few_shot_examples(
            examples=examples,
            datasource_type=datasource_type,
            batch_size=batch_size
        )
        
        # Convert to DataFrames
        quality_results_df = _cases_to_dataframe(result.success_cases + result.failure_cases)
        success_cases_df = _cases_to_dataframe(result.success_cases)
        failure_cases_df = _cases_to_dataframe(result.failure_cases)
        
        # Get conflict details as DataFrame
        conflict_details_list = _get_conflict_details(
            result.conflict_analysis,
            examples,
            dataset_name=config.get("display_name", "Unknown")
        )
        conflict_details_df = pd.DataFrame(conflict_details_list)
        
        # Count conflicts
        conflict_count = len(result.conflict_analysis.get("conflicts", []))
        
        # Return user-friendly dataclass
        return FewShotEvaluation(
            quality_results=quality_results_df,
            success_cases=success_cases_df,
            failure_cases=failure_cases_df,
            conflict_details=conflict_details_df,
            success_rate=result.success_rate,
            total_examples=result.total,
            success_count=result.success_count,
            conflict_count=conflict_count
        )

    def add_fewshots(self, fewshots: dict) -> None:
        """
        Add fewshots to the datasource.

        Parameters
        ----------
        fewshots : dict
            The dictionary of question and query.
        """
        datasource_fewshots = self._client.get_datasource_fewshots(self._id)

        data = datasource_fewshots.value.get("fewShots", [])

        for question, query in fewshots.items():
            data.append(
                {
                    "Id": str(uuid4()),
                    "Index": len(data),
                    "Question": question,
                    "Query": query,
                }
            )

        parentId = datasource_fewshots.value.get("parentId")
        if not parentId:
            datasource_fewshots.value["parentId"] = self._id

        datasource_fewshots.value["fewShots"] = data

        self._client.set_datasource_fewshots(self._id, datasource_fewshots)

    def remove_fewshot(self, fewshot_id: str) -> None:
        """
        Remove a fewshot from the datasource.

        Parameters
        ----------
        fewshot_id : str
            The ID of the fewshot to remove.
        """
        fewshots = self._client.get_datasource_fewshots(self._id)

        data = fewshots.value.get("fewShots", [])

        # remove the fewshot
        data = [f for f in data if f["id"] != fewshot_id]

        fewshots.value["fewShots"] = data

        self._client.set_datasource_fewshots(self._id, fewshots)

    def get_configuration(self) -> dict:
        """
        Get the configuration of the datasource.

        Returns
        -------
        dict
            The configuration of the datasource.
        """
        return self._client.get_datasource(self._id).value

    def update_configuration(
        self,
        instructions: str | None = None,
        schema_mode: str | None = None,
        user_description: str | None = None,
    ) -> None:
        """
        Update the configuration of the datasource.

        Parameters
        ----------
        instructions : str, optional
            Additional instructions for the datasource.
        schema_mode : str, optional
            The schema mode.
        user_description : str, optional
            The user description.
        """
        config = self._client.get_datasource(self._id)
        datasource_type = config.value.get("type")

        if datasource_type not in CONFIGURABLE_DATASOURCE_TYPES:
            raise ValueError(
                f"Datasource type '{datasource_type}' does not support configuration updates. Only {CONFIGURABLE_DATASOURCE_TYPES} are supported."
            )

        if instructions:
            config.value["additional_instructions"] = instructions

        if schema_mode:
            config.value["schema_mode"] = schema_mode

        if user_description:
            config.value["user_description"] = user_description

        self._client.set_datasource(config)

    def _set_is_selected(self, selected: bool, *path: t.Union[str, t.List[str]]) -> TaggedValue:
        """
        Set the selection status of a specific path in the datasource.

        Parameters
        ----------
        selected : bool
            The selection status to set.
        *path : str
            The path to set the selection status for.

        Returns
        -------
        TaggedValue
            The updated configuration.
        """
        config = self._client.get_datasource(self._id)

        # recursive function to set the selection status
        def recurse(l_path: t.List[str], elements: t.List[dict] | None):
            if l_path is None or len(l_path) == 0 or elements is None:
                return

            for elem in elements:
                if elem["display_name"] == l_path[0]:
                    if len(l_path) == 1:
                        elem_type = elem.get("type")
                        if elem_type not in SELECTABLE_ELEMENT_TYPES:
                            raise ValueError(f"Only table elements can be selected: '{elem_type}'")

                        elem["is_selected"] = selected
                    else:
                        recurse(l_path[1:], elem["children"])

                    return

            warnings.warn(f"Path {path} not found in datasource")

        elements = config.value.get("elements")

        if isinstance(path[0], list):
            for p in path:
                recurse(t.cast(t.List[str], p), elements)
        else:
            recurse(list(t.cast(t.Tuple[str, ...], path)), elements)

        return config

    def _set_is_selected_all(self, selected: bool) -> TaggedValue:
        """
        Set the selection status for all elements in the datasource.

        Parameters
        ----------
        selected : bool
            The selection status to set.

        Returns
        -------
        TaggedValue
            The updated configuration.
        """
        config = self._client.get_datasource(self._id)

        def set_selected(elements):
            for elem in elements:
                if elem.get("type") in SELECTABLE_ELEMENT_TYPES:
                    elem["is_selected"] = selected

                set_selected(elem["children"])

        set_selected(config.value["elements"])

        return config

    def _select(self, is_selected: bool, *path: t.Union[str, t.List[str]]) -> None:
        """
        Select or unselect elements in the datasource.

        Parameters
        ----------
        is_selected : bool
            Whether to select or unselect the elements.
        *path : str
            The path to select or unselect. e.g. self._select(True, "dbo", "table1", "col1").
        """
        if len(path) == 0:
            config = self._set_is_selected_all(is_selected)
        else:
            config = self._set_is_selected(is_selected, *path)

        self._client.set_datasource(config)

    def select(self, *path: t.Union[str, t.List[str]]) -> None:
        """
        Select elements in the datasource.

        Parameters
        ----------
        *path : str
            The path to select.
        """
        self._select(True, *path)

    def unselect(self, *path: t.Union[str, t.List[str]]) -> None:
        """
        Unselect elements in the datasource.

        Parameters
        ----------
        *path : str
            The path to unselect.
        """
        self._select(False, *path)

    def update_description(
        self,
        descriptions_by_path: dict[tuple[str, ...], str | None],
    ) -> None:
        """
        Update the description of the tables and columns in the datasource.

        Parameters
        ----------
        descriptions_by_path : dict[tuple[str, ...], str | None]
            A dictionary where the key is a tuple of strings representing the path to the element
            and the value is the description to set. e.g. self.update_description({("dbo", "table1", "col1"): "col1 description"}).
        """

        config = self._client.get_datasource(self._id)
        datasource_type = config.value.get("type")

        if datasource_type not in DESCRIPTION_ENABLED_DATASOURCE_TYPES:
            raise ValueError(
                f"Datasource type '{datasource_type}' does not support description updates. Only {DESCRIPTION_ENABLED_DATASOURCE_TYPES} are supported."
            )

        for path, description in descriptions_by_path.items():
            elements = config.value.get("elements", [])
            current = elements
            target_element = None
            for name in path:
                found = False
                for candidate in current:
                    if candidate["display_name"] == name:
                        target_element = candidate
                        current = candidate.get("children", [])
                        found = True
                        break
                if not found:
                    raise ValueError(f"Path {path} not found in datasource")

            if target_element is not None:
                if target_element.get("type") not in DESCRIPTION_ENABLED_ELEMENT_TYPES:
                    raise ValueError(
                        f"Only table and column elements can have descriptions: '{target_element.get('type')}'"
                    )
                target_element["description"] = description

        self._client.set_datasource(config)

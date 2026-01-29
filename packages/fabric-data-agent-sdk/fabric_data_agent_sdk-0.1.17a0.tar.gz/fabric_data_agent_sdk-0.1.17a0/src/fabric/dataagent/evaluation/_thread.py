"""
Functions for handling thread and message interactions with the data agent.
"""
import json
import logging
import re
import pandas as pd
from openai import NotFoundError
from openai.types.beta.threads import FilePathAnnotation, TextContentBlock
from typing import Any, Iterable, List, Optional
from fabric.dataagent.client import FabricOpenAI, FabricDataAgentManagement
from fabric.dataagent.evaluation._models import CommandOutput, RunSteps, RunResult


# Constants
OPEN_AI_MODEL = "gpt-4o"
USER_ROLE = "user"
SPARK_HOST = "spark.trident.pbiHost"
TOP_N_JSON_ROWS = 25
DEEPLINK_STAGE_MAP = {
    "sandbox": "draft",
    "production": "published",
}

def _get_annotations(content):
    annotations = []
    if isinstance(content, TextContentBlock):
        for annotation in content.text.annotations:
            if isinstance(annotation, FilePathAnnotation):
                annotations.append(annotation)
    return annotations

def _get_file_head(fabric_client: FabricOpenAI, file_id: str):
    text_file_extensions = {".txt", ".md", ".csv", ".json", ".log"}

    file_info = fabric_client.files.retrieve(file_id)
    file_name = file_info.filename
    file_extension = (
        file_name[file_name.rfind(".") :].lower() if "." in file_name else ""
    )

    if file_extension not in text_file_extensions:
        return ""
    file_content = fabric_client.files.content(file_id)

    if file_extension == ".json":
        return _process_json(file_content, top_n=TOP_N_JSON_ROWS)
    
    try:
        head_str = next(file_content.iter_text(1024 * 4))
    except StopIteration:
        head_str = ""
    return head_str

def _process_json(file_content: Any, top_n: int = 25) -> str:
    """
    Read JSON from an OpenAI file_content-like object and return a markdown string
    describing the top `top_n` rows.

    The JSON is expected to look like:
        {
          "columns": [{"name": "...", "data_type": "..."}, ...],
          "rows": [
            [...],
            [...],
            ...
          ]
        }

    :param file_content: Object with a .read() method returning bytes (e.g. client.files.content(file_id))
    :param top_n: Number of rows to include.
    :return: string.
    """
    data = json.loads(file_content.read().decode("utf-8"))

    columns = [c["name"] for c in data["columns"]]
    df = pd.DataFrame(data["rows"], columns=columns)

    return df.head(top_n).to_markdown(index=False)

def _get_message(fabric_client: FabricOpenAI, thread_id: str, query: str):
    """
    Get message for the input query and thread.

    Parameters
    ----------
    fabric_client: FabricOpenAI
        An instance of the fabric client created to interact with Data Agent.
    thread_id: str
        An unique identifier of the thread.
    query : str
        Question from the input DataFrame.

    Returns
    -------
    tuple[str, object]
        Tuple with actual answer and run instance.

    Raises
    -------
        RuntimeError: If fabric client is None.
    """

    import os

    # Raise RuntimeError if fabric client is None
    if fabric_client is None:
        logging.debug("Fabric client is None")
        raise RuntimeError("Fabric client is None")

    message_ids = []

    try:
        # Create assistant
        assistant = fabric_client.beta.assistants.create(model=OPEN_AI_MODEL)

        # Add message to the thread
        fabric_client.beta.threads.messages.create(
            thread_id=thread_id, role=USER_ROLE, content=query
        )

        try:
            # Start the run
            run = fabric_client.beta.threads.runs.create_and_poll(
                thread_id=thread_id, assistant_id=assistant.id
            )
        except NotFoundError:
            raise ValueError("Invalid input for data_agent_stage. Please use sandbox/draft if DataAgent is not published.")
        except Exception as e:
            # Handle other errors
            logging.error(f"Error in create_and_poll: {str(e)}")
            return f"Error: {str(e)}", RunResult(status="failed"), message_ids

        status = run.status
        # Log error message if status is failed
        if status == "failed" and hasattr(run, 'last_error') and run.last_error:
            generated_answer = f"Error ({run.last_error.code}): {run.last_error.message}"
            message_ids = []
            logging.debug(generated_answer)
        else:
            try:
                # Get the messages from response
                messages = fabric_client.beta.threads.messages.list(
                    thread_id=thread_id
                )
                run_assistant_messages = [m for m in messages.data if m.run_id == run.id and m.role == "assistant"]
                messages_list = sorted(run_assistant_messages,key=lambda m: (m.created_at, m.id))
                if messages_list:
                    generated_answers = []
                    for message in messages_list:
                        if hasattr(message, 'content') and len(message.content) > 0 and hasattr(message.content[0], 'text'):
                            generated_answers.append(message.content[0].text.value)
                            content = message.content[0]
                            annotations = _get_annotations(content)
                            for annotation in annotations:
                                generated_answers.append(_get_file_head(fabric_client, annotation.file_path.file_id))
                    generated_answer = "\n\n".join(generated_answers)
                    message_ids = [m.id for m in messages_list]
                else:
                    generated_answer = "No answer returned from Data Agent"
                    message_ids = []
            except Exception as e:
                logging.error(f"Error retrieving message: {str(e)}")
                generated_answer = f"Error retrieving message: {str(e)}"
                message_ids = []
    except Exception as e:
        logging.error(f"Unexpected error in _get_message: {str(e)}")
        generated_answer = f"Unexpected error: {str(e)}"
        message_ids = []
        run = RunResult(status="failed")

    return generated_answer, run, message_ids


def _get_message_url(thread_id: str, run_id: str, message_id: str, stage: str, data_agent: FabricDataAgentManagement) -> Optional[str]:
    """
    Get message URL for the message.

    Parameters
    ----------
    thread_id : str
        An unique identifier of the thread.
    message_id : str
        An unique identifier of the message.
    run_id : str
        An unique identifier of the run.
    data_agent : FabricDataAgentManagement
        An instance of FabricDataAgentManagement to get the details of the Data Agent.

    Returns
    -------
    Optional[str]
        Message URL for the input message id, or None if message_id is empty.
    """
    if not message_id:
        return None
    stage = DEEPLINK_STAGE_MAP.get(stage.lower(), "draft")

    host = _get_fabric_host()
    data_agent_workspace = data_agent._client.workspace_id
    data_agent_id = data_agent._client.data_agent_id

    message_url = f"https://{host}/groups/{data_agent_workspace}/aiskills/{data_agent_id}/stage/{stage}/threads/{thread_id}/runs/{run_id}/question/{message_id}/source/any?debug.dataAgentDeepLinks=1"
    return message_url


def _get_steps(
    fabric_client: FabricOpenAI, thread_id: str, run_id: str, unique_id: Optional[str] = None
) -> RunSteps:
    """
    Get steps for the run.

    Parameters
    ----------
    fabric_client : FabricOpenAI
        An instance of the fabric client created to interact with Data Agent.
    thread_id : str
        An unique identifier of the thread.
    run_id : str
        An unique identifier of the run.
    unique_id : str
        An unique identifier for the input processing row.

    Returns
    -------
    RunSteps
        Run steps in the Data Agent response.

    Raises
    -------
        RuntimeError: If fabric client is None.
    """

    # Raise RuntimeError if fabric client is None
    if fabric_client is None:
        logging.debug("Fabric client is None")
        raise RuntimeError("Fabric client is None")

    function_names = []
    function_queries = []
    function_outputs = []
    sql_commands = []
    dax_commands = []
    kql_commands = []

    # Get run steps for a thread
    try:
        run_steps = fabric_client.beta.threads.runs.steps.list(
            thread_id=thread_id, run_id=run_id
        )

        # Extract list of run steps
        for run_step in run_steps:
            if run_step.step_details.type == "tool_calls":
                for tool_call in run_step.step_details.tool_calls:
                    if tool_call.type == "function":
                        function_names.append(str(tool_call.function.name))
                        try:
                            arguments = json.loads(tool_call.function.arguments)
                            # Convert to json dict if arguments is not dict
                            if not isinstance(arguments, dict):
                                arguments = json.loads(arguments)
                            # Check if arguments is dict to get the params or save arguments as function query
                            if isinstance(arguments, dict):
                                query = arguments.get("query") or arguments.get("natural_language_query")
                            else:
                                query = arguments
                            function_queries.append(str(query))
                        except Exception:
                            # If JSON parsing fails, store the raw arguments
                            function_queries.append(str(tool_call.function.arguments))
                        
                        function_output = tool_call.function.output
                        function_outputs.append(str(function_output))
                        commands = _get_commands(function_output)
                        sql_commands.append(str(commands.sql))
                        dax_commands.append(str(commands.dax))
                        kql_commands.append(str(commands.kql))
    except Exception:
        # If there's an error getting run steps, return a minimal object
        logging.warning(f"Error getting run steps for thread {thread_id}, run {run_id}")

    return RunSteps(
        id=unique_id,
        thread_id=thread_id,
        run_id=run_id,
        function_names=str(function_names),
        function_queries=str(function_queries),
        function_outputs=str(function_outputs),
        # TODO: Make seperate tables for the commands.
        sql_steps=str(sql_commands),
        dax_steps=str(dax_commands),
        kql_steps=str(kql_commands),
    )


def _get_commands(output: str) -> CommandOutput:
    """
    Get commands from run steps.

    Parameters
    ----------
    output : str
        Output string from a Data Agent response.

    Returns
    -------
    CommandOutput
        Command type and command value returned in run steps.
    """
    commands = {}
    # Regular expression pattern to extract content inside triple backticks
    pattern = r"```(sql|dax|kql)\s(.*?)```"

    if output:
        try:
            # Extract matches
            matches = re.findall(pattern, output, re.DOTALL)
            # Store extracted commands in a dictionary
            commands = {match[0]: match[1] for match in matches}
        except Exception:
            # Handle any regex errors
            pass

    return CommandOutput(
        sql=commands.get('sql'),
        dax=commands.get('dax'),
        kql=commands.get('kql')
    )


def _generate_prompt(
    query: str, expected_answer: str, critic_prompt: Optional[str] = None
):
    """
    Generate the prompt for the evaluation.

    Parameters
    ----------
    query : str
        Question from an input DataFrame.
    expected_answer : str
        Expected answer from an input DataFrame.
    critic_prompt : str, optional
        Prompt to evaluate the actual answer from Data Agent. Default to None.

    Returns
    -------
    str
        String prompt for the evaluation.
    """

    import textwrap

    if critic_prompt:
        prompt = critic_prompt.format(
            query=query, expected_answer=expected_answer
        )
    else:
        prompt = f"""
        Given the following query and ground truth, please determine if the most recent answer is equivalent or satifies the ground truth. If they are numerically and semantically equivalent or satify (even with reasonable rounding), respond with "Yes". If they clearly differ, respond with "No". If it is ambiguous or unclear, respond with "Unclear". Return only one word: Yes, No, or Unclear..

        Query: {query}

        Ground Truth: {expected_answer}
        """

    return textwrap.dedent(prompt)


def _get_fabric_host():
    """
    Get Fabric host address.

    Returns
    -------
    str
        Fabric host address.

    Raises
    -------
        RuntimeError: If host address is None.
    """
    from synapse.ml.internal_utils.session_utils import get_fabric_context
    
    host = get_fabric_context().get(SPARK_HOST)
    if host is None:
        logging.debug(f"Fabric Host address is empty")
        raise RuntimeError("Fabric Host address is empty")
    
    if host.startswith('api.'):
        return host.replace('api.', 'app.', 1)

    return host.replace('api', "", 1)

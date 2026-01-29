
import json
import re
from typing import List, Dict, Tuple, Any
from pandas import DataFrame
from fabric.dataagent.evaluation._models import FewShotCase, FewShotEvalResult

# Default model name for Fabric inbuilt LLM
FABRIC_DEFAULT_MODEL = "gpt-4.1"
MIN_CONFLICT_CONFIDENCE = 0  # Set to 0 to see all conflicts by default

try:
    import openai
    openai.api_version = "2024-02-15-preview"    
except ImportError:
    raise ImportError("Fabric inbuilt LLM requires the 'openai' package available in the environment.")
    


def _build_batch_prompt_fewshot_validation(examples: List[Dict[str, str]]) -> str:
    """Build a prompt to evaluate multiple examples in a single LLM call"""
    prompt = """
    You will be given multiple few-shot examples, each consisting of a natural language question and its corresponding SQL query.
    Your task is to determine if each is a good quality example for teaching a model how to translate natural language to SQL.

    A good quality example must have the following properties:
    1. The natural language question must be clear.
    2. The natural language question and the SQL query must be closely related, meaning that the SQL query should accurately reflect the intent of the natural language question.
    3. All the literals in the natural language question should be mapped to some literals in the SQL query. It should be straightforward to identify this mapping. Evaluate when there is a mapping of all the literals. Do not judge mappings based on the names of the columns the filter is applied on.

    Think step-by-step for each example and explain your reasoning. Return JSON in the form:
    {
        "evaluations": [
            {
                "example_id": 1,
                "reasoning": "Explanation of answer for example 1.",
                "quality": "yes" if the example is a good quality example, otherwise "no",
                "reasoning_details": {
                    "clarity": "yes" or "no",
                    "mapping": "yes" or "no",
                    "relatedness": "yes" or "no"
                }
            }
            // Add more example evaluations as needed
        ]
    }

    Here are the examples to evaluate:
    """
    for i, example in enumerate(examples, 1):
        prompt += f"\nExample {i}:\n"
        prompt += f"Natural language: {example['natural language']}\n"
        prompt += f"SQL: {example['sql']}\n"
    return prompt


def _sanitize_llm_json(raw: str) -> str:
    """
    Cleans up LLM-generated 'almost-JSON' strings so they can be safely passed to json.loads.
    - Removes ```json or ``` wrappers
    - Fixes illegal escape sequences
    - Escaped single quotes to normal quotes
    - Escapes control characters in string values
    - Handles unterminated strings and other batch response issues
    - Fixes missing commas and malformed JSON structure
    - Strips prefixes
    Returns a cleaned JSON string.
    """
    s = raw.strip()
    s = re.sub(r'^\w+:\s*', '', s, count=1)
    if s.startswith("```"):
        s = re.sub(r'^```[a-zA-Z]*\n?', '', s)
        s = re.sub(r'\n?```$', '', s).strip()
    s = s.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    s = re.sub(r'\s+', ' ', s)
    s = s.replace("\\'", "'")
    s = s.replace("\\\\n", "\\n")
    s = s.replace("\\\\r", "\\r")
    s = s.replace("\\\\t", "\\t")
    s = s.replace("\\\n", " ")
    s = s.replace("\\n", " ")
    s = s.replace("\\r", " ")
    # Safer function to fix missing commas between JSON objects
    def fix_missing_commas(text):
        corrected = []
        in_string = False
        i = 0
        while i < len(text):
            char = text[i]
            if char == '"':
                in_string = not in_string
            if not in_string and char == '}':
                # Look ahead for opening brace
                j = i + 1
                while j < len(text) and text[j].isspace():
                    j += 1
                if j < len(text) and text[j] == '{':
                    corrected.append('}, {')
                    i = j  # Skip to opening brace
                    continue
            corrected.append(char)
            i += 1
        return ''.join(corrected)

    s = fix_missing_commas(s)
    s = re.sub(r'}\s*]', '} ]', s)
    s = re.sub(r'"\s*"([^"]+)":', '", "$1":', s)
    def fix_string_termination(text):
        result = []
        in_string = False
        escaped = False
        for char in text:
            if escaped:
                result.append(char)
                escaped = False
                continue
            if char == '\\' and in_string:
                result.append(char)
                escaped = True
                continue
            if char == '"':
                if not in_string:
                    in_string = True
                    result.append(char)
                else:
                    in_string = False
                    result.append(char)
            else:
                result.append(char)
        if in_string:
            result.append('"')
        return ''.join(result)
    s = fix_string_termination(s)
    def fix_quotes_in_strings(text):
        patterns = [
            r'"reasoning":\s*"([^"]*)"',
            r'"quality":\s*"([^"]*)"'
        ]
        for pattern in patterns:
            def fix_content(match):
                field_name = match.group(0).split(':')[0]
                content = match.group(1)
                content = re.sub(r'(?<!\\)"', '\\"', content)
                return f'{field_name}: "{content}"'
            text = re.sub(pattern, fix_content, text)
        return text
    s = fix_quotes_in_strings(s)
    s = re.sub(r'}\s*{\s*"example_id"', '}, { "example_id"', s)
    open_braces = s.count('{')
    close_braces = s.count('}')
    if open_braces > close_braces:
        s += '}' * (open_braces - close_braces)
    open_brackets = s.count('[')
    close_brackets = s.count(']')
    if open_brackets > close_brackets:
        s += ']' * (open_brackets - close_brackets)
    return s

def safe_parse_json(raw_text: str, fallback: dict):
    """Minimal JSON parser: strip fences, try load, fallback on failure."""
    if not isinstance(raw_text, str):
        return fallback
    txt = raw_text.strip()
    if txt.startswith("```"):
        txt = re.sub(r"^```[a-zA-Z]*\n?", "", txt)
        txt = re.sub(r"\n?```$", "", txt).strip()
    try:
        return json.loads(txt)
    except json.JSONDecodeError as e:
        print(f"[warn] JSON parse failed: {e}")
        return fallback

def _filter_conflicts(conflicts: list, min_confidence: int = None) -> list:
    """Return conflicts meeting minimum confidence threshold."""
    if min_confidence is None:
        min_confidence = MIN_CONFLICT_CONFIDENCE

    if not isinstance(conflicts, list):
        return []

    filtered = []
    for conf in conflicts:
        if not isinstance(conf, dict):
            continue
        idxs = conf.get("examples", [])
        if not isinstance(idxs, list) or len(set(idxs)) < 2:
            continue
        
        confidence = _validate_confidence(conf.get("confidence", 0))
        if min_confidence == 0 or confidence >= min_confidence:
            conf_copy = dict(conf)
            conf_copy["examples"] = sorted(set(idx for idx in idxs if isinstance(idx, int)))
            conf_copy["confidence"] = confidence
            filtered.append(conf_copy)

    return filtered

def _validate_confidence(value) -> int:
    """
    Validates and coerces confidence rating to 1-5 integer scale.
    Invalid or missing -> default 0 (will be filtered out).
    """
    if isinstance(value, (int, float)):
        v = int(value)
    elif isinstance(value, str):
        try:
            v = int(float(value.strip()))
        except ValueError:
            print(f"[warn] Invalid confidence string '{value}' - defaulting to 0")
            return 0
    else:
        if value is not None:
            print(f"[warn] Invalid confidence type {type(value)} - defaulting to 0")
        return 0
    
    # Validate range
    if 1 <= v <= 5:
        return v
    
    if v > 5:
        print(f"[warn] Confidence {v} > 5, capping at 5")
        return 5
    if v < 1:
        print(f"[warn] Confidence {v} < 1, setting to 0 (invalid)")
        return 0
    
    return 0

def _evaluate_few_shot_examples(
    examples: list[dict[str, str]],
    datasource_type: str,
    batch_size: int = 10
) -> FewShotEvalResult:
    """
    Internal utility function to evaluate few-shot examples using an LLM model.
    
    NOTE: SQL-only. This function is designed for SQL queries (Lakehouse/Warehouse).
    It is not suitable for KQL (KustoDb), Ontology, or DAX (Semantic Models) yet.
    
    NOTE: This is an internal utility function. Users should call datasource.evaluate_few_shots()
    instead, which provides a cleaner API and returns results as DataFrames.

    Args:
        examples: List of dicts with 'natural language' and 'sql' keys.
        datasource_type: Type of datasource (e.g., 'lakehouse', 'warehouse').
        batch_size: Number of examples per batch.

    Returns:
        FewShotEvalResult: NamedTuple with fields:
            - success_cases: List[FewShotCase]
            - failure_cases: List[FewShotCase]
            - success_count: int
            - total: int
            - success_rate: float
            - conflict_analysis: Dict[str, Any]

    Example:
        >>> # Internal usage (for testing or advanced scenarios)
        >>> examples = [{"natural language": "...", "sql": "..."}]
        >>> result = _evaluate_few_shot_examples(examples, "lakehouse")
    """
    # SQL-only gate: raise exception for non-SQL datasources
    # Accept only external Fabric API types (lakehouse, warehouse)
    if datasource_type not in {"lakehouse", "warehouse"}:
        raise ValueError(
            f"Few-shot evaluation is only supported for SQL datasources (lakehouse, warehouse). "
            f"Datasource type '{datasource_type}' is not supported."
        )
    
    # Parameter validation
    if not isinstance(examples, list) or not examples:
        raise ValueError("'examples' must be a non-empty list of dicts.")
    for ex in examples:
        if not isinstance(ex, dict) or 'natural language' not in ex or 'sql' not in ex:
            raise ValueError("Each example must be a dict with 'natural language' and 'sql' keys.")

    
    llm_client = openai

    all_success_cases = []
    all_failure_cases = []
    total_success_count = 0
    total = len(examples)
    for i in range(0, total, batch_size):
        batch = examples[i:min(i+batch_size, total)]
        prompt = _build_batch_prompt_fewshot_validation(batch)
        response = llm_client.chat.completions.create(
            model= FABRIC_DEFAULT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        result = response.choices[0].message.content.strip()
        result = _sanitize_llm_json(result)
        try:
            result_json = json.loads(result)
        except Exception as e:
            raise RuntimeError(f"Failed to parse LLM output as JSON: {e}\nRaw output: {result}")
        success_cases = []
        failure_cases = []
        success_count = 0
        evaluations = result_json.get("evaluations", [])
        for eval_result in evaluations:
            example_id = int(eval_result.get("example_id", 0)) - 1
            if 0 <= example_id < len(batch):
                example = batch[example_id]
                quality = eval_result.get("quality", "").strip().lower()
                reasoning = eval_result.get("reasoning", "No reasoning provided")
                original_index = i + example_id + 1  # Preserve original 1-based index
                case: FewShotCase = {
                    "example": example,
                    "reasoning": reasoning,
                    "quality": quality,
                    "reasoning_details": eval_result.get("reasoning_details", {}),
                    "original_index": original_index
                }
                if quality == "yes":
                    success_count += 1
                    success_cases.append(case)
                else:
                    failure_cases.append(case)
        all_success_cases.extend(success_cases)
        all_failure_cases.extend(failure_cases)
        total_success_count += success_count
    success_rate = (total_success_count / total) * 100 if total > 0 else 0
    # Use only successful good quality examples for conflict detection
    approved_examples = []
    approved_original_indices = set()
    for case in all_success_cases:
        ex_copy = dict(case["example"])
        original_idx = case.get("original_index")
        ex_copy["_original_index"] = original_idx
        approved_examples.append(ex_copy)
        if isinstance(original_idx, int):
            approved_original_indices.add(original_idx)

    print(
        f"Quality-approved examples: {len(approved_examples)}/{total} "
        f"(filtered out {total - len(approved_examples)} low-quality examples)"
    )

    completion_tokens = None
    if not approved_examples:
        print("[conflict] Skipping conflict detection because no quality-approved examples remain.")
        conflict_json = {"conflicts": []}
    else:
        conflict_analysis_raw, completion_tokens = _detect_conflicts_between_examples(
            approved_examples, llm_client, FABRIC_DEFAULT_MODEL
        )
        conflict_json = safe_parse_json(conflict_analysis_raw, {"conflicts": []})

        if not isinstance(conflict_json.get("conflicts"), list):
            conflict_json["conflicts"] = []

        dedup = {}
        for conf in conflict_json["conflicts"]:
            raw_idxs = conf.get("examples", [])
            if not isinstance(raw_idxs, list):
                continue
            invalid_idxs = [
                idx for idx in raw_idxs
                if isinstance(idx, int) and (not approved_original_indices or idx not in approved_original_indices)
            ]
            if invalid_idxs:
                print(
                    "[warn] Conflict references indices outside approved set; "
                    f"received={sorted(set(invalid_idxs))}"
                )
            original_order = []
            seen_local = set()
            for idx_value in raw_idxs:
                try:
                    idx_int = int(idx_value)
                except (ValueError, TypeError):
                    print(f"[warn] Conflict index '{idx_value}' is not an integer; dropping.")
                    continue
                if idx_int in seen_local:
                    continue
                if approved_original_indices and idx_int not in approved_original_indices:
                    print(f"[warn] Conflict index {idx_int} not in approved set; dropping.")
                    continue
                seen_local.add(idx_int)
                original_order.append(idx_int)
            if not original_order:
                continue
            key = frozenset(original_order)
            validated_conf = _validate_confidence(conf.get("confidence", 0))
            entry = {
                "examples": sorted(original_order),
                "description": conf.get("description", ""),
                "confidence": validated_conf,
            }
            if conf.get("relationship"):
                entry["relationship"] = conf["relationship"].strip().lower()
            if key in dedup:
                existing = dedup[key]
                desc = entry["description"]
                if desc and desc not in existing["description"]:
                    existing["description"] = (existing["description"] + " | " + desc).strip(" |")
                existing["confidence"] = max(existing["confidence"], entry["confidence"])
            else:
                dedup[key] = entry

        filtered_conflicts = _filter_conflicts(list(dedup.values()))
        conflict_json["conflicts"] = filtered_conflicts

    conflict_json["_completion_tokens"] = completion_tokens

    return FewShotEvalResult(
        success_cases=all_success_cases,
        failure_cases=all_failure_cases,
        success_count=total_success_count,
        total=total,
        success_rate=success_rate,
        conflict_analysis=conflict_json
    )


def _cases_to_dataframe(cases: List[Dict]) -> DataFrame:
    return DataFrame([
        {
            "Few-shot question": case["example"]["natural language"],
            "Query (answer)": case["example"]["sql"],
            "Quality score": case.get("quality", ""),
            "Feedback (Reasoning)": case.get("reasoning", ""),
            "Clarity": case.get("reasoning_details", {}).get("clarity", ""),
            "Mapping": case.get("reasoning_details", {}).get("mapping", ""),
            "Relatedness": case.get("reasoning_details", {}).get("relatedness", "")
        }
        for case in cases
    ])

def _detect_conflicts_between_examples(examples, client, model_name):
    """
    Use the LLM to surface true conflicts between few-shot examples.
    
    Returns:
        tuple: (conflict_response_str, completion_tokens)
            - conflict_response_str: JSON string from LLM with conflict analysis
            - completion_tokens: Number of completion tokens used (int or None)
    """
    prompt = f""" You are auditing a library of few-shot training examples. Each example (indexed from 1 in this prompt) contains:
    - a natural language question (NL)
    - an accompanying SQL query (SQL)
    - example's original dataset position index.
    Your task: identify TRUE conflicts (semantic contradictions) between examples.

    Definition of a TRUE conflict (all must hold):
    - The natural language questions (after normalizing superficial wording) express essentially the SAME user intent and scope.
    - The SQL queries would yield MEANINGFULLY DIFFERENT sets (different aggregation level, different measure vs count, different table(s), contradictory filters, mismatched grouping, or differing distinctness semantics).

    ANALYSIS WORKFLOW (follow this order)
    1. Normalize the question (lowercase, remove stop words, lemmatize) and repair literals before comparison. Map month names (Jan, January, or spelling mistakes) to canonical month tokens, fix obvious typos, and convert time windows or fiscal labels into normalized representations so the same template is recognized even when literals differ.
    2. Treat two questions as the same analytic intent when they target the same subject, metric, and filter grain, even if their literal values (dates, months, percentages, thresholds) are different or only shifted in time. Treat offsets across different years or rolling windows as the same template. When the only substantive difference is the time window or tolerance phrasing (for example, different months or +/- thresholds expressed with different words), you must still consider them candidates for conflict.
    3. When two or more questions share the same intent, compare their SQL:
    - List the tables or views referenced.
    - Note the selected measures, filters, and grouping logic.
    - Highlight substantive differences in data sources, aggregation logic, date windows, or metric definitions that would change the answer.
    4. Apply domain-level intent normalization before comparing SQL: consolidate synonymous phrases (engagement, interactions, touches, outreach, activity count, activity volume, success events) into a shared canonical metric unless the wording explicitly distinguishes conversion vs engagement. Document any assumptions you make about synonymy. Keep explicitly conversion-only KPIs (for example, win rate vs activity volume) distinct when the language clearly separates them.
    5. When normalized intent matches but the SQL relies on materially different source views, fact tables, or measures, treat that as conflicting logic and surface it with a clear description.
    6. Flag the group as a conflict if the semantic intent is equivalent but the SQL uses conflicting data sources, metrics, filters, or other logic that would yield materially different answers. Provide concise descriptions that explain the divergence (for example, \"Same intent template, different month window\" or \"Same metric but different fact view\").

    Confidence scale (1-5):
    5 - Clear identical intent + unambiguous material semantic divergence with markedly different tables, views or grouping logic.
    4 - NL wording has similar intent and template; SQL differences reinforce the clash e.g. unclear join or subquery handling, different aggregations for the same intent
    3 - NL wording slightly different, but within semantic neighborhood; SQL still has structural differences ambiguous or overlapping filters.
    2 - Low confidence; NL ambiguity and some SQL structural similarity
    1 - Speculative; avoid conflicts when evidence is weak, or unclear NL, possible mapping issue between NL and SQL.

    Output:
    Return ONLY a single valid JSON object with this shape:
    {{
    "conflicts": [
        {{
        "examples": [i, j, k, ...], // 1-based indices WITH the same ordering used in this prompt, always i<j<k...
        "description": "Reasoning of why the examples (referenced) would conflict. Be very specific and concise, but accurate about the reason of conflict.",
        "confidence": 1-5
        }}
    ]
    }}
    - Use the original dataset indices exactly as shown below when populating every `examples` array. Do NOT invent new numbering.
    - Reference examples in descriptions using the just the example number as reference e.g. for example X refer as "X".
    - Keep descriptions under 200 characters.
    - Confidence is an integer 1 (speculative) through 5 (certain); omit the conflict if you cannot justify at least 1.
    - STRICTLY OMIT: If NL are identical and SQL is structurally same, it is not a conflict. Do not report such examples.

    If no conflicts are found, return exactly: {{ "conflicts": [] }}

    CRITICAL RULE: Before marking as conflict, ask yourself: "Are these questions asking for the SAME thing with DIFFERENT SQL, or DIFFERENT things with appropriately DIFFERENT SQL?" Only flag the first case, omit the second.

    Avoid false positives: if intent similarity is uncertain, do not emit a conflict. Ignore cosmetic SQL differences such as whitespace, aliases, or column order.

    Original-indexed examples follow (do not reuse text verbatim)."""
    for example in examples:
        original_idx = example.get("_original_index")
        if original_idx is None:
            label = "Original index unknown"
        else:
            label = f"Original index {original_idx}"
        prompt += (
            f"\n{label}:\n"
            f"Natural language: {example['natural language']}\n"
            f"SQL: {example['sql']}\n"
        )

    prompt += "\nIf there are NO conflicts at all, return: { \"conflicts\": [] }\n"

    expected = len(examples)
    counted = prompt.count("\nOriginal index ")
    if counted != expected:
        print(f"[warn] Original-index block count mismatch (counted={counted}, expected={expected})")

    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        response_format={"type": "json_object"}
    )

    completion_tokens = None
    usage = getattr(response, "usage", None)
    if usage is not None:
        if hasattr(usage, "to_dict"):
            usage_data = usage.to_dict()
        elif hasattr(usage, "dict"):
            usage_data = usage.dict()
        elif isinstance(usage, dict):
            usage_data = usage
        else:
            usage_data = {key: getattr(usage, key) for key in dir(usage) if key == "completion_tokens"}
        completion_tokens = usage_data.get("completion_tokens")
        if completion_tokens is not None:
            print(f"[conflict-usage] completion={completion_tokens}")
        else:
            print("[conflict-usage] completion tokens unavailable.")
    else:
        print("[conflict-usage] completion tokens unavailable.")

    return response.choices[0].message.content.strip(), completion_tokens

# Show summary of conflicts with full example details

def _get_conflict_details(conflict_analysis, examples, dataset_name):
    """
    Expand conflicts into per-example rows with dataset label.
    Uses 1-5 integer confidence rating directly.
    """
    details = []
    total = len(examples)
    for conflict in conflict_analysis.get("conflicts", []):
        raw_idxs = conflict.get("examples", [])
        if not isinstance(raw_idxs, list):
            continue
        seen = set()
        ordered_valid = []
        for x in raw_idxs:
            if isinstance(x, int) and 1 <= x <= total and x not in seen:
                seen.add(x)
                ordered_valid.append(x)
        if not ordered_valid:
            continue
        desc = conflict.get("description", "")
        conf = _validate_confidence(conflict.get("confidence", 0))
        
        for one_based in ordered_valid:
            ex = examples[one_based - 1]
            details.append({
                "Dataset": dataset_name,
                "Conflict Examples": ordered_valid,
                "Example Number": one_based,
                "Question": ex.get("natural language", ""),
                "SQL": ex.get("sql", ""),
                "Conflict Description": desc,
                "Confidence": conf,
                "Confidence Level": "High" if conf == 5 else ("Medium" if conf == 4 else ("Low" if conf == 3 else ("Very Low" if conf == 2 else "Speculative")))
            })
    return details
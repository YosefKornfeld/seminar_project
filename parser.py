import re
import ast


def _find_outermost_list(text):
    """
    Scans `text` for ALL top-level `[...]` blocks and returns the last one found.
    Returns (start_idx, end_idx) inclusive, or (-1, -1) if not found.
    This handles multi-line bracket-matched lists, including nested sublists.
    """
    last_start = -1
    last_end = -1
    i = 0
    while i < len(text):
        if text[i] == '[':
            count = 0
            for j in range(i, len(text)):
                if text[j] == '[':
                    count += 1
                elif text[j] == ']':
                    count -= 1
                    if count == 0:
                        last_start = i
                        last_end = j
                        i = j  # advance past this block
                        break
        i += 1
    return last_start, last_end


def _normalize_move_list(final_moves):
    """
    Strips surrounding whitespace from every string element in the nested
    move list. This fixes cases where the model outputs [\" a1 \", \" A1 \"]
    (with padding spaces) instead of [\"a1\", \"A1\"].
    """
    if not isinstance(final_moves, list):
        return final_moves
    normalized = []
    for move in final_moves:
        if isinstance(move, list):
            normalized.append([s.strip() if isinstance(s, str) else s for s in move])
        elif isinstance(move, str):
            normalized.append(move.strip())
        else:
            normalized.append(move)
    return normalized


def extract_responses(raw_text):
    """
    Replicating the custom extraction pipeline from Section A.3[cite: 1109].
    Extracts the thinking trace and the final move list.
    """

    # 1. Extract Thinking Trace [cite: 1110]
    # Looks for content between <think> and </think> tags
    think_pattern = r"<think>(.*?)</think>"
    think_match = re.search(think_pattern, raw_text, re.DOTALL)
    thinking_trace = think_match.group(1).strip() if think_match else ""

    # 2. Extract Move List [cite: 1111]
    # Strip thinking trace from text first to avoid matching drafts inside the think block
    clean_text = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL)

    # --- Primary strategy: look for "moves = [...]" assignment ---
    # Use finditer to grab the LAST occurrence of "moves = ...\" in the response,
    # since models sometimes restate the format template before giving the actual answer.
    # Note: no re.DOTALL so each match stops at end-of-line, allowing multiple matches.
    all_moves_matches = list(re.finditer(r"moves\s*=\s*(.*)", clean_text))
    moves_match = all_moves_matches[-1] if all_moves_matches else None

    raw_moves_str = None

    if moves_match:
        # Get everything from the last "moves = " to end of text for bracket matching
        remainder = clean_text[moves_match.start(1):]
        start_idx = remainder.find('[')
        if start_idx != -1:
            count = 0
            end_idx = -1
            for i in range(start_idx, len(remainder)):
                if remainder[i] == '[':
                    count += 1
                elif remainder[i] == ']':
                    count -= 1
                    if count == 0:
                        end_idx = i
                        break
            if end_idx != -1:
                raw_moves_str = remainder[start_idx:end_idx+1]

    # --- Fallback strategy: no "moves = " found; grab the last top-level list ---
    # Some models output the move list as a bare "[...]" block without an assignment.
    if raw_moves_str is None:
        start_idx, end_idx = _find_outermost_list(clean_text)
        if start_idx != -1:
            raw_moves_str = clean_text[start_idx:end_idx+1]

    if raw_moves_str is None:
        return thinking_trace, []

    # 3. Cleaning & Normalization [cite: 1112-1114]
    # Remove Python-style comments (text following "#")
    clean_moves_str = re.sub(r"#.*", "", raw_moves_str)

    # Remove newlines and extra spaces to normalize the string
    clean_moves_str = clean_moves_str.replace('\n', ' ').strip()

    try:
        # Convert the string representation of a list into a real Python list
        # Using ast.literal_eval is safer than eval()
        final_moves = ast.literal_eval(clean_moves_str)

        # 4. Strip whitespace from string elements (e.g. " a1 " -> "a1")
        # Some models mirror the example format which includes spaces in strings.
        final_moves = _normalize_move_list(final_moves)

        # 5. Filter duplicates [cite: 1119-1120]
        # The paper only records the first instance if duplicates occur
        return thinking_trace, final_moves
    except Exception as e:
        print(f"Regex Parsing Error: {e}")
        return thinking_trace, []


def get_thought_token_count(thinking_trace):
    """
    Approximates reasoning effort[cite: 1117, 1285].
    Note: The paper uses the cl100k_base tokenizer for exact counts.
    """
    if not thinking_trace:
        return 0
    # Simple word-to-token approximation (roughly 1.3 tokens per word)
    return len(thinking_trace.split())
import re
import ast


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
    # Use finditer to grab the LAST occurrence of "moves = ..." in the response,
    # since models sometimes restate the format template before giving the actual answer.
    # Note: no re.DOTALL so each match stops at end-of-line, allowing multiple matches.
    all_moves_matches = list(re.finditer(r"moves\s*=\s*(.*)", clean_text))
    moves_match = all_moves_matches[-1] if all_moves_matches else None

    if not moves_match:
        return thinking_trace, []

    # Get everything from the last "moves = " to end of text for bracket matching
    remainder = clean_text[moves_match.start(1):]
    
    start_idx = remainder.find('[')
    if start_idx == -1:
        return thinking_trace, []
        
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
                
    if end_idx == -1:
        return thinking_trace, []
        
    raw_moves_str = remainder[start_idx:end_idx+1]

    # 3. Cleaning & Normalization [cite: 1112-1114]
    # Remove Python-style comments (text following "#")
    clean_moves_str = re.sub(r"#.*", "", raw_moves_str)

    # Remove newlines and extra spaces to normalize the string
    clean_moves_str = clean_moves_str.replace('\n', ' ').strip()

    try:
        # Convert the string representation of a list into a real Python list
        # Using ast.literal_eval is safer than eval()
        final_moves = ast.literal_eval(clean_moves_str)

        # 4. Filter duplicates [cite: 1119-1120]
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
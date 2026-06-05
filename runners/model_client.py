import math
import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from prompts.factory import (
    get_hanoi_prompt,
    get_river_crossing_prompt,
    get_blocks_world_prompt,
    get_checker_jumping_prompt,
)
from parser import extract_responses

# Load environment variables securely
load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")

# Optional: comma-separated list of puzzles to run (e.g. "hanoi,river_crossing").
# If not set, all puzzles in EXPERIMENT_CONFIG are run.
_PUZZLES_ENV = os.getenv("PUZZLES", "").strip()

# Initialize the OpenRouter client (using the OpenAI library wrapper)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)

import sys
# Ensure Python can resolve config.py in the parent folder
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import TEST_RUN
from main import get_simulator


EXPERIMENT_CONFIG = {
    "test_run": TEST_RUN,
    "models": [
        "deepseek/deepseek-r1",
        "deepseek/deepseek-v3",
        "openai/o3-mini"
    ],
    "puzzles": {
        "hanoi": [3, 4, 5, 6, 7],
        "river_crossing": [2, 3, 4],
        "blocks_world": [2, 4, 6], # Even N required for blocks world logic
        "checker_jumping": [1, 2, 3]
    },
    "samples_per_config": 10,
    "max_tokens": 16000,
    "temperature": 1.0
}


def get_progress_file():
    # Points to progress_tracker.json directly in the project root folder
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "progress_tracker.json"))

def load_progress():
    progress_file = get_progress_file()
    if os.path.exists(progress_file):
        with open(progress_file, "r") as f:
            return json.load(f)
    return {}

def save_progress(progress_data):
    progress_file = get_progress_file()
    with open(progress_file, "w") as f:
        json.dump(progress_data, f, indent=4)


def save_log(metadata, prompts, raw_response, usage_data=None):
    """Saves the output matching the exact Data Contract agreed upon with Yosef."""
    test_run = EXPERIMENT_CONFIG.get("test_run", "test-run-1")
    log_dir = os.path.join(
        "logs",
        test_run,
        metadata["model"].replace("/", "_"),
        metadata["puzzle"],
        f"n{metadata['complexity_n']}"
    )
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = (
        f"{metadata['puzzle']}_n{metadata['complexity_n']}"
        f"_sample{metadata['sample_id']}_{timestamp}.json"
    )
    filepath = os.path.join(log_dir, filename)

    log_data = {
        "metadata": metadata,
        "prompts": prompts,
        "raw_response": raw_response,
    }
    if usage_data:
        log_data["usage"] = usage_data

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)

    print(f"    Saved valid sample to: {filepath}")


def call_model(system_prompt, user_prompt, model_name, max_tokens, temperature):
    """
    Handles the actual API request to OpenRouter with proper experiment parameters.
    Uses streaming to avoid silent hangs on long reasoning traces.
    """
    try:
        print(f"    [API] Streaming from OpenRouter ({model_name})...")
        stream = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            extra_body={"include_reasoning": True},
            timeout=180.0,
            stream=True,
        )

        thinking_chunks = []
        content_chunks = []
        token_count = 0
        usage_data = {}

        for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta:
                # Reasoning/thinking tokens (DeepSeek R1 / o3-mini)
                reasoning_piece = getattr(delta, "reasoning", None)
                if reasoning_piece:
                    thinking_chunks.append(reasoning_piece)
                    token_count += 1
                    print(f"\r    [Thinking... ~{token_count} tokens]", end="", flush=True)

                # Final answer tokens
                if delta.content:
                    content_chunks.append(delta.content)
                    token_count += 1
                    print(f"\r    [Generating... ~{token_count} tokens]", end="", flush=True)

            # Capture usage from the last chunk if provided
            if getattr(chunk, "usage", None):
                usage = chunk.usage
                usage_data = {
                    "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                    "completion_tokens": getattr(usage, "completion_tokens", 0),
                    "total_tokens": getattr(usage, "total_tokens", 0),
                }

        print(f"\r    [API] Done. ~{token_count} tokens received.          ")

        thinking = "".join(thinking_chunks)
        content = "".join(content_chunks)

        raw_response = content
        if thinking:
            raw_response = f"<think>{thinking}</think>\n{content}"

        return raw_response, usage_data
    except Exception as e:
        print(f"\n    API Error: {e}")
        return None, None


def run_experiment(puzzle, complexity_n, num_samples, model):
    """
    The main execution loop for a specific puzzle and complexity level.
    """
    print(f"[{model}] Starting: {puzzle} | N={complexity_n} | Target={num_samples} samples")

    # --- PROGRESS TRACKING ---
    progress = load_progress()
    model_key = model.split("/")[-1]
    
    if model_key not in progress:
        progress[model_key] = {}
    if puzzle not in progress[model_key]:
        progress[model_key][puzzle] = {}
        
    n_str = str(complexity_n)
    completed_samples = progress[model_key][puzzle].get(n_str, 0)
    
    if completed_samples >= num_samples:
        print(f"  Skipping: Already collected {completed_samples} samples (Target is {num_samples}).")
        return
        
    valid_samples_collected = completed_samples
    if valid_samples_collected > 0:
        print(f"  Resuming from sample {valid_samples_collected + 1}...")
    # -------------------------

    initial_state = None
    goal_state = None

    if puzzle == "hanoi":
        system_prompt, user_prompt = get_hanoi_prompt(complexity_n)
    elif puzzle == "river_crossing":
        system_prompt, user_prompt = get_river_crossing_prompt(n_pairs=complexity_n, boat_capacity=2)
    elif puzzle == "blocks_world":
        system_prompt, user_prompt, initial_state, goal_state = get_blocks_world_prompt(complexity_n)
    elif puzzle == "checker_jumping":
        system_prompt, user_prompt = get_checker_jumping_prompt(complexity_n)
    else:
        raise ValueError(f"Unknown puzzle: {puzzle}")

    prompts_data = {
        "system": system_prompt,
        "user": user_prompt,
    }

    attempts = 0
    max_attempts = math.floor(num_samples * 1.5)  # Prevent infinite loops if model is failing hard

    while valid_samples_collected < num_samples and attempts < max_attempts:
        attempts += 1
        sample_id = valid_samples_collected + 1
        print(f"  Attempting Sample {sample_id}...")

        metadata = {
            "puzzle": puzzle,
            "complexity_n": complexity_n,
            "sample_id": sample_id,
            "model": model.split("/")[-1],
            "model_full": model,
            "timestamp": datetime.now().isoformat(),
        }
        if puzzle == "blocks_world":
            metadata["initial_state"] = initial_state
            metadata["goal_state"] = goal_state

        raw_response, usage_data = call_model(
            system_prompt, 
            user_prompt, 
            model,
            max_tokens=EXPERIMENT_CONFIG["max_tokens"],
            temperature=EXPERIMENT_CONFIG["temperature"]
        )

        if raw_response is None:
            print("    API failed. Waiting 5s...")
            time.sleep(5)
            continue

        # Extract response moves
        _, final_moves = extract_responses(raw_response)
        
        is_correct = False
        error_message = ""
        
        if not final_moves:
            error_message = "Invalid format or cut off (could not parse move list)"
        else:
            try:
                sim = get_simulator(puzzle, complexity_n, metadata)
                if sim:
                    is_correct, error_message = sim.validate_full_solution(final_moves)
                else:
                    error_message = "Simulator not found"
            except Exception as e:
                error_message = f"Simulator error: {e}"

        # Inject correctness evaluation directly into metadata
        metadata["is_correct"] = is_correct
        metadata["error_message"] = error_message if not is_correct else ""

        if is_correct:
            print("    [RESULT] Correct solution verified by simulator!")
        else:
            print(f"    [RESULT] Invalid/Incorrect: {error_message}")

        # Always count this as a collected sample and save it
        save_log(metadata, prompts_data, raw_response, usage_data)
        valid_samples_collected += 1
        
        # Save progress
        progress[model_key][puzzle][n_str] = valid_samples_collected
        save_progress(progress)
        
        time.sleep(2) # Polite sleep
        
    if valid_samples_collected < num_samples:
        print(f"  WARNING: Only collected {valid_samples_collected}/{num_samples} samples after {max_attempts} attempts.")


if __name__ == "__main__":
    print("Initializing Automated Experiment Runner...")
    print(f"Temperature: {EXPERIMENT_CONFIG['temperature']} | Max Tokens: {EXPERIMENT_CONFIG['max_tokens']}")

    # Filter puzzles based on the PUZZLES env var (if set)
    all_puzzles = EXPERIMENT_CONFIG["puzzles"]
    if _PUZZLES_ENV:
        selected = [p.strip() for p in _PUZZLES_ENV.split(",") if p.strip()]
        unknown = [p for p in selected if p not in all_puzzles]
        if unknown:
            print(f"WARNING: Unknown puzzle(s) in PUZZLES env var (will be skipped): {unknown}")
        active_puzzles = {p: all_puzzles[p] for p in selected if p in all_puzzles}
        print(f"Running only these puzzles (from PUZZLES env var): {list(active_puzzles.keys())}")
    else:
        active_puzzles = all_puzzles
        print("PUZZLES env var not set — running all puzzles.")

    print("---")

    for model in EXPERIMENT_CONFIG["models"]:
        for puzzle, complexities in active_puzzles.items():
            for n in complexities:
                run_experiment(
                    puzzle=puzzle,
                    complexity_n=n,
                    num_samples=EXPERIMENT_CONFIG["samples_per_config"],
                    model=model
                )
    print("All experiments completed.")
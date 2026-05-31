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

# Initialize the OpenRouter client (using the OpenAI library wrapper)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)

EXPERIMENT_CONFIG = {
    "models": [
        "deepseek/deepseek-r1",
        "deepseek/deepseek-v3",
        "openai/o3-mini"
    ],
    "puzzles": {
        "hanoi": [3, 4, 5],
        "river_crossing": [3, 4, 5],
        "blocks_world": [4, 6, 8], # Even N required for blocks world logic
        "checker_jumping": [3, 4, 5]
    },
    "samples_per_config": 10,
    "max_tokens": 64000,
    "temperature": 1.0
}


PROGRESS_FILE = "progress_tracker.json"

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_progress(progress_data):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress_data, f, indent=4)


def save_log(metadata, prompts, raw_response):
    """Saves the output matching the exact Data Contract agreed upon with Yosef."""
    log_dir = os.path.join("logs", metadata["model"].replace("/", "_"))
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

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)

    print(f"    Saved valid sample to: {filepath}")


def call_model(system_prompt, user_prompt, model_name, max_tokens, temperature):
    """
    Handles the actual API request to OpenRouter with proper experiment parameters.
    """
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            extra_body={"include_reasoning": True},
        )
        message = response.choices[0].message
        thinking = getattr(message, "reasoning", "")
        content = message.content or ""
        
        # Stitch it back into a single string for Yosef's regex parser
        if thinking:
            return f"<think>{thinking}</think>\n{content}"
        return content
    except Exception as e:
        print(f"    API Error: {e}")
        return None


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

        raw_response = call_model(
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

        # Filtering Process: Check if it's a validly formatted response
        _, final_moves = extract_responses(raw_response)
        
        if not final_moves:
            print(f"    Validation Failed: Model output invalid format. Discarding and retrying.")
            
            # --- Save invalid log ---
            invalid_dir = os.path.join("logs", "invalid", model_key)
            os.makedirs(invalid_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            invalid_filename = f"{puzzle}_n{complexity_n}_attempt{attempts}_{timestamp}.json"
            
            invalid_data = {
                "metadata": metadata,
                "prompts": prompts_data,
                "raw_response": raw_response
            }
            with open(os.path.join(invalid_dir, invalid_filename), "w", encoding="utf-8") as f:
                json.dump(invalid_data, f, indent=2, ensure_ascii=False)
            # ------------------------
            
            time.sleep(2)
            continue
            
        # If we reach here, the sample is valid
        save_log(metadata, prompts_data, raw_response)
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
    print("---")
    
    for model in EXPERIMENT_CONFIG["models"]:
        for puzzle, complexities in EXPERIMENT_CONFIG["puzzles"].items():
            for n in complexities:
                run_experiment(
                    puzzle=puzzle,
                    complexity_n=n,
                    num_samples=EXPERIMENT_CONFIG["samples_per_config"],
                    model=model
                )
    print("All experiments completed.")
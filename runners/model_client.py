import os
import json
import time
import random
import string
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from prompts.factory import (
    get_hanoi_prompt,
    get_river_crossing_prompt,
    get_blocks_world_prompt,
    get_checker_jumping_prompt
)

# Load environment variables securely
load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")

# Initialize the OpenRouter client (using the OpenAI library wrapper)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)


def save_log(metadata, prompts, raw_response):
    """Saves the output matching the exact Data Contract agreed upon with Yosef."""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Create a unique filename: hanoi_n5_sample1_TIMESTAMP.json
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = (
        f"{metadata['puzzle']}_n{metadata['complexity_n']}"
        f"_sample{metadata['sample_id']}_{timestamp}.json"
    )
    filepath = os.path.join(log_dir, filename)

    # Build the exact JSON structure per the Data Contract
    log_data = {
        "metadata": metadata,
        "prompts": prompts,
        "raw_response": raw_response,
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)

    print(f"Saved: {filepath}")


def call_model(system_prompt, user_prompt, model_name):
    """
    Handles the actual API request to OpenRouter.

    FIX 1: `include_reasoning` must be passed via `extra_body`, not as a
            top-level keyword argument — the standard OpenAI SDK does not
            recognise it and will raise a TypeError.

    FIX 2: We return both the thinking tokens (reasoning) AND the final
            content separately, so both are preserved in the log. Returning
            only `message.content` silently discards the chain-of-thought.
    """
    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            extra_body={"include_reasoning": True},  # FIX 1
        )
        message = response.choices[0].message
        
        thinking = getattr(message, "reasoning", "")
        content = message.content or ""
        
        # Stitch it back into a single string for Yosef's regex parser
        if thinking:
            return f"<think>{thinking}</think>\n{content}"
        return content
    except Exception as e:
        print(f"API Error: {e}")
        return None


def generate_blocks_world_states(complexity_n):
    """
    Generates distinct initial and goal states for Blocks World puzzle.
    """
    blocks = list(string.ascii_uppercase)[:complexity_n]
    
    def random_stacks():
        shuffled = blocks.copy()
        random.shuffle(shuffled)
        stacks = [[], [], []]
        for b in shuffled:
            stacks[random.choice([0, 1, 2])].append(b)
        return stacks
        
    initial_stacks = random_stacks()
    goal_stacks = random_stacks()
    while initial_stacks == goal_stacks:
        goal_stacks = random_stacks()
        
    return initial_stacks, goal_stacks


def run_experiment(
    puzzle="hanoi",
    complexity_n=3,
    num_samples=25,
    model="deepseek/deepseek-r1",
):
    """
    The main execution loop. Generates prompts, calls the API, and saves logs.
    """
    print(f"Starting experiment: {puzzle} | N={complexity_n} | Samples={num_samples}")

    initial_state = None
    goal_state = None

    if puzzle == "hanoi":
        system_prompt, user_prompt = get_hanoi_prompt(complexity_n)
    elif puzzle == "river_crossing":
        boat_capacity = 2 if complexity_n <= 3 else 3
        system_prompt, user_prompt = get_river_crossing_prompt(complexity_n, boat_capacity)
    elif puzzle == "blocks_world":
        initial_state, goal_state = generate_blocks_world_states(complexity_n)
        system_prompt, user_prompt = get_blocks_world_prompt(initial_state, goal_state)
    elif puzzle == "checker_jumping":
        system_prompt, user_prompt = get_checker_jumping_prompt(complexity_n)
    else:
        raise ValueError(f"Unknown puzzle: {puzzle}")

    prompts_data = {
        "system": system_prompt,
        "user": user_prompt,
    }

    for sample_id in range(1, num_samples + 1):
        print(f"Running Sample {sample_id}/{num_samples}...")

        # FIX 3: Timestamp is now recorded inside the metadata so Yosef can
        #         always tell exactly when a sample was collected from the log
        #         content alone — not just from the filename.
        # FIX 4: Full model string is stored alongside the short name so there
        #         is no ambiguity if the model identifier changes later.
        metadata = {
            "puzzle": puzzle,
            "complexity_n": complexity_n,
            "sample_id": sample_id,
            "model": model.split("/")[-1],   # short name for readability
            "model_full": model,             # FIX 4: full identifier preserved
            "timestamp": datetime.now().isoformat(),  # FIX 3
        }
        if puzzle == "blocks_world":
            metadata["initial_state"] = initial_state
            metadata["goal_state"] = goal_state

        raw_response = call_model(system_prompt, user_prompt, model)

        if raw_response is None:
            # FIX 5: Basic retry instead of silently skipping the sample
            print(f"  Sample {sample_id} failed. Waiting 5s then retrying once...")
            time.sleep(5)
            raw_response = call_model(system_prompt, user_prompt, model)

        if raw_response is not None:
            save_log(metadata, prompts_data, raw_response)
        else:
            print(f"  Sample {sample_id} failed on retry too. Skipping.")

        # Polite sleep to avoid hitting API rate limits
        time.sleep(2)


def run_full_scale_study(puzzle, min_n=3, max_n=10, samples_per_n=25, model="deepseek/deepseek-r1"):
    """
    Iterates complexity_n from min_n to max_n. For each N, calls run_experiment.
    Includes polite sleep timers to avoid API rate limits.
    """
    print(f"--- Starting Full Scale Study for {puzzle} ({model}) ---")
    for n in range(min_n, max_n + 1):
        run_experiment(puzzle=puzzle, complexity_n=n, num_samples=samples_per_n, model=model)
        # Polite sleep between different complexity levels
        time.sleep(5)
    print(f"--- Finished Full Scale Study for {puzzle} ---")


if __name__ == "__main__":
    # Test run: 2 samples at N=3 to verify the pipeline before burning budget
    run_experiment(
        puzzle="hanoi",
        complexity_n=3,
        num_samples=2,
        model="deepseek/deepseek-r1",
    )
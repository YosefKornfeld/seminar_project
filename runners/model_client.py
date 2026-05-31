import os
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from prompts.factory import get_hanoi_prompt

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
        return {
            "thinking": getattr(message, "reasoning", None),  # FIX 2
            "content": message.content,
        }
    except Exception as e:
        print(f"API Error: {e}")
        return None


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

    if puzzle == "hanoi":
        system_prompt, user_prompt = get_hanoi_prompt(complexity_n)
    else:
        raise ValueError("Only 'hanoi' is implemented right now.")

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


if __name__ == "__main__":
    # Test run: 2 samples at N=3 to verify the pipeline before burning budget
    run_experiment(
        puzzle="hanoi",
        complexity_n=3,
        num_samples=2,
        model="deepseek/deepseek-r1",
    )
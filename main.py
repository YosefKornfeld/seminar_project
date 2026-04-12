"""
this is a work in progress
"""
import os
import json
import pandas as pd
from parser import extract_responses, get_thought_token_count
from simulators.hanoi import HanoiSimulator
from simulators.river_crossing import RiverCrossingSimulator
from simulators.blocks_world import BlocksWorldSimulator
from simulators.checker_jumping import CheckerJumpingSimulator


def get_simulator(puzzle_type, n, metadata):
    """
    Factory to initialize the correct simulator based on metadata.
    """
    if puzzle_type == "hanoi":
        return HanoiSimulator(n)
    elif puzzle_type == "river_crossing":
        # k=2 for N<=3, k=3 for larger [cite: 346, 1022]
        k = 2 if n <= 3 else 3
        return RiverCrossingSimulator(n, k)
    elif puzzle_type == "blocks_world":
        # These patterns must match the ones Tomer uses in his Prompt Factory [cite: 1065-1068]
        return BlocksWorldSimulator(metadata['initial_state'], metadata['goal_state'])
    elif puzzle_type == "checker_jumping":
        return CheckerJumpingSimulator(n)
    return None


def process_logs(log_dir):
    results = []

    for filename in os.listdir(log_dir):
        if not filename.endswith(".json"): continue

        with open(os.path.join(log_dir, filename), 'r') as f:
            log_data = json.load(f)

        # 1. Extraction
        raw_text = log_data['raw_response']
        thinking_trace, moves = extract_responses(raw_text)

        # 2. Reasoning Effort Analysis [cite: 1117-1118]
        token_count = get_thought_token_count(thinking_trace)

        # 3. Validation [cite: 1121-1125]
        meta = log_data['metadata']
        sim = get_simulator(meta['puzzle'], meta['complexity_n'], meta)

        if sim:
            is_correct, report = sim.validate_full_solution(moves)

            # 4. Create Contract B Record [cite: 1125, 1375]
            results.append({
                "puzzle": meta['puzzle'],
                "n": meta['complexity_n'],
                "model": meta['model'],
                "is_correct": is_correct,
                "thinking_tokens": token_count,
                "error_message": report if not is_correct else ""
            })

    # Save to CSV for the final presentation graphs
    df = pd.DataFrame(results)
    df.to_csv("experiment_results.csv", index=False)
    print("Evaluation complete. Results saved to experiment_results.csv")


if __name__ == "__main__":
    process_logs("./logs")
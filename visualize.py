import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def plot_experiment_results(csv_path="experiment_results.csv", output_dir="data"):
    if not os.path.exists(csv_path):
        print(f"Error: Could not find {csv_path}")
        return

    # 1. Read experiment results
    df = pd.read_csv(csv_path)

    if df.empty:
        print("Error: The CSV file is empty.")
        return

    # Replace model name "deepseek-chat" with "deepseek-V3" in graphs
    df["model"] = df["model"].replace("deepseek-chat", "deepseek-V3")

    # Ensure output dir exists
    os.makedirs(output_dir, exist_ok=True)

    # 2. Group by puzzle, complexity_n (n), and model
    summary = df.groupby(["puzzle", "n", "model"]).agg({
        "is_correct": "mean",
        "thinking_tokens": "mean"
    }).reset_index()

    summary.rename(columns={
        "is_correct": "Accuracy",
        "n": "Complexity N",
        "thinking_tokens": "Thinking Tokens"
    }, inplace=True)

    # We will generate one accuracy graph for each puzzle
    puzzles = summary["puzzle"].unique()

    for puzzle in puzzles:
        puzzle_data = summary[summary["puzzle"] == puzzle]

        plt.figure(figsize=(10, 6))
        sns.lineplot(
            data=puzzle_data,
            x="Complexity N",
            y="Accuracy",
            hue="model",
            style="model",
            markers=True,
            dashes=True
        )
        plt.title(f"Accuracy vs Complexity N ({puzzle})")
        plt.xlabel("Complexity N")
        plt.ylabel("Accuracy")
        plt.ylim(-0.05, 1.05)
        plt.legend(title="Model", bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        output_path = os.path.join(output_dir, f"accuracy_{puzzle}.png")
        plt.savefig(output_path)
        plt.close()
        print(f"Plot successfully saved to {output_path}")

    # Generate ONE combined graph for Thinking Tokens
    # We only care about models that actually use thinking tokens (like deepseek-r1)
    thinking_data = summary[summary["Thinking Tokens"] > 0]
    
    if not thinking_data.empty:
        plt.figure(figsize=(10, 6))
        sns.lineplot(
            data=thinking_data,
            x="Complexity N",
            y="Thinking Tokens",
            hue="puzzle",
            style="model",
            markers=True,
            dashes=True
        )
        plt.title("Thinking Tokens vs Complexity N (All Tests)")
        plt.xlabel("Complexity N")
        plt.ylabel("Thinking Tokens")
        plt.legend(title="Test", bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        output_path = os.path.join(output_dir, "thinking_tokens_all_tests.png")
        plt.savefig(output_path)
        plt.close()
        print(f"Plot successfully saved to {output_path}")

    # Generate ONE combined graph for deepseek-r1 Accuracy
    # Filter only for deepseek-r1
    r1_data = summary[summary["model"] == "deepseek-r1"]
    
    if not r1_data.empty:
        plt.figure(figsize=(10, 6))
        sns.lineplot(
            data=r1_data,
            x="Complexity N",
            y="Accuracy",
            hue="puzzle",
            marker="o",
            markersize=8,
            dashes=True
        )
        plt.title("Accuracy vs Complexity N (deepseek-r1 - All Tests)")
        plt.xlabel("Complexity N")
        plt.ylabel("Accuracy")
        plt.ylim(-0.05, 1.05)
        plt.legend(title="Test", bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        output_path = os.path.join(output_dir, "accuracy_all_tests_r1.png")
        plt.savefig(output_path)
        plt.close()
        print(f"Plot successfully saved to {output_path}")

if __name__ == "__main__":
    plot_experiment_results()

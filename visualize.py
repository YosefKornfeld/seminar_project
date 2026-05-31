import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def plot_accuracy_vs_complexity(csv_path="experiment_results.csv", output_dir="data"):
    if not os.path.exists(csv_path):
        print(f"Error: Could not find {csv_path}")
        return

    # 1. Read experiment results
    df = pd.read_csv(csv_path)

    if df.empty:
        print("Error: The CSV file is empty.")
        return

    # 2. Calculate the success rate
    # Group by puzzle, complexity_n (n), and model
    # is_correct should be a boolean or 1/0, mean() gives the success rate (0.0 to 1.0)
    summary = df.groupby(["puzzle", "n", "model"])["is_correct"].mean().reset_index()
    summary.rename(columns={"is_correct": "Accuracy", "n": "Complexity N"}, inplace=True)

    # 3. Generate a line plot
    plt.figure(figsize=(10, 6))
    
    # Use seaborn to plot lines with different colors for models and styles for puzzles
    sns.lineplot(
        data=summary,
        x="Complexity N",
        y="Accuracy",
        hue="model",
        style="puzzle",
        markers=True,
        dashes=True
    )

    plt.title("Accuracy vs Complexity N")
    plt.xlabel("Complexity N")
    plt.ylabel("Accuracy")
    plt.ylim(0, 1.05) # Limit Y-axis from 0.0 to 1.0 (with slight padding at the top)
    
    # Move the legend outside the plot for better visibility if needed
    plt.legend(title="Model & Puzzle", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()

    # 4. Save the generated plot
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "accuracy_vs_complexity.png")
    plt.savefig(output_path)
    print(f"Plot successfully saved to {output_path}")

if __name__ == "__main__":
    plot_accuracy_vs_complexity()

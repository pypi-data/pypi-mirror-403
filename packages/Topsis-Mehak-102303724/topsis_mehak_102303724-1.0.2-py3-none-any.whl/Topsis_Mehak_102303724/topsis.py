import sys
import pandas as pd
import numpy as np

def topsis_logic(input_file, weights, impacts, result_file):
    # Handle missing input file
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print("Error: File not found.")
        return

    # Basic input checks
    if len(df.columns) < 3:
        print("Error: Input file must contain three or more columns.")
        return
    try:
        data = df.iloc[:, 1:].values.astype(float)
    except ValueError:
        print("Error: From 2nd to last columns must contain numeric values only.")
        return

    # Validate weights and impacts
    weights_list = [float(w) for w in weights.split(',')]
    impacts_list = impacts.split(',')

    # Ensure counts match the number of criteria
    if len(weights_list) != data.shape[1] or len(impacts_list) != data.shape[1]:
        print("Error: Number of weights, impacts, and columns must be the same.")
        return

    # Impacts must be '+' or '-'
    if not all(i in ['+', '-'] for i in impacts_list):
        print("Error: Impacts must be either +ve or -ve.")
        return

    # Vector normalization
    rss = np.sqrt(np.sum(data**2, axis=0))
    normalized_data = data / rss

    # Apply weights
    weighted_data = normalized_data * weights_list

    # Determine ideal (best) and nadir (worst) solutions
    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts_list)):
        if impacts_list[i] == '+':
            ideal_best.append(np.max(weighted_data[:, i]))
            ideal_worst.append(np.min(weighted_data[:, i]))
        else: # Impact is '-'
            ideal_best.append(np.min(weighted_data[:, i]))
            ideal_worst.append(np.max(weighted_data[:, i]))

    # Compute distances to ideal solutions
    dist_best = np.sqrt(np.sum((weighted_data - ideal_best)**2, axis=1))
    dist_worst = np.sqrt(np.sum((weighted_data - ideal_worst)**2, axis=1))

 
    scores = dist_worst / (dist_best + dist_worst)

    # Rank alternatives
    df['Topsis Score'] = scores
    df['Rank'] = df['Topsis Score'].rank(ascending=False).astype(int)

    # Write results to CSV
    df.to_csv(result_file, index=False)
    print(f"Result saved to {result_file}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python <program.py> <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")
        print('Example: python topsis.py data.csv "1,1,1,2" "+,+,-,+" output.csv')
    else:
        topsis_logic(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
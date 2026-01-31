import sys
import pandas as pd
import numpy as np

def topsis_logic(input_file, weights, impacts, result_file):
    # 1. File Not Found Exception Handling [cite: 12]
    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print("Error: File not found.")
        return

    # 2. Input File Checks
    if len(df.columns) < 3:
        print("Error: Input file must contain three or more columns.")
        return
    try:
        data = df.iloc[:, 1:].values.astype(float)
    except ValueError:
        print("Error: From 2nd to last columns must contain numeric values only.")
        return

    # 3. Weights and Impacts Validation
    weights_list = [float(w) for w in weights.split(',')]
    impacts_list = impacts.split(',')

    # Check length mismatch [cite: 15]
    if len(weights_list) != data.shape[1] or len(impacts_list) != data.shape[1]:
        print("Error: Number of weights, impacts, and columns must be the same.")
        return

    # Check valid impacts (+ or -) 
    if not all(i in ['+', '-'] for i in impacts_list):
        print("Error: Impacts must be either +ve or -ve.")
        return

    # Step 1: Vector Normalization
    rss = np.sqrt(np.sum(data**2, axis=0))
    normalized_data = data / rss

    # Step 2: Weight Assignment
    weighted_data = normalized_data * weights_list

    # Step 3: Find Ideal Best and Ideal Worst
    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts_list)):
        if impacts_list[i] == '+':
            ideal_best.append(np.max(weighted_data[:, i]))
            ideal_worst.append(np.min(weighted_data[:, i]))
        else: # Impact is '-'
            ideal_best.append(np.min(weighted_data[:, i]))
            ideal_worst.append(np.max(weighted_data[:, i]))

    # Step 4: Calculate Euclidean Distance
    dist_best = np.sqrt(np.sum((weighted_data - ideal_best)**2, axis=1))
    dist_worst = np.sqrt(np.sum((weighted_data - ideal_worst)**2, axis=1))

 
    scores = dist_worst / (dist_best + dist_worst)

    # Step 6: Assign Rank
    df['Topsis Score'] = scores
    df['Rank'] = df['Topsis Score'].rank(ascending=False).astype(int)

    # Save output 
    df.to_csv(result_file, index=False)
    print(f"Result saved to {result_file}")

if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python <program.py> <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")
        print('Example: python topsis.py data.csv "1,1,1,2" "+,+,-,+" output.csv')
    else:
        topsis_logic(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
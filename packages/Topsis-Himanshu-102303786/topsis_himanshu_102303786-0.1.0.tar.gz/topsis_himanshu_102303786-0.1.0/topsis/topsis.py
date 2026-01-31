# topsis.py
import sys
import os
import pandas as pd
import numpy as np

def topsis(input_file, weights, impacts, result_file):
    """Compute TOPSIS scores and ranks for a given dataset."""
    
    # ----- Step 1: Check file exists -----
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found!")
        sys.exit(1)

    # ----- Step 2: Read file -----
    try:
        if input_file.lower().endswith('.csv'):
            data = pd.read_csv(input_file)
        elif input_file.lower().endswith(('.xlsx', '.xls')):
            data = pd.read_excel(input_file)
        else:
            print("Error: Only .csv or .xlsx files are supported!")
            sys.exit(1)
    except Exception as e:
        print("Error reading file:", e)
        sys.exit(1)

    # ----- Step 3: Check number of columns -----
    if data.shape[1] < 3:
        print("Error: Input file must contain at least 3 columns (1 identifier + 2 numeric criteria)!")
        sys.exit(1)

    # ----- Step 4: Ensure numeric data from 2nd to last column -----
    numeric_data = data.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')
    if numeric_data.isnull().values.any():
        non_numeric_cols = numeric_data.columns[numeric_data.isnull().any()].tolist()
        print(f"Error: Non-numeric values found in columns: {non_numeric_cols}")
        sys.exit(1)

    # ----- Step 5: Parse weights & impacts -----
    try:
        weights = [float(i) for i in weights.split(',')]
        impacts = impacts.split(',')
    except:
        print("Error: Weights and impacts must be comma-separated numbers and signs!")
        sys.exit(1)

    if len(weights) != numeric_data.shape[1] or len(impacts) != numeric_data.shape[1]:
        print(f"Error: Number of weights ({len(weights)}), impacts ({len(impacts)}), "
              f"and numeric columns ({numeric_data.shape[1]}) must match!")
        sys.exit(1)

    if not all(i in ['+', '-'] for i in impacts):
        print("Error: Impacts must be '+' or '-' only!")
        sys.exit(1)

    # ----- Step 6: Normalize and weight -----
    numeric_data = numeric_data.astype(float)
    norm = numeric_data / np.sqrt((numeric_data ** 2).sum())
    weighted = norm * weights

    # ----- Step 7: Ideal best & worst -----
    ideal_best, ideal_worst = [], []
    for i in range(len(impacts)):
        if impacts[i] == '+':
            ideal_best.append(weighted.iloc[:, i].max())
            ideal_worst.append(weighted.iloc[:, i].min())
        else:
            ideal_best.append(weighted.iloc[:, i].min())
            ideal_worst.append(weighted.iloc[:, i].max())

    # ----- Step 8: Distances to ideal best & worst -----
    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    # ----- Step 9: Score & Rank -----
    denom = dist_best + dist_worst
    denom[denom == 0] = np.finfo(float).eps  # prevent divide-by-zero
    score = dist_worst / denom
    data['Topsis Score'] = score
    data['Rank'] = score.rank(ascending=False).astype(int)

    # ----- Step 10: Save result -----
    try:
        data.to_csv(result_file, index=False)
        print(f"✅ Result saved successfully to '{result_file}'")
    except Exception as e:
        print("Error writing result file:", e)
        sys.exit(1)


# ----- Command-line interface -----
def main():
    if len(sys.argv) != 5:
        print("Usage: python topsis.py <InputDataFile> <Weights> <Impacts> <OutputResultFileName>")
        sys.exit(1)

    _, input_file, weights, impacts, result_file = sys.argv
    topsis(input_file, weights, impacts, result_file)


# ----- Demo mode (for testing your actual Excel file) -----
if __name__ == "__main__":
    if len(sys.argv) == 5:
        main()
    else:
        print("Running TOPSIS demo with your Excel file data...")
        demo_file = "your_data.xlsx"  # <-- replace this with your Excel filename
        demo_result = "result.csv"
        # You can leave weights & impacts same as assignment example
        topsis(demo_file, "1,1,1,1,1", "+,+,+,+,+", demo_result)
        print(f"Demo completed. Check '{demo_result}'.")

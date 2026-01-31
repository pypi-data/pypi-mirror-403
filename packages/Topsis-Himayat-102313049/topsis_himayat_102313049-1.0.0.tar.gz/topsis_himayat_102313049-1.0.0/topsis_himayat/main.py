import sys
import pandas as pd
import numpy as np

def error_exit(message):
    print("Error:", message)
    sys.exit(1)

def main():
    if len(sys.argv) != 5:
        error_exit("Usage: topsis <InputFile> <Weights> <Impacts> <OutputFile>")

    input_file = sys.argv[1]
    weights_str = sys.argv[2]
    impacts_str = sys.argv[3]
    output_file = sys.argv[4]

    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        error_exit("File not found.")

    if df.shape[1] < 3:
        error_exit("Input file must contain at least three columns.")

    criteria_data = df.iloc[:, 1:]

    if not np.all(criteria_data.applymap(np.isreal)):
        error_exit("From 2nd to last columns must contain numeric values only.")

    criteria_data = criteria_data.astype(float)

    try:
        weights = list(map(float, weights_str.split(",")))
    except:
        error_exit("Weights must be numeric and comma separated.")

    impacts = impacts_str.split(",")

    if len(weights) != criteria_data.shape[1]:
        error_exit("Weights count must match criteria columns.")

    if len(impacts) != criteria_data.shape[1]:
        error_exit("Impacts count must match criteria columns.")

    for impact in impacts:
        if impact not in ["+", "-"]:
            error_exit("Impacts must be '+' or '-' only.")

    norm_data = criteria_data / np.sqrt((criteria_data ** 2).sum())

    weighted_data = norm_data * weights

    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == "+":
            ideal_best.append(weighted_data.iloc[:, i].max())
            ideal_worst.append(weighted_data.iloc[:, i].min())
        else:
            ideal_best.append(weighted_data.iloc[:, i].min())
            ideal_worst.append(weighted_data.iloc[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    dist_best = np.sqrt(((weighted_data - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted_data - ideal_worst) ** 2).sum(axis=1))

    scores = dist_worst / (dist_best + dist_worst)

    df["Topsis Score"] = scores
    df["Rank"] = df["Topsis Score"].rank(ascending=False, method="dense")

    df.to_csv(output_file, index=False)

    print("TOPSIS result saved to:", output_file)

if __name__ == "__main__":
    main()


import csv
import os
import statistics
import matplotlib.pyplot as plt

# Create output folder
os.makedirs("results/graphs", exist_ok=True)

# Read benchmark data
def load_data(filename):
    with open(filename, "r") as file:
        return list(csv.DictReader(file))

baseline = load_data("results/baseline.csv")
node3_down = load_data("results/node3_down.csv")

# Calculate metrics
def calculate(data):
    latencies = sorted(float(row["latency_ms"]) for row in data)

    successful = sum(row["success"] == "True" for row in data)
    failed = len(data) - successful

    p95_index = int(0.95 * (len(latencies) - 1))

    return {
        "total": len(data),
        "successful": successful,
        "failed": failed,
        "average": statistics.mean(latencies),
        "median": statistics.median(latencies),
        "p95": latencies[p95_index]
    }

base = calculate(baseline)
failure = calculate(node3_down)

labels = ["Baseline", "Node 3 Down"]

# Graph 1: Average latency
plt.figure(figsize=(8, 5))
plt.bar(labels, [base["average"], failure["average"]])
plt.title("Average Query Latency Comparison")
plt.ylabel("Latency (ms)")
plt.savefig("results/graphs/average_latency.png")
plt.close()

# Graph 2: Successful and failed queries
plt.figure(figsize=(8, 5))
plt.bar(labels, [base["successful"], failure["successful"]],
        label="Successful")
plt.bar(labels, [base["failed"], failure["failed"]],
        bottom=[base["successful"], failure["successful"]],
        label="Failed")
plt.title("Query Success and Failure Comparison")
plt.ylabel("Number of Queries")
plt.legend()
plt.savefig("results/graphs/query_success.png")
plt.close()

# Graph 3: P95 latency
plt.figure(figsize=(8, 5))
plt.bar(labels, [base["p95"], failure["p95"]])
plt.title("95th Percentile Latency Comparison")
plt.ylabel("Latency (ms)")
plt.savefig("results/graphs/p95_latency.png")
plt.close()

# Print summary
print("\nBENCHMARK COMPARISON")
print("--------------------")

for name, result in [
    ("Baseline", base),
    ("Node 3 Down", failure)
]:
    print("\n", name)
    for key, value in result.items():
        print(key, ":", round(value, 3) if isinstance(value, float) else value)

print("\nGraphs saved in results/graphs/")

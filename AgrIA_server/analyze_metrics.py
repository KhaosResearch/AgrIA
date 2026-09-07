import json
import math


# Load metrics from JSON file
def load_metrics(file_path):
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading metrics: {e}")
        return None


def analyze_metrics(metrics):
    # Analyze vegetation percentage
    veg_value = float(metrics["vegetation_percentage"])
    if veg_value < 11:
        vegetation = "low vegetation"
    elif veg_value < 26:
        vegetation = "moderate vegetation"
    elif veg_value < 50:
        vegetation = "high vegetation"
    elif veg_value < 75:
        vegetation = "very high vegetation"
    else:
        vegetation = "dense vegetation"

    # Analyze edge density
    edge_density = float(metrics["edge_density"])
    if edge_density < 0.001:
        edge_status = "low parcel definition"
    elif edge_density < 0.005:
        edge_status = "moderate parcel definition"
    else:
        edge_status = "well-defined parcels"

    # Analyze building structural variance
    building_variance = float(metrics["building_structural_variance"])
    if building_variance < 1.0:
        building_status = "few structures"
    elif building_variance < 5.0:
        building_status = "moderate structures"
    else:
        building_status = "significant infrastructure"

    # Format summary very concisely
    summary = [
        vegetation,
        edge_status,
        building_status,
        f"current state: {metrics['phenological_stage']}",
    ]

    return "; ".join(summary)


if __name__ == "__main__":
    metrics_path = "/home/miguel/Dev/AgrIA/AgrIA_server/metrics.json"
    metrics = load_metrics(metrics_path)
    if metrics:
        analysis = analyze_metrics(metrics)
        print(f"Image analysis: {analysis}")
        print(f"Word count: {len(analysis.split())}")

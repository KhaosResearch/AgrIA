import sys
import json
import numpy as np
from PIL import Image


class SatelliteImageAnalyzer:
    def __init__(self, image_path):
        self.image = Image.open(image_path).convert("RGB")
        self.image_array = np.array(self.image)

    def detect_edges(self, threshold=25):
        gray = np.mean(self.image_array, axis=2)
        h_edges = np.abs(np.diff(gray, axis=1))[:-1, :]
        v_edges = np.abs(np.diff(gray, axis=0))[:, :-1]
        combined = np.maximum(h_edges, v_edges)
        return float(np.mean(combined > threshold))

    def analyze_patterns(self):
        # Convert to HSV to detect vibrant green vegetation accurately
        hsv_img = self.image.convert("HSV")
        hsv_array = np.array(hsv_img)

        hue = hsv_array[:, :, 0]
        sat = hsv_array[:, :, 1]
        val = hsv_array[:, :, 2]

        # True green vegetation in HSV (Hue between ~35 and 85 out of 255, with decent saturation)
        green_mask = (hue >= 35) & (hue <= 85) & (sat > 40) & (val > 30)
        vegetation_pct = float(np.mean(green_mask) * 100)

        edge_density = self.detect_edges()
        color_variance = float(np.mean(np.std(self.image_array, axis=2)))

        # Classification: Primary driver is high edge density OR high green vegetation percentage
        if vegetation_pct > 25.0 or (vegetation_pct > 10.0 and edge_density < 0.04):
            image_type = "agricultural"
        else:
            image_type = "urban"

        if image_type == "agricultural":
            if vegetation_pct > 40.0:
                phenology = "crops_growing"
            elif vegetation_pct > 15.0:
                phenology = "partial_canopy_or_harvested"
            else:
                phenology = "crops_not_present_bare_soil"
        else:
            phenology = "not_applicable"

        return {
            "image_type": image_type,
            "vegetation_percentage": round(vegetation_pct, 2),
            "building_structural_variance": round(color_variance, 2),
            "edge_density": round(edge_density, 4),
            "phenological_stage": phenology,
        }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python satellite_analyzer.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    analyzer = SatelliteImageAnalyzer(image_path)
    results = analyzer.analyze_patterns()

    with open("analysis_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(json.dumps(results, indent=2))

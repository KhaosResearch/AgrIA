import sys
import json
import numpy as np
from PIL import Image

class SatelliteImageAnalyzer:
    def __init__(self, image_path):
        self.raw_image = Image.open(image_path)
        
        # 1. Create a mask to ignore transparent or pure white/black background margins
        if self.raw_image.mode == "RGBA":
            alpha = np.array(self.raw_image)[:, :, 3]
            self.mask = alpha > 10  # Non-transparent pixels
        else:
            self.mask = np.ones((self.raw_image.height, self.raw_image.width), dtype=bool)

        # Convert to standard RGB array
        self.rgb_image = self.raw_image.convert("RGB")
        self.image_array = np.array(self.rgb_image)

        # Exclude white background borders (common in GIS-cropped imagery)
        white_bg = (self.image_array[:, :, 0] > 240) & (self.image_array[:, :, 1] > 240) & (self.image_array[:, :, 2] > 240)
        self.mask = self.mask & (~white_bg)

        # Valid field pixels
        self.valid_pixels = self.image_array[self.mask]

    def analyze_colors_and_tones(self):
        """Extracts dominant color tones and soil characteristics."""
        if len(self.valid_pixels) == 0:
            return {"dominant_tones": ["unknown"], "bare_soil_pct": 0.0}

        r, g, b = self.valid_pixels[:, 0], self.valid_pixels[:, 1], self.valid_pixels[:, 2]

        # Bare Soil Index (Soil reflects higher Red/Orange than Green/Blue)
        bare_soil_mask = (r > g) & (g >= b) & (r > 60)
        bare_soil_pct = float(np.mean(bare_soil_mask) * 100)

        # Color Tone Detection
        mean_r, mean_g, mean_b = np.mean(r), np.mean(g), np.mean(b)
        
        tones = []
        if mean_r > mean_g and mean_g > mean_b:
            if mean_r > 150:
                tones.append("warm light-ochre / sandy soil")
            else:
                tones.append("reddish-brown / terra-cotta soil")
        elif mean_g > mean_r:
            tones.append("greenish vegetative cover")
        else:
            tones.append("neutral gray / asphalt / concrete tone")

        # Color heterogeneity (patchiness across the parcel)
        patchiness_score = float(np.std(r) + np.std(g) + np.std(b)) / 3.0

        return {
            "dominant_tone": tones[0] if tones else "heterogeneous soil",
            "bare_soil_percentage": round(bare_soil_pct, 2),
            "patchiness_score": round(patchiness_score, 2),
            "mean_rgb": [round(float(mean_r), 1), round(float(mean_g), 1), round(float(mean_b), 1)]
        }

    def analyze_patterns(self):
        if len(self.valid_pixels) == 0:
            return {"error": "No valid imagery pixels inside mask"}

        # Convert valid pixels to HSV
        hsv_img = self.rgb_image.convert("HSV")
        hsv_array = np.array(hsv_img)[self.mask]
        
        hue, sat, val = hsv_array[:, 0], hsv_array[:, 1], hsv_array[:, 2]

        # Vegetation Detection (HSV)
        green_mask = (hue >= 35) & (hue <= 85) & (sat > 40) & (val > 30)
        vegetation_pct = float(np.mean(green_mask) * 100)

        # Color analysis
        color_info = self.analyze_colors_and_tones()

        # Structural variance within field pixels only (excluding background boundary)
        field_variance = float(np.mean(np.std(self.valid_pixels, axis=1)))

        # Classification Logic
        # High soil percentage or low intra-field variance indicates agricultural land
        if color_info["bare_soil_percentage"] > 40.0 or vegetation_pct > 15.0 or field_variance < 30.0:
            image_type = "agricultural"
        else:
            image_type = "urban"

        # Phenological Status
        if image_type == "agricultural":
            if vegetation_pct > 45.0:
                phenology = "active_crop_growth"
            elif vegetation_pct > 15.0:
                phenology = "partial_canopy_or_emerging_crops"
            elif color_info["bare_soil_percentage"] > 50.0:
                phenology = "crops_not_present_bare_soil_or_tilled"
            else:
                phenology = "fallow_or_overexploited_land"
        else:
            phenology = "not_applicable"

        return {
            "image_type": image_type,
            "vegetation_percentage": round(vegetation_pct, 2),
            "bare_soil_percentage": color_info["bare_soil_percentage"],
            "dominant_color_tone": color_info["dominant_tone"],
            "patchiness_score": color_info["patchiness_score"],
            "field_structural_variance": round(field_variance, 2),
            "phenological_stage": phenology
        }

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python satellite_analyzer.py <image_path>")
        sys.exit(1)

    analyzer = SatelliteImageAnalyzer(sys.argv[1])
    results = analyzer.analyze_patterns()
    print(json.dumps(results, indent=2))
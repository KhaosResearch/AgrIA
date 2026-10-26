import os

import pandas as pd

from .constants import DATA_DIR, OUT_DIR
from .generate_dataset_plots import generate_dataset_plots
from .process_cap_data import process_cap_data
from .utils import get_merge_cap_data


years = [2023, 2024]
OUT_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

for year in years:
    # Generate merged and processed CAP datasets
    merged_filename = f"PAC_{year}_MERGED.csv"
    processed_filename = f"PAC_{year}_PROCESSED.csv"
    merged_output_file = (
        str(OUT_DIR / merged_filename)
        if merged_filename not in os.listdir(OUT_DIR)
        else None
    )
    processed_output_file = (
        str(OUT_DIR / processed_filename)
        if processed_filename not in os.listdir(OUT_DIR)
        else None
    )

    if None not in [merged_output_file, processed_output_file]:
        classification_file = str(DATA_DIR / f"classification_{year}.json")
        merged_output_file = get_merge_cap_data(year, output_file=merged_output_file)
        out = process_cap_data(
            processed_output_file=processed_output_file,
            merged_output_file=merged_output_file,
            classification_file=classification_file,
        )
        if out is not None and len(out) > 0:
            with open(DATA_DIR / f"{year}_unprocessed_entries.txt", "w") as f:
                f.write(out)

    df = pd.read_csv(processed_output_file, encoding="latin1", low_memory=False)

    # Generate dataset plots for information
    if not len(os.listdir(OUT_DIR)) == 4:
        generate_dataset_plots(df)

    # Correct ecoschemes subvention amounts
    break  # Only do one year

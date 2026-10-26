import os

import pandas as pd
from concurrent.futures import ProcessPoolExecutor

from .constants import DATA_DIR, OUT_DIR
from .generate_dataset_plots import generate_dataset_plots
from .process_cap_data import process_cap_data
from .utils import get_merge_cap_data


def process_year(year: int) -> None:
    """Processes datasets for a single year."""
    merged_filename = f"PAC_{year}_MERGED.csv"
    processed_filename = f"PAC_{year}_PROCESSED.csv"

    merged_output_path = OUT_DIR / merged_filename
    processed_output_path = OUT_DIR / processed_filename

    merged_output_file = (
        str(merged_output_path) if not merged_output_path.exists() else None
    )
    processed_output_file = (
        str(processed_output_path) if not processed_output_path.exists() else None
    )

    if merged_output_file is not None and processed_output_file is not None:
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

    if processed_output_path.exists():
        # High-performance engine setup utilizing Xeon vector extensions
        df = pd.read_csv(
            processed_output_path,
            encoding="latin1",
            low_memory=False,
            engine="c",  # Fast C parser
        )

        # Generate dataset plots for information
        if len(os.listdir(OUT_DIR)) != 4:
            generate_dataset_plots(df)


def run_pipeline(years: list[int]) -> None:
    """Saturates all available VM CPU cores to run year workloads in parallel."""
    OUT_DIR.mkdir(exist_ok=True)
    DATA_DIR.mkdir(exist_ok=True)

    # Use all 8 logical cores
    max_workers = os.cpu_count() or 8

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Executes process_year across all cores concurrently
        list(executor.map(process_year, years))


if __name__ == "__main__":
    years_to_process = [2023, 2024]  # Expand to as many years as needed
    run_pipeline(years_to_process)

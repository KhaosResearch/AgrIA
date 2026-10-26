import os

import pandas as pd
import matplotlib.pyplot as plt

from structlog import get_logger

from .constants import OUT_DIR, PLOTS_DIR

logger = get_logger(__file__)

# Styling Constants
BAR_COLOR = "#316926"  # Dark purple theme matching provided plots
FIGURE_SIZE = (16, 9)

PLOTS_DIR.mkdir(exist_ok=True)


def plot_land_area_distribution(
    df,
    target_col="SUP_TOTAL_HA",
    output_path=str(PLOTS_DIR / "land_area_distribution.png"),
):
    """Generates percentage distribution bar chart across hectare categories."""
    logger.info("Generating Land Area Distribution plot...")

    if target_col not in df.columns:
        logger.error("Column 'SUP_TOTAL_HA' missing from dataset.")
        return

    # Categorize land area into specified bins
    bins = [-float("inf"), 1, 2, 5, 10, 20, 50, 100, float("inf")]
    labels = ["<1", "1-2", "2-5", "5-10", "10-20", "20-50", "50-100", "100+"]

    area_series = pd.to_numeric(df[target_col], errors="coerce")
    categories = pd.cut(area_series, bins=bins, labels=labels, right=False)

    # Calculate percentages
    percentages = categories.value_counts(sort=False, normalize=True) * 100

    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    # bars = ax.bar(
    #     percentages.index.astype(str), percentages.values, color=BAR_COLOR, width=0.45
    # )

    ax.set_title("Land Area Distribution by Percentage", fontsize=14, pad=12)
    ax.set_xlabel("Area Category (Hectares)", fontsize=11, labelpad=10)
    ax.set_ylabel("Percentage of Parcels (%)", fontsize=11, labelpad=10)

    plt.xticks(rotation=45, ha="right")
    ax.set_xlim(-0.6, len(labels) - 0.4)
    ax.set_ylim(0, max(percentages.values) * 1.05 if len(percentages) > 0 else 70)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info("Saved plot", path=output_path)


def plot_land_practices_distribution(
    df,
    target_col="LNA_CODIGO",
    output_path=str(PLOTS_DIR / "land_practices_distribution.png"),
):
    """Generates Top 20 Land Management Practices distribution chart."""
    logger.info("Generating Land Management Practices distribution plot...")

    if target_col not in df.columns:
        logger.error("Column 'LNA_CODIGO' missing from dataset.")
        return

    top20_lna = df[target_col].dropna().astype(str).value_counts().head(20)

    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    ax.bar(top20_lna.index, top20_lna.values, color=BAR_COLOR, width=0.45)

    ax.set_title("Top 20 Land Management Practices Distribution", fontsize=14, pad=12)
    ax.set_xlabel("Practice Code", fontsize=11, labelpad=10)
    ax.set_ylabel("Count", fontsize=11, labelpad=10)

    plt.xticks(rotation=45, ha="right")
    ax.set_xlim(-0.6, 19.4)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info("Saved plot", path=output_path)


def plot_crop_types_distribution(
    df,
    target_col="PRD_CODIGO",
    output_path=str(PLOTS_DIR / "crop_types_distribution.png"),
):
    """Generates Top 20 Crop Types distribution chart."""
    logger.info("Generating Crop Types distribution plot...")

    if target_col not in df.columns:
        logger.error("Column 'PRD_CODIGO' missing from dataset.")
        return

    top20_crops = df[target_col].dropna().astype(str).value_counts().head(20)

    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    ax.bar(top20_crops.index, top20_crops.values, color=BAR_COLOR, width=0.45)

    ax.set_title("Top 20 Crop Types Distribution", fontsize=14, pad=12)
    ax.set_xlabel("Crop Code", fontsize=11, labelpad=10)
    ax.set_ylabel("Count", fontsize=11, labelpad=10)

    plt.xticks(rotation=45, ha="right")
    ax.set_xlim(-0.6, 19.4)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info("Saved plot", path=output_path)


def plot_crop_payment_distribution(
    df,
    target_col="PRD_CODIGO",
    payment_cols=[
        "PENINSULAR_PAGO_BASE",
        "PENINSULAR_PAGO_PLURI",
        "INSULAR_PAGO_BASE",
        "INSULAR_PAGO_PLURI",
    ],
    output_path=str(PLOTS_DIR / "crop_payment_distribution.png"),
):
    """Generates Average Payment by Crop Type (Top 10) chart."""
    logger.info("Generating Average Payment by Crop Type plot...")

    if target_col not in df.columns or not any(
        col in df.columns for col in payment_cols
    ):
        logger.error("Required crop code or payment columns missing from dataset.")
        return

    # Calculate total payment per row
    df_copy = df.copy()
    for col in payment_cols:
        if col in df_copy.columns:
            df_copy[col] = pd.to_numeric(df_copy[col], errors="coerce").fillna(0)
        else:
            df_copy[col] = 0

    df_copy["TOTAL_PAYMENT"] = df_copy[payment_cols].sum(axis=1)

    # Group by crop code and calculate mean payment
    crop_avg_payment = (
        df_copy.groupby(target_col)["TOTAL_PAYMENT"]
        .mean()
        .sort_values(ascending=False)
        .head(10)
    )

    fig, ax = plt.subplots(figsize=FIGURE_SIZE)
    ax.bar(
        [str(x) for x in crop_avg_payment.index],
        crop_avg_payment.values,
        color=BAR_COLOR,
        width=0.45,
    )

    ax.set_title("Average Payment by Crop Type (Top 10)", fontsize=14, pad=12)
    ax.set_xlabel("Crop Code", fontsize=11, labelpad=10)
    ax.set_ylabel("Average Payment (Euros)", fontsize=11, labelpad=10)

    plt.xticks(rotation=45, ha="right")
    ax.set_xlim(-0.6, 9.4)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info("Saved plot", path=output_path)


def generate_dataset_plots(
    df: pd.DataFrame,
    land_area: bool = True,
    land_practices: bool = True,
    land_practices_target_col: str = "DESC_LNA",
    crop_types: bool = True,
    crop_types_target_col: str = "PRD_DESC",
    crop_payment: bool = True,
    crop_payment_target_col: str = "PRD_DESC",
) -> None:
    """Generate selected dataset distribution plots."""
    plots = {
        "land area": (land_area, plot_land_area_distribution, {}),
        "land practices": (
            land_practices,
            plot_land_practices_distribution,
            {"target_col": land_practices_target_col},
        ),
        "crop types": (
            crop_types,
            plot_crop_types_distribution,
            {"target_col": crop_types_target_col},
        ),
        "crop payment": (
            crop_payment,
            plot_crop_payment_distribution,
            {"target_col": crop_payment_target_col},
        ),
    }

    selected_plots = [
        (name, plot_func, kwargs)
        for name, (enabled, plot_func, kwargs) in plots.items()
        if enabled
    ]

    if not selected_plots:
        logger.info("No plots selected for generation.")
        return

    logger.info("Generating %d plot(s)...", len(selected_plots))

    for name, plot_func, kwargs in selected_plots:
        logger.debug("Generating %s plot...", name)
        plot_func(df, **kwargs)
        logger.info("Generated %s plot successfully.", name)

    logger.info("All %d plot(s) generated successfully.", len(selected_plots))


if __name__ == "__main__":
    OUT_DIR.mkdir(exist_ok=True)
    PLOTS_DIR.mkdir(exist_ok=True)
    years = [2023, 2024]
    for year in years:
        file_path = str(OUT_DIR / f"PAC_{year}_PROCESSED.csv")

        if not os.path.exists(file_path):
            logger.error("Dataset file does not exist", file_path=file_path)
        else:
            logger.info("Loading dataset...", file_path=file_path)
            df = pd.read_csv(file_path, encoding="latin1", low_memory=False)

            generate_dataset_plots(df)

            break  # just do one year

import csv
import os

from collections import Counter
from structlog import get_logger

from .constants import OUT_DIR

logger = get_logger(__file__)


# --- Utility / Helper Functions ---


def _get_header_analysis(file_path):
    """Read and return the dataset headers."""
    try:
        with open(file_path, "r", encoding="latin1") as f:
            reader = csv.reader(f)
            try:
                return next(reader)
            except StopIteration:
                return None
    except FileNotFoundError:
        logger.error("File not found", file_path=file_path)
        return None


# --- Data Analysis Methods ---


def analyze_land_management(headers, sample_rows=5):
    logger.info("Analyzing Land Management Practices...")
    lna_cols = [col for col in headers if "LNA" in col]
    if not lna_cols:
        logger.info("No land management practice columns found")
        return {}

    logger.info("Analyzing land practice column", column=lna_cols[0])
    return {
        "columns": lna_cols,
        "description": f"The dataset contains {len(lna_cols)} columns related to land management practices"
        if len(lna_cols) > 1
        else "The dataset contains one column for land management practices",
    }


def analyze_crop_types(headers, sample_rows=5):
    logger.info("Analyzing Crop Types...")
    prd_cols = [col for col in headers if "PRD" in col]
    if not prd_cols:
        logger.info("No crop type columns found")
        return {}

    logger.info("Analyzing crop column", column=prd_cols[0])
    return {
        "columns": prd_cols,
        "description": f"The dataset contains {len(prd_cols)} columns related to crop types and descriptions"
        if len(prd_cols) > 1
        else "The dataset contains one column for crop types",
    }


def analyze_land_area(headers, sample_rows=5):
    logger.info("Analyzing Land Area...")
    sup_cols = [col for col in headers if "SUP" in col and "HA" in col]
    if not sup_cols:
        logger.info("No land area columns found")
        return {}

    logger.info("Found area columns", columns=sup_cols)

    # Analyze area distribution characteristics
    area_types = []
    for col in sup_cols:
        col_lower = col.lower()
        if "total" in col_lower:
            area_types.append("total_area")
        elif "sec" in col_lower:
            area_types.append("dry_area")
        elif "rigo" in col_lower:
            area_types.append("irrigated_area")

    return {
        "columns": sup_cols,
        "area_types": list(set(area_types)),
        "description": f"The dataset contains {len(sup_cols)} land area columns covering total, dry, and irrigated farming",
    }


def analyze_payment_columns(headers, sample_rows=5):
    logger.info("Analyzing Payment & Funding...")
    pago_cols = [col for col in headers if "PAGO" in col]
    if not pago_cols:
        logger.info("No payment columns found")
        return {}

    logger.info("Found payment columns", columns=pago_cols)

    payment_categories = []
    for col in pago_cols:
        col_lower = col.lower()
        if "base" in col_lower:
            payment_categories.append("base_payment")
        elif "pluri" in col_lower:
            payment_categories.append("pluriannual_payment")
        elif "pen" in col_lower:
            payment_categories.append("peninsular")
        elif "ins" in col_lower:
            payment_categories.append("insular")

    return {
        "columns": pago_cols,
        "categories": list(set(payment_categories)),
        "description": f"The dataset contains {len(pago_cols)} payment columns covering base and pluriannual subsidies",
    }


def analyze_parcel_identification(headers, sample_rows=5):
    logger.info("Analyzing Parcel Identification System...")
    rec_cols = [col for col in headers if "REC" in col]
    if not rec_cols:
        logger.info("No parcel identification columns found")
        return {}

    identification_levels = []
    for col in rec_cols:
        col_lower = col.lower()
        if "poligono" in col_lower:
            identification_levels.append("polygon")
        elif "parcela" in col_lower:
            identification_levels.append("parcel")
        elif "recinto" in col_lower:
            identification_levels.append("yard")
        elif (
            "codigo" in col_lower
            and "poligono" not in col_lower
            and "parcela" not in col_lower
        ):
            identification_levels.append("code")

    return {
        "columns": rec_cols,
        "levels": list(set(identification_levels)),
        "description": f"The parcel identification system has {len(rec_cols)} components including polygons, parcels, and yards",
    }


def _analyze_column_classification(headers):
    logger.info("Analyzing Data Classification...")
    category_counts = Counter()
    column_categories = []

    for header in headers:
        header_lower = header.lower()

        # Identify data categories
        if any(keyword in header_lower for keyword in ["codigo", "id", "seq"]):
            category = "identifier"
        elif any(keyword in header_lower for keyword in ["area", "ha", "sup"]):
            category = "area_measurement"
        elif any(
            keyword in header_lower for keyword in ["tax", "taxa", "pago", "payment"]
        ):
            category = "payment"
        elif any(keyword in header_lower for keyword in ["year", "ano", "date"]):
            category = "year"
        elif any(
            keyword in header_lower for keyword in ["crop", "prod", "prd", "product"]
        ):
            category = "crop"
        elif any(
            keyword in header_lower for keyword in ["land", "lna", "land_management"]
        ):
            category = "land_practice"
        elif any(
            keyword in header_lower for keyword in ["rec", "parcel", "polygon", "yard"]
        ):
            category = "parcel_identification"
        elif any(
            keyword in header_lower for keyword in ["ecor", "ecoreg", "ecoregimen"]
        ):
            category = "ecoregime"
        else:
            category = "other"

        column_categories.append((header, category))
        category_counts[category] += 1

    logger.info(
        "Column Category Distribution",
        distribution={
            cat.replace("_", " ").title(): count
            for cat, count in category_counts.items()
        },
    )
    return category_counts, column_categories


def _analyze_naming_conventions(headers):
    logger.info("Analyzing Column Naming Conventions...")

    prefix_analysis = Counter()
    length_analysis = Counter()

    for header in headers:
        prefix_analysis[header[:3]] += 1
        length_analysis[len(header)] += 1

    logger.info(
        "Common Column Prefixes",
        prefixes=dict(prefix_analysis.most_common(10)),
    )
    logger.info(
        "Column Length Distribution",
        lengths=dict(length_analysis.most_common()),
    )
    return prefix_analysis, length_analysis


def _generate_report(
    output_file,
    file_path,
    file_size,
    headers,
    category_counts,
    parcel_id,
    land_management,
    crop_types,
    land_area,
    payments,
    insights,
):
    with open(output_file, "w", encoding="utf-8") as report:
        report.write("PAC 2023 Agricultural Parcels Data Structure Analysis Report\n")
        report.write("=" * 80 + "\n\n")

        report.write(f"Dataset: {os.path.basename(file_path)}\n")
        report.write(f"File size: {file_size / (1024 * 1024):.2f} MB\n\n")

        report.write("Column Structure:\n")
        report.write(f"  Total columns: {len(headers)}\n")
        report.write(f"  Column IDs: {headers}\n")
        report.write(f"  Column categories: {dict(category_counts)}\n\n")

        report.write("Key Components:\n")
        report.write(
            f"  - Parcel Identification: {len(parcel_id.get('columns', []))} columns\n"
        )
        report.write(
            f"  - Land Management: {len(land_management.get('columns', []))} columns\n"
        )
        report.write(f"  - Crop Types: {len(crop_types.get('columns', []))} columns\n")
        report.write(f"  - Land Area: {len(land_area.get('columns', []))} columns\n")
        report.write(f"  - Payments: {len(payments.get('columns', []))} columns\n\n")

        report.write("Key Insights:\n")
        for i, insight in enumerate(insights, 1):
            report.write(f"  {i}. {insight}\n")


# --- Pipeline / Processing Steps ---


def run_dataset_analysis(file_path, report_output_path):
    logger.info("Starting Comprehensive PAC 2023 Agricultural Data Analysis...")

    if not os.path.exists(file_path):
        logger.error("Dataset file does not exist", file_path=file_path)
        return

    file_size = os.path.getsize(file_path)
    logger.info(
        "Dataset Details",
        dataset="PAC 2023 Agricultural Parcels (Processed)",
        file_size_mb=round(file_size / (1024 * 1024), 2),
    )

    headers = _get_header_analysis(file_path)
    if headers:
        logger.info("Column Structure", total_columns=len(headers))
    else:
        logger.error("Could not read headers - terminating analysis")
        return

    logger.info("Performing Comprehensive Data Structure Analysis")

    # 1. Land Management Analysis
    land_management = analyze_land_management(headers)

    # 2. Crop Type Analysis
    crop_types = analyze_crop_types(headers)

    # 3. Land Area Analysis
    land_area = analyze_land_area(headers)

    # 4. Payment Columns
    payments = analyze_payment_columns(headers)

    # 5. Parcel Identification
    parcel_id = analyze_parcel_identification(headers)

    # 6. Column Classification Analysis
    category_counts, column_categories = _analyze_column_classification(headers)

    # 7. Column Naming Conventions Analysis
    prefix_analysis, length_analysis = _analyze_naming_conventions(headers)

    # Generate Insights Summary
    logger.info("Generating Key Data Insights Summary...")

    insights = [
        "The dataset is a comprehensive record of agricultural parcels with a multi-layered data structure",
        "Data is organized around five main categories: parcel identification, land management practices, crop types, land area measurements, and subsidy payments",
        f"The parcel identification system uses {len(parcel_id.get('columns', []))} components including polygon, parcel, and yard identifiers",
        "Land management practices are tracked using multiple columns providing detailed practice classifications",
        "Crop data is recorded with specific codes and descriptions for precise agricultural reporting",
        f"Land measurements are available in {len(land_area.get('area_types', []))} different types (total, dry, and irrigated farming areas)",
        "Payment columns cover both base subsidies and pluriannual payments, differentiated by regional type (Peninsular vs Insular)",
        f"The dataset contains {sum(category_counts.values())} total columns, indicating a highly detailed agricultural record",
        "Column naming convention suggests a structured approach with consistent prefixes (SEC, REC, LNA, PRD, SUP, etc.) for data organization",
        "The data structure is designed to support precise agricultural policy implementation and subsidy calculations",
    ]

    for i, insight in enumerate(insights, 1):
        logger.info(f"Insight {i}: {insight}")

    # Generate analysis report
    _generate_report(
        report_output_path,
        file_path,
        file_size,
        headers,
        category_counts,
        parcel_id,
        land_management,
        crop_types,
        land_area,
        payments,
        insights,
    )

    logger.info("Comprehensive analysis completed!")
    logger.info("Full structure analysis saved", report_file=report_output_path)
    if os.path.exists(report_output_path):
        logger.info(
            "Analysis summary file size",
            size_kb=round(os.path.getsize(report_output_path) / 1024, 2),
        )


if __name__ == "__main__":
    OUT_DIR.mkdir(exist_ok=True)

    years = [2023, 2024]
    for year in years:
        file_path = str(OUT_DIR / f"PAC_{year}_PROCESSED.csv")
        report_output_path = str(OUT_DIR / f"PAC_{year}_structure_analysis.txt")

        run_dataset_analysis(file_path, report_output_path)

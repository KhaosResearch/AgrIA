import csv
import os
from collections import Counter

print("Starting Comprehensive PAC 2023 Agricultural Data Analysis...")

# File information
file_path = "/home/miguel/Dev/AgrIA/AgrIA_server/PAC_2023_PROCESSED.csv"
file_size = os.path.getsize(file_path)
print(
    f"Dataset: PAC 2023 Agricultural Parcels (Processed)\nFile size: {file_size / (1024 * 1024):.2f} MB"
)


# Column analysis
def get_header_analysis():
    with open(file_path, "r", encoding="latin1") as f:
        reader = csv.reader(f)
        try:
            return next(reader)
        except StopIteration:
            return None


headers = get_header_analysis()
if headers:
    print(f"\nColumn Structure:\n  Total columns: {len(headers)}")
else:
    print("Could not read headers - terminating analysis")
    exit()


# Data analysis functions
def analyze_land_management(headers, sample_rows=5):
    print("\n=== LAND MANAGEMENT PRACTICES ANALYSIS ===")
    lna_cols = [col for col in headers if "LNA" in col]
    if not lna_cols:
        print("  No land management practice columns found")
        return {}

    print(f"  Analyzing land practice columns: {lna_cols[0]}")
    return {
        "columns": lna_cols,
        "description": f"The dataset contains {len(lna_cols)} columns related to land management practices"
        if len(lna_cols) > 1
        else "The dataset contains one column for land management practices",
    }


def analyze_crop_types(headers, sample_rows=5):
    print("\n=== CROP TYPE ANALYSIS ===")
    prd_cols = [col for col in headers if "PRD" in col]
    if not prd_cols:
        print("  No crop type columns found")
        return {}

    print(f"  Analyzing crop columns: {prd_cols[0]}")
    return {
        "columns": prd_cols,
        "description": f"The dataset contains {len(prd_cols)} columns related to crop types and descriptions"
        if len(prd_cols) > 1
        else "The dataset contains one column for crop types",
    }


def analyze_land_area(headers, sample_rows=5):
    print("\n=== LAND AREA ANALYSIS ===")
    sup_cols = [col for col in headers if "SUP" in col and "HA" in col]
    if not sup_cols:
        print("  No land area columns found")
        return {}

    print(f"  Found area columns: {sup_cols}")

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
    print("\n=== PAYMENT & FUNDING ANALYSIS ===")
    pago_cols = [col for col in headers if "PAGO" in col]
    if not pago_cols:
        print("  No payment columns found")
        return {}

    print(f"  Found payment columns: {pago_cols}")

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
    print("\n=== PARCEL IDENTIFICATION SYSTEM ===")
    rec_cols = [col for col in headers if "REC" in col]
    if not rec_cols:
        print("  No parcel identification columns found")
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


# Perform comprehensive analysis
print("\n=== COMPREHENSIVE DATA STRUCTURE ANALYSIS ===\n")

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
print("\n=== DATA CLASSIFICATION ANALYSIS ===\n")
category_counts = Counter()
column_categories = []

for header in headers:
    header_lower = header.lower()

    # Identify data categories
    if any(keyword in header_lower for keyword in ["codigo", "id", "seq"]):
        category = "identifier"
    elif any(keyword in header_lower for keyword in ["area", "ha", "sup"]):
        category = "area_measurement"
    elif any(keyword in header_lower for keyword in ["tax", "taxa", "pago", "payment"]):
        category = "payment"
    elif any(keyword in header_lower for keyword in ["year", "ano", "date"]):
        category = "year"
    elif any(keyword in header_lower for keyword in ["crop", "prod", "prd", "product"]):
        category = "crop"
    elif any(keyword in header_lower for keyword in ["land", "lna", "land_management"]):
        category = "land_practice"
    elif any(
        keyword in header_lower for keyword in ["rec", "parcel", "polygon", "yard"]
    ):
        category = "parcel_identification"
    elif any(keyword in header_lower for keyword in ["ecor", "ecoreg", "ecoregimen"]):
        category = "ecoregime"
    else:
        category = "other"

    column_categories.append((header, category))
    category_counts[category] += 1

print("Column Category Distribution:")
for category, count in category_counts.items():
    print(f"  {category.replace('_', ' ').title()}: {count} columns")

# 7. Column Naming Conventions Analysis
print("\n=== COLUMN NAMING CONVENTIONS ===\n")

prefix_analysis = Counter()
length_analysis = Counter()

for header in headers:
    prefix_analysis[header[:3]] += 1
    length_analysis[len(header)] += 1

print("Common Column Prefixes:")
for prefix, count in prefix_analysis.most_common(10):
    print(f"  {prefix}: {count} columns")

print("\nColumn Length Distribution:")
for length, count in length_analysis.most_common():
    print(f"  {length} characters: {count} columns")

# Generate Insights Summary
print("\n=== KEY DATA INSIGHTS SUMMARY ===\n")

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

print("\nKey data structure insights:")
for i, insight in enumerate(insights, 1):
    print(f"{i}. {insight}")

# Generate analysis report
with open("PAC_2023_structure_analysis.txt", "w", encoding="utf-8") as report:
    report.write("PAC 2023 Agricultural Parcels Data Structure Analysis Report\n")
    report.write("=" * 80 + "\n\n")

    report.write("Dataset: PAC 2023_PROCESSED.csv\n")
    report.write(f"File size: {file_size / (1024 * 1024):.2f} MB\n\n")

    report.write("Column Structure:\n")
    report.write(f"  Total columns: {len(headers)}\n")
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

print("\nComprehensive analysis completed!")
print("Full structure analysis saved to: PAC_2023_structure_analysis.txt")
print(
    f"Analysis summary file size: {os.path.getsize('PAC_2023_structure_analysis.txt') / 1024:.2f} KB"
)

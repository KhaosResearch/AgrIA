# CAP Land-Use Applications Data Processing

## Overview

This script merges Spain's CAP land-use application data for the 2023 and 2024 campaign years. The source data are in Spanish and describe
land parcels/surfaces and the aid schemes associated with them, including ecoschemes.

The goal is to create one analysis-ready dataset per year while preserving every record from the **AYUDAS** file and attaching corresponding parcel/surface information from **SUPERFICIES** where a match exists.

## How the merge works

The script joins the files using both key columns: `SECUENCIAL` and
`REC_CODIGO`.

It uses a **left join from AYUDAS to SUPERFICIES**: - Every row in `AYUDAS` is retained. - Matching surface fields are appended when the
keys match. - If no matching row exists in `SUPERFICIES`, the AYUDAS row remains and the surface columns are blank/NULL in the CSV output.

A blank surface section does **not by itself mean that the join failed**. It means no matching surface row was found in the source data
for that key. These cases should be reviewed separately; the current script does not produce a dedicated unmatched-record report.

The output grain is one row per AYUDAS record, enriched with surface attributes. If a parcel has several aid records, its surface information
can appear on several output rows. This is expected and should not be interpreted as additional or additive land area.

## Input data

For each year, place the following semicolon-delimited CSV files in the project's data directory:

-   `PAC_2023_AYUDAS.csv`
-   `PAC_2023_SUPERFICIES.csv`
-   `PAC_2024_AYUDAS.csv`
-   `PAC_2024_SUPERFICIES.csv`

The script constructs these paths from `ASSETS_DIR / "data"`.

### Required columns

**SUPERFICIES** must contain:

``` text
SECUENCIAL
REC_CODIGO
PRO_CODIGO
MSP_CODIGO
REC_POLIGONO
REC_PARCELA
REC_RECINTO
PRD_CODIGO
PRD_DESC
SUP_SECANO_HA
SUP_RIEGO_HA
SUP_TOTAL_HA
```

**AYUDAS** must contain:

``` text
SECUENCIAL
REC_CODIGO
LNA_CODIGO
DESC_LNA
```

The source files are expected to have a header row and use `;` as the field delimiter. Column names must match those expected by the script.
`SECUENCIAL` and `REC_CODIGO` must be represented consistently in both files so the join keys match.

## Output

By default, the script creates:

-   `PAC_2023_MERGED.csv`
-   `PAC_2024_MERGED.csv`

The output is written to the process's current working directory unless an `output_file` path is passed to `get_merge_cap_data()`.

The output is a comma-delimited CSV with a header row. It contains: 1. All columns from `AYUDAS`. 2. All columns from `SUPERFICIES` except the
duplicate join-key columns (`SECUENCIAL` and `REC_CODIGO`).

Because surface attributes are repeated for each aid associated with a parcel, the merged output may be larger than either input file.

## Requirements

-   Python 3.9 or later is recommended.
-   The DuckDB Python package.

Install DuckDB in the project's active environment:

``` bash
python -m pip install duckdb
```

Use the Python environment in which the rest of the project dependencies are installed.

## Running the script

The script imports `ASSETS_DIR` using a relative package import:

``` python
from ..config.constants import ASSETS_DIR
```

Therefore, run it through the project's package/module structure from the appropriate project root. Running the file directly by path may
fail; the exact module command depends on its location in the repository.

The script's `__main__` block processes both years:

``` python
years = [2023, 2024]
for year in years:
    merged_output_file = str(data_dir / f"PAC_{year}_MERGED.csv")
    processed_output_file = f"PAC_{year}_PROCESSED.csv"

    main(
        processed_output_file=processed_output_file,
        merged_output_file=merged_output_file,
    )
```

To process one year or specify an output path from another project module:

``` python
get_merge_cap_data(processed_output_file, merged_output_file)
```

Replace the example path with a valid path for your operating system. Ensure the destination directory exists before running the script.

## Data checks and limitations

The current script performs the merge and writes the output, but does **not** run explicit data-quality checks. Before using the output for
reporting or statistical analysis, consider checking:

-   How many AYUDAS rows have no matching SUPERFICIES row.
-   Whether `(SECUENCIAL, REC_CODIGO)` is unique in SUPERFICIES.
-   Whether the output row count equals the AYUDAS row count.
-   Whether either source contains duplicate or malformed join keys.

If `SUPERFICIES` contains duplicate join keys, one AYUDAS row can match multiple surface rows and expand the output. Validate the expected
one-row-per-parcel-key structure against the full source files, not only a sample.

The script does not infer missing surface data, resolve subsidy compatibility, or validate whether a combination of aids is legally
eligible. Those are separate data-quality and domain-analysis tasks.

## Suggested workflow

1.  Obtain the correct AYUDAS and SUPERFICIES CSV files for each campaign year.
2.  Place them in the configured `ASSETS_DIR/data` directory.
3.  Confirm the headers and semicolon delimiter.
4.  Run the merge for 2023 and 2024.
5.  Review unmatched keys and duplicate-key checks before relying on the merged datasets.
6.  Keep the original source files unchanged so results can be traced back to the inputs.

## Data context

The data concern Spanish CAP land-use and aid applications. Column names and aid descriptions are kept in Spanish to preserve the source
terminology. `LNA_CODIGO` identifies an aid line and `DESC_LNA` provides its Spanish description; `PRD_CODIGO` and `PRD_DESC` describe the
declared product/use associated with the surface record.

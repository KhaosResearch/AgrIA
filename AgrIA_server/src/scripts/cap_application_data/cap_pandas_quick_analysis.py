import pandas as pd

from ...config.constants import ASSETS_DIR

# ============================================================
# FILES
# ============================================================

AYUDAS_FILE = ASSETS_DIR / "data" / "PAC_2023_AYUDAS.csv"
SUPERFICIES_FILE = ASSETS_DIR / "data" / "PAC_2023_SUPERFICIES.csv"

# Number of applications/farmers to inspect
N_SAMPLES = 20

# Chunk size: adjust according to your RAM
CHUNKSIZE = 100_000


# ============================================================
# 1. GET A SAMPLE OF SECUENCIAL
# ============================================================

secuenciales = []

for chunk in pd.read_csv(
    AYUDAS_FILE, sep=";", usecols=["SECUENCIAL"], chunksize=CHUNKSIZE
):
    values = chunk["SECUENCIAL"].dropna().unique()

    secuenciales.extend(values)

    if len(secuenciales) >= N_SAMPLES:
        break

secuenciales = secuenciales[:N_SAMPLES]

print("Selected SECUENCIALES:")
print(secuenciales)


# ============================================================
# 2. FUNCTION TO EXTRACT COMPLETE RECORDS
# ============================================================


def extract_records(filename, secuenciales):
    pieces = []

    for chunk in pd.read_csv(filename, sep=";", chunksize=CHUNKSIZE):
        filtered = chunk[chunk["SECUENCIAL"].isin(secuenciales)]

        if not filtered.empty:
            pieces.append(filtered)

    return pd.concat(pieces, ignore_index=True)


# ============================================================
# 3. EXTRACT SAMPLE
# ============================================================

print("\nReading AYUDAS sample...")

ayudas = extract_records(AYUDAS_FILE, secuenciales)

print(f"AYUDAS rows: {len(ayudas):,}")


print("\nReading SUPERFICIES sample...")

superficies = extract_records(SUPERFICIES_FILE, secuenciales)

print(f"SUPERFICIES rows: {len(superficies):,}")


# ============================================================
# 4. BASIC INFORMATION
# ============================================================

print("\n================ AYUDAS ================")

print(ayudas.head())
print("\nColumns:")
print(ayudas.columns.tolist())

print("\n================ SUPERFICIES ================")

print(superficies.head())
print("\nColumns:")
print(superficies.columns.tolist())


# ============================================================
# 5. HOW MANY AIDS PER PARCEL?
# ============================================================

ayudas_por_parcela = (
    ayudas.groupby(["SECUENCIAL", "REC_CODIGO"]).size().reset_index(name="N_AYUDAS")
)

print("\n================ AYUDAS PER PARCEL ================")

print(ayudas_por_parcela.sort_values("N_AYUDAS", ascending=False).head(30))


# ============================================================
# 6. HOW MANY SURFACE RECORDS PER PARCEL?
# ============================================================

superficies_por_parcela = (
    superficies.groupby(["SECUENCIAL", "REC_CODIGO"])
    .size()
    .reset_index(name="N_SUPERFICIES")
)

print("\n================ SUPERFICIES PER PARCEL ================")

print(superficies_por_parcela.sort_values("N_SUPERFICIES", ascending=False).head(30))


# ============================================================
# 7. COMBINE THE COUNTS
# ============================================================

relacion = ayudas_por_parcela.merge(
    superficies_por_parcela, on=["SECUENCIAL", "REC_CODIGO"], how="outer"
)

print("\n================ RELATIONSHIP ================")

print(relacion.sort_values(["N_AYUDAS", "N_SUPERFICIES"], ascending=False).head(50))


# ============================================================
# 8. SHOW ALL SURFACES FOR THE SAME APPLICATION
# ============================================================

example_secuencial = secuenciales[0]

print("\n================ EXAMPLE SURFACES ================")

print(
    superficies[superficies["SECUENCIAL"] == example_secuencial]
    .sort_values(["REC_CODIGO"])
    .to_string(index=False)
)


# ============================================================
# 9. SHOW ALL AIDS FOR ONE SECUENCIAL
# ============================================================

print("\n================ EXAMPLE APPLICATION ================")

print(
    ayudas[ayudas["SECUENCIAL"] == example_secuencial]
    .sort_values(["REC_CODIGO", "LNA_CODIGO"])
    .to_string(index=False)
)

print("\n" + "=" * 80 + "\n")

# ============================================================
# 1. CHECK IF REC_CODIGO IS UNIQUE WITHIN SECUENCIAL
# ============================================================

parcel_duplicates = (
    superficies.groupby(["SECUENCIAL", "REC_CODIGO"]).size().reset_index(name="COUNT")
)

print("\n================ DUPLICATE PARCEL KEYS ================")

duplicates = parcel_duplicates[parcel_duplicates["COUNT"] > 1]

print(f"Duplicate SECUENCIAL + REC_CODIGO combinations: {len(duplicates):,}")

print(duplicates.head(30))


# ============================================================
# 2. CHECK WHETHER THE OTHER SURFACE IDENTIFIERS
#    ARE ACTUALLY DIFFERENT WITHIN A REC_CODIGO
# ============================================================

surface_structure = (
    superficies.groupby(["SECUENCIAL", "REC_CODIGO"])
    .agg(
        N_PRO=("PRO_CODIGO", "nunique"),
        N_MSP=("MSP_CODIGO", "nunique"),
        N_POLIGONO=("REC_POLIGONO", "nunique"),
        N_PARCELA=("REC_PARCELA", "nunique"),
        N_RECINTO=("REC_RECINTO", "nunique"),
        N_PRD=("PRD_CODIGO", "nunique"),
    )
    .reset_index()
)

print("\n================ STRUCTURE OF REC_CODIGO ================")

print(
    surface_structure[
        (surface_structure["N_PRO"] > 1)
        | (surface_structure["N_MSP"] > 1)
        | (surface_structure["N_POLIGONO"] > 1)
        | (surface_structure["N_PARCELA"] > 1)
        | (surface_structure["N_RECINTO"] > 1)
        | (surface_structure["N_PRD"] > 1)
    ].head(50)
)


# ============================================================
# 3. IDENTIFY ECOSCHEMES
# ============================================================

ayudas["ES_ECOSCHEME"] = ayudas["LNA_CODIGO"].astype(str).str.startswith("5")

print("\n================ ECOSCHEMES ================")

print(
    ayudas[ayudas["ES_ECOSCHEME"]][
        ["SECUENCIAL", "REC_CODIGO", "LNA_CODIGO", "DESC_LNA"]
    ]
    .drop_duplicates()
    .sort_values(["SECUENCIAL", "REC_CODIGO", "LNA_CODIGO"])
    .head(100)
)


# ============================================================
# 4. CHECK FOR MULTIPLE ECOSCHEMES ON THE SAME PARCEL
# ============================================================

ecos_por_parcela = (
    ayudas[ayudas["ES_ECOSCHEME"]]
    .groupby(["SECUENCIAL", "REC_CODIGO"])["LNA_CODIGO"]
    .nunique()
    .reset_index(name="N_ECOSCHEMES")
)

multiple_ecos = ecos_por_parcela[ecos_por_parcela["N_ECOSCHEMES"] > 1]

print("\n================ MULTIPLE ECOSCHEMES ================")

print(f"Parcels with >1 ecoscheme: {len(multiple_ecos):,}")

print(multiple_ecos.head(50))


# ============================================================
# 5. SHOW WHICH ECOSCHEMES ARE BEING COMBINED
# ============================================================

ecos_combinations = (
    ayudas[ayudas["ES_ECOSCHEME"]]
    .groupby(["SECUENCIAL", "REC_CODIGO"])["LNA_CODIGO"]
    .apply(lambda x: sorted(x.astype(str).unique()))
    .reset_index(name="ECOSCHEMES")
)

print("\n================ ECOSCHEME COMBINATIONS ================")

print(ecos_combinations.head(50))


# ============================================================
# 6. COUNT AIDS BY PARCEL, SEPARATING ECOSCHEMES
# ============================================================

aid_structure = (
    ayudas.groupby(["SECUENCIAL", "REC_CODIGO"])
    .agg(TOTAL_AIDS=("LNA_CODIGO", "nunique"), ECOSCHEMES=("ES_ECOSCHEME", "sum"))
    .reset_index()
)

aid_structure["OTHER_AIDS"] = aid_structure["TOTAL_AIDS"] - aid_structure["ECOSCHEMES"]

print("\n================ AID STRUCTURE ================")

print(aid_structure.sort_values(["TOTAL_AIDS"], ascending=False).head(50))


# ============================================================
# 7. FIND PARCELS WITH MULTIPLE AIDS
# ============================================================

multiple_aids = aid_structure[aid_structure["TOTAL_AIDS"] > 1]

print("\n================ MULTIPLE AIDS ================")

print(f"Parcels with multiple aids: {len(multiple_aids):,}")

print(multiple_aids.head(50))


# ============================================================
# 8. SHOW THE ACTUAL AID COMBINATIONS
# ============================================================

aid_combinations = (
    ayudas.groupby(["SECUENCIAL", "REC_CODIGO"])
    .agg(
        AIDS=("LNA_CODIGO", lambda x: sorted(x.astype(str).unique())),
        DESCRIPTIONS=("DESC_LNA", lambda x: sorted(x.astype(str).unique())),
    )
    .reset_index()
)

print("\n================ AID COMBINATIONS ================")

print(aid_combinations.head(50))


# ============================================================
# 9. CHECK WHETHER ALL AYUDAS KEYS EXIST IN SUPERFICIES
# ============================================================

ayudas_keys = ayudas[["SECUENCIAL", "REC_CODIGO"]].drop_duplicates()

superficies_keys = superficies[["SECUENCIAL", "REC_CODIGO"]].drop_duplicates()

missing_surfaces = ayudas_keys.merge(
    superficies_keys, on=["SECUENCIAL", "REC_CODIGO"], how="left", indicator=True
)

missing_surfaces = missing_surfaces[missing_surfaces["_merge"] == "left_only"]

print("\n================ AYUDAS WITHOUT SUPERFICIES ================")

print(f"AYUDAS parcel keys without SUPERFICIES: {len(missing_surfaces):,}")

print(missing_surfaces.head(50))


# ============================================================
# 10. CHECK THE OPPOSITE
# ============================================================

missing_ayudas = superficies_keys.merge(
    ayudas_keys, on=["SECUENCIAL", "REC_CODIGO"], how="left", indicator=True
)

missing_ayudas = missing_ayudas[missing_ayudas["_merge"] == "left_only"]

print("\n================ SUPERFICIES WITHOUT AYUDAS ================")

print(f"SUPERFICIES parcel keys without AYUDAS: {len(missing_ayudas):,}")

print(missing_ayudas.head(50))

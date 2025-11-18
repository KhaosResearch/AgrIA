import pytest
from decimal import Decimal
import json

# --- Dummy Rules Data Fixture (Minimal set covering all assigned schemes) ---
@pytest.fixture
def dummy_rules_data():
    """Provides a sample of the raw rules data dictionary based on the expected output."""
    return [
        # P1 - Extensive Grazing (Mediterranean Pastures)
        {
            "Ecoscheme": "P1 - Extensive Grazing (Mediterranean Pastures)",
            "Land_Uses": "PA, PR, PS, MT",
            "Rates": {
                "Threshold_ha": "95.0",
                "Pluriannuality": "N/A", # No bonus
                "Peninsular": {"Tier_1": "27.27", "Tier_2": "27.27"},
                "Insular": {"Tier_1": "49.27", "Tier_2": "49.27"},
            }
        },
        # P3/P4 - Rotation/No-Till (Irrigated)
        {
            "Ecoscheme": "P3/P4 - Rotation/No-Till (Irrigated)",
            "Land_Uses": "TA",
            "Rates": {
                "Threshold_ha": "30.0", # Set > 22.7474ha to force Tier 1
                "Pluriannuality": "Applicable", # Bonus applies
                "Peninsular": {"Tier_1": "141.742439", "Tier_2": "100.00"}, # Tier 2 assumed lower
                "Insular": {"Tier_1": "221.742439", "Tier_2": "180.00"},
            }
        },
        # P5(B) - Biodiversity Spaces (Under Water)
        {
            "Ecoscheme": "P5(B) - Biodiversity Spaces (Under Water)",
            "Land_Uses": "AG",
            "Rates": {
                "Threshold_ha": "N/A",
                "Pluriannuality": "N/A",
                "Peninsular": "145.098595", # Flat Rate
                "Insular": "0.0",
            }
        },
        # P6/P7 - Plant Cover (Flat Woody Crops)
        {
            "Ecoscheme": "P6/P7 - Plant Cover (Flat Woody Crops)",
            "Land_Uses": "VI, FY",
            "Rates": {
                "Threshold_ha": "15.0", # Set > 9.4863ha to force Tier 1
                "Pluriannuality": "Applicable", # Bonus applies
                "Peninsular": {"Tier_1": "59.12", "Tier_2": "41.384"},
                "Insular": {"Tier_1": "99.12", "Tier_2": "81.384"},
            }
        },
        # Non-Eligible Scheme (Includes all non-eligible LUs from the sample)
        {
            "Ecoscheme": "Non-Eligible Scheme",
            "Land_Uses": "FO, CA, IM, ED, ZU",
            "Rates": {}
        }
    ]

# --- Parsed Data Fixture (Simulating dictionary after parsing the input string) ---
@pytest.fixture
def parsed_data_fixture():
    """Provides the dictionary structure of parsed input land uses based on the new sample."""
    return {
        "TA": {"area": Decimal("22.7474"), "irrigation_coef": "83.0%", "slope_coef": ""},
        "VI": {"area": Decimal("9.3441"), "irrigation_coef": "89.88%", "slope_coef": "1.01%"},
        "FO": {"area": Decimal("3.4562"), "irrigation_coef": "80.0%", "slope_coef": ""},
        "AG": {"area": Decimal("0.4099"), "irrigation_coef": "0.0%", "slope_coef": ""},
        "PA": {"area": Decimal("0.1257"), "irrigation_coef": "100.0%", "slope_coef": ""},
        "PS": {"area": Decimal("0.2272"), "irrigation_coef": "100.0%", "slope_coef": ""},
        "PR": {"area": Decimal("4.0175"), "irrigation_coef": "100.0%", "slope_coef": ""},
        "CA": {"area": Decimal("0.4838"), "irrigation_coef": "0.0%", "slope_coef": ""},
        "IM": {"area": Decimal("1.9813"), "irrigation_coef": "0.0%", "slope_coef": ""},
        "MT": {"area": Decimal("2.6999"), "irrigation_coef": "20.0%", "slope_coef": ""},
        "ED": {"area": Decimal("0.0894"), "irrigation_coef": "0.0%", "slope_coef": ""},
        "ZU": {"area": Decimal("0.0086"), "irrigation_coef": "0.0%", "slope_coef": ""},
        "FY": {"area": Decimal("0.1422"), "irrigation_coef": "100.0%", "slope_coef": "1.7%"},
    }

# --- Input Data String Fixture (For end-to-end test) ---
@pytest.fixture
def sample_input_data_str():
    """Provides the multi-LU string input for the main function test."""
    return """
        - Land Use: TA
        - Eligible surface (ha): 22.7474
        - Irrigation Coeficient: 83.0%

        - Land Use: VI
        - Eligible surface (ha): 9.3441
        - Irrigation Coeficient: 89.88%
        - Slope Coeficient: 1.01%

        - Land Use: FO
        - Eligible surface (ha): 3.4562
        - Irrigation Coeficient: 80.0%

        - Land Use: AG
        - Eligible surface (ha): 0.4099
        - Irrigation Coeficient: 0.0%

        - Land Use: PA
        - Eligible surface (ha): 0.1257
        - Irrigation Coeficient: 100.0%

        - Land Use: PS
        - Eligible surface (ha): 0.2272
        - Irrigation Coeficient: 100.0%

        - Land Use: PR
        - Eligible surface (ha): 4.0175
        - Irrigation Coeficient: 100.0%

        - Land Use: CA
        - Eligible surface (ha): 0.4838
        - Irrigation Coeficient: 0.0%

        - Land Use: IM
        - Eligible surface (ha): 1.9813
        - Irrigation Coeficient: 0.0%

        - Land Use: MT
        - Eligible surface (ha): 2.6999
        - Irrigation Coeficient: 20.0%

        - Land Use: ED
        - Eligible surface (ha): 0.0894
        - Irrigation Coeficient: 0.0%

        - Land Use: ZU
        - Eligible surface (ha): 0.0086
        - Irrigation Coeficient: 0.0%

        - Land Use: FY
        - Eligible surface (ha): 0.1422
        - Irrigation Coeficient: 100.0%
        - Slope Coeficient: 1.7%

        TOTAL ELIGIBLE SURFACE (ha): 45.733
    """
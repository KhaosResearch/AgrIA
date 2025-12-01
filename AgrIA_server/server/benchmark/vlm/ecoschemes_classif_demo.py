from datetime import datetime, timedelta
import json
import os
import structlog
from decimal import Decimal

from ...benchmark.vlm.constants import CLASSIFICATION_OUT_DIR
from ...services.ecoscheme_payments.main import calculate_ecoscheme_payment
from ...utils.parcel_finder_utils import reset_dir


# Fixed constant for the pluriannuality bonus (€25.00/ha) as per instructions
PLURIANNUALITY_BONUS_PER_HA = Decimal('25.00')

# Define rounding constants
ROUNDING_RATE = Decimal('0.000001')  # 6 decimals for applied rate
ROUNDING_AREA = Decimal('0.0001')   # 4 decimals for total area
ROUNDING_PAYMENT = Decimal('0.01')  # 2 decimals for total payments

logger = structlog.get_logger()


# Example usage
def demo():

    init_time = datetime.now()

    cad_ref_dict = {
        "en": {
            "26002A001000010000EQ": """IMAGE DATE: 2025-6-6
        LAND USES DETECTED: 13

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
        """,
            "14048A001001990000RM": """IMAGE DATE: 2024-10-19
        LAND USES DETECTED: 2

        - Land Use: OV
        - Eligible surface (ha): 7.4659
        - Irrigation Coeficient: 0.0%
        - Slope Coeficient: 12.4%

        - Land Use: CA
        - Eligible surface (ha): 0.0352
        - Irrigation Coeficient: 0.0%

        TOTAL ELIGIBLE SURFACE (ha): 7.501

        """,
            "45054A067000090000QA": """IMAGE DATE: 2025-03-30
        LAND USES DETECTED: 2

        - Land Use: IM
        - Eligible surface (ha): 0.0065
        - Irrigation Coeficient: 0.0%

        - Land Use: TA
        - Eligible surface (ha): 42.8326
        - Irrigation Coeficient: 0.0%

        TOTAL ELIGIBLE SURFACE (ha): 42.839

        """,
            "43157A024000010000KE": """IMAGE DATE: 2024-03-15
        LAND USES DETECTED: 4

        - Land Use: OV
        - Eligible surface (ha): 30.7162
        - Irrigation Coeficient: 0.0%
        - Slope Coeficient: 4.7%

        - Land Use: PR
        - Eligible surface (ha): 0.3574
        - Irrigation Coeficient: 0.0%

        - Land Use: IM
        - Eligible surface (ha): 0.0966
        - Irrigation Coeficient: 0.0%

        - Land Use: ED
        - Eligible surface (ha): 0.0065
        - Irrigation Coeficient: 0.0%

        TOTAL ELIGIBLE SURFACE (ha): 31.177

        """
        },
        "es": {
            "26002A001000010000EQ": """FECHA DE IMAGEN: 2025-6-6
        TIPOS DE USO DETECTADAS: 13

        - Tipo de Uso: TA
        - Superficie admisible (ha): 22.7474
        - Coef. de Regadío: 83.0%

        - Tipo de Uso: VI
        - Superficie admisible (ha): 9.3441
        - Coef. de Regadío: 89.88%
        - Pendiente media: 1.01%

        - Tipo de Uso: FO
        - Superficie admisible (ha): 3.4562
        - Coef. de Regadío: 80.0%

        - Tipo de Uso: AG
        - Superficie admisible (ha): 0.4099
        - Coef. de Regadío: 0.0%

        - Tipo de Uso: PA
        - Superficie admisible (ha): 0.1257
        - Coef. de Regadío: 100.0%

        - Tipo de Uso: PS
        - Superficie admisible (ha): 0.2272
        - Coef. de Regadío: 100.0%

        - Tipo de Uso: PR
        - Superficie admisible (ha): 4.0175
        - Coef. de Regadío: 100.0%

        - Tipo de Uso: CA
        - Superficie admisible (ha): 0.4838
        - Coef. de Regadío: 0.0%

        - Tipo de Uso: IM
        - Superficie admisible (ha): 1.9813
        - Coef. de Regadío: 0.0%

        - Tipo de Uso: MT
        - Superficie admisible (ha): 2.6999
        - Coef. de Regadío: 20.0%

        - Tipo de Uso: ED
        - Superficie admisible (ha): 0.0894
        - Coef. de Regadío: 0.0%

        - Tipo de Uso: ZU
        - Superficie admisible (ha): 0.0086
        - Coef. de Regadío: 0.0%

        - Tipo de Uso: FY
        - Superficie admisible (ha): 0.1422
        - Coef. de Regadío: 100.0%
        - Pendiente media: 1.7%

        SUPERFICIE ADMISIBLE TOTAL (ha): 45.733
        """,
            "14048A001001990000RM": """FECHA DE IMAGEN: 2024-10-19
        TIPOS DE USO DETECTADAS: 2

        - Tipo de Uso: OV
        - Superficie admisible (ha): 7.4659
        - Coef. de Regadío: 0.0%
        - Pendiente media: 12.4%

        - Tipo de Uso: CA
        - Superficie admisible (ha): 0.0352
        - Coef. de Regadío: 0.0%

        SUPERFICIE ADMISIBLE TOTAL (ha): 7.501
        """,
            "45054A067000090000QA": """FECHA DE IMAGEN: 2025-03-30
        TIPOS DE USO DETECTADAS: 2

        - Tipo de Uso: IM
        - Superficie admisible (ha): 0.0065
        - Coef. de Regadío: 0.0%

        - Tipo de Uso: TA
        - Superficie admisible (ha): 42.8326
        - Coef. de Regadío: 0.0%

        SUPERFICIE ADMISIBLE TOTAL (ha): 42.839
        """,
            "43157A024000010000KE": """FECHA DE IMAGEN: 2024-03-15
        TIPOS DE USO DETECTADAS: 4

        - Tipo de Uso: OV
        - Superficie admisible (ha): 30.7162
        - Coef. de Regadío: 0.0%
        - Pendiente media: 4.7%

        - Tipo de Uso: PR
        - Superficie admisible (ha): 0.3574
        - Coef. de Regadío: 0.0%

        - Tipo de Uso: IM
        - Superficie admisible (ha): 0.0966
        - Coef. de Regadío: 0.0%

        - Tipo de Uso: ED
        - Superficie admisible (ha): 0.0065
        - Coef. de Regadío: 0.0%

        SUPERFICIE ADMISIBLE TOTAL (ha): 31.177
        """
        }
    }

    languages = ["EN", "ES"]

    os.makedirs(CLASSIFICATION_OUT_DIR, exist_ok=True)
    reset_dir(CLASSIFICATION_OUT_DIR)

    for lang in languages:
        # Get ecoschemes classification
        data_dict = cad_ref_dict[lang.lower()]
        for key in data_dict.keys():
            output_dict = calculate_ecoscheme_payment(data_dict[key], lang)
            out_path = CLASSIFICATION_OUT_DIR / f"{key}_example_{lang}.json"
            with open(out_path, 'w') as file:
                json.dump(output_dict, file, indent=4)
            logger.info(f"Ecoscheme classification saved to {out_path}")
        logger.debug(f"Current Lang:\t{lang}")
    time_taken = (datetime.now() - init_time).total_seconds()
    time_taken_formatted = str(timedelta(seconds=time_taken))
    logger.info(f"Time taken for parcel processing {time_taken_formatted}")


demo()

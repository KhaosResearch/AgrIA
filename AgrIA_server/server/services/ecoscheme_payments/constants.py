from decimal import Decimal

# Fixed constant for the pluriannuality bonus (€25.00/ha) as per instructions
PLURIANNUALITY_BONUS_PER_HA = Decimal('25.00')

# Define rounding constants
ROUNDING_RATE = Decimal('0.000001') # 6 decimals for applied rate
ROUNDING_AREA = Decimal('0.0001')   # 4 decimals for total area
ROUNDING_PAYMENT = Decimal('0.01')  # 2 decimals for total payments

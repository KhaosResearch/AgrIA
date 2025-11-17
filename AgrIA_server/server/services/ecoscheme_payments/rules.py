from decimal import Decimal

def get_ecoscheme_rules_data(rules_data_list) -> dict:
    eligible_schemes_by_land_use = {}
    non_eligible_uses = set()
    
    for rule in rules_data_list:
        scheme_full_name = rule['Ecoscheme']
        

        scheme_parts = scheme_full_name.split(' - ')
        if len(scheme_parts) < 2:
            non_eligible_uses.update(rule['Land_Uses'].split(', '))
            continue
        scheme_id = scheme_parts[0]
        scheme_name = scheme_parts[1].split('(')[0].strip()
        scheme_subtype = scheme_full_name.split('(')[-1].strip(')')
        
        land_use_list = rule['Land_Uses'].split(', ')
        
        rates = rule['Rates']
        threshold_ha = str(rates['Threshold_ha'])
        threshold = Decimal(threshold_ha) if threshold_ha.replace('.', '', 1).isdigit() else None
        pluri_applicable = rates['Pluriannuality'] != 'N/A'
        
        base_rate_details = get_base_rate_details(rates, threshold)

        for land_use in land_use_list:
            if land_use not in eligible_schemes_by_land_use:
                eligible_schemes_by_land_use[land_use] = []
            
            eligible_schemes_by_land_use[land_use].append({
                'id': scheme_id,
                'name': scheme_name,
                'subtype': scheme_subtype,
                'rates': base_rate_details, # Contains {'Peninsular': {...}, 'Insular': {...}}
                'pluriannuality_applicable': pluri_applicable,
            })
            
    return eligible_schemes_by_land_use, non_eligible_uses

def get_base_rate_details(rates: dict, threshold: Decimal, keys: list = ["Peninsular", "Insular"]) -> dict:
    """Extracts and formats Tier/Flat rate details for both Peninsular and Insular areas."""
    base_rate_details = {}
    for key in keys:
        key_rates = rates.get(key)
        if key_rates is None: continue # Skip if rate type is missing
        if isinstance(key_rates, dict):
            # Tiered rates (Tier_1, Tier_2, Threshold_ha)
            tier1 = 0 if '/' in str(key_rates['Tier_1']) else Decimal(str(key_rates['Tier_1']))
            tier2 = 0 if '/' in str(key_rates['Tier_2']) else Decimal(str(key_rates['Tier_2']))
            base_rate_details[key] = {'Tier_1': tier1, 'Tier_2': tier2, 'Threshold_ha': threshold}
        else:
            # Flat rate
            # Handle potential string/Decimal conversion
            flat_rate_value = key_rates if isinstance(key_rates, str) else Decimal(str(key_rates))
            base_rate_details[key] = {'Flat': flat_rate_value}
            
    return base_rate_details

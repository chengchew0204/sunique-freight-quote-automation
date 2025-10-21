"""
Pallet Calculation Logic
Ported from development/main.py lines 582-760
"""

# Pallet specifications
STANDARD_PALLET_LENGTH = 48
STANDARD_PALLET_WIDTH = 40
LONG_PALLET_LENGTH = 96
LONG_PALLET_WIDTH = 48

# Calculate the base areas of the pallets (in square inches)
STANDARD_PALLET_BASE_AREA = STANDARD_PALLET_LENGTH * STANDARD_PALLET_WIDTH
LONG_PALLET_BASE_AREA = LONG_PALLET_LENGTH * LONG_PALLET_WIDTH

# Pallet limits
PALLET_HEIGHT_LIMIT = 60  # Maximum pallet height (in inches)
PALLET_WEIGHT_LIMIT = 2200  # Maximum pallet weight (in lbs)


def determine_order_situation(products_df):
    """
    Determine if order contains Index 100 products
    Ported from development/main.py lines 596-604
    """
    if 100 in products_df['Index'].values:
        return "Contains Index 100"
    else:
        return "Index 0 Only"


def calculate_pallets(selected_sales_order, order_situation):
    """
    Calculate optimal pallet configuration based on order situation
    Ported from development/main.py lines 606-760
    
    Args:
        selected_sales_order: DataFrame with product information
        order_situation: String indicating order type
        
    Returns:
        tuple: (pallets list, total_weight, total_volume)
    """
    pallets = []
    
    # Calculate total volume and weight
    total_volume = (selected_sales_order['Length'] * 
                    selected_sales_order['Width'] * 
                    selected_sales_order['Height'] * 
                    selected_sales_order['quantity']).sum()
    total_weight = (selected_sales_order['weight(kg)'] * 
                    selected_sales_order['quantity'] * 
                    2.20462).sum()  # Convert to lbs

    if order_situation == "Index 0 Only":
        # Situation 1: All Index 0 products
        height = total_volume / STANDARD_PALLET_BASE_AREA
        num_pallets = 0
        while height > PALLET_HEIGHT_LIMIT:
            num_pallets += 1
            height -= PALLET_HEIGHT_LIMIT
        if height > 0:
            num_pallets += 1

        # Create pallets
        for i in range(num_pallets):
            pallets.append({
                'Type': 'Standard',
                'Height': PALLET_HEIGHT_LIMIT if i < num_pallets - 1 else height,
                'Weight': 0  # Placeholder for weight
            })

    elif order_situation == "Contains Index 100":
        # Situation 3: Contains Index 100 products
        index_100_products = selected_sales_order[selected_sales_order['Index'] == 100]
        index_100_volume = (index_100_products['Length'] *
                            index_100_products['Width'] *
                            index_100_products['Height'] *
                            index_100_products['quantity']).sum()
        index_100_weight = (index_100_products['weight(kg)'] *
                            index_100_products['quantity'] * 
                            2.20462).sum()

        height_100 = index_100_volume / LONG_PALLET_BASE_AREA
        remaining_volume = total_volume - index_100_volume
        remaining_weight = total_weight - index_100_weight

        # Allocate long pallets for Index 100 products while considering weight limit
        while height_100 > 0 and index_100_weight > 0:
            pallet_height = min(height_100, PALLET_HEIGHT_LIMIT)

            # Calculate the volume for this pallet
            pallet_volume = pallet_height * LONG_PALLET_BASE_AREA

            # Determine the proportion of volume assigned
            proportion = pallet_volume / index_100_volume

            # Calculate the corresponding weight
            pallet_weight = min(index_100_weight * proportion, PALLET_WEIGHT_LIMIT)

            pallets.append({
                'Type': 'Long',
                'Height': pallet_height,
                'Weight': pallet_weight
            })

            height_100 -= pallet_height
            index_100_weight -= pallet_weight

        # Allocate remaining products, prioritizing filling the last long pallet first
        last_long_pallet = pallets[-1] if pallets and pallets[-1]['Type'] == 'Long' else None
        if last_long_pallet:
            available_height = PALLET_HEIGHT_LIMIT - last_long_pallet['Height']
            available_weight = PALLET_WEIGHT_LIMIT - last_long_pallet['Weight']
            available_volume = available_height * LONG_PALLET_BASE_AREA

            volume_to_add = min(remaining_volume, available_volume)
            weight_to_add = min(remaining_weight, available_weight)

            if volume_to_add > 0 and weight_to_add > 0:
                last_long_pallet['Height'] += volume_to_add / LONG_PALLET_BASE_AREA
                last_long_pallet['Weight'] += weight_to_add
                remaining_volume -= volume_to_add
                remaining_weight -= weight_to_add

        # Allocate standard pallets for remaining products while maintaining weight constraints
        while remaining_volume > PALLET_HEIGHT_LIMIT * STANDARD_PALLET_BASE_AREA or remaining_weight > PALLET_WEIGHT_LIMIT:
            pallet_height = min(remaining_volume / STANDARD_PALLET_BASE_AREA, PALLET_HEIGHT_LIMIT)
            pallet_weight = min(remaining_weight, PALLET_WEIGHT_LIMIT)

            pallets.append({
                'Type': 'Standard',
                'Height': pallet_height,
                'Weight': pallet_weight
            })

            remaining_volume -= pallet_height * STANDARD_PALLET_BASE_AREA
            remaining_weight -= pallet_weight

        if remaining_volume > 0 or remaining_weight > 0:
            pallets.append({
                'Type': 'Standard',
                'Height': remaining_volume / STANDARD_PALLET_BASE_AREA,
                'Weight': remaining_weight
            })

    # Redistribute weight based on actual pallet volume (lines 711-720)
    for pallet in pallets:
        if pallet['Height'] < 96:
            # Use exact height for weight calculation
            pallet_volume = pallet['Height'] * STANDARD_PALLET_BASE_AREA
        else:
            # Cap the height at 96 for weight calculation if it's greater than 96
            pallet_volume = 96 * STANDARD_PALLET_BASE_AREA

        # Calculate weight based on actual pallet volume
        pallet['Weight'] = (pallet_volume / total_volume) * total_weight

    return pallets, total_weight, total_volume


def adjust_low_height_pallets(pallets, total_volume, total_weight):
    """
    Adjust low-height last pallet by redistributing to other pallets
    Ported from development/main.py lines 729-760
    
    Args:
        pallets: List of pallet dictionaries
        total_volume: Total order volume
        total_weight: Total order weight
        
    Returns:
        list: Adjusted pallets list
    """
    # Adjust low-height last pallet
    last_pallet = pallets[-1]
    if last_pallet['Height'] < 20 and len(pallets) > 1:
        last_pallet_volume = last_pallet['Height'] * (LONG_PALLET_BASE_AREA if last_pallet['Type'] == 'Long' else STANDARD_PALLET_BASE_AREA)
        last_pallet_weight = last_pallet['Weight']

        # Find adjustable pallets (those with height < 96 inches)
        adjustable_pallets = [p for p in pallets[:-1] if p['Height'] < 96]

        if adjustable_pallets:
            for pallet in adjustable_pallets:
                if last_pallet_volume <= 0:
                    break

                available_height = 96 - pallet['Height']
                available_volume = available_height * (LONG_PALLET_BASE_AREA if pallet['Type'] == 'Long' else STANDARD_PALLET_BASE_AREA)

                volume_to_add = min(last_pallet_volume, available_volume)
                weight_to_add = (volume_to_add / last_pallet_volume) * last_pallet_weight

                pallet['Height'] += volume_to_add / (LONG_PALLET_BASE_AREA if pallet['Type'] == 'Long' else STANDARD_PALLET_BASE_AREA)
                pallet['Weight'] += weight_to_add

                last_pallet_volume -= volume_to_add
                last_pallet_weight -= weight_to_add

            if last_pallet_volume <= 0:
                pallets.pop()

    # Final weight redistribution (lines 758-760)
    for pallet in pallets:
        pallet_volume = pallet['Height'] * (LONG_PALLET_BASE_AREA if pallet['Type'] == 'Long' else STANDARD_PALLET_BASE_AREA)
        pallet['Weight'] = (pallet_volume / total_volume) * total_weight

    return pallets


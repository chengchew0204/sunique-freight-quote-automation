"""
Quote Selection Logic
Ported from development-web/script.js lines 458-488
"""


def select_optimal_quote(quotes):
    """
    Select the optimal quote (second-cheapest) with markup
    Ported from development-web/script.js lines 458-488
    
    Args:
        quotes: List of quote dictionaries with carrier, total_cost, distance
        
    Returns:
        dict: Selected quote with markup information
    """
    if len(quotes) == 0:
        raise ValueError('No quotes available')
    
    if len(quotes) == 1:
        quote = quotes[0]
        markup_rate = 1.3 if quote['total_cost'] > 1000 else 1.2
        return {
            'carrier': quote['carrier'],
            'baseRate': quote['total_cost'],
            'markup': quote['total_cost'] * (markup_rate - 1),
            'finalQuote': quote['total_cost'] * markup_rate,
            'markupPercentage': (markup_rate - 1) * 100,
            'distance': quote['distance']
        }
    
    # Sort by total cost
    sorted_quotes = sorted(quotes, key=lambda x: x['total_cost'])
    
    # Select second cheapest
    second_cheapest = sorted_quotes[1] if len(sorted_quotes) > 1 else sorted_quotes[0]
    markup_rate = 1.3 if second_cheapest['total_cost'] > 1000 else 1.2
    
    return {
        'carrier': second_cheapest['carrier'],
        'baseRate': second_cheapest['total_cost'],
        'markup': second_cheapest['total_cost'] * (markup_rate - 1),
        'finalQuote': second_cheapest['total_cost'] * markup_rate,
        'markupPercentage': (markup_rate - 1) * 100,
        'distance': second_cheapest['distance']
    }


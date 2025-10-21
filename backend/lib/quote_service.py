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
        dict: Selected quote with markup information (camelCase keys for frontend)
    """
    if len(quotes) == 0:
        raise ValueError('No quotes available')
    
    if len(quotes) == 1:
        quote = quotes[0]
        total_cost = quote.get('total_cost', 0)
        markup_rate = 1.3 if total_cost > 1000 else 1.2
        return {
            'carrier': quote.get('carrier', 'Unknown'),
            'baseRate': total_cost,
            'markup': total_cost * (markup_rate - 1),
            'finalQuote': total_cost * markup_rate,
            'markupPercentage': (markup_rate - 1) * 100,
            'distance': quote.get('distance', 'N/A')
        }
    
    # Sort by total cost
    sorted_quotes = sorted(quotes, key=lambda x: x.get('total_cost', 0))
    
    # Select second cheapest
    second_cheapest = sorted_quotes[1] if len(sorted_quotes) > 1 else sorted_quotes[0]
    total_cost = second_cheapest.get('total_cost', 0)
    markup_rate = 1.3 if total_cost > 1000 else 1.2
    
    return {
        'carrier': second_cheapest.get('carrier', 'Unknown'),
        'baseRate': total_cost,
        'markup': total_cost * (markup_rate - 1),
        'finalQuote': total_cost * markup_rate,
        'markupPercentage': (markup_rate - 1) * 100,
        'distance': second_cheapest.get('distance', 'N/A')
    }


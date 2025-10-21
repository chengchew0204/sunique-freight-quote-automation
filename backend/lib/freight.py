"""
Freight Class Calculation and C.H. Robinson Integration
Ported from development/main.py lines 767-1030
"""

import requests


# Standard and long pallet dimensions
STANDARD_PALLET_DIMENSIONS = {"length": 48, "width": 40}
LONG_PALLET_DIMENSIONS = {"length": 96, "width": 48}

# Freight class mapping based on density
FREIGHT_CLASS_MAP = [
    (50, 50),
    (35, 55),
    (30, 60),
    (22.5, 65),
    (15, 70),
    (13.5, 77.5),
    (12, 85),
    (10.5, 92.5),
    (9, 100),
    (8, 110),
    (7, 125),
    (6, 150),
    (5, 175),
    (4, 200),
    (3, 250),
    (2, 300),
    (1, 400),
    (0, 500)
]


def calculate_freight_class(density):
    """
    Calculate freight class based on density
    Ported from development/main.py lines 816-820
    
    Args:
        density: Density in lbs/cubic foot
        
    Returns:
        int: Freight class
    """
    for threshold, freight_class in FREIGHT_CLASS_MAP:
        if density >= threshold:
            return freight_class
    return 500


def build_freight_items(pallets):
    """
    Build freight items from pallet data
    Ported from development/main.py lines 772-850
    
    Args:
        pallets: List of pallet dictionaries with Type, Height, Weight
        
    Returns:
        list: Freight items with dimensions and freight class
    """
    freight_items = []
    
    for idx, pallet in enumerate(pallets, start=1):
        if pallet["Type"] == "Standard":
            dimensions = STANDARD_PALLET_DIMENSIONS
            adjusted_weight = pallet["Weight"] + 50  # Add 50 lbs for standard pallet
            adjusted_height = pallet["Height"] + (0 if pallet["Height"] >= 96 else 5)
        elif pallet["Type"] == "Long":
            dimensions = LONG_PALLET_DIMENSIONS
            adjusted_weight = pallet["Weight"] + 100  # Add 100 lbs for long pallet
            adjusted_height = pallet["Height"] + (0 if pallet["Height"] >= 96 else 5)
        else:
            raise ValueError(f"Unknown pallet type: {pallet['Type']}")
        
        # Calculate volume in cubic feet
        volume_cubic_feet = (dimensions['length'] * dimensions['width'] * adjusted_height) / 1728
        
        # Calculate density (lbs/ft^3)
        density = adjusted_weight / volume_cubic_feet
        
        # Determine freight class
        freight_class = calculate_freight_class(density)
        
        freight_items.append({
            "Length": dimensions['length'],
            "Width": dimensions['width'],
            "Height": round(adjusted_height),
            "Weight": round(adjusted_weight),
            "Stackable": False,
            "Hazmat": False,
            "FreightClass": freight_class
        })
    
    return freight_items


def get_city_state_from_zip(zip_code):
    """
    Get city and state from ZIP code
    Ported from development/main.py lines 853-866
    
    Args:
        zip_code: 5-digit ZIP code string
        
    Returns:
        tuple: (city, state) or (None, None) if not found
    """
    try:
        response = requests.get(f"http://api.zippopotam.us/us/{zip_code}")
        if response.status_code == 200:
            data = response.json()
            city = data['places'][0]['place name']
            state = data['places'][0]['state abbreviation']
            return city, state
        else:
            print(f"Error: Unable to fetch data for ZIP code {zip_code}")
            return None, None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None


def build_chr_quote_request(pallets, pickup_info, delivery_info, ship_date, 
                            is_residential, needs_liftgate, customer_code):
    """
    Build C.H. Robinson quote request from pallet data
    Ported from development/main.py lines 893-970
    
    Args:
        pallets: List of freight item dictionaries
        pickup_info: Dict with zip, city, state
        delivery_info: Dict with zip, city, state
        ship_date: ISO format date string (YYYY-MM-DDTHH:MM:SS)
        is_residential: Boolean
        needs_liftgate: Boolean
        customer_code: C.H. Robinson customer code
        
    Returns:
        dict: C.H. Robinson API request payload
    """
    # Transform pallets to C.H. Robinson items format
    items_payload = []
    for idx, pallet in enumerate(pallets, start=1):
        item = {
            "description": f"Cabinet pallet {idx}",
            "freightClass": int(pallet['FreightClass']),
            "weight": float(pallet['Weight']),
            "weightUnitOfMeasure": "Pounds",
            "packagingLength": float(pallet['Length']),
            "packagingWidth": float(pallet['Width']),
            "packagingHeight": float(pallet['Height']),
            "packagingUnitOfMeasure": "Inches",
            "packagingType": "PLT",
            "quantity": 1,
            "pallets": 1,
            "insuranceValue": float(pallet['Weight']) * 5
        }
        items_payload.append(item)
    
    # Map service flags to C.H. Robinson special requirements
    origin_requirements = {
        "liftGate": needs_liftgate,
        "insidePickup": False,
        "residentialNonCommercial": False,
        "limitedAccess": False,
        "tradeShoworConvention": False,
        "constructionSite": False,
        "dropOffAtCarrierTerminal": False
    }
    
    destination_requirements = {
        "liftGate": needs_liftgate,
        "insideDelivery": False,
        "residentialNonCommercial": is_residential,
        "limitedAccess": False,
        "tradeShoworConvention": False,
        "constructionSite": False,
        "pickupAtCarrierTerminal": False
    }
    
    # Build request payload
    payload = {
        "items": items_payload,
        "origin": {
            "countryCode": "US",
            "postalCode": pickup_info['zip'],
            "city": pickup_info['city'],
            "stateProvinceCode": pickup_info['state'],
            "openDateTime": ship_date,
            "closeDateTime": ship_date,
            "specialRequirement": origin_requirements
        },
        "destination": {
            "countryCode": "US",
            "postalCode": delivery_info['zip'],
            "city": delivery_info['city'],
            "stateProvinceCode": delivery_info['state'],
            "specialRequirement": destination_requirements
        },
        "shipDate": ship_date,
        "customerCode": customer_code,
        "transportModes": [{
            "mode": "LTL",
            "equipments": [{
                "equipmentType": "Van",
                "quantity": 1
            }]
        }]
    }
    
    return payload


def parse_chr_quote_response(response_data):
    """
    Parse C.H. Robinson response
    Ported from development/main.py lines 973-995
    
    Args:
        response_data: JSON response from C.H. Robinson API
        
    Returns:
        list: Parsed quotes with carrier, total_cost, service, mode, distance
    """
    quotes = []
    quote_summaries = response_data.get('quoteSummaries', [])
    
    for quote_summary in quote_summaries:
        carrier_info = quote_summary.get('carrier', {})
        
        quote = {
            "carrier": carrier_info.get('carrierName', 'Unknown Carrier'),
            "total_cost": quote_summary.get('totalCharge', 0),
            "service": quote_summary.get('transportModeType', 'N/A'),
            "mode": quote_summary.get('transportModeType', 'N/A'),
            "distance": quote_summary.get('distance', 'N/A')
        }
        quotes.append(quote)
    
    return quotes


def get_chr_quotes(chr_auth, freight_items, pickup_info, delivery_info, 
                   ship_date, is_residential, needs_liftgate, customer_code):
    """
    Get shipping quotes from C.H. Robinson
    Ported from development/main.py lines 998-1030
    
    Args:
        chr_auth: CHRobinsonAuth instance
        freight_items: List of freight items
        pickup_info, delivery_info: Location dictionaries
        ship_date: ISO date string
        is_residential: Boolean
        needs_liftgate: Boolean
        customer_code: Customer code string
        
    Returns:
        list: Parsed quotes
    """
    # Build request payload
    payload = build_chr_quote_request(
        freight_items, pickup_info, delivery_info, ship_date,
        is_residential, needs_liftgate, customer_code
    )
    
    # Get authentication headers
    headers = chr_auth.get_headers()
    
    # Make API request
    url = f"{chr_auth.base_url}/v1/quotes"
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 201:
        data = response.json()
        return parse_chr_quote_response(data)
    else:
        raise Exception(f"C.H. Robinson API error {response.status_code}: {response.text}")


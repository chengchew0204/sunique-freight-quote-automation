"""
Netlify Serverless Function for Freight Quote Processing
Main orchestration endpoint that combines all business logic
"""

import json
import os
import sys
from pathlib import Path

# Add lib directory to path
current_dir = Path(__file__).parent
lib_path = str(current_dir / 'lib')
if lib_path not in sys.path:
    sys.path.insert(0, lib_path)

from lib.inflow_api import InflowAPI
from lib.product_dimensions import ProductDimensionsLoader
from lib.pallet_calculator import determine_order_situation, calculate_pallets, adjust_low_height_pallets
from lib.freight import build_freight_items, get_city_state_from_zip, get_chr_quotes
from lib.chr_auth import CHRobinsonAuth
from lib.quote_service import select_optimal_quote


def handler(event, context):
    """
    Main Netlify Function handler
    
    Expected POST body:
    {
        "orderNumber": "SO-009537" or "Quote-001277",
        "needsAssembly": "yes" or "no",
        "pickupZip": "12345",
        "destinationZip": "67890",
        "deliveryType": "Commercial" or "Residential",
        "liftgateService": "yes" or "no",
        "pickupDate": "2024-01-15T08:00:00"
    }
    
    Note: orderNumber can accept both Sales Orders (SO-XXXXX) and Quotes (Quote-XXXXX)
    
    Returns:
    {
        "orderSummary": {...},
        "products": [...],
        "pallets": [...],
        "quotes": [...],
        "selectedQuote": {...}
    }
    """
    
    # CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Content-Type': 'application/json'
    }
    
    # Handle OPTIONS request (CORS preflight)
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Extract parameters
        order_number = body.get('orderNumber', '').strip()
        needs_assembly = body.get('needsAssembly', 'no')
        pickup_zip = body.get('pickupZip', '').strip()
        destination_zip = body.get('destinationZip', '').strip()
        delivery_type = body.get('deliveryType', 'Commercial')
        liftgate_service = body.get('liftgateService', 'no')
        pickup_date = body.get('pickupDate', '')
        
        # Validate inputs
        if not order_number:
            raise ValueError("Order or quote number is required")
        if len(pickup_zip) != 5 or not pickup_zip.isdigit():
            raise ValueError("Invalid pickup ZIP code")
        if len(destination_zip) != 5 or not destination_zip.isdigit():
            raise ValueError("Invalid destination ZIP code")
        if not pickup_date:
            raise ValueError("Pickup date is required")
        
        # Get environment variables
        inflow_company_id = os.environ.get('INFLOW_COMPANY_ID')
        inflow_api_key = os.environ.get('INFLOW_API_KEY')
        chr_client_id = os.environ.get('CHR_CLIENT_ID')
        chr_client_secret = os.environ.get('CHR_CLIENT_SECRET')
        chr_customer_code = os.environ.get('CHR_CUSTOMER_CODE')
        chr_environment = os.environ.get('CHR_ENVIRONMENT', 'sandbox')
        
        if not all([inflow_company_id, inflow_api_key, chr_client_id, chr_client_secret, chr_customer_code]):
            raise ValueError("Missing required environment variables")
        
        # Initialize API clients
        inflow_api = InflowAPI(inflow_company_id, inflow_api_key)
        chr_auth = CHRobinsonAuth(chr_client_id, chr_client_secret, chr_environment)
        
        # Load product dimensions
        dimensions_path = str(current_dir / 'data' / 'Product Dimension.xlsx')
        dimensions_loader = ProductDimensionsLoader(dimensions_path)
        
        # Step 1: Fetch order or quote from inFlow
        order_df = inflow_api.search_order_or_quote(order_number)
        
        if order_df.empty:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': f'"{order_number}" not found in inFlow. Please check the number and try again.'})
            }
        
        # Step 2: Process products
        products_df = inflow_api.process_order_products(order_df)
        
        if products_df.empty:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'No valid products found in this order'})
            }
        
        # Step 3: Merge dimensions
        products_with_dims = dimensions_loader.merge_dimensions(products_df, needs_assembly)
        
        # Filter out products without dimensions
        valid_products = products_with_dims[products_with_dims['Length'].notna()].copy()
        
        if valid_products.empty:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'No products with valid dimensions found'})
            }
        
        # Step 4: Calculate pallets
        order_situation = determine_order_situation(valid_products)
        pallets, total_weight, total_volume = calculate_pallets(valid_products, order_situation)
        
        # Adjust low-height pallets
        pallets = adjust_low_height_pallets(pallets, total_volume, total_weight)
        
        # Step 5: Build freight items
        freight_items = build_freight_items(pallets)
        
        # Step 6: Get location info from ZIP codes
        pickup_city, pickup_state = get_city_state_from_zip(pickup_zip)
        dest_city, dest_state = get_city_state_from_zip(destination_zip)
        
        if not pickup_city or not dest_city:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Invalid ZIP code. Could not determine city/state.'})
            }
        
        pickup_info = {'zip': pickup_zip, 'city': pickup_city, 'state': pickup_state}
        delivery_info = {'zip': destination_zip, 'city': dest_city, 'state': dest_state}
        
        # Step 7: Get shipping quotes from C.H. Robinson
        is_residential = delivery_type == 'Residential'
        needs_liftgate = liftgate_service == 'yes'
        
        quotes = get_chr_quotes(
            chr_auth, freight_items, pickup_info, delivery_info,
            pickup_date, is_residential, needs_liftgate, chr_customer_code
        )
        
        if not quotes:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'No shipping quotes available for this route'})
            }
        
        # Step 8: Select optimal quote
        selected_quote = select_optimal_quote(quotes)
        
        # Step 9: Format response
        # Convert products DataFrame to list of dicts
        products_list = []
        for _, row in valid_products.iterrows():
            products_list.append({
                'name': row['name'],
                'quantity': float(row['quantity']),
                'length': float(row['Length']),
                'width': float(row['Width']),
                'height': float(row['Height']),
                'weight': float(row['weight(kg)']),
                'index': int(row['Index'])
            })
        
        # Format pallets with type information
        pallets_list = []
        for i, (pallet, freight_item) in enumerate(zip(pallets, freight_items)):
            pallets_list.append({
                'length': freight_item['Length'],
                'width': freight_item['Width'],
                'height': freight_item['Height'],
                'weight': freight_item['Weight'],
                'freightClass': freight_item['FreightClass'],
                'stackable': freight_item['Stackable'],
                'hazmat': freight_item['Hazmat'],
                'palletType': pallet['Type'],
                'originalHeight': pallet['Height']
            })
        
        response_data = {
            'orderSummary': {
                'orderNumber': order_number,
                'totalProducts': len(products_list),
                'totalWeight': float(total_weight),
                'totalVolume': float(total_volume)
            },
            'products': products_list,
            'pallets': pallets_list,
            'quotes': quotes,
            'selectedQuote': selected_quote
        }
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(response_data)
        }
        
    except ValueError as e:
        return {
            'statusCode': 400,
            'headers': headers,
            'body': json.dumps({'error': str(e)})
        }
    except Exception as e:
        print(f"Error processing quote: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': f'Internal server error: {str(e)}'})
        }


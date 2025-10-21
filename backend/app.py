"""
Flask API for Sunique Freight Quote System
Backend service for Render.com deployment
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
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

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'freight-quote-api'}), 200

@app.route('/api/quote', methods=['POST', 'OPTIONS'])
def get_quote():
    """
    Main quote endpoint
    
    Expected POST body:
    {
        "orderNumber": "SO-009537",
        "needsAssembly": "yes" or "no",
        "pickupZip": "12345",
        "destinationZip": "67890",
        "deliveryType": "Commercial" or "Residential",
        "liftgateService": "yes" or "no",
        "pickupDate": "2024-01-15T08:00:00"
    }
    """
    
    # Handle OPTIONS request (CORS preflight)
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        # Parse request body
        data = request.get_json()
        
        # Extract parameters
        order_number = data.get('orderNumber', '').strip()
        needs_assembly = data.get('needsAssembly', 'no')
        pickup_zip = data.get('pickupZip', '').strip()
        destination_zip = data.get('destinationZip', '').strip()
        delivery_type = data.get('deliveryType', 'Commercial')
        liftgate_service = data.get('liftgateService', 'no')
        pickup_date = data.get('pickupDate', '')
        
        # Validate inputs
        if not order_number:
            return jsonify({'error': 'Order number is required'}), 400
        if len(pickup_zip) != 5 or not pickup_zip.isdigit():
            return jsonify({'error': 'Invalid pickup ZIP code'}), 400
        if len(destination_zip) != 5 or not destination_zip.isdigit():
            return jsonify({'error': 'Invalid destination ZIP code'}), 400
        if not pickup_date:
            return jsonify({'error': 'Pickup date is required'}), 400
        
        # Get environment variables
        inflow_company_id = os.environ.get('INFLOW_COMPANY_ID')
        inflow_api_key = os.environ.get('INFLOW_API_KEY')
        chr_client_id = os.environ.get('CHR_CLIENT_ID')
        chr_client_secret = os.environ.get('CHR_CLIENT_SECRET')
        chr_customer_code = os.environ.get('CHR_CUSTOMER_CODE')
        chr_environment = os.environ.get('CHR_ENVIRONMENT', 'sandbox')
        
        if not all([inflow_company_id, inflow_api_key, chr_client_id, chr_client_secret, chr_customer_code]):
            return jsonify({'error': 'Missing required environment variables'}), 500
        
        # Initialize API clients
        inflow_api = InflowAPI(inflow_company_id, inflow_api_key)
        chr_auth = CHRobinsonAuth(chr_client_id, chr_client_secret, chr_environment)
        
        # Load product dimensions
        dimensions_path = str(current_dir / 'data' / 'Product Dimension.xlsx')
        dimensions_loader = ProductDimensionsLoader(dimensions_path)
        
        # Step 1: Fetch order from inFlow
        order_df = inflow_api.search_todays_orders(order_number)
        
        if order_df.empty:
            return jsonify({'error': f'Order "{order_number}" not found in today\'s orders'}), 404
        
        # Step 2: Process products
        products_df = inflow_api.process_order_products(order_df)
        
        if products_df.empty:
            return jsonify({'error': 'No valid products found in this order'}), 400
        
        # Step 3: Merge dimensions
        products_with_dims = dimensions_loader.merge_dimensions(products_df, needs_assembly)
        
        # Filter out products without dimensions
        valid_products = products_with_dims[products_with_dims['Length'].notna()].copy()
        
        if valid_products.empty:
            return jsonify({'error': 'No products with valid dimensions found'}), 400
        
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
            return jsonify({'error': 'Invalid ZIP code. Could not determine city/state.'}), 400
        
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
            return jsonify({'error': 'No shipping quotes available for this route'}), 400
        
        # Step 8: Select optimal quote
        selected_quote = select_optimal_quote(quotes)
        
        # Step 9: Format response
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
        
        return jsonify(response_data), 200
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Error processing quote: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)


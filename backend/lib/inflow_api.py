"""
inFlow API Client
Ported from development/main.py lines 91-498
"""

import requests
import time
import pandas as pd


class InflowAPI:
    """Client for inFlow Inventory API"""
    
    def __init__(self, company_id, api_key, api_version='2025-06-24'):
        self.company_id = company_id
        self.api_key = api_key
        self.base_url = f"https://cloudapi.inflowinventory.com/{company_id}"
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Accept': f'application/json;version={api_version}',
            'X-OverrideAllowNegativeInventory': 'TRUE'
        }
    
    def fetch_with_retries(self, url, timeout=60, max_attempts=5):
        """
        Fetch with retry mechanism for rate limiting and timeouts
        Ported from development/main.py lines 92-128
        """
        attempt = 0
        wait_time_timeout = 10  # Initial timeout wait seconds
        wait_time_429 = 20      # Initial 429 wait seconds

        while attempt < max_attempts:
            attempt += 1
            try:
                resp = requests.get(url, headers=self.headers, timeout=timeout)
                
                if resp.status_code == 429:
                    print(f"Rate limited (429). Waiting {wait_time_429} seconds...")
                    time.sleep(wait_time_429)
                    wait_time_429 += 10
                    continue
                    
                if resp.status_code == 200:
                    return resp
                else:
                    print(f"HTTP {resp.status_code}: {resp.text}")
                    if attempt < max_attempts:
                        time.sleep(wait_time_timeout)
                        wait_time_timeout += attempt * 10
                        
            except requests.exceptions.Timeout:
                print(f"Timeout on attempt {attempt}/{max_attempts}")
                if attempt < max_attempts:
                    time.sleep(wait_time_timeout)
                    wait_time_timeout += attempt * 10
                    
            except Exception as e:
                print(f"Error on attempt {attempt}/{max_attempts}: {e}")
                if attempt < max_attempts:
                    time.sleep(wait_time_timeout)
                    wait_time_timeout += attempt * 10
        
        raise Exception(f"Failed to fetch data after {max_attempts} attempts")
    
    def fetch_single_order_from_api(self, sales_order_id):
        """
        Fetch a single order by ID
        Ported from development/main.py lines 130-143
        """
        url = f"{self.base_url}/sales-orders/{sales_order_id}?include=lines,customer"
        response = self.fetch_with_retries(url, timeout=60, max_attempts=5)
        
        if response.status_code == 200:
            json_data = response.json()
            return pd.json_normalize([json_data])
        else:
            raise Exception(f"Failed to fetch order {sales_order_id}")
    
    def search_todays_orders(self, order_number):
        """
        Search for an order by order number (all dates)
        Modified to search all orders, not just today
        """
        # Search all orders with the specific order number
        # Using orderNumber filter for efficient search
        url = (
            f"{self.base_url}/sales-orders"
            f"?count=100&include=lines,customer"
        )
        
        response = self.fetch_with_retries(url, timeout=60, max_attempts=5)
        
        if response.status_code == 200:
            orders = response.json()
            if isinstance(orders, list):
                # Find the order with matching order number
                for order in orders:
                    if order.get('orderNumber') == order_number:
                        return pd.json_normalize([order])
        
        # If not found in first 100, try searching more pages
        # This searches up to 500 most recent orders
        for skip in [100, 200, 300, 400]:
            url = (
                f"{self.base_url}/sales-orders"
                f"?count=100&include=lines,customer&skip={skip}"
            )
            
            response = self.fetch_with_retries(url, timeout=60, max_attempts=5)
            
            if response.status_code == 200:
                orders = response.json()
                if isinstance(orders, list) and len(orders) > 0:
                    for order in orders:
                        if order.get('orderNumber') == order_number:
                            return pd.json_normalize([order])
                else:
                    # No more orders to search
                    break
            
        return pd.DataFrame()  # Return empty DataFrame if not found
    
    def get_product_details(self, product_id):
        """
        Get product details by product ID
        Ported from development/main.py lines 473-484
        """
        url = f"{self.base_url}/products/{product_id}?include=category"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            # Retry on rate limit
            attempts = 0
            while response.status_code == 429 and attempts < 5:
                time.sleep(40)
                response = requests.get(url, headers=self.headers)
                attempts += 1
                if response.status_code == 200:
                    break
        
        if response.status_code == 200:
            json_data = response.json()
            return pd.json_normalize([json_data])
        else:
            raise Exception(f"Failed to fetch product {product_id}")
    
    def process_order_products(self, order_df):
        """
        Process order to extract product list with quantities
        Ported from development/main.py lines 466-498
        
        Returns:
            DataFrame with columns: productId, name, quantity
        """
        # Expand lines to get detailed product list
        df_product_uuid = order_df.explode('lines')
        df_product_uuid = pd.json_normalize(df_product_uuid['lines'])
        df_product_uuid['quantity'] = pd.to_numeric(
            df_product_uuid['quantity.standardQuantity'], errors='coerce'
        )
        
        # Get product SKUs
        df_product_sku = pd.DataFrame()
        for product_id in df_product_uuid['productId']:
            try:
                product_details = self.get_product_details(product_id)
                df_product_sku = pd.concat([df_product_sku, product_details], ignore_index=True)
            except Exception as e:
                print(f"Error fetching product {product_id}: {e}")
        
        # Merge product SKU and quantities
        df_product_sku = df_product_sku[['productId', 'name']]
        df_product_uuid['quantity'] = pd.to_numeric(df_product_uuid['quantity'], errors='coerce')
        df_product_uuid = df_product_uuid[['productId', 'quantity']].groupby('productId', as_index=False).agg({
            'quantity': 'sum',
        })
        
        selected_sales_order = pd.merge(df_product_uuid, df_product_sku, on="productId", how="inner")
        selected_sales_order = selected_sales_order[['name', 'quantity']]
        
        # Filter out test products (starting with 'z' or 'Z')
        selected_sales_order = selected_sales_order[
            ~selected_sales_order['name'].str.startswith(('z', 'Z'), na=False)
        ]
        
        # Filter out zero quantity items
        selected_sales_order = selected_sales_order[~(selected_sales_order['quantity'] == 0)]
        
        return selected_sales_order


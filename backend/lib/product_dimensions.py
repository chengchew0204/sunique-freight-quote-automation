"""
Product Dimensions Loader
Ported from development/main.py lines 502-573
"""

import pandas as pd
import os


class ProductDimensionsLoader:
    """Load and manage product dimension data from Excel"""
    
    def __init__(self, excel_path):
        self.excel_path = excel_path
        self.assembled_dimensions = None
        self.rta_dimensions = None
        self.load_dimensions()
    
    def load_dimensions(self):
        """
        Load product dimensions from Excel file
        Ported from development/main.py lines 502-533
        """
        # Load the Excel file
        sheets = pd.ExcelFile(self.excel_path)
        
        # Load assembled dimensions (sheet 0)
        self.assembled_dimensions = sheets.parse(sheet_name=0).rename(columns={
            'length(inch)': 'Length',
            'width(inch)': 'Width',
            'height(inch)': 'Height',
            'name': 'name',
            'Index': 'Index',
            'weight(kg)': 'weight(kg)'
        })
        
        # Load RTA dimensions (sheet 1)
        self.rta_dimensions = sheets.parse(sheet_name=1).rename(columns={
            'length(inch)': 'Length',
            'width(inch)': 'Width',
            'height(inch)': 'Height',
            'name': 'name',
            'Index': 'Index',
            'weight(kg)': 'weight(kg)'
        })
        
        # Extract product type (content after "-") and ensure consistent string type
        self.assembled_dimensions['ProductType'] = self.assembled_dimensions['name'].str.split('-').str[1].astype(str)
        self.rta_dimensions['ProductType'] = self.rta_dimensions['name'].str.split('-').str[1].astype(str)
    
    def get_dimensions_table(self, needs_assembly):
        """
        Get the appropriate dimensions table based on assembly requirement
        Ported from development/main.py lines 535-540
        
        Args:
            needs_assembly: 'yes' or 'no'
            
        Returns:
            DataFrame with dimensions
        """
        if needs_assembly not in ['yes', 'no']:
            raise ValueError("Invalid input. needs_assembly must be 'yes' or 'no'.")
        
        return self.assembled_dimensions if needs_assembly == 'yes' else self.rta_dimensions
    
    def merge_dimensions(self, products_df, needs_assembly):
        """
        Merge product dimensions with product list
        Ported from development/main.py lines 543-573
        
        Args:
            products_df: DataFrame with product names and quantities
            needs_assembly: 'yes' or 'no'
            
        Returns:
            DataFrame with merged dimension data
        """
        # Choose the correct dimensions table
        dimensions_table = self.get_dimensions_table(needs_assembly)
        
        # Extract product type (content after "-") and ensure consistent string type
        products_df['ProductType'] = products_df['name'].str.split('-').str[1].astype(str)
        
        # Debug logging
        print(f"DEBUG: Available ProductTypes in dimensions ({needs_assembly}): {sorted(dimensions_table['ProductType'].unique())}")
        print(f"DEBUG: Product ProductTypes from order: {sorted(products_df['ProductType'].unique())}")
        
        # Merge dimensions based on product type
        merged_df = pd.merge(
            products_df,
            dimensions_table[['ProductType', 'Length', 'Width', 'Height', 'weight(kg)', 'Index']],
            on='ProductType',
            how='left'
        )
        
        # Ensure 'quantity' column is numeric
        merged_df['quantity'] = pd.to_numeric(merged_df['quantity'], errors='coerce')
        
        # Calculate volume for each product
        merged_df['Volume (cubic inches)'] = (
            merged_df['Length'] *
            merged_df['Width'] *
            merged_df['Height'] *
            merged_df['quantity']
        )
        
        # Calculate weight (kg and lbs)
        merged_df['Weight (kg)'] = merged_df['weight(kg)'] * merged_df['quantity']
        merged_df['Weight (lb)'] = merged_df['Weight (kg)'] * 2.20462
        
        return merged_df


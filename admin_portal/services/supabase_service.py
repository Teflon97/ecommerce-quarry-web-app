from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()

class SupabaseService:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        self.client = create_client(self.supabase_url, self.supabase_key)
    
    def get_employees(self):
        """Get all employees"""
        response = self.client.table('employees').select('*').execute()
        return response.data
    
    def get_employee_by_email(self, email):
        """Get employee by email"""
        response = self.client.table('employees').select('*').eq('email', email).execute()
        return response.data[0] if response.data else None
    
    def create_employee(self, employee_data):
        """Create new employee"""
        response = self.client.table('employees').insert(employee_data).execute()
        return response.data[0] if response.data else None
    
    def update_employee(self, employee_id, employee_data):
        """Update employee"""
        response = self.client.table('employees').update(employee_data).eq('id', employee_id).execute()
        return response.data[0] if response.data else None
    
    def delete_employee(self, employee_id):
        """Delete employee"""
        response = self.client.table('employees').delete().eq('id', employee_id).execute()
        return response.data
    
    def get_orders(self):
        """Get all orders"""
        response = self.client.table('orders').select('*').execute()
        return response.data
    
    def get_products(self):
        """Get all products"""
        response = self.client.table('products').select('*').execute()
        return response.data
    
    def get_trucks(self):
        """Get all trucks"""
        response = self.client.table('trucks').select('*').execute()
        return response.data
    
    def get_deliveries(self):
        """Get all deliveries"""
        response = self.client.table('deliveries').select('*').execute()
        return response.data

# Create a single instance
supabase_service = SupabaseService()
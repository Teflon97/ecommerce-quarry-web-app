import requests
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class SupabaseRestAPI:
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        self.service_key = os.getenv('SUPABASE_SERVICE_KEY', self.supabase_key)
        self.headers = {
            'apikey': self.supabase_key,
            'Content-Type': 'application/json'
        }
    
    def get_auth_headers(self, token=None):
        """Get headers with optional auth token"""
        headers = {
            'apikey': self.supabase_key,
            'Content-Type': 'application/json'
        }
        if token:
            headers['Authorization'] = f'Bearer {token}'
        else:
            # Use service key for admin operations when no token
            headers['Authorization'] = f'Bearer {self.service_key}'
        return headers
    
    def get_employees(self, token=None):
        try:
            headers = self.get_auth_headers(token)
            response = requests.get(
                f"{self.supabase_url}/rest/v1/employees?select=*&order=created_at.desc",
                headers=headers
            )
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting employees: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    def get_employee_by_id(self, employee_id, token=None):
        try:
            headers = self.get_auth_headers(token)
            response = requests.get(
                f"{self.supabase_url}/rest/v1/employees?select=*&id=eq.{employee_id}",
                headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                return data[0] if data else None
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def get_employee_by_email(self, email, token=None):
        try:
            headers = self.get_auth_headers(token)
            response = requests.get(
                f"{self.supabase_url}/rest/v1/employees?select=*&email=eq.{email}",
                headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                return data[0] if data else None
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def create_employee(self, employee_data, token=None):
        try:
            headers = self.get_auth_headers(token)
            print(f"Creating employee with data: {employee_data}")
            response = requests.post(
                f"{self.supabase_url}/rest/v1/employees",
                headers=headers,
                json=employee_data
            )
            print(f"Response status: {response.status_code}")
            print(f"Response text: {response.text}")
            
            if response.status_code == 201:
                # Success - employee created
                # Try to parse JSON if there's content, otherwise return True
                if response.text and response.text.strip():
                    try:
                        result = response.json()
                        return result[0] if result else True
                    except:
                        return True
                else:
                    return True
            else:
                print(f"Error creating employee: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def update_employee(self, employee_id, employee_data, token=None):
        try:
            headers = self.get_auth_headers(token)
            response = requests.patch(
                f"{self.supabase_url}/rest/v1/employees?id=eq.{employee_id}",
                headers=headers,
                json=employee_data
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def delete_employee(self, employee_id, token=None):
        try:
            headers = self.get_auth_headers(token)
            response = requests.delete(
                f"{self.supabase_url}/rest/v1/employees?id=eq.{employee_id}",
                headers=headers
            )
            return response.status_code == 204
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def get_orders(self, token=None):
        try:
            headers = self.get_auth_headers(token)
            response = requests.get(
                f"{self.supabase_url}/rest/v1/orders?select=*&order=created_at.desc",
                headers=headers
            )
            return response.json() if response.status_code == 200 else []
        except Exception as e:
            print(f"Error: {e}")
            return []

    def get_order_by_id(self, order_id, token=None):
        try:
            headers = self.get_auth_headers(token)
            response = requests.get(
                f"{self.supabase_url}/rest/v1/orders?id=eq.{order_id}&select=*",
                headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                return data[0] if data else None
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    def get_order_requests(self, order_id, token=None):
        try:
            headers = self.get_auth_headers(token)
            response = requests.get(
                f"{self.supabase_url}/rest/v1/requests?select=*,assigned_by(*),assigned_to(*),rejected_by(*)&order_id=eq.{order_id}&order=created_at.desc",
                headers=headers
            )
            return response.json() if response.status_code == 200 else []
        except Exception as e:
            print(f"Error: {e}")
            return []

    def create_request(self, request_data, token=None):
        try:
            headers = self.get_auth_headers(token)
            response = requests.post(
                f"{self.supabase_url}/rest/v1/requests",
                headers=headers,
                json=request_data
            )
            if response.status_code == 201:
                return True
            else:
                print(f"Error creating request: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    def update_request_status(self, request_id, status, token=None, rejected_by=None, rejection_reason=None):
        try:
            headers = self.get_auth_headers(token)
            update_data = {'status': status, 'updated_at': datetime.now().isoformat()}
            
            if status == 'accepted':
                update_data['accepted_at'] = datetime.now().isoformat()
            elif status == 'rejected':
                update_data['rejected_at'] = datetime.now().isoformat()
                if rejected_by:
                    update_data['rejected_by'] = rejected_by
                if rejection_reason:
                    update_data['rejection_reason'] = rejection_reason
            
            response = requests.patch(
                f"{self.supabase_url}/rest/v1/requests?id=eq.{request_id}",
                headers=headers,
                json=update_data
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error: {e}")
            return False

    def get_available_drivers(self, token=None):
        """Get drivers available for assignment"""
        try:
            headers = self.get_auth_headers(token)
            response = requests.get(
                f"{self.supabase_url}/rest/v1/employees?select=*&role=eq.Driver&is_active=eq.true",
                headers=headers
            )
            return response.json() if response.status_code == 200 else []
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    def get_products(self, token=None):
        """Get all products"""
        try:
            headers = self.get_auth_headers(token)
            response = requests.get(
                f"{self.supabase_url}/rest/v1/products?select=*&order=created_at.desc",
                headers=headers
            )
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting products: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            print(f"Error: {e}")
            return []

    def get_product_by_id(self, product_id, token=None):
        """Get product by UUID"""
        try:
            headers = self.get_auth_headers(token)
            response = requests.get(
                f"{self.supabase_url}/rest/v1/products?id=eq.{product_id}&select=*",
                headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                return data[0] if data else None
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    def get_product_by_product_id(self, product_id, token=None):
        """Get product by product_id string"""
        try:
            headers = self.get_auth_headers(token)
            response = requests.get(
                f"{self.supabase_url}/rest/v1/products?product_id=eq.{product_id}&select=*",
                headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                return data[0] if data else None
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    def create_product(self, product_data, token=None):
        """Create new product"""
        try:
            headers = self.get_auth_headers(token)
            print(f"Creating product with data: {product_data}")
            response = requests.post(
                f"{self.supabase_url}/rest/v1/products",
                headers=headers,
                json=product_data
            )
            print(f"Response status: {response.status_code}")
            print(f"Response text: {response.text}")
            
            if response.status_code == 201:
                # Success - return True regardless of response body
                return True
            else:
                print(f"Error creating product: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    def update_product(self, product_id, product_data, token=None):
        """Update product"""
        try:
            headers = self.get_auth_headers(token)
            response = requests.patch(
                f"{self.supabase_url}/rest/v1/products?id=eq.{product_id}",
                headers=headers,
                json=product_data
            )
            print(f"Update response status: {response.status_code}")
            print(f"Update response text: {response.text}")
            # 200 or 204 means success
            return response.status_code in [200, 204]
        except Exception as e:
            print(f"Error: {e}")
            return False

    def delete_product(self, product_id, token=None):
        """Delete product"""
        try:
            headers = self.get_auth_headers(token)
            response = requests.delete(
                f"{self.supabase_url}/rest/v1/products?id=eq.{product_id}",
                headers=headers
            )
            print(f"Delete response status: {response.status_code}")
            print(f"Delete response text: {response.text}")
            # 204 means success (No Content)
            return response.status_code == 204
        except Exception as e:
            print(f"Error: {e}")
            return False

    def get_next_product_id(self, token=None):
        """Generate next product ID"""
        try:
            headers = self.get_auth_headers(token)
            response = requests.get(
                f"{self.supabase_url}/rest/v1/products?select=product_id&order=product_id.desc&limit=1",
                headers=headers
            )
            
            if response.status_code == 200:
                products = response.json()
                if products and products[0].get('product_id'):
                    last_id = products[0]['product_id']
                    # Extract prefix and number (e.g., PS-01)
                    parts = last_id.split('-')
                    if len(parts) == 2:
                        prefix = parts[0]
                        num = int(parts[1]) + 1
                        return f"{prefix}-{num:02d}"
            
            return "PS-01"
        except Exception as e:
            print(f"Error: {e}")
            return "PS-01"
    
    def get_trucks(self, token=None):
        try:
            headers = self.get_auth_headers(token)
            # Remove the select nested query that might be causing issues
            response = requests.get(
                f"{self.supabase_url}/rest/v1/trucks?select=*&order=created_at.desc",
                headers=headers
            )
            if response.status_code == 200:
                trucks = response.json()
                # Manually fetch driver names for each truck
                for truck in trucks:
                    if truck.get('assigned_driver_id'):
                        driver_response = requests.get(
                            f"{self.supabase_url}/rest/v1/employees?select=id,first_name,last_name,email&id=eq.{truck['assigned_driver_id']}",
                            headers=headers
                        )
                        if driver_response.status_code == 200:
                            drivers = driver_response.json()
                            if drivers:
                                truck['assigned_driver'] = drivers[0]
                return trucks
            else:
                print(f"Error getting trucks: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            print(f"Error: {e}")
            return []

    def get_available_drivers(self, token=None):
        """Get drivers who are not assigned to any truck"""
        try:
            headers = self.get_auth_headers(token)
            # Get all drivers
            response = requests.get(
                f"{self.supabase_url}/rest/v1/employees?select=*&role=eq.Driver&is_active=eq.true",
                headers=headers
            )
            
            if response.status_code == 200:
                all_drivers = response.json()
                
                # Get assigned drivers from trucks
                trucks_response = requests.get(
                    f"{self.supabase_url}/rest/v1/trucks?select=assigned_driver_id",
                    headers=headers
                )
                
                assigned_driver_ids = []
                if trucks_response.status_code == 200:
                    trucks = trucks_response.json()
                    assigned_driver_ids = [truck.get('assigned_driver_id') for truck in trucks if truck.get('assigned_driver_id')]
                
                # Filter out assigned drivers
                available_drivers = [driver for driver in all_drivers if driver.get('id') not in assigned_driver_ids]
                
                return available_drivers
            else:
                return []
        except Exception as e:
            print(f"Error: {e}")
            return []

    def get_next_truck_number(self, token=None):
        """Generate next truck number"""
        try:
            headers = self.get_auth_headers(token)
            response = requests.get(
                f"{self.supabase_url}/rest/v1/trucks?select=truck_number&order=truck_number.desc&limit=1",
                headers=headers
            )
            
            if response.status_code == 200:
                trucks = response.json()
                if trucks and trucks[0].get('truck_number'):
                    last_number = trucks[0]['truck_number']
                    # Extract number from TRK001 format
                    import re
                    match = re.search(r'TRK(\d+)', last_number)
                    if match:
                        next_num = int(match.group(1)) + 1
                        return f"TRK{next_num:03d}"
            
            # Default first truck number
            return "TRK001"
        except Exception as e:
            print(f"Error: {e}")
            return "TRK001"
    
    def get_truck_by_id(self, truck_id, token=None):
        try:
            headers = self.get_auth_headers(token)
            response = requests.get(
                f"{self.supabase_url}/rest/v1/trucks?select=*,assigned_driver_id(*,first_name,last_name,email)&id=eq.{truck_id}",
                headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                return data[0] if data else None
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    def create_truck(self, truck_data, token=None):
        try:
            headers = self.get_auth_headers(token)
            print(f"Creating truck with data: {truck_data}")
            response = requests.post(
                f"{self.supabase_url}/rest/v1/trucks",
                headers=headers,
                json=truck_data
            )
            print(f"Response status: {response.status_code}")
            print(f"Response text: {response.text}")
            
            if response.status_code == 201:
                if response.text and response.text.strip():
                    try:
                        result = response.json()
                        return result[0] if result else True
                    except:
                        return True
                else:
                    return True
            else:
                print(f"Error creating truck: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    def update_truck(self, truck_id, truck_data, token=None):
        try:
            headers = self.get_auth_headers(token)
            response = requests.patch(
                f"{self.supabase_url}/rest/v1/trucks?id=eq.{truck_id}",
                headers=headers,
                json=truck_data
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error: {e}")
            return False

    def delete_truck(self, truck_id, token=None):
        try:
            headers = self.get_auth_headers(token)
            response = requests.delete(
                f"{self.supabase_url}/rest/v1/trucks?id=eq.{truck_id}",
                headers=headers
            )
            return response.status_code == 204
        except Exception as e:
            print(f"Error: {e}")
            return False

    def get_available_drivers(self, token=None):
        """Get drivers who are not assigned to any truck"""
        try:
            headers = self.get_auth_headers(token)
            # Get all drivers
            response = requests.get(
                f"{self.supabase_url}/rest/v1/employees?select=*&role=eq.Driver&is_active=eq.true",
                headers=headers
            )
            
            if response.status_code == 200:
                all_drivers = response.json()
                
                # Get assigned drivers from trucks
                trucks_response = requests.get(
                    f"{self.supabase_url}/rest/v1/trucks?select=assigned_driver_id",
                    headers=headers
                )
                
                assigned_driver_ids = []
                if trucks_response.status_code == 200:
                    trucks = trucks_response.json()
                    assigned_driver_ids = [truck.get('assigned_driver_id') for truck in trucks if truck.get('assigned_driver_id')]
                
                # Filter out assigned drivers
                available_drivers = [driver for driver in all_drivers if driver.get('id') not in assigned_driver_ids]
                
                return available_drivers
            else:
                return []
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    def get_deliveries(self, token=None):
        try:
            headers = self.get_auth_headers(token)
            response = requests.get(
                f"{self.supabase_url}/rest/v1/deliveries?select=*,driver_id(*),truck_id(*),assigned_to(*)&order=created_at.desc",
                headers=headers
            )
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error getting deliveries: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            print(f"Error: {e}")
            return []

    def get_delivery_by_id(self, delivery_id, token=None):
        try:
            headers = self.get_auth_headers(token)
            response = requests.get(
                f"{self.supabase_url}/rest/v1/deliveries?select=*,driver_id(*),truck_id(*),assigned_to(*)&id=eq.{delivery_id}",
                headers=headers
            )
            if response.status_code == 200:
                data = response.json()
                return data[0] if data else None
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    def create_delivery(self, delivery_data, token=None):
        try:
            headers = self.get_auth_headers(token)
            
            # Generate unique assignment_id if not provided
            if 'assignment_id' not in delivery_data or not delivery_data['assignment_id']:
                import uuid
                delivery_data['assignment_id'] = str(uuid.uuid4())
            
            response = requests.post(
                f"{self.supabase_url}/rest/v1/deliveries",
                headers=headers,
                json=delivery_data
            )
            if response.status_code == 201:
                if response.text and response.text.strip():
                    try:
                        result = response.json()
                        return result[0] if result else True
                    except:
                        return True
                else:
                    return True
            else:
                print(f"Error creating delivery: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error: {e}")
            return None

    def update_delivery_status(self, delivery_id, status, token=None):
        try:
            headers = self.get_auth_headers(token)
            response = requests.patch(
                f"{self.supabase_url}/rest/v1/deliveries?id=eq.{delivery_id}",
                headers=headers,
                json={'status': status}
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def get_monthly_sales(self, token=None):
        try:
            headers = self.get_auth_headers(token)
            response = requests.get(
                f"{self.supabase_url}/rest/v1/orders?select=total,created_at&status=eq.delivered",
                headers=headers
            )
            orders = response.json() if response.status_code == 200 else []
            
            monthly_data = {}
            for order in orders:
                created_at = order.get('created_at')
                if created_at:
                    try:
                        date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        month_key = date.strftime('%Y-%m')
                        if month_key not in monthly_data:
                            monthly_data[month_key] = 0
                        monthly_data[month_key] += float(order.get('total', 0))
                    except:
                        pass
            
            sorted_months = sorted(monthly_data.items())
            return {
                'months': [m[0] for m in sorted_months][-6:],
                'sales': [m[1] for m in sorted_months][-6:]
            }
        except Exception as e:
            print(f"Error: {e}")
            return {'months': [], 'sales': []}
    
    def get_recent_orders(self, limit=10, token=None):
        try:
            headers = self.get_auth_headers(token)
            response = requests.get(
                f"{self.supabase_url}/rest/v1/orders?select=*&order=created_at.desc&limit={limit}",
                headers=headers
            )
            return response.json() if response.status_code == 200 else []
        except Exception as e:
            print(f"Error: {e}")
            return []

supabase_service = SupabaseRestAPI()
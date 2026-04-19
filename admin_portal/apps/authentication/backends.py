from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from supabase import create_client
import os

class SupabaseAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            return None
        
        try:
            supabase = create_client(supabase_url, supabase_key)
            
            # Try to sign in with Supabase Auth
            response = supabase.auth.sign_in_with_password({
                "email": username,
                "password": password
            })
            
            if response.user:
                # Check if user exists in employees table
                employee_data = supabase.table('employees')\
                    .select('*')\
                    .eq('email', username)\
                    .execute()
                
                if employee_data.data:
                    employee = employee_data.data[0]
                    
                    # Create or get Django user
                    user, created = User.objects.get_or_create(
                        username=username,
                        defaults={
                            'email': username,
                            'first_name': employee.get('first_name', ''),
                            'last_name': employee.get('last_name', '')
                        }
                    )
                    
                    # Store additional info in user's session via request
                    if request:
                        request.session['user_role'] = employee.get('role', 'Staff')
                        request.session['user_id'] = str(employee.get('id'))
                    
                    return user
                    
        except Exception as e:
            print(f"Authentication error: {e}")
            return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
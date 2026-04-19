from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import logout as django_logout
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def supabase_login(request):
    # Clear any existing messages first
    storage = messages.get_messages(request)
    storage.used = True
    
    if request.method == 'POST':
        email = request.POST.get('username')
        password = request.POST.get('password')
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_anon_key = os.getenv('SUPABASE_ANON_KEY')
        # Use the correct standard key name
        supabase_service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not supabase_url or not supabase_anon_key:
            messages.error(request, 'Supabase configuration missing')
            return redirect('/custom-admin/login/')
        
        try:
            # First, check if employee exists in employees table
            headers = {
                'apikey': supabase_anon_key,
                'Authorization': f'Bearer {supabase_anon_key}',
                'Content-Type': 'application/json'
            }
            
            employee_url = f"{supabase_url}/rest/v1/employees?email=eq.{email}&select=*"
            emp_response = requests.get(employee_url, headers=headers)
            
            if emp_response.status_code == 200:
                employees = emp_response.json()
                
                if employees and len(employees) > 0:
                    employee = employees[0]
                    
                    # Try to authenticate with Supabase Auth
                    auth_url = f"{supabase_url}/auth/v1/token?grant_type=password"
                    auth_headers = {
                        'apikey': supabase_anon_key,
                        'Content-Type': 'application/json'
                    }
                    auth_data = {
                        'email': email,
                        'password': password
                    }
                    
                    auth_response = requests.post(auth_url, headers=auth_headers, json=auth_data)
                    
                    if auth_response.status_code == 200:
                        auth_response_data = auth_response.json()
                        
                        # Store user info in session
                        request.session['user_id'] = str(employee.get('id'))
                        request.session['user_email'] = employee.get('email')
                        request.session['user_name'] = f"{employee.get('first_name', '')} {employee.get('last_name', '')}"
                        request.session['user_role'] = employee.get('role', 'Staff')
                        request.session['is_authenticated'] = True
                        request.session['supabase_token'] = auth_response_data.get('access_token')
                        
                        messages.success(request, f'Welcome back, {employee.get("first_name", email)}!')
                        
                        # Redirect based on role
                        if employee.get('role') == 'Driver':
                            return redirect('/driver/dashboard/')
                        else:
                            return redirect('/custom-admin/portal/dashboard/')
                    else:
                        # Auth failed - user might not exist in Supabase Auth
                        # Check if we have service role key to create user
                        if supabase_service_role_key:
                            # Use service role key for admin operations
                            admin_headers = {
                                'apikey': supabase_anon_key,
                                'Authorization': f'Bearer {supabase_service_role_key}',
                                'Content-Type': 'application/json'
                            }
                            
                            # Check if user exists in Supabase Auth
                            list_users_url = f"{supabase_url}/auth/v1/admin/users"
                            list_response = requests.get(list_users_url, headers=admin_headers)
                            
                            user_exists = False
                            if list_response.status_code == 200:
                                users = list_response.json()
                                for user in users:
                                    if user.get('email') == email:
                                        user_exists = True
                                        break
                            
                            if not user_exists:
                                # Create user in Supabase Auth
                                create_user_url = f"{supabase_url}/auth/v1/admin/users"
                                create_user_data = {
                                    'email': email,
                                    'password': password,
                                    'email_confirm': True,
                                    'user_metadata': {
                                        'first_name': employee.get('first_name', ''),
                                        'last_name': employee.get('last_name', ''),
                                        'role': employee.get('role', 'Staff')
                                    }
                                }
                                
                                create_response = requests.post(create_user_url, headers=admin_headers, json=create_user_data)
                                
                                if create_response.status_code == 200:
                                    messages.info(request, 'Account created successfully! Please login again.')
                                    return redirect('/custom-admin/login/')
                                else:
                                    # User creation failed
                                    error_detail = create_response.json() if create_response.text else {}
                                    error_msg = error_detail.get('msg', 'Unknown error')
                                    messages.error(request, f'Unable to create account: {error_msg}')
                            else:
                                messages.error(request, 'Password is incorrect. Please try again.')
                        else:
                            messages.error(request, 'Authentication service unavailable. Please contact administrator.')
                else:
                    messages.error(request, 'Employee record not found. Please contact administrator.')
            else:
                messages.error(request, 'Error checking employee record. Please try again.')
                
        except Exception as e:
            messages.error(request, f'Login error: {str(e)}')
        
        return redirect('/custom-admin/login/')
    
    return render(request, 'login.html')

def supabase_logout(request):
    # Clear all session data
    request.session.flush()
    
    # Clear all messages
    storage = messages.get_messages(request)
    storage.used = True
    
    messages.success(request, 'You have been successfully logged out.')
    return redirect('/custom-admin/login/')
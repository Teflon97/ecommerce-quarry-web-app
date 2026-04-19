from django.shortcuts import render, redirect
from django.contrib import messages
import requests
import json
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
                # Parse the response as JSON
                try:
                    employees = emp_response.json()
                except json.JSONDecodeError:
                    messages.error(request, 'Invalid response from server')
                    return redirect('/custom-admin/login/')
                
                # Check if we got a list and it has data
                if isinstance(employees, list) and len(employees) > 0:
                    employee = employees[0]  # This should be a dictionary
                    
                    # Verify employee is a dictionary
                    if not isinstance(employee, dict):
                        messages.error(request, 'Invalid employee data format')
                        return redirect('/custom-admin/login/')
                    
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
                        try:
                            auth_response_data = auth_response.json()
                        except json.JSONDecodeError:
                            messages.error(request, 'Invalid auth response')
                            return redirect('/custom-admin/login/')
                        
                        # Store user info in session using .get() safely
                        request.session['user_id'] = str(employee.get('id', ''))
                        request.session['user_email'] = employee.get('email', '')
                        request.session['user_name'] = f"{employee.get('first_name', '')} {employee.get('last_name', '')}".strip()
                        request.session['user_role'] = employee.get('role', 'Staff')
                        request.session['is_authenticated'] = True
                        request.session['supabase_token'] = auth_response_data.get('access_token', '')
                        
                        messages.success(request, f'Welcome back, {employee.get("first_name", email)}!')
                        
                        # Redirect based on role
                        if employee.get('role') == 'Driver':
                            return redirect('/driver/dashboard/')
                        else:
                            return redirect('/custom-admin/portal/dashboard/')
                    else:
                        # Auth failed - try to create user in Supabase Auth
                        if supabase_service_role_key:
                            admin_headers = {
                                'apikey': supabase_anon_key,
                                'Authorization': f'Bearer {supabase_service_role_key}',
                                'Content-Type': 'application/json'
                            }
                            
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
                                # Get error message from response
                                try:
                                    error_data = create_response.json()
                                    error_msg = error_data.get('msg', error_data.get('message', 'Unknown error'))
                                except:
                                    error_msg = create_response.text or 'Unknown error'
                                messages.error(request, f'Unable to create account: {error_msg}')
                        else:
                            messages.error(request, 'Invalid email or password. Please try again.')
                else:
                    messages.error(request, 'Employee record not found. Please contact administrator.')
            else:
                # Try to get error message from response
                try:
                    error_data = emp_response.json()
                    error_msg = error_data.get('msg', error_data.get('message', 'Unknown error'))
                except:
                    error_msg = emp_response.text or 'Unknown error'
                messages.error(request, f'Error checking employee record: {error_msg}')
                
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
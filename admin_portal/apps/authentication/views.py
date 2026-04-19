from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.contrib.auth.decorators import login_required
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def supabase_login(request):
    # Clear any existing messages
    storage = messages.get_messages(request)
    storage.used = True
    
    # Redirect if already logged in
    if request.session.get('is_authenticated'):
        role = request.session.get('user_role', 'Staff')
        if role == 'Driver':
            return redirect('/driver/dashboard/')
        return redirect('/custom-admin/portal/dashboard/')
    
    if request.method == 'POST':
        email = request.POST.get('username')
        password = request.POST.get('password')
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY', supabase_key)
        
        if not supabase_url or not supabase_key:
            messages.error(request, 'Supabase configuration missing')
            return redirect('/custom-admin/login/')
        
        try:
            # First, check if employee exists
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
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
                        'apikey': supabase_key,
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
                        
                        # Set session expiry (1 day)
                        request.session.set_expiry(86400)
                        
                        messages.success(request, f'Welcome back, {employee.get("first_name", email)}!')
                        
                        # Redirect based on role
                        if employee.get('role') == 'Driver':
                            return redirect('/driver/dashboard/')
                        else:
                            return redirect('/custom-admin/portal/dashboard/')
                    else:
                        # Auth failed - check if user exists in Supabase Auth
                        admin_headers = {
                            'apikey': supabase_key,
                            'Authorization': f'Bearer {supabase_service_key}',
                            'Content-Type': 'application/json'
                        }
                        
                        # Check if user exists in auth
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
                                messages.info(request, 'Account created! Please login again.')
                                return redirect('/custom-admin/login/')
                            else:
                                messages.error(request, 'Invalid email or password.')
                        else:
                            messages.error(request, 'Password is incorrect. Please try again.')
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
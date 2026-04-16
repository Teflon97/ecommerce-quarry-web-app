from django.shortcuts import render, redirect
from django.contrib import messages
from apps.authentication.decorators import login_required
from django.contrib import messages
from services import supabase_service

def dashboard(request):
    # Check if user is authenticated via session
    if not request.session.get('is_authenticated', False):
        messages.error(request, 'Please login to access the dashboard.')
        return redirect('/custom-admin/login/')
    
    # Get data from Supabase via REST API
    employees = supabase_service.get_employees()
    orders = supabase_service.get_orders()
    products = supabase_service.get_products()
    
    # Calculate pending orders
    pending_orders = 0
    if orders:
        pending_orders = len([o for o in orders if o.get('status') == 'pending'])
    
    context = {
        'total_employees': len(employees),
        'total_orders': len(orders),
        'total_products': len(products),
        'pending_orders': pending_orders,
        'user_name': request.session.get('user_name', 'Admin'),
        'user_role': request.session.get('user_role', 'Staff'),
    }
    return render(request, 'admin/portal/dashboard.html', context)

@login_required
def employee_list(request):
    """List all employees"""
    employees = supabase_service.get_employees()
    
    context = {
        'employees': employees,
        'total_employees': len(employees),
    }
    return render(request, 'admin/portal/employees/list.html', context)

@login_required
def employee_create(request):
    """Create new employee"""
    if request.method == 'POST':
        employee_data = {
            'first_name': request.POST.get('first_name'),
            'last_name': request.POST.get('last_name'),
            'email': request.POST.get('email'),
            'phone': request.POST.get('phone'),
            'address': request.POST.get('address', ''),
            'department': request.POST.get('department'),
            'role': request.POST.get('role'),
            'is_active': request.POST.get('is_active') == 'on',
        }
        
        # Add driver-specific fields
        if employee_data['role'] == 'Driver':
            employee_data['driver_license_number'] = request.POST.get('driver_license_number')
            employee_data['max_load_capacity_kg'] = request.POST.get('max_load_capacity_kg')
            employee_data['available_for_delivery'] = request.POST.get('available_for_delivery') == 'on'
        
        result = supabase_service.create_employee(employee_data)
        
        if result:
            messages.success(request, f'Employee {employee_data["first_name"]} {employee_data["last_name"]} created successfully!')
        else:
            messages.error(request, 'Error creating employee')
        
        return redirect('employee_list')
    
    context = {
        'departments': ['Sales', 'Accounting', 'Finance', 'Delivery', 'Warehouse', 'Management'],
        'roles': ['Admin', 'Manager', 'Sales Rep', 'Accountant', 'Finance Officer', 'Driver', 'Warehouse Staff', 'Dispatcher'],
    }
    return render(request, 'admin/portal/employees/form.html', context)

@login_required
def employee_detail(request, employee_id):
    """View employee details"""
    employees = supabase_service.get_employees()
    employee = next((e for e in employees if e.get('id') == employee_id), None)
    
    if not employee:
        messages.error(request, 'Employee not found')
        return redirect('employee_list')
    
    context = {'employee': employee}
    return render(request, 'admin/portal/employees/detail.html', context)

@login_required
def employee_edit(request, employee_id):
    """Edit employee"""
    employees = supabase_service.get_employees()
    employee = next((e for e in employees if e.get('id') == employee_id), None)
    
    if not employee:
        messages.error(request, 'Employee not found')
        return redirect('employee_list')
    
    if request.method == 'POST':
        employee_data = {
            'first_name': request.POST.get('first_name'),
            'last_name': request.POST.get('last_name'),
            'email': request.POST.get('email'),
            'phone': request.POST.get('phone'),
            'address': request.POST.get('address', ''),
            'department': request.POST.get('department'),
            'role': request.POST.get('role'),
            'is_active': request.POST.get('is_active') == 'on',
        }
        
        if employee_data['role'] == 'Driver':
            employee_data['driver_license_number'] = request.POST.get('driver_license_number')
            employee_data['max_load_capacity_kg'] = request.POST.get('max_load_capacity_kg')
            employee_data['available_for_delivery'] = request.POST.get('available_for_delivery') == 'on'
        
        result = supabase_service.update_employee(employee_id, employee_data)
        
        if result:
            messages.success(request, 'Employee updated successfully!')
        else:
            messages.error(request, 'Error updating employee')
        
        return redirect('employee_list')
    
    context = {
        'employee': employee,
        'departments': ['Sales', 'Accounting', 'Finance', 'Delivery', 'Warehouse', 'Management'],
        'roles': ['Admin', 'Manager', 'Sales Rep', 'Accountant', 'Finance Officer', 'Driver', 'Warehouse Staff', 'Dispatcher'],
    }
    return render(request, 'admin/portal/employees/form.html', context)

@login_required
def employee_delete(request, employee_id):
    """Delete employee"""
    if request.method == 'POST':
        result = supabase_service.delete_employee(employee_id)
        if result:
            messages.success(request, 'Employee deleted successfully!')
        else:
            messages.error(request, 'Error deleting employee')
        return redirect('employee_list')
    
    employees = supabase_service.get_employees()
    employee = next((e for e in employees if e.get('id') == employee_id), None)
    context = {'employee': employee}
    return render(request, 'admin/portal/employees/delete.html', context)
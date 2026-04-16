import os
import requests
import json
import uuid
import base64
from django.utils.safestring import mark_safe
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from services import supabase_service
from django.core.serializers.json import DjangoJSONEncoder
from datetime import datetime, date


def admin_portal_root(request):
    if request.session.get('is_authenticated', False):
        return redirect('/custom-admin/portal/dashboard/')
    else:
        return redirect('/custom-admin/login/')


def dashboard(request):
    if not request.session.get('is_authenticated', False):
        messages.error(request, 'Please login to access the dashboard.')
        return redirect('/custom-admin/login/')
    
    token = request.session.get('supabase_token')
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Fetch employees
    try:
        employees = supabase_service.get_employees(token=token)
    except:
        employees = []
    
    # Fetch orders
    try:
        orders_response = requests.get(
            f"{supabase_url}/rest/v1/orders?select=*&order=created_at.desc",
            headers=headers
        )
        orders = orders_response.json() if orders_response.status_code == 200 else []
    except:
        orders = []
    
    # Fetch products
    try:
        products_response = requests.get(
            f"{supabase_url}/rest/v1/products?select=*",
            headers=headers
        )
        products = products_response.json() if products_response.status_code == 200 else []
    except:
        products = []
    
    # Fetch trucks
    try:
        trucks_response = requests.get(
            f"{supabase_url}/rest/v1/trucks?select=*",
            headers=headers
        )
        trucks = trucks_response.json() if trucks_response.status_code == 200 else []
    except:
        trucks = []
    
    # Fetch deliveries
    try:
        deliveries_response = requests.get(
            f"{supabase_url}/rest/v1/deliveries?select=*",
            headers=headers
        )
        deliveries = deliveries_response.json() if deliveries_response.status_code == 200 else []
    except:
        deliveries = []
    
    # Calculate order statistics
    total_orders = len(orders)
    pending_orders = len([o for o in orders if o.get('status') == 'pending'])
    processing_orders = len([o for o in orders if o.get('status') == 'processing'])
    delivered_orders = len([o for o in orders if o.get('status') == 'delivered'])
    cancelled_orders = len([o for o in orders if o.get('status') == 'cancelled'])
    
    # Calculate revenue (in BWP)
    total_revenue = sum([float(o.get('total', 0)) for o in orders if o.get('status') == 'delivered'])
    
    # Get recent paid orders for receipts (maximum 10)
    recent_paid_orders = []
    for order in orders:
        if order.get('payment_status') == 'paid':
            recent_paid_orders.append(order)
        if len(recent_paid_orders) >= 10:
            break
    
    # Get low stock products
    low_stock_products = []
    for product in products:
        stock_quantity = product.get('stock_quantity', 0)
        if stock_quantity < 10:
            low_stock_products.append(product)
        if len(low_stock_products) >= 5:
            break
    
    # Prepare context
    context = {
        'total_employees': len(employees) if employees else 0,
        'total_orders': total_orders,
        'total_products': len(products) if products else 0,
        'total_trucks': len(trucks) if trucks else 0,
        'total_deliveries': len(deliveries) if deliveries else 0,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'delivered_orders': delivered_orders,
        'cancelled_orders': cancelled_orders,
        'total_revenue': total_revenue,
        'recent_orders': orders[:10] if orders else [],
        'recent_paid_orders': recent_paid_orders,
        'low_stock_products': low_stock_products,
        'user_name': request.session.get('user_name', 'Admin'),
        'user_role': request.session.get('user_role', 'Staff'),
        'current_date': timezone.now(),
        'notification_count': pending_orders,
    }
    
    return render(request, 'admin/portal/dashboard.html', context)

def products_page(request):
    """List all products"""
    if not request.session.get('is_authenticated', False):
        messages.error(request, 'Please login to access the dashboard.')
        return redirect('/custom-admin/login/')
    
    token = request.session.get('supabase_token')
    products = supabase_service.get_products(token=token)
    
    context = {
        'products': products,
        'user_name': request.session.get('user_name', 'Admin'),
        'user_role': request.session.get('user_role', 'Staff'),
    }
    return render(request, 'admin/portal/products/list.html', context)

def public_api_products(request):
    """Public API endpoint for frontend to get products (no authentication required)"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(
            f"{supabase_url}/rest/v1/products?select=*&is_active=eq.true&order=category,name",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            products = response.json()
            formatted = []
            for product in products:
                formatted.append({
                    'id': product.get('product_id'),
                    'name': product.get('name'),
                    'price': float(product.get('price', 0)),
                    'category': product.get('category'),
                    'unit': product.get('unit', 'ton'),
                    'imageUrl': product.get('image_url', f"/images/{product.get('product_id')}.jpg"),
                    'description': product.get('description', ''),
                    'stock': product.get('stock_quantity', 0)
                })
            
            # Create response with CORS headers
            json_response = JsonResponse({'products': formatted})
            json_response['Access-Control-Allow-Origin'] = '*'
            json_response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            json_response['Access-Control-Allow-Headers'] = 'Content-Type'
            return json_response
        else:
            print(f"Supabase error: {response.status_code} - {response.text}")
            json_response = JsonResponse({'error': 'Failed to fetch products from database'}, status=500)
            json_response['Access-Control-Allow-Origin'] = '*'
            return json_response
            
    except Exception as e:
        print(f"Error fetching products: {e}")
        json_response = JsonResponse({'error': str(e)}, status=500)
        json_response['Access-Control-Allow-Origin'] = '*'
        return json_response

def upload_product_image(file, product_id, token):
    """Upload product image to Supabase storage"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_ANON_KEY')
    
    # Get file extension
    file_extension = file.name.split('.')[-1].lower()
    if file_extension not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
        file_extension = 'jpg'
    
    filename = f"{product_id}.{file_extension}"
    
    # Read file content
    file_content = file.read()
    
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}',
        'Content-Type': file.content_type or f'image/{file_extension}'
    }
    
    # Upload to Supabase storage
    response = requests.post(
        f"{supabase_url}/storage/v1/object/products/{filename}",
        headers=headers,
        data=file_content
    )
    
    if response.status_code == 200:
        # Return the public URL
        return f"{supabase_url}/storage/v1/object/public/products/{filename}"
    
    return None

def product_create_page(request):
    """Create new product"""
    if not request.session.get('is_authenticated', False):
        messages.error(request, 'Please login to access the dashboard.')
        return redirect('/custom-admin/login/')
    
    token = request.session.get('supabase_token')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        category = request.POST.get('category')
        status = request.POST.get('status')
        unit = request.POST.get('unit', 'ton')
        stock_quantity = request.POST.get('stock_quantity', 0)
        
        if not name or not price or not category:
            messages.error(request, 'Name, price, and category are required.')
            context = {
                'categories': ['Sand', 'Gravel', 'Stones', 'Base Materials', 'Filling Materials'],
                'statuses': ['normal', 'sale'],
                'user_name': request.session.get('user_name', 'Admin'),
            }
            return render(request, 'admin/portal/products/form.html', context)
        
        # Generate product_id
        category_prefix = {
            'Sand': 'PS',
            'Gravel': 'GS',
            'Stones': 'CS',
            'Base Materials': 'BM',
            'Filling Materials': 'FM'
        }.get(category, 'PR')
        
        existing_products = supabase_service.get_products(token=token)
        category_products = [p for p in existing_products if p.get('category') == category]
        next_num = len(category_products) + 1
        product_id = f"{category_prefix}-{next_num:02d}"
        
        # Handle image upload to Supabase storage
        image_url = None
        if request.FILES.get('image'):
            image_url = upload_product_image(request.FILES['image'], product_id, token)
        
        product_data = {
            'product_id': product_id,
            'name': name,
            'description': description,
            'price': float(price),
            'category': category,
            'status': status,
            'unit': unit,
            'image_url': image_url,
            'stock_quantity': int(stock_quantity) if stock_quantity else 0,
            'is_active': True
        }
        
        result = supabase_service.create_product(product_data, token=token)
        
        if result:
            messages.success(request, f'Product {name} created successfully!')
            return redirect('/custom-admin/portal/products/')
        else:
            messages.error(request, 'Error creating product.')
    
    context = {
        'categories': ['Sand', 'Gravel', 'Stones', 'Base Materials', 'Filling Materials'],
        'statuses': ['normal', 'sale'],
        'user_name': request.session.get('user_name', 'Admin'),
        'user_role': request.session.get('user_role', 'Staff'),
    }
    return render(request, 'admin/portal/products/form.html', context)

def delete_product_image(image_url, product_id, token):
    """Delete old product image from Supabase storage"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_KEY') or os.getenv('SUPABASE_ANON_KEY')
    
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}',
    }
    
    # Extract filename from URL
    if image_url and f"/storage/v1/object/public/products/{product_id}" in image_url:
        # Delete the file
        response = requests.delete(
            f"{supabase_url}/storage/v1/object/products/{product_id}.{image_url.split('.')[-1]}",
            headers=headers
        )
        return response.status_code in [200, 204]
    return False

def product_edit_page(request, product_id):
    """Edit product"""
    if not request.session.get('is_authenticated', False):
        messages.error(request, 'Please login to access the dashboard.')
        return redirect('/custom-admin/login/')
    
    token = request.session.get('supabase_token')
    product = supabase_service.get_product_by_id(product_id, token=token)
    
    if not product:
        messages.error(request, 'Product not found')
        return redirect('/custom-admin/portal/products/')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        category = request.POST.get('category')
        status = request.POST.get('status')
        unit = request.POST.get('unit', 'ton')
        stock_quantity = request.POST.get('stock_quantity', 0)
        is_active = request.POST.get('is_active') == 'on'
        
        product_data = {
            'name': name,
            'description': description,
            'price': float(price),
            'category': category,
            'status': status,
            'unit': unit,
            'stock_quantity': int(stock_quantity) if stock_quantity else 0,
            'is_active': is_active,
            'updated_at': timezone.now().isoformat()
        }
        
        # Handle image upload - delete old image if new one is uploaded
        if request.FILES.get('image'):
            # Delete old image from storage
            if product.get('image_url'):
                delete_product_image(product.get('image_url'), product['product_id'], token)
            
            # Upload new image
            image_url = upload_product_image(request.FILES['image'], product['product_id'], token)
            if image_url:
                product_data['image_url'] = image_url
        
        result = supabase_service.update_product(product_id, product_data, token=token)
        
        if result:
            messages.success(request, f'Product {name} updated successfully!')
            return redirect('/custom-admin/portal/products/')
        else:
            messages.error(request, 'Error updating product.')
    
    context = {
        'product': product,
        'categories': ['Sand', 'Gravel', 'Stones', 'Base Materials', 'Filling Materials'],
        'statuses': ['normal', 'sale'],
        'user_name': request.session.get('user_name', 'Admin'),
        'user_role': request.session.get('user_role', 'Staff'),
    }
    return render(request, 'admin/portal/products/form.html', context)

def product_delete_page(request, product_id):
    """Delete product"""
    if not request.session.get('is_authenticated', False):
        messages.error(request, 'Please login to access the dashboard.')
        return redirect('/custom-admin/login/')
    
    token = request.session.get('supabase_token')
    product = supabase_service.get_product_by_id(product_id, token=token)
    
    if not product:
        messages.error(request, 'Product not found')
        return redirect('/custom-admin/portal/products/')
    
    if request.method == 'POST':
        success = supabase_service.delete_product(product_id, token=token)
        if success:
            messages.success(request, f'Product {product.get("name")} deleted successfully!')
        else:
            messages.error(request, 'Error deleting product')
        return redirect('/custom-admin/portal/products/')
    
    context = {
        'product': product,
        'user_name': request.session.get('user_name', 'Admin'),
        'user_role': request.session.get('user_role', 'Staff'),
    }
    return render(request, 'admin/portal/products/delete.html', context)

def product_detail_page(request, product_id):
    """View product details"""
    if not request.session.get('is_authenticated', False):
        messages.error(request, 'Please login to access the dashboard.')
        return redirect('/custom-admin/login/')
    
    token = request.session.get('supabase_token')
    product = supabase_service.get_product_by_id(product_id, token=token)
    
    if not product:
        messages.error(request, 'Product not found')
        return redirect('/custom-admin/portal/products/')
    
    context = {
        'product': product,
        'user_name': request.session.get('user_name', 'Admin'),
        'user_role': request.session.get('user_role', 'Staff'),
    }
    return render(request, 'admin/portal/products/detail.html', context)

def orders_page(request):
    """List all orders with assign button"""
    if not request.session.get('is_authenticated', False):
        messages.error(request, 'Please login to access the dashboard.')
        return redirect('/custom-admin/login/')
    
    token = request.session.get('supabase_token')
    orders = supabase_service.get_orders(token=token)
    
    # Check each order for pending requests
    for order in orders:
        # Check if order has pending request
        requests_history = supabase_service.get_order_requests(order.get('id'), token=token)
        has_pending = any(req.get('status') == 'pending' for req in requests_history)
        order['has_pending_request'] = has_pending
    
    context = {
        'orders': orders,
        'user_name': request.session.get('user_name', 'Admin'),
        'user_role': request.session.get('user_role', 'Staff'),
    }
    return render(request, 'admin/portal/orders/list.html', context)

def get_order_history(request, order_id):
    """Get order assignment history as JSON"""
    if not request.session.get('is_authenticated', False):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    token = request.session.get('supabase_token')
    
    # Get order details
    order = supabase_service.get_order_by_id(order_id, token=token)
    
    # Get request history
    requests_history = supabase_service.get_order_requests(order_id, token=token)
    
    # Get current active request (pending)
    active_request = None
    for req in requests_history:
        if req.get('status') == 'pending':
            active_request = req
            break
    
    return JsonResponse({
        'order': order,
        'requests': requests_history,
        'active_request': active_request
    }, safe=False)

def create_assignment(request, order_id):
    """Create a new assignment request"""
    import requests
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    if not request.session.get('is_authenticated', False):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    token = request.session.get('supabase_token')
    admin_id = request.session.get('user_id')
    
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError as e:
        return JsonResponse({'error': f'Invalid JSON: {str(e)}'}, status=400)
    
    driver_employee_id = data.get('driver_id')
    notes = data.get('notes', '')
    
    if not driver_employee_id:
        return JsonResponse({'error': 'Driver ID is required'}, status=400)
    
    # Get the order
    order = supabase_service.get_order_by_id(order_id, token=token)
    if not order:
        return JsonResponse({'error': 'Order not found'}, status=404)
    
    # Get driver UUID
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Get driver by employee_id
    driver_response = requests.get(
        f"{supabase_url}/rest/v1/employees?employee_id=eq.{driver_employee_id}&select=id",
        headers=headers
    )
    
    if driver_response.status_code != 200:
        return JsonResponse({'error': 'Driver not found'}, status=404)
    
    drivers = driver_response.json()
    if not drivers:
        return JsonResponse({'error': 'Driver not found'}, status=404)
    
    driver_uuid = drivers[0].get('id')
    
    # Create request record
    request_data = {
        'order_id': order_id,
        'assigned_by': admin_id,
        'assigned_to': driver_uuid,
        'status': 'pending',
        'notes': notes,
        'expires_at': (timezone.now() + timezone.timedelta(hours=24)).isoformat()
    }
    
    # Create the request
    result = supabase_service.create_request(request_data, token=token)
    
    if result:
        return JsonResponse({'success': True, 'message': 'Assignment created successfully'})
    else:
        return JsonResponse({'error': 'Failed to create assignment'}, status=500)

def update_request_status(request, request_id):
    """Update request status (accept/reject) - Called by driver"""
    import requests
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    if not request.session.get('is_authenticated', False):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    token = request.session.get('supabase_token')
    driver_id = request.session.get('user_id')
    driver_role = request.session.get('user_role')
    
    # Only drivers can accept/reject
    if driver_role != 'Driver':
        return JsonResponse({'error': 'Only drivers can accept/reject assignments'}, status=403)
    
    data = json.loads(request.body)
    new_status = data.get('status')
    rejection_reason = data.get('rejection_reason', '')
    
    if new_status not in ['accepted', 'rejected']:
        return JsonResponse({'error': 'Invalid status'}, status=400)
    
    # Update request status
    result = supabase_service.update_request_status(
        request_id, 
        new_status, 
        token=token,
        rejected_by=driver_id if new_status == 'rejected' else None,
        rejection_reason=rejection_reason if new_status == 'rejected' else None
    )
    
    if not result:
        return JsonResponse({'error': 'Failed to update status'}, status=500)
    
    # If accepted, create delivery record
    if new_status == 'accepted':
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        req_response = requests.get(
            f"{supabase_url}/rest/v1/requests?id=eq.{request_id}&select=*",
            headers=headers
        )
        
        if req_response.status_code == 200:
            requests_data = req_response.json()
            if requests_data:
                req = requests_data[0]
                order = supabase_service.get_order_by_id(req.get('order_id'), token=token)
                
                if order:
                    # Get coordinates from order delivery_location
                    lat = None
                    lng = None
                    delivery_location = order.get('delivery_location')
                    if delivery_location:
                        if isinstance(delivery_location, dict):
                            lat = delivery_location.get('lat')
                            lng = delivery_location.get('lng')
                    
                    # Create delivery record
                    delivery_data = {
                        'order_id': req.get('order_id'),
                        'driver_id': driver_id,
                        'assigned_to': driver_id,
                        'request_id': request_id,
                        'total_weight_kg': 0,
                        'delivery_address': delivery_location.get('address', '') if delivery_location else '',
                        'status': 'accepted',
                        'current_latitude': lat,
                        'current_longitude': lng,
                        'assigned_at': timezone.now().isoformat()
                    }
                    
                    supabase_service.create_delivery(delivery_data, token=token)
    
    return JsonResponse({'success': True, 'message': f'Request {new_status}'})

def employees_page(request):
    return render(request, 'admin/portal/employees/list.html')

def employee_create_page(request):
    if request.method == 'POST':
        # Get phone number (user only enters 8 digits, we add +267)
        phone_digits = request.POST.get('phone', '')
        
        # Validate phone - should be exactly 8 digits
        if not phone_digits or not phone_digits.isdigit() or len(phone_digits) != 8:
            messages.error(request, 'Please enter exactly 8 digits for phone number')
            context = {
                'departments': ['Sales', 'Accounting', 'Finance', 'Delivery', 'Warehouse', 'Management'],
                'roles': ['Admin', 'Manager', 'Sales Rep', 'Accountant', 'Finance Officer', 'Driver', 'Warehouse Staff', 'Dispatcher'],
            }
            return render(request, 'admin/portal/employees/form.html', context)
        
        # Add +267 prefix
        phone = f"+267{phone_digits}"
        
        # Generate employee_id based on role
        role = request.POST.get('role')
        role_prefix = {
            'Admin': 'ADM',
            'Manager': 'MGR',
            'Driver': 'DRV',
            'Sales Rep': 'SAL',
            'Accountant': 'ACC',
            'Finance Officer': 'FIN',
            'Warehouse Staff': 'WRH',
            'Dispatcher': 'DSP'
        }.get(role, 'EMP')
        
        # Get existing employees with same role to count
        existing_employees = supabase_service.get_employees(token=request.session.get('supabase_token'))
        role_count = len([e for e in existing_employees if e.get('role') == role])
        
        # Generate employee_id
        employee_id = f"{role_prefix}{role_count + 1:03d}"
        
        # Set available_for_delivery based on role (only TRUE for Drivers)
        available_for_delivery = (role == 'Driver')
        
        # Get form data
        employee_data = {
            'employee_id': employee_id,
            'first_name': request.POST.get('first_name'),
            'last_name': request.POST.get('last_name'),
            'email': request.POST.get('email'),
            'phone': phone,
            'address': request.POST.get('address', ''),
            'department': request.POST.get('department'),
            'role': role,
            'is_active': request.POST.get('is_active') == 'on',
            'available_for_delivery': available_for_delivery,
        }
        
        # Add driver-specific fields (only if role is Driver)
        if role == 'Driver':
            employee_data['driver_license_number'] = request.POST.get('driver_license_number')
            employee_data['max_load_capacity_kg'] = request.POST.get('max_load_capacity_kg')
        else:
            employee_data['driver_license_number'] = None
            employee_data['max_load_capacity_kg'] = None
        
        # Pass the session token for authentication
        result = supabase_service.create_employee(employee_data, token=request.session.get('supabase_token'))
        
        if result:
            messages.success(request, f'Employee {employee_data["first_name"]} {employee_data["last_name"]} created successfully!')
            return redirect('/custom-admin/portal/employees/')
        else:
            messages.error(request, 'Error creating employee. Please check the console for details.')
            # Still redirect to employees page even if error message shows (since employee was created)
            return redirect('/custom-admin/portal/employees/')
    
    context = {
        'departments': ['Sales', 'Accounting', 'Finance', 'Delivery', 'Warehouse', 'Management'],
        'roles': ['Admin', 'Manager', 'Sales Rep', 'Accountant', 'Finance Officer', 'Driver', 'Warehouse Staff', 'Dispatcher'],
    }
    return render(request, 'admin/portal/employees/form.html', context)

def employee_edit_page(request, employee_id):
    employee = supabase_service.get_employee_by_id(employee_id)
    
    if not employee:
        messages.error(request, 'Employee not found')
        return redirect('/custom-admin/portal/employees/')
    
    if request.method == 'POST':
        # Validate phone number
        phone = request.POST.get('phone', '')
        if not phone.startswith('+267') or len(phone) != 12 or not phone[4:].isdigit():
            messages.error(request, 'Phone number must start with +267 followed by 8 digits (e.g., +26771234567)')
            context = {
                'employee': employee,
                'departments': ['Sales', 'Accounting', 'Finance', 'Delivery', 'Warehouse', 'Management'],
                'roles': ['Admin', 'Manager', 'Sales Rep', 'Accountant', 'Finance Officer', 'Driver', 'Warehouse Staff', 'Dispatcher'],
            }
            return render(request, 'admin/portal/employees/form.html', context)
        
        employee_data = {
            'first_name': request.POST.get('first_name'),
            'last_name': request.POST.get('last_name'),
            'email': request.POST.get('email'),
            'phone': phone,
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
        
        return redirect('/custom-admin/portal/employees/')
    
    context = {
        'employee': employee,
        'departments': ['Sales', 'Accounting', 'Finance', 'Delivery', 'Warehouse', 'Management'],
        'roles': ['Admin', 'Manager', 'Sales Rep', 'Accountant', 'Finance Officer', 'Driver', 'Warehouse Staff', 'Dispatcher'],
    }
    return render(request, 'admin/portal/employees/form.html', context)

def employee_delete_page(request, employee_id):
    if request.method == 'POST':
        success = supabase_service.delete_employee(employee_id)
        if success:
            messages.success(request, 'Employee deleted successfully!')
        else:
            messages.error(request, 'Error deleting employee')
        return redirect('/custom-admin/portal/employees/')
    
    employee = supabase_service.get_employee_by_id(employee_id)
    context = {'employee': employee}
    return render(request, 'admin/portal/employees/delete.html', context)

def trucks_page(request):
    """List all trucks"""
    if not request.session.get('is_authenticated', False):
        messages.error(request, 'Please login to access the dashboard.')
        return redirect('/custom-admin/login/')
    
    # Refresh token from session
    token = request.session.get('supabase_token')
    trucks = supabase_service.get_trucks(token=token)
    
    context = {
        'trucks': trucks,
        'user_name': request.session.get('user_name', 'Admin'),
        'user_role': request.session.get('user_role', 'Staff'),
    }
    return render(request, 'admin/portal/trucks/list.html', context)

def truck_create_page(request):
    """Create new truck"""
    if not request.session.get('is_authenticated', False):
        messages.error(request, 'Please login to access the dashboard.')
        return redirect('/custom-admin/login/')
    
    token = request.session.get('supabase_token')
    
    if request.method == 'POST':
        # Get form data (truck number is NOT in the form)
        license_plate = request.POST.get('license_plate', '').strip().upper()
        capacity_kg = request.POST.get('capacity_kg')
        model = request.POST.get('model', '')
        year = request.POST.get('year')
        assigned_driver_id = request.POST.get('assigned_driver_id')
        
        # Validate required fields
        if not license_plate:
            messages.error(request, 'License plate is required.')
            available_drivers = supabase_service.get_available_drivers(token=token)
            context = {
                'available_drivers': available_drivers,
                'user_name': request.session.get('user_name', 'Admin'),
            }
            return render(request, 'admin/portal/trucks/form.html', context)
        
        if not capacity_kg:
            messages.error(request, 'Capacity is required.')
            available_drivers = supabase_service.get_available_drivers(token=token)
            context = {
                'available_drivers': available_drivers,
                'user_name': request.session.get('user_name', 'Admin'),
            }
            return render(request, 'admin/portal/trucks/form.html', context)
        
        # Generate truck number automatically
        truck_number = supabase_service.get_next_truck_number(token=token)
        
        # Prepare truck data
        truck_data = {
            'truck_number': truck_number,
            'license_plate': license_plate,
            'capacity_kg': float(capacity_kg),
            'current_load_kg': 0,
            'model': model,
            'year': int(year) if year else None,
            'assigned_driver_id': assigned_driver_id if assigned_driver_id else None,
            'is_available': True,
            'is_operational': True,
        }
        
        # Create truck
        result = supabase_service.create_truck(truck_data, token=token)
        
        if result:
            messages.success(request, f'Truck {truck_number} created successfully!')
            return redirect('/custom-admin/portal/trucks/')
        else:
            messages.error(request, 'Error creating truck. Please check the console for details.')
    
    # Get available drivers
    available_drivers = supabase_service.get_available_drivers(token=token)
    
    context = {
        'available_drivers': available_drivers,
        'user_name': request.session.get('user_name', 'Admin'),
        'user_role': request.session.get('user_role', 'Staff'),
    }
    return render(request, 'admin/portal/trucks/form.html', context)

def truck_edit_page(request, truck_id):
    """Edit truck"""
    if not request.session.get('is_authenticated', False):
        messages.error(request, 'Please login to access the dashboard.')
        return redirect('/custom-admin/login/')
    
    token = request.session.get('supabase_token')
    truck = supabase_service.get_truck_by_id(truck_id, token=token)
    
    if not truck:
        messages.error(request, 'Truck not found')
        return redirect('/custom-admin/portal/trucks/')
    
    if request.method == 'POST':
        # Get form data
        license_plate = request.POST.get('license_plate')
        capacity_kg = request.POST.get('capacity_kg')
        model = request.POST.get('model')
        year = request.POST.get('year')
        assigned_driver_id = request.POST.get('assigned_driver_id')
        is_available = request.POST.get('is_available') == 'on'
        is_operational = request.POST.get('is_operational') == 'on'
        
        # Prepare truck data (truck number cannot be changed)
        truck_data = {
            'license_plate': license_plate.upper(),
            'capacity_kg': float(capacity_kg),
            'model': model,
            'year': int(year) if year else None,
            'assigned_driver_id': assigned_driver_id if assigned_driver_id else None,
            'is_available': is_available,
            'is_operational': is_operational,
        }
        
        # Update truck
        result = supabase_service.update_truck(truck_id, truck_data, token=token)
        
        if result:
            messages.success(request, f'Truck {truck.get("truck_number")} updated successfully!')
            return redirect('/custom-admin/portal/trucks/')
        else:
            messages.error(request, 'Error updating truck. Please check the console for details.')
    
    # Get available drivers (excluding current driver)
    all_available_drivers = supabase_service.get_available_drivers(token=token)
    current_driver = truck.get('assigned_driver_id')
    
    # If truck has a driver, include them in the list
    available_drivers = all_available_drivers
    if current_driver:
        # Fetch current driver details if not already in list
        current_in_list = any(d.get('id') == current_driver for d in available_drivers)
        if not current_in_list:
            driver_response = requests.get(
                f"{supabase_service.supabase_url}/rest/v1/employees?select=*&id=eq.{current_driver}",
                headers=supabase_service.get_auth_headers(token)
            )
            if driver_response.status_code == 200:
                drivers = driver_response.json()
                if drivers:
                    available_drivers.append(drivers[0])
    
    context = {
        'truck': truck,
        'available_drivers': available_drivers,
        'user_name': request.session.get('user_name', 'Admin'),
        'user_role': request.session.get('user_role', 'Staff'),
    }
    return render(request, 'admin/portal/trucks/form.html', context)

def truck_edit_page(request, truck_id):
    """Edit truck"""
    if not request.session.get('is_authenticated', False):
        messages.error(request, 'Please login to access the dashboard.')
        return redirect('/custom-admin/login/')
    
    truck = supabase_service.get_truck_by_id(truck_id, token=request.session.get('supabase_token'))
    
    if not truck:
        messages.error(request, 'Truck not found')
        return redirect('/custom-admin/portal/trucks/')
    
    if request.method == 'POST':
        # Get form data
        truck_number = request.POST.get('truck_number')
        license_plate = request.POST.get('license_plate')
        capacity_kg = request.POST.get('capacity_kg')
        model = request.POST.get('model')
        year = request.POST.get('year')
        assigned_driver_id = request.POST.get('assigned_driver_id')
        is_available = request.POST.get('is_available') == 'on'
        is_operational = request.POST.get('is_operational') == 'on'
        
        # Prepare truck data
        truck_data = {
            'truck_number': truck_number.upper(),
            'license_plate': license_plate.upper(),
            'capacity_kg': float(capacity_kg),
            'model': model,
            'year': int(year) if year else None,
            'assigned_driver_id': assigned_driver_id if assigned_driver_id else None,
            'is_available': is_available,
            'is_operational': is_operational,
        }
        
        # Update truck
        result = supabase_service.update_truck(truck_id, truck_data, token=request.session.get('supabase_token'))
        
        if result:
            messages.success(request, f'Truck {truck_number} updated successfully!')
            return redirect('/custom-admin/portal/trucks/')
        else:
            messages.error(request, 'Error updating truck. Please check the console for details.')
    
    # Get available drivers (excluding current driver)
    all_available_drivers = supabase_service.get_available_drivers(token=request.session.get('supabase_token'))
    current_driver = truck.get('assigned_driver_id')
    
    # If truck has a driver, include them in the list
    available_drivers = all_available_drivers
    if current_driver:
        # Check if current driver is already in the list
        current_in_list = any(d.get('id') == current_driver.get('id') for d in available_drivers)
        if not current_in_list:
            available_drivers.append(current_driver)
    
    context = {
        'truck': truck,
        'available_drivers': available_drivers,
        'user_name': request.session.get('user_name', 'Admin'),
        'user_role': request.session.get('user_role', 'Staff'),
    }
    return render(request, 'admin/portal/trucks/form.html', context)

def truck_delete_page(request, truck_id):
    """Delete truck"""
    if not request.session.get('is_authenticated', False):
        messages.error(request, 'Please login to access the dashboard.')
        return redirect('/custom-admin/login/')
    
    truck = supabase_service.get_truck_by_id(truck_id, token=request.session.get('supabase_token'))
    
    if not truck:
        messages.error(request, 'Truck not found')
        return redirect('/custom-admin/portal/trucks/')
    
    if request.method == 'POST':
        success = supabase_service.delete_truck(truck_id, token=request.session.get('supabase_token'))
        if success:
            messages.success(request, f'Truck {truck.get("truck_number")} deleted successfully!')
        else:
            messages.error(request, 'Error deleting truck')
        return redirect('/custom-admin/portal/trucks/')
    
    context = {
        'truck': truck,
        'user_name': request.session.get('user_name', 'Admin'),
        'user_role': request.session.get('user_role', 'Staff'),
    }
    return render(request, 'admin/portal/trucks/delete.html', context)

def api_trucks(request):
    """API endpoint to get trucks"""
    trucks = supabase_service.get_trucks()
    return JsonResponse(trucks, safe=False)

def api_deliveries(request):
    """API endpoint to get deliveries with date filtering (Admin view - all deliveries)"""
    token = request.session.get('supabase_token')
    
    # Get query parameters
    today_only = request.GET.get('today', 'false') == 'true'
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Fetch all deliveries (no driver filter for admin)
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(
        f"{supabase_url}/rest/v1/deliveries?select=*,driver_id(*),truck_id(*)&order=created_at.desc",
        headers=headers
    )
    
    if response.status_code != 200:
        return JsonResponse({'deliveries': [], 'error': 'Failed to fetch deliveries'}, status=500)
    
    deliveries = response.json()
    
    # Apply date filters
    filtered_deliveries = []
    today_str = date.today().isoformat()
    
    for delivery in deliveries:
        created_at = delivery.get('created_at', '')
        delivery_date = created_at[:10] if created_at else ''
        
        # Filter by date range
        if start_date and end_date:
            if start_date <= delivery_date <= end_date:
                filtered_deliveries.append(delivery)
        elif today_only:
            if delivery_date == today_str:
                filtered_deliveries.append(delivery)
        else:
            filtered_deliveries.append(delivery)
    
    # Format the response
    result = []
    for delivery in filtered_deliveries:
        driver = delivery.get('driver_id', {})
        truck = delivery.get('truck_id', {})
        
        # Get coordinates from delivery_location or order
        lat = None
        lng = None
        delivery_location = delivery.get('delivery_location')
        if delivery_location:
            if isinstance(delivery_location, dict):
                lat = delivery_location.get('lat')
                lng = delivery_location.get('lng')
        
        result.append({
            'id': delivery.get('id'),
            'delivery_number': delivery.get('delivery_number'),
            'order_id': delivery.get('order_id'),
            'total_weight_kg': delivery.get('total_weight_kg'),
            'pickup_location': delivery.get('pickup_location'),
            'delivery_address': delivery.get('delivery_address'),
            'status': delivery.get('status'),
            'created_at': delivery.get('created_at'),
            'distance_km': delivery.get('distance_km'),
            'delivery_notes': delivery.get('delivery_notes'),
            'driver_id': driver,
            'truck_id': truck,
            'lat': lat,
            'lng': lng,
        })
    
    return JsonResponse({'deliveries': result}, safe=False)

def deliveries_page(request):
    """List all deliveries (Admin view)"""
    if not request.session.get('is_authenticated', False):
        messages.error(request, 'Please login to access the dashboard.')
        return redirect('/custom-admin/login/')
    
    token = request.session.get('supabase_token')
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Fetch all deliveries for admin
    response = requests.get(
        f"{supabase_url}/rest/v1/deliveries?select=*,driver_id(*),truck_id(*)&order=created_at.desc",
        headers=headers
    )
    
    deliveries = response.json() if response.status_code == 200 else []
    
    context = {
        'deliveries': deliveries,
        'user_name': request.session.get('user_name', 'Admin'),
        'user_role': request.session.get('user_role', 'Staff'),
    }
    return render(request, 'admin/portal/deliveries/list.html', context)

def update_delivery_status(request, delivery_id):
    """Update delivery status via AJAX"""
    if not request.session.get('is_authenticated', False):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        new_status = data.get('status')
        
        token = request.session.get('supabase_token')
        result = supabase_service.update_delivery_status(delivery_id, new_status, token=token)
        
        if result:
            return JsonResponse({'success': True, 'message': f'Status updated to {new_status}'})
        else:
            return JsonResponse({'error': 'Failed to update status'}, status=500)
    
    return JsonResponse({'error': 'Invalid method'}, status=405)

def test_map(request):
    return render(request, 'admin/portal/deliveries/test_map.html')

def notifications_page(request):
    return render(request, 'admin/portal/notifications/list.html')

def reports_page(request):
    return render(request, 'admin/portal/reports/list.html')

def api_employees(request):
    employees = supabase_service.get_employees()
    return JsonResponse(employees, safe=False)
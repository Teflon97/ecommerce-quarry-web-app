from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
import requests
import os
import uuid
from services import supabase_service

def driver_required(view_func):
    """Decorator to check if user is a driver"""
    def wrapper(request, *args, **kwargs):
        if not request.session.get('is_authenticated', False):
            messages.error(request, 'Please login to access the dashboard.')
            return redirect('/custom-admin/login/')
        
        if request.session.get('user_role') != 'Driver':
            messages.error(request, 'Access denied. Driver portal only.')
            return redirect('/custom-admin/portal/dashboard/')
        
        return view_func(request, *args, **kwargs)
    return wrapper

@driver_required
def driver_dashboard(request):
    """Driver dashboard with map"""
    context = {
        'user_name': request.session.get('user_name', 'Driver'),
        'user_role': request.session.get('user_role', 'Driver'),
    }
    return render(request, 'driver/dashboard.html', context)

@driver_required
def driver_notifications(request):
    """Driver notifications page with assignments"""
    context = {
        'user_name': request.session.get('user_name', 'Driver'),
        'user_role': request.session.get('user_role', 'Driver'),
    }
    return render(request, 'driver/notifications.html', context)

@driver_required
def get_driver_requests(request):
    """Get pending requests for the driver"""
    token = request.session.get('supabase_token')
    driver_id = request.session.get('user_id')
    
    if not driver_id:
        return JsonResponse({'requests': []}, safe=False)
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(
        f"{supabase_url}/rest/v1/requests?select=*,order_id(*)&assigned_to=eq.{driver_id}&status=eq.pending&order=created_at.desc",
        headers=headers
    )
    
    if response.status_code == 200:
        return JsonResponse({'requests': response.json()}, safe=False)
    
    return JsonResponse({'requests': []}, safe=False)

@driver_required
def get_driver_deliveries(request):
    """Get deliveries for the driver"""
    token = request.session.get('supabase_token')
    driver_id = request.session.get('user_id')
    
    if not driver_id:
        return JsonResponse({'deliveries': []}, safe=False)
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(
        f"{supabase_url}/rest/v1/deliveries?select=*,order_id(*)&driver_id=eq.{driver_id}&order=created_at.desc",
        headers=headers
    )
    
    if response.status_code == 200:
        deliveries = response.json()
        formatted = []
        for d in deliveries:
            order = d.get('order_id', {})
            delivery_location = order.get('delivery_location', {})
            if isinstance(delivery_location, str):
                try:
                    delivery_location = json.loads(delivery_location)
                except:
                    delivery_location = {}
            
            formatted.append({
                'id': d.get('id'),
                'delivery_number': d.get('delivery_number'),
                'order_id': d.get('order_id'),
                'status': d.get('status'),
                'total_weight_kg': d.get('total_weight_kg'),
                'delivery_address': d.get('delivery_address'),
                'distance_km': d.get('distance_km'),
                'accepted_at': d.get('accepted_at'),
                'loaded_up_at': d.get('loaded_up_at'),
                'in_transit_at': d.get('in_transit_at'),
                'delivered_at': d.get('delivered_at'),
                'delivery_location': delivery_location,
                'customer_name': order.get('customer'),
                'customer_phone': order.get('customer_phone'),
                'latitude': delivery_location.get('lat'),
                'longitude': delivery_location.get('lng')
            })
        return JsonResponse({'deliveries': formatted}, safe=False)
    
    return JsonResponse({'deliveries': []}, safe=False)

@driver_required
def respond_to_request(request, request_id):
    """Driver accepts or rejects a request"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    token = request.session.get('supabase_token')
    driver_session_id = request.session.get('user_id')
    
    if not driver_session_id:
        return JsonResponse({'error': 'Driver not identified'}, status=401)
    
    try:
        data = json.loads(request.body)
    except:
        data = {}
    
    action = data.get('action')
    rejection_reason = data.get('rejection_reason', '')
    
    if action not in ['accept', 'reject']:
        return JsonResponse({'error': 'Invalid action'}, status=400)
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        return JsonResponse({'error': 'Supabase configuration missing'}, status=500)
    
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Get the driver's employee_id
    driver_info_response = requests.get(
        f"{supabase_url}/rest/v1/employees?id=eq.{driver_session_id}&select=employee_id",
        headers=headers
    )
    
    if driver_info_response.status_code != 200:
        return JsonResponse({'error': 'Driver not found'}, status=404)
    
    driver_info = driver_info_response.json()
    if not driver_info:
        return JsonResponse({'error': 'Driver not found'}, status=404)
    
    driver_employee_id = driver_info[0].get('employee_id')
    
    if not driver_employee_id:
        return JsonResponse({'error': 'Driver employee_id not found'}, status=404)
    
    # Get the driver's assigned truck UUID from trucks table using assigned_driver_id
    truck_response = requests.get(
        f"{supabase_url}/rest/v1/trucks?assigned_driver_id=eq.{driver_session_id}&select=id,truck_number",
        headers=headers
    )
    
    truck_uuid = None
    if truck_response.status_code == 200:
        trucks = truck_response.json()
        if trucks:
            truck_uuid = trucks[0].get('id')
    
    # Get the request details
    get_req = requests.get(
        f"{supabase_url}/rest/v1/requests?id=eq.{request_id}&select=*,order_id(*)",
        headers=headers
    )
    
    if get_req.status_code != 200:
        return JsonResponse({'error': 'Failed to fetch request'}, status=500)
    
    req_data = get_req.json()
    if not req_data:
        return JsonResponse({'error': 'Request not found'}, status=404)
    
    req = req_data[0]
    order = req.get('order_id', {})
    
    # Extract the actual order ID string
    order_id_value = order.get('id') if isinstance(order, dict) else str(order)
    
    # Update request status
    update_data = {
        'status': 'accepted' if action == 'accept' else 'rejected',
        'updated_at': timezone.now().isoformat()
    }
    
    if action == 'accept':
        update_data['accepted_at'] = timezone.now().isoformat()
    else:
        update_data['rejected_at'] = timezone.now().isoformat()
        update_data['rejected_by'] = driver_session_id
        update_data['rejection_reason'] = rejection_reason
    
    req_response = requests.patch(
        f"{supabase_url}/rest/v1/requests?id=eq.{request_id}",
        headers=headers,
        json=update_data
    )
    
    if req_response.status_code not in [200, 204]:
        return JsonResponse({'error': 'Failed to update request'}, status=500)
    
    # If accepted, create delivery record
    if action == 'accept':
        # Get delivery location from order
        delivery_location = order.get('delivery_location')
        lat = None
        lng = None
        address = ''
        
        if delivery_location:
            if isinstance(delivery_location, dict):
                lat = delivery_location.get('lat')
                lng = delivery_location.get('lng')
                address = delivery_location.get('address', '')
            elif isinstance(delivery_location, str):
                try:
                    import json as json_module
                    parsed = json_module.loads(delivery_location)
                    lat = parsed.get('lat')
                    lng = parsed.get('lng')
                    address = parsed.get('address', '')
                except:
                    address = delivery_location
        
        if not address:
            address = order.get('delivery_address', 'Delivery address not specified')
        
        delivery_number = f"DLV-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
        
        delivery_data = {
            'delivery_number': delivery_number,
            'order_id': order_id_value,
            'driver_id': driver_session_id,
            'assigned_to': driver_employee_id,
            'truck_id': truck_uuid,  # Use the UUID, not the truck number
            'request_id': request_id,
            'total_weight_kg': 0,
            'delivery_address': address,
            'status': 'accepted',
            'current_latitude': lat,
            'current_longitude': lng,
            'accepted_at': timezone.now().isoformat(),
            'assigned_at': timezone.now().isoformat()
        }
        
        print(f"Creating delivery: {delivery_data}")
        
        create_response = requests.post(
            f"{supabase_url}/rest/v1/deliveries",
            headers=headers,
            json=delivery_data
        )
        
        print(f"Delivery creation response: {create_response.status_code} - {create_response.text}")
        
        if create_response.status_code == 201:
            # Update driver availability
            requests.patch(
                f"{supabase_url}/rest/v1/employees?id=eq.{driver_session_id}",
                headers=headers,
                json={'available_for_delivery': False}
            )
            return JsonResponse({'success': True, 'message': 'Delivery created successfully', 'redirect': '/driver/dashboard/'})
        else:
            return JsonResponse({'success': True, 'message': 'Request accepted', 'redirect': '/driver/dashboard/'})
    
    return JsonResponse({'success': True, 'message': f'Request {action}ed'})

@driver_required
def get_request_details(request, request_id):
    """Get details of a specific request for the modal"""
    token = request.session.get('supabase_token')
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(
        f"{supabase_url}/rest/v1/requests?id=eq.{request_id}&select=*,order_id(*)",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        if data:
            req = data[0]
            order = req.get('order_id', {})
            
            delivery_location = order.get('delivery_location', {})
            if isinstance(delivery_location, str):
                try:
                    delivery_location = json.loads(delivery_location)
                except:
                    delivery_location = {}
            
            address = delivery_location.get('address', 'Address not available')
            
            # Parse items
            items = []
            order_items = order.get('items', [])
            if isinstance(order_items, str):
                try:
                    order_items = json.loads(order_items)
                except:
                    order_items = []
            
            for item in order_items:
                product = item.get('product', {})
                items.append({
                    'name': product.get('name', 'Unknown'),
                    'quantity': item.get('quantity', 0),
                    'price': product.get('price', 0)
                })
            
            result = {
                'id': req.get('id'),
                'order_id': order.get('id'),
                'customer': order.get('customer', 'N/A'),
                'customer_phone': order.get('customer_phone', 'N/A'),
                'total': order.get('total', 0),
                'status': req.get('status'),
                'delivery_address': address,
                'latitude': delivery_location.get('lat'),
                'longitude': delivery_location.get('lng'),
                'items': items,
                'notes': req.get('notes', ''),
                'created_at': req.get('created_at')
            }
            return JsonResponse(result)
    
    return JsonResponse({'error': 'Request not found'}, status=404)

@driver_required
def update_delivery_status(request, delivery_id):
    """Update delivery status (loading, in_transit, delivered)"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    token = request.session.get('supabase_token')
    driver_id = request.session.get('user_id')
    
    if not driver_id:
        return JsonResponse({'error': 'Driver not identified'}, status=401)
    
    try:
        data = json.loads(request.body)
    except:
        data = {}
    
    new_status = data.get('status')
    delivery_notes = data.get('delivery_notes', '')
    distance_km = data.get('distance_km')
    total_weight_kg = data.get('total_weight_kg')
    actual_delivery_time = data.get('actual_delivery_time')
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        return JsonResponse({'error': 'Supabase configuration missing'}, status=500)
    
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    update_data = {
        'status': new_status,
        'updated_at': timezone.now().isoformat()
    }
    
    if new_status == 'delivered':
        update_data['delivered_at'] = timezone.now().isoformat()
        if delivery_notes:
            update_data['delivery_notes'] = delivery_notes
        if distance_km:
            update_data['distance_km'] = float(distance_km)
        if total_weight_kg:
            update_data['total_weight_kg'] = float(total_weight_kg)
        if actual_delivery_time:
            update_data['actual_delivery_time'] = actual_delivery_time
        
        # Update order status
        delivery_response = requests.get(
            f"{supabase_url}/rest/v1/deliveries?select=order_id&id=eq.{delivery_id}",
            headers=headers
        )
        if delivery_response.status_code == 200:
            deliveries_data = delivery_response.json()
            if deliveries_data:
                order_id = deliveries_data[0].get('order_id')
                requests.patch(
                    f"{supabase_url}/rest/v1/orders?id=eq.{order_id}",
                    headers=headers,
                    json={'status': 'delivered'}
                )
                # Make driver available again
                requests.patch(
                    f"{supabase_url}/rest/v1/employees?id=eq.{driver_id}",
                    headers=headers,
                    json={'available_for_delivery': True}
                )
    
    response = requests.patch(
        f"{supabase_url}/rest/v1/deliveries?id=eq.{delivery_id}",
        headers=headers,
        json=update_data
    )
    
    print(f"Update response status: {response.status_code}")
    print(f"Update response text: {response.text}")
    
    if response.status_code in [200, 204]:
        return JsonResponse({'success': True, 'message': 'Delivery completed successfully'})
    
    return JsonResponse({'error': 'Failed to update status'}, status=500)

@driver_required
def update_driver_location(request):
    """Update driver's current location for tracking"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    token = request.session.get('supabase_token')
    driver_id = request.session.get('user_id')
    
    if not driver_id:
        return JsonResponse({'error': 'Driver not identified'}, status=401)
    
    try:
        data = json.loads(request.body)
        current_lat = data.get('latitude')
        current_lng = data.get('longitude')
        
        if not current_lat or not current_lng:
            return JsonResponse({'error': 'Invalid coordinates'}, status=400)
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        headers = {
            'apikey': supabase_key,
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # First, get the driver's UUID
        driver_response = requests.get(
            f"{supabase_url}/rest/v1/employees?id=eq.{driver_id}&select=id",
            headers=headers
        )
        
        if driver_response.status_code != 200:
            return JsonResponse({'error': 'Driver not found'}, status=404)
        
        drivers = driver_response.json()
        if not drivers:
            return JsonResponse({'error': 'Driver not found'}, status=404)
        
        driver_uuid = drivers[0].get('id')
        
        response = requests.patch(
            f"{supabase_url}/rest/v1/employees?id=eq.{driver_uuid}",
            headers=headers,
            json={
                'last_latitude': current_lat,
                'last_longitude': current_lng,
                'last_location_update': timezone.now().isoformat()
            }
        )
        
        if response.status_code in [200, 204]:
            return JsonResponse({'success': True})
        
        return JsonResponse({'error': 'Failed to update location'}, status=500)
        
    except Exception as e:
        print(f"Error updating location: {e}")
        return JsonResponse({'error': str(e)}, status=500)

@driver_required
def get_delivery_details(request, delivery_id):
    """Get details of a specific delivery for the modal"""
    token = request.session.get('supabase_token')
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(
        f"{supabase_url}/rest/v1/deliveries?id=eq.{delivery_id}&select=*,order_id(*)",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        if data:
            delivery = data[0]
            order = delivery.get('order_id', {})
            
            delivery_location = order.get('delivery_location', {})
            if isinstance(delivery_location, str):
                try:
                    import json
                    delivery_location = json.loads(delivery_location)
                except:
                    delivery_location = {}
            
            address = delivery_location.get('address', delivery.get('delivery_address', 'Address not available'))
            
            # Parse items
            items = []
            order_items = order.get('items', [])
            if isinstance(order_items, str):
                try:
                    import json
                    order_items = json.loads(order_items)
                except:
                    order_items = []
            
            for item in order_items:
                product = item.get('product', {})
                items.append({
                    'name': product.get('name', 'Unknown'),
                    'quantity': item.get('quantity', 0),
                    'price': product.get('price', 0)
                })
            
            result = {
                'id': delivery.get('id'),
                'delivery_number': delivery.get('delivery_number'),
                'order_id': order.get('id'),
                'customer': order.get('customer', 'N/A'),
                'customer_phone': order.get('customer_phone', 'N/A'),
                'total': order.get('total', 0),
                'status': delivery.get('status'),
                'delivery_address': address,
                'latitude': delivery_location.get('lat'),
                'longitude': delivery_location.get('lng'),
                'items': items,
                'notes': delivery.get('delivery_notes', ''),
                'created_at': delivery.get('created_at'),
                'accepted_at': delivery.get('accepted_at'),
                'delivered_at': delivery.get('delivered_at'),
                'total_weight_kg': delivery.get('total_weight_kg', 0),
                'distance_km': delivery.get('distance_km', 0)
            }
            return JsonResponse(result)
    
    return JsonResponse({'error': 'Delivery not found'}, status=404)

@driver_required
def get_notifications(request):
    """Get notifications for driver (pending requests count)"""
    token = request.session.get('supabase_token')
    driver_id = request.session.get('user_id')
    
    if not driver_id:
        return JsonResponse({'notifications': 0})
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    headers = {
        'apikey': supabase_key,
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.get(
        f"{supabase_url}/rest/v1/requests?select=id&assigned_to=eq.{driver_id}&status=eq.pending",
        headers=headers
    )
    
    if response.status_code == 200:
        pending_count = len(response.json())
        return JsonResponse({'notifications': pending_count})
    
    return JsonResponse({'notifications': 0})
from django.shortcuts import redirect
from django.contrib import messages

def login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('is_authenticated', False):
            messages.error(request, 'Please login to access this page.')
            return redirect('/custom-admin/login/')
        return view_func(request, *args, **kwargs)
    return wrapper
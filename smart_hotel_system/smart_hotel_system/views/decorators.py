#Create a custom decorator to ensure the user cant access the admin dashboard unless login
from django.shortcuts import redirect

def admin_login_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('admin_id'):
            return redirect('super_admin_login')
        return view_func(request, *args, **kwargs)
    return wrapper
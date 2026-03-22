from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .decorators import admin_login_required
from django.shortcuts import render, redirect
from apps.platform_admin_flow.models import SuperAdminProfile
from django.contrib.auth.hashers import make_password, check_password
import json

@csrf_exempt
@admin_login_required
def admin_view(request):
    """Admin endpoint - for demonstration purposes"""
    return render(request, 'platform_template/quickdine-admin.html')

# Render the signup/login page for super admins
# Actual authentication logic for super admins
@csrf_exempt
def super_admin_signup(request):
    if request.method == 'POST':
        data = json.loads(request.body)

        email = data.get('email')
        password = data.get('password')

        # check if email is already blocked
        if SuperAdminProfile.objects.filter(email=email, is_blocked=True).exists():
            return JsonResponse({'error': 'This email is blocked. Contact support.'}, status=403)

        # check if email already exists
        if SuperAdminProfile.objects.filter(email=email).exists():
            return JsonResponse({'error': 'An account with this email already exists.'}, status=400)

        SuperAdminProfile.objects.create(
            fName=data.get('first_name'),
            lName=data.get('last_name'),
            email=email,
            telephone=data.get('phone'),
            password=make_password(password),
            platformName=data.get('platform_name'),
        )

        return JsonResponse({'success': True})

    return render(request, 'platform_template/quickdine-auth.html')
        
# Handle login for super admins
@csrf_exempt
def super_admin_login(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')

        try:
            admin = SuperAdminProfile.objects.get(email=email)

            if admin.is_blocked:
                return JsonResponse({'error': 'Account is blocked. Contact support.'}, status=403)

            if check_password(password, admin.password):
                admin.failed_attempt = 0
                admin.save()
                request.session['admin_id'] = admin.id
                return JsonResponse({'success': True})
            else:
                admin.failed_attempt += 1
                if admin.failed_attempt >= 3:
                    admin.is_blocked = True
                    admin.save()
                    return JsonResponse({'error': 'Account blocked due to too many failed attempts.'}, status=403)
                
                admin.save()
                remaining = 3 - admin.failed_attempt
                return JsonResponse({'error': f'Invalid credentials. {remaining} attempt(s) remaining.'}, status=400)

        except SuperAdminProfile.DoesNotExist:
            return JsonResponse({'error': 'No account found with this email.'}, status=404)

    return render(request, 'platform_template/quickdine-auth.html')
def logout_view(request):
    request.session.pop('admin_id', None)
    return redirect('super_admin_login')
from django.shortcuts import render
from django.http import JsonResponse,HttpResponse
from django.template.loader import render_to_string
from apps.common_flow.models import Menu,Category,InbuiltMenuItems
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
import json


def is_htmx(request):
    """Robust detection for HTMX requests.

    Checks common headers Django/HTMX set. Returns True when the request
    originates from HTMX (so views can return partials).
    """
    try:
        # request.headers is case-insensitive mapping in recent Django
        hdr = request.headers.get('HX-Request', None)
        if hdr is None:
            hdr = request.headers.get('Hx-Request', None)
        if hdr is None:
            # WSGI may expose it in META as HTTP_HX_REQUEST
            hdr = request.META.get('HTTP_HX_REQUEST', None)
        if isinstance(hdr, str):
            return hdr.lower() == 'true'
        return False
    except Exception:
        return False
    

# Additional order management views would go here
# MENU MANAGEMENT VIEWS
def add_menu_item(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        image = request.FILES.get('image')
        category_id = request.POST.get('category')
        category = Category.objects.get(pk=category_id) if category_id else None

        Menu.objects.create(
            title=name,
            description=description,
            price=price,
            picture=image,
            category=category
        )

        # Query the menu row items again to update the menu list
        menu_items = Menu.objects.all().order_by('menu_item_id')
        context = {'menu_items': menu_items}
        
        # if it is htmx request return the updated menu rows partial
        if is_htmx(request):
            return render(request, 'admin_templates/partials/menu-forms/manage_menu_rows.html', context)
    
    categories = Category.objects.all()
    context = {'categories': categories}
    return render(request, 'admin_templates/partials/menu-forms/add-menu-item-form.html', context)


def add_inbuilt_menu_item(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        image = request.FILES.get('image')
        category_id = request.POST.get('category')

        print(f"the category id is {category_id}")

        try:
            category = Category.objects.get(pk=category_id) if category_id else None
            # prevent duplication of inbuilt menu items
            if InbuiltMenuItems.objects.filter(title=name, description=description, price=price).exists():
               return HttpResponse(
                   status=204,
                   headers={
                       "HX-Trigger":json.dumps({
                           "toast-error":{
                               "message":"This inbuilt menu item already exists."
                           }
                       })
                   }
               )
            InbuiltMenuItems.objects.create(
                title=name,
                description=description,
                price=price,
                picture=image,
                category=category
            )

            # Return updated catalog
            builtin_foods = InbuiltMenuItems.objects.all()
            categories = Category.objects.all()
            context = {'builtin_foods': builtin_foods, 'categories': categories}
            html = render_to_string('admin_templates/partials/builtin_catalog.html', context)
            return HttpResponse(html)

        except Category.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Selected category does not exist.'})


    categories = Category.objects.all()
    context = {'categories': categories}

    return render(request, 'admin_templates/partials/menu-forms/add-inbuilt-menu-item-form.html', context)

def add_new_category(request):
    return render(request, 'admin_templates/partials/menu-forms/add-category.html')

def add_category(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')

        # prevent duplication of categories
        if Category.objects.filter(name=name).exists():
           return HttpResponse(
               status=204,
               headers={
                   "HX-Trigger":json.dumps({
                       "toast-error":{
                           "message":"This category already exists."
                       }
                   })
               }
           )

        Category.objects.create(
            name=name,
            description=description
        )

        # Return updated category list
        categories = Category.objects.all()
        context = {'categories': categories}
        html = render_to_string('admin_templates/partials/category-list.html', context)
        return HttpResponse(html)

    return render(request, 'admin_templates/partials/menu-forms/add-category.html')

def tap_add_inbuilt_menu_item(request,item_id):
    if request.method != "POST":
      return HttpResponse("Invalid request method.")
    inbuilt_item = get_object_or_404(InbuiltMenuItems, pk=item_id)

    #    prevent duplication of items by adding same inbuilt item
    if Menu.objects.filter(title=inbuilt_item.title, description=inbuilt_item.description, price=inbuilt_item.price).exists():
       return JsonResponse({'status': 'error', 'message': 'This inbuilt menu item already exists in the menu.'})

    # Get category
    if inbuilt_item.category:
        category_obj = inbuilt_item.category
    else:
        # Set a default category if none
        category_obj, _ = Category.objects.get_or_create(name='Uncategorized')

    Menu.objects.create(
       title=inbuilt_item.title,
       description=inbuilt_item.description,
       price=inbuilt_item.price,
       picture=inbuilt_item.picture,
       category=category_obj
    )
    # Query the menu row items again to update the menu list
    menu_items = Menu.objects.all().order_by('menu_item_id')
    context = {'menu_items': menu_items}
    
    # if it is htmx request return the updated menu rows partial
    if is_htmx(request):
        return render(request, 'admin_templates/partials/menu-forms/manage_menu_rows.html', context)
    
    # Otherwise redirect to the menu partial
    return render(request, 'admin_templates/partials/menu.html', context)

def menu_search(request):
    query = request.GET.get('query','')
    menu_items = Menu.objects.filter(Q(title__icontains=query) | Q(description__icontains=query))
    context = {'menu_items': menu_items}
    return render(request, 'admin_templates/partials/menu-forms/manage_menu_rows.html', context)

def menu_filter(request,slug):
    category = get_object_or_404(Category, slug=slug)
    menu_items = Menu.objects.filter(category=category)
    context = {'menu_items': menu_items}
    return render(request, 'admin_templates/partials/menu-forms/manage_menu_rows.html', context)

def toggle_menu_availability(request, item_id):
    menu_item = get_object_or_404(Menu, menu_item_id = item_id)
    menu_item.is_available = not menu_item.is_available
    menu_item.save()

    menu_items = Menu.objects.all().order_by('menu_item_id')
    context = {'menu_items': menu_items}
    return render(request, 'admin_templates/partials/menu-forms/manage_menu_rows.html', context)

def edit_menu_item(request, item_id):
    menu_item = get_object_or_404(Menu, menu_item_id=item_id)

    if request.method == 'POST':
        menu_item.title = request.POST.get('name')
        menu_item.description = request.POST.get('description')
        menu_item.price = request.POST.get('price')
        image = request.FILES.get('image')
        if image:
            menu_item.picture = image
        category_id = request.POST.get('category')
        menu_item.category = Category.objects.get(pk=category_id) if category_id else None
        menu_item.save()

        return JsonResponse({'status': 'success', 'message': 'Menu item updated successfully.'})

    categories = Category.objects.all()
    context = {
        'menu_item': menu_item,
        'categories': categories
    }
    return render(request, 'admin_templates/partials/menu-forms/edit-menu-item-form.html', context)

def delete_menu_item(request, item_id):
    menu_item = get_object_or_404(Menu, menu_item_id=item_id)
    menu_item.delete()

    menu_items = Menu.objects.all().order_by('menu_item_id')
    context = {'menu_items': menu_items}
    return render(request, 'admin_templates/partials/menu-forms/manage_menu_rows.html', context)

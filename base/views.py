
from django.shortcuts import render,redirect,get_object_or_404
from django.views import View
from .models import *
from store.utils import cookieCart, cartData, guestOrder
from store.models import *
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST




class Home(View):
    def get(self, request):
        cars = Car_Model.objects.all()
        products = Products.objects.all()    
        wishlist_product_ids = []
        if request.user.is_authenticated:
            wishlist_product_ids = WishlistItem.objects.filter(
                user=request.user
            ).values_list('product_id', flat=True)
        data = cartData(request)
                               
        cartItems = data['cartItems']

        cats = Catalogue.objects.all()
        context = {
                   'cats': cats,
                   'cars': cars,
                    'cartItems':cartItems,
                    'products': products,
                    'wishlist_product_ids': wishlist_product_ids
                    }
        
        return render(request, 'base/index1.html',context)




# def autocomplete(request):
#     if 'term' in request.GET:
#         term = request.GET.get('term', '').strip()
#         qs = Product.objects.filter(name__icontains=term) if term else []
        
#         if qs.exists():
#             titles = [{"label": product.name, "url": f"/product_details/{product.pk}/"} for product in qs]
#         else:
#             titles = [{"label": "No results found", "url": "#"}]  # Placeholder, no redirect
        
#         return JsonResponse(titles, safe=False)
    
#     return render(request, 'base/index1.html')


def autocomplete(request):
    if 'term' in request.GET:
        qs = Products.objects.filter(name__icontains=request.GET.get('term'))
        titles = []
        for product in qs:
            titles.append({
                'id': product.id,  # Assuming you have an id field
                'label': product.name,  # What shows in the dropdown
                'value': product.name   # What fills the input after selection
            })
        return JsonResponse(titles, safe=False)
    return render(request, 'base/index1.html')





# # @login_required
# @require_POST
# def toggle_wishlist(request):
#     product_id = request.POST.get('product_id')
#     product = get_object_or_404(Products, id=product_id)
    
#     # Check if this product is already in the user's wishlist
#     wishlist_item = WishlistItem.objects.filter(user=request.user, product=product).first()
    
#     if wishlist_item:
#         # Product is in wishlist, so remove it
#         wishlist_item.delete()
#         in_wishlist = False
#     else:
#         # Product is not in wishlist, so add it
#         WishlistItem.objects.create(user=request.user, product=product)
#         in_wishlist = True
    
#     return JsonResponse({
#         'success': True,
#         'in_wishlist': in_wishlist,
#         'product_id': product_id
#     })


# # @login_required
# def wishlist(request):
#     wishlist_items = WishlistItem.objects.filter(user=request.user).select_related('product')
    
#     context = {
#         'wishlist_items': wishlist_items
#     }
#     return render(request, 'base/wishlist.html', context)





@require_POST
def toggle_wishlist(request):
    product_id = request.POST.get('product_id')
    product = get_object_or_404(Products, id=product_id)
    
    if request.user.is_authenticated:
        # Logged-in user: Use the database
        wishlist_item = WishlistItem.objects.filter(user=request.user, product=product).first()
        
        if wishlist_item:
            # Product is in wishlist, so remove it
            wishlist_item.delete()
            in_wishlist = False
        else:
            # Product is not in wishlist, so add it
            WishlistItem.objects.create(user=request.user, product=product)
            in_wishlist = True
    else:
        # Anonymous user: Use session
        # Initialize wishlist in session if it doesn't exist
        if 'wishlist' not in request.session:
            request.session['wishlist'] = []
        
        # Get the current wishlist
        wishlist = request.session['wishlist']
        
        # Check if product is in wishlist
        if product_id in wishlist:
            # Remove it
            wishlist.remove(product_id)
            in_wishlist = False
        else:
            # Add it
            wishlist.append(product_id)
            in_wishlist = True
        
        # Save the updated wishlist to session
        request.session['wishlist'] = wishlist
        request.session.modified = True
    
    return JsonResponse({
        'success': True,
        'in_wishlist': in_wishlist,
        'product_id': product_id
    })


def wishlist(request):
    if request.user.is_authenticated:
        # Logged-in user: Get wishlist from database
        wishlist_items = WishlistItem.objects.filter(user=request.user).select_related('product')
        context = {
            'wishlist_items': wishlist_items
        }
    else:
        # Anonymous user: Get wishlist from session
        session_wishlist = request.session.get('wishlist', [])
        
        # Get the product objects
        wishlist_products = Products.objects.filter(id__in=session_wishlist)
        
        # Create a list of dictionary items to mimic WishlistItem objects
        wishlist_items = [{'product': product} for product in wishlist_products]
        
        context = {
            'wishlist_items': wishlist_items
        }
    
    return render(request, 'base/wishlist.html', context)











class Blog(View):
    def get(self, request):
        catalogue = Catalogue.objects.all()
        context = {'catalogue': catalogue}
        return render(request, 'base/blog.html', context)

        

class ProductView(View):
    def get(self, request):
        products = Products.objects.all()
        sidemirrors = Products.objects.filter(cat__name ='Side Mirrors')
        hoods = Products.objects.filter(cat__name ='Hoods & Bonnets')
        brakes = Products.objects.filter(cat__name ='Brakes & Brakepads')
        lightlamp = Products.objects.filter(cat__name ='Ligtning and Lamps')
        mirrors = Products.objects.filter(cat__name ='Accesories') 
        mirrors = Products.objects.filter(cat__name ='Bumbers & Grilles') 


        context = {'products': products,
                   'lightlamp':lightlamp,
                    'brakes': brakes,
                    'sidemirrors': sidemirrors,
                    'hoods': hoods}
        return render(request, 'base/products.html', context)
    


class ProductDetailView(View):
    def get(self,request,pk):
        single_product = Products.objects.get(pk=pk)
        context ={'single_product': single_product}
        return render(request, 'base/product-details.html', context)

# class ProductDetailView(View):
#     def get(self,request):
#        return render(request, 'base/product-details.html')


def car_model_items(request, pk):
  
    car_model = Car_Model.objects.get(pk=pk)
    products = Products.objects.filter(car_model=car_model)
    
    context = {
        'car_model': car_model,
        'products': products
    }
    
    return render(request, 'base/car_item_details.html', context)

class AboutView(View):
    def get(self,request):
        return render(request,'base/About.html')



class SearchView(View):
    def get(self,request):
       return render(request,'base/Search.html')

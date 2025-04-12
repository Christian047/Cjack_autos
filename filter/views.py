

import logging
from django.shortcuts import render
from django.http import JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
import traceback
import json

# Import your models - adjust the import path as needed for your project structure
from store.models import Products
from base.models import Car_Model
from store.utils import *


# Set up logger
logger = logging.getLogger(__name__)





def advanced_search_view(request):
    """View for rendering the advanced search template"""
    products = Products.objects.all()
    logger.info("Advanced search page accessed by user: %s", request.user)

    try:
        # Get all car models for the dropdown
        car_models = Car_Model.objects.all()
        logger.debug("Retrieved %d car models for dropdown", car_models.count())

        # Get chassis choices from the model
        chassis_choices = Products._meta.get_field('chassis').choices
        logger.debug("Retrieved chassis choices: %s", chassis_choices)

        # Prepare cart data (similar to Home view)
        data = cartData(request)
        cartItems = data['cartItems']

        # Prepare wishlist data for authenticated users
    
        context = {
            'car_models': car_models,
            'chassis_choices': chassis_choices,
            'cartItems': cartItems,
            'products': products,
       
        }

        # Keep using your existing template path
        return render(request, 'filter/filter.html', context)

    except Exception as e:
        logger.error("Error in advanced_search_view: %s", str(e))
        logger.error(traceback.format_exc())

        # Add error message to context
        context = {
            'error_message': 'An error occurred while loading the search page.',
            'car_models': [],
            'chassis_choices': [],
            'products': products,
            'cartItems': 0,
            'wishlist_product_ids': []
        }

        return render(request, 'filter/filter.html', context)







def product_search_api(request):
    """API endpoint to handle the product search functionality"""
    logger.info("Product search API called with params: %s", dict(request.GET))
    
    try:
        # Get filter parameters from request
        car_model = request.GET.get('car_model', '')
        chassis = request.GET.get('chassis', '')
        price_min = request.GET.get('price_min', '')
        price_max = request.GET.get('price_max', '')
        rating = request.GET.get('rating', '')
        
        # Log the parameters for debugging
        logger.debug("Search parameters - car_model: %s, chassis: %s, price_min: %s, price_max: %s, rating: %s", 
                    car_model, chassis, price_min, price_max, rating)
        
        # Start with all products
        products = Products.objects.all()
        logger.debug("Initial product count: %d", products.count())
        
        # Apply filters if provided and log the count after each filter
        if car_model:
            try:
                products = products.filter(car_model_id=car_model)
                logger.debug("After car_model filter, product count: %d", products.count())
            except ValueError as e:
                logger.warning("Invalid car_model parameter: %s", car_model)
                logger.warning(str(e))
        
        if chassis:
            products = products.filter(chassis=chassis)
            logger.debug("After chassis filter, product count: %d", products.count())
        
        if price_min:
            try:
                products = products.filter(price__gte=int(price_min))
                logger.debug("After price_min filter, product count: %d", products.count())
            except ValueError as e:
                logger.warning("Invalid price_min parameter: %s", price_min)
                logger.warning(str(e))
        
        if price_max:
            try:
                products = products.filter(price__lte=int(price_max))
                logger.debug("After price_max filter, product count: %d", products.count())
            except ValueError as e:
                logger.warning("Invalid price_max parameter: %s", price_max)
                logger.warning(str(e))
        
        if rating:
            try:
                products = products.filter(rating_value__gte=float(rating))
                logger.debug("After rating filter, product count: %d", products.count())
            except ValueError as e:
                logger.warning("Invalid rating parameter: %s", rating)
                logger.warning(str(e))
        
        # Prepare the response data
        results = []
        for product in products:
            try:
                car_model_name = product.car_model.name if product.car_model else ''
                chassis_display = product.get_chassis_display() if hasattr(product, 'get_chassis_display') else product.chassis
                picture_url = product.picture.url if product.picture else None
                
                product_data = {
                    'id': product.id,
                    'name': product.name,
                    'car_model_id': product.car_model_id,
                    'car_model_name': car_model_name,
                    'chassis': chassis_display,
                    'price': product.price,
                    'rating_value': float(product.rating_value) if product.rating_value is not None else 0.0,
                    'rating_count': product.rating_count if product.rating_count is not None else 0,
                    'picture': picture_url,
                }
                
                results.append(product_data)
                
            except Exception as e:
                logger.error("Error processing product id %s: %s", product.id, str(e))
                logger.error(traceback.format_exc())
                # Continue with the next product instead of breaking the entire response
        
        logger.info("Search returned %d products", len(results))
        logger.debug("First few results: %s", json.dumps(results[:3]) if results else "[]")
        
        return JsonResponse(results, safe=False)
    
    except Exception as e:
        logger.error("Error in product_search_api: %s", str(e))
        logger.error(traceback.format_exc())
        
        return JsonResponse({
            'error': 'An error occurred while searching for products.',
            'error_details': str(e)
        }, status=500)
    """Middleware to log the time taken for each request"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        import time
        start_time = time.time()
        
        response = self.get_response(request)
        
        duration = time.time() - start_time
        logger.info(
            "Request to %s took %.2fs to process",
            request.path,
            duration
        )
        
        return response
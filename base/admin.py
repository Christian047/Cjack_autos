from django.contrib import admin
from .models import Products, Catalogue, WishlistItem, Car_Model
from django.utils.safestring import mark_safe

# Register your models here.




@admin.register(Catalogue)
class CatalogueAdminh(admin.ModelAdmin):
    list_display = ('name', 'price', 'model', 'category_image' )
    
    def category_image(self, obj):
        if obj.picture:  # Ensure there's an image
            return mark_safe(f'<img src="{obj.picture.url}" width="50" height="50" />')
        return "No Image"




@admin.register(Products)
class ProductsAdmin(admin.ModelAdmin):
    list_display = ("name","category_image" , "price", "cat", "free_shipping",  "is_trending", "stock_quantity", "rating_count", "rating_value", "original_price", "discount_percentage","description", "free_installation", "picture", "chassis", "model",)


    def category_image(self, obj):
        if obj.picture:  # Ensure there's an image
            return mark_safe(f'<img src="{obj.picture.url}" width="100" height="100" />')
        return "No Image"

@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ("created_at", "product", "user")


@admin.register(Car_Model)
class Car_ModelAdmin(admin.ModelAdmin):
    list_display = ("name","category_image", )
    
    def category_image(self, obj):
        if obj.picture:  # Ensure there's an image
            return mark_safe(f'<img src="{obj.picture.url}" width="80" height="40" />')
        return "No Image"


from django.db import models
from django.contrib.auth.models import User
from django.utils.html import mark_safe
# Create your models here.




class Catalogue(models.Model):
    name= models.CharField(max_length=200, null=True, blank=True)
    price= models.DecimalField(max_digits=10,decimal_places=2,null=True, blank=True)
    model= models.CharField(max_length=200,null=True, blank=True)
    picture = models.ImageField(upload_to='images',null=True, blank=True)
    

    class Meta:
        verbose_name_plural = 'Catalogue'

    def __str__(self):
        return self.name
    
    
class Car_Model(models.Model):
    name= models.CharField(max_length=200, null=True, blank=True)
    picture = models.ImageField(upload_to='car_images',null=True, blank=True)
    date_added = models.DateTimeField(blank= True, null=True)
    
    
    def __str__(self):
            return self.name
        
    class Meta:
        ordering = ['-date_added']

myproducts = [
    ('2012', '2012'),
    ('2013', '2013'),
    ('2014', '2014'),
    ('2015', '2015'),
    ('2016', '2016'),
    ('2017', '2017'),
    ('2018', '2018'),
    ('2019', '2019'),
    ('2020', '2020'),
    ('2021', '2021'),
    ('2022', '2022'),
    ('2023', '2023'),
    ('2024', '2024'),
]



class Products(models.Model):
    name= models.CharField(max_length=200, null=True, blank=True)
    cat = models.ForeignKey(Catalogue, null=True, blank=True, on_delete=models.CASCADE,related_name='prods')
    car_model = models.ForeignKey(Car_Model, null=True, blank=True, on_delete=models.CASCADE,related_name='car_products')

    price= models.IntegerField(null=True, blank=True,default=0)
    model= models.CharField(max_length=200,null=True, blank=True)
    chassis = models.CharField(max_length=100,choices=myproducts,null=True, blank=True)
    picture = models.ImageField(upload_to='images',null=True, blank=True)
    free_installation = models.BooleanField(default=False, blank=True)
    
    
    description = models.TextField(blank=True, null=True)
    stock_quantity = models.IntegerField(default=10, null=True)
    is_trending = models.BooleanField(default=False, null=True)
    discount_percentage = models.IntegerField(default=0, null=True)
    original_price = models.IntegerField(null=True, blank=True)
    rating_value = models.DecimalField(max_digits=3, decimal_places=1, default=0, null=True)
    rating_count = models.IntegerField(default=0, null=True)
    free_shipping = models.BooleanField(default=False)
    

    class Meta:
        verbose_name_plural = 'Products'
    def __str__(self):
        return self.name
    




class WishlistItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'product')
        
    def __str__(self):
        return f"{self.user.username}'s wishlist: {self.product.name}"
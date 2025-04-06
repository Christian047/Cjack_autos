# Generated by Django 5.1.3 on 2025-03-08 15:08

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0013_products_cat'),
    ]

    operations = [
        migrations.AddField(
            model_name='products',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='products',
            name='discount_percentage',
            field=models.IntegerField(default=0, null=True),
        ),
        migrations.AddField(
            model_name='products',
            name='free_shipping',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='products',
            name='is_trending',
            field=models.BooleanField(default=False, null=True),
        ),
        migrations.AddField(
            model_name='products',
            name='original_price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='products',
            name='rating_count',
            field=models.IntegerField(default=0, null=True),
        ),
        migrations.AddField(
            model_name='products',
            name='rating_value',
            field=models.DecimalField(decimal_places=1, default=0, max_digits=3, null=True),
        ),
        migrations.AddField(
            model_name='products',
            name='stock_quantity',
            field=models.IntegerField(default=0, null=True),
        ),
        migrations.AlterField(
            model_name='products',
            name='cat',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='prods', to='base.catalogue'),
        ),
    ]

from django.contrib import admin
from .models import (
    Category, PackageType, MeasurementUnit, Culture,
    Product, ProductImage, Order, OrderItem,
    Inventory, ProductMovement, BackupSettings, SystemParameter
)

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'culture', 'quantity', 'price', 'is_available')
    list_filter = ('category', 'culture', 'is_available')
    search_fields = ('name', 'real_name', 'import_name', 'lot_number')
    inlines = [ProductImageInline]

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'comment')
    inlines = [OrderItemInline]

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity_expected', 'quantity_actual', 'difference', 'created_at')
    list_filter = ('created_at', 'performed_by')
    search_fields = ('product__name', 'comment')

@admin.register(ProductMovement)
class ProductMovementAdmin(admin.ModelAdmin):
    list_display = ('product', 'movement_type', 'quantity', 'date', 'performed_by')
    list_filter = ('movement_type', 'date', 'performed_by')
    search_fields = ('product__name', 'document_number', 'comment')

# Register simple models
admin.site.register(Category)
admin.site.register(PackageType)
admin.site.register(MeasurementUnit)
admin.site.register(Culture)
admin.site.register(BackupSettings)
admin.site.register(SystemParameter) 
from django.contrib import admin
from .models import (
    PackageType, MeasurementUnit, Culture,
    Product, ProductImage, ProductVariation, ProductVariationImage, Order, OrderItem,
    Inventory, ProductIncome, BackupSettings, SystemParameter, ProductInventory, ProductIncomeItem
)

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductVariationImageInline(admin.TabularInline):
    model = ProductVariationImage
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'real_name', 'culture', 'quantity', 'price', 'is_available')
    list_filter = ('culture', 'is_available')
    search_fields = ('name', 'real_name', 'import_name', 'lot_number')
    inlines = [ProductImageInline]

@admin.register(ProductVariation)
class ProductVariationAdmin(admin.ModelAdmin):
    list_display = ('parent_product', 'real_name', 'quantity', 'price', 'is_available')
    list_filter = ('parent_product', 'is_available')
    search_fields = ('parent_product__name', 'real_name', 'import_name', 'lot_number')
    inlines = [ProductVariationImageInline]

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

# Register simple models
admin.site.register(PackageType)
admin.site.register(MeasurementUnit)
admin.site.register(Culture)
admin.site.register(BackupSettings)
admin.site.register(SystemParameter) 
admin.site.register(ProductImage)
admin.site.register(ProductVariationImage)
admin.site.register(OrderItem)
admin.site.register(ProductInventory)
admin.site.register(ProductIncome)
admin.site.register(ProductIncomeItem)

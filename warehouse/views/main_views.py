from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, F, Q
from ..models import Product, Order, Inventory, ProductIncome, ProductVariation

@login_required
def home(request):
    """Home page view with dashboard statistics."""
    total_products = Product.objects.count()
    successful_orders = Order.objects.filter(status='completed').count()
    orders_count = Order.objects.count()
    recent_orders = Order.objects.order_by('-created_at')[:5]
    successful_orders = Order.objects.filter(status='successful').count()
    
    # Get low stock products (less than 5 units)
    low_stock_variations_products = ProductVariation.objects.filter(quantity__lt=5, is_available=True)
    
    # Get top 5 products by order count
    top_products = Product.objects.annotate(
        total_ordered=Sum('variations__orderitem__quantity', distinct=True)
    ).order_by('-total_ordered')[:5]
    
    context = {
        'total_products': total_products,
        'orders_count': orders_count,
        'successful_orders': successful_orders,
        'recent_orders': recent_orders,
        'low_stock_variations_products': low_stock_variations_products,
        'top_products': top_products,
    }
    
    return render(request, 'warehouse/home.html', context)

@login_required
def dashboard(request):
    """View to display dashboard with key metrics and recent activity."""
    # Get recent orders
    recent_orders = Order.objects.all().order_by('-created_at')[:5]
    
    # Get low stock products
    low_stock_threshold = 5  # This could be a setting
    low_stock_products = Product.objects.filter(
        quantity__lt=low_stock_threshold,
        is_available=True
    ).order_by('quantity')[:5]
    
    # Get total products count
    total_products = Product.objects.count()
    
    # Get total orders count
    total_orders = Order.objects.count()
    
    # Get pending orders count
    pending_orders = Order.objects.filter(status='pending').count()
    
    # Get inventory discrepancies
    # Fix: Changed from difference__ne=0 to use ~Q(difference=0) instead
    inventory_discrepancies = Inventory.objects.filter(
        ~Q(difference=0)
    ).order_by('-created_at')[:5]
    
    # Get recent movements
    recent_movements = ProductMovement.objects.all().order_by('-date')[:5]

    # Get top products by quantity
    top_products = Product.objects.order_by('-quantity')[:5]
    
    # Calculate general statistics
    total_stock_value = Product.objects.filter(is_available=True).aggregate(
        total_value=Sum(F('quantity') * F('price'))
    )['total_value'] or 0
    
    # Recent activity (combined and sorted)
    recent_activities = []
    
    # Add orders to activities
    for order in recent_orders:
        recent_activities.append({
            'type': 'order',
            'date': order.created_at,
            'object': order,
            'description': f'Замовлення #{order.id} створено'
        })
    
    # Add movements to activities
    for movement in recent_movements:
        recent_activities.append({
            'type': 'movement',
            'date': movement.date,
            'object': movement,
            'description': f'{movement.get_movement_type_display()} товару "{movement.product.name}"'
        })
    
    # Add inventory to activities
    for inventory in inventory_discrepancies:
        recent_activities.append({
            'type': 'inventory',
            'date': inventory.created_at,
            'object': inventory,
            'description': f'Виявлено розбіжність ({inventory.difference}) для "{inventory.product.name}"'
        })
    
    # Sort activities by date (newest first)
    recent_activities.sort(key=lambda x: x['date'], reverse=True)
    recent_activities = recent_activities[:10]  # Limit to 10
    
    context = {
        'recent_orders': recent_orders,
        'low_stock_products': low_stock_products,
        'total_products': total_products,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'inventory_discrepancies': inventory_discrepancies,
        'recent_movements': recent_movements,
        'categories': categories,
        'top_products': top_products,
        'total_stock_value': total_stock_value,
        'recent_activities': recent_activities,
    }
    
    return render(request, 'warehouse/dashboard.html', context) 
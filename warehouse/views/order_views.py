from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db.models import Q, F
from ..models import Culture, Order, OrderItem, Product, ProductVariation
from ..forms import OrderForm, OrderItemFormSet, AddToCartForm, CartItemForm, CheckoutForm, ProductVariationFilterForm
import json

@login_required
def order_list(request):
    """View to display the list of orders."""
    orders = Order.objects.all().order_by('-created_at')
    
    # Filter by status if provided
    status = request.GET.get('status', '')
    if status:
        orders = orders.filter(status=status)
    
    # Paginate results
    paginator = Paginator(orders, 10)  # Show 10 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'orders': page_obj,
        'current_status': status,
    }
    
    return render(request, 'warehouse/order/order_list.html', context)

@login_required
def order_detail(request, pk):
    """View to display order details."""
    order = get_object_or_404(Order.objects.prefetch_related(
        'items__product_variation__parent_product__culture',
        'items__product_variation__measurement_unit',
        'items__product_variation__package_type',
        'items__product_variation__parent_product__productimage_set'
    ), id=pk)
    
    context = {
        'order': order
    }
    
    return render(request, 'warehouse/order/order_detail.html', context)

@login_required
def order_create(request):
    """View to create a new order."""
    # Get all available cultures for the filter
    cultures = Culture.objects.all()
    
    # Get all product variations with their related data
    variations = ProductVariation.objects.select_related(
        'parent_product',
        'parent_product__culture',
        'measurement_unit',
        'package_type'
    ).prefetch_related(
        'parent_product__productimage_set'
    ).filter(
        is_available=True  # Only show available variations
    ).order_by('parent_product__culture__name', 'parent_product__real_name', 'name')
    
    # Apply filters if provided
    culture_id = request.GET.get('culture')
    real_name = request.GET.get('real_name')
    name = request.GET.get('name')
    lot_number = request.GET.get('lot_number')
    
    if culture_id:
        variations = variations.filter(parent_product__culture_id=culture_id)
    if real_name:
        variations = variations.filter(parent_product__real_name__icontains=real_name)
    if name:
        variations = variations.filter(
            Q(name__icontains=name) | 
            Q(import_name__icontains=name) | 
            Q(parent_product__real_name__icontains=name)
        )
    if lot_number:
        variations = variations.filter(lot_number__icontains=lot_number)
    
    context = {
        'cultures': cultures,
        'variations': variations,
    }
    
    return render(request, 'warehouse/order/order_form.html', context)

@login_required
def order_confirm(request):
    """View to confirm order details before creation."""
    if request.method != 'POST':
        return redirect('order_create')
    
    try:
        items_json = request.POST.get('items_json')
        if not items_json:
            raise ValueError("No items selected")
        
        items_data = json.loads(items_json)
        if not items_data:
            raise ValueError("No items selected")
        
        # Get all selected variations in one query
        variation_ids = [item['id'] for item in items_data]
        variations = ProductVariation.objects.select_related(
            'parent_product',
            'parent_product__culture',
            'measurement_unit',
            'package_type'
        ).prefetch_related(
            'parent_product__productimage_set'
        ).filter(id__in=variation_ids)
        
        # Create a lookup dictionary for quantities
        quantities = {str(item['id']): item['quantity'] for item in items_data}
        
        # Prepare items for display
        order_items = []
        total_items = 0
        
        for variation in variations:
            quantity = quantities.get(str(variation.id), 0)
            if quantity > variation.quantity:
                messages.error(request, f'Недостатньо товару "{variation.name}" (доступно: {variation.quantity} {variation.measurement_unit.name})')
                return redirect('order_create')
            
            order_items.append({
                'variation': variation,
                'quantity': quantity,
            })
            total_items += quantity
        
        # Store data in session for the next step
        request.session['order_items'] = items_json
        
        context = {
            'order_items': order_items,
            'total_items': total_items,
        }
        
        return render(request, 'warehouse/order/order_confirm.html', context)
        
    except (json.JSONDecodeError, ValueError) as e:
        messages.error(request, 'Помилка при обробці даних замовлення. Будь ласка, спробуйте ще раз.')
        return redirect('order_create')
    except Exception as e:
        messages.error(request, f'Сталася помилка: {str(e)}')
        return redirect('order_create')

@login_required
def order_create_final(request):
    """View to create the order after confirmation."""
    if request.method != 'POST':
        return redirect('order_create')
    
    try:
        items_json = request.session.get('order_items')
        if not items_json:
            raise ValueError("No items found in session")
        
        items_data = json.loads(items_json)
        if not items_data:
            raise ValueError("No items to process")
        
        # Create the order
        order = Order.objects.create(
            status='pending',
            created_by=request.user
        )
        
        # Get all variations in one query
        variation_ids = [item['id'] for item in items_data]
        variations = ProductVariation.objects.select_related(
            'measurement_unit'
        ).filter(id__in=variation_ids)
        variations_dict = {str(var.id): var for var in variations}
        
        # Create order items and update stock
        for item_data in items_data:
            variation = variations_dict.get(str(item_data['id']))
            if not variation:
                continue
                
            quantity = item_data['quantity']
            
            # Create order item
            OrderItem.objects.create(
                order=order,
                product_variation=variation,
                quantity=quantity
            )
            
            # Update stock
            variation.quantity = F('quantity') - quantity
            variation.save()
        
        # Clear session data
        if 'order_items' in request.session:
            del request.session['order_items']
        
        messages.success(request, f'Замовлення #{order.id} успішно створено!')
        return redirect('order_detail', pk=order.id)
        
    except Exception as e:
        messages.error(request, f'Помилка при створенні замовлення: {str(e)}')
        return redirect('order_create')

@login_required
def order_cancel(request, pk):
    """View to cancel an order."""
    order = get_object_or_404(Order, pk=pk)
    
    # Ensure users can only cancel their own orders (except for staff)
    if not request.user.is_staff and order.created_by != request.user:
        messages.error(request, 'У вас немає доступу для скасування цього замовлення.')
        return redirect('order_list')
    
    if request.method == 'POST':
        order.status = 'canceled'
        # Return quantities to variations
        for item in order.items.all():
            variation = item.product_variation
            variation.quantity += item.quantity
            variation.save()
        order.save()

        messages.success(request, f'Замовлення #{order.id} успішно скасовано.')
        return redirect('order_list')
    
    context = {
        'order': order,
    }
    
    return render(request, 'warehouse/order/order_confirm_cancel.html', context)

@login_required
def order_complete(request):
    """View для завершення та збереження замовлення."""
    if request.method != 'POST':
        messages.error(request, 'Неправильний метод запиту.')
        return redirect('order_create')
    
    # Отримуємо дані про вибрані товари
    items_json = request.POST.get('items_json', '[]')
    comment = request.POST.get('comment', '')
    
    try:
        selected_items = json.loads(items_json)
        
        # Перевіряємо, чи є вибрані товари
        if not selected_items:
            messages.error(request, 'Не вибрано жодного товару.')
            return redirect('order_create')
        
        # Створюємо нове замовлення
        order = Order.objects.create(
            created_by=request.user,
            status='successful',  # Статус "успішно"
            comment=comment,
            total_price=0  # Початкова сума, оновимо пізніше
        )
        
        # Додаємо товари до замовлення
        total_sum = 0
        
        for item in selected_items:
            variation = get_object_or_404(ProductVariation, id=item['id'])
            quantity = int(item['quantity'])
            
            # Перевіряємо наявність товару
            if quantity > variation.quantity:
                # Видаляємо замовлення, якщо товару недостатньо
                order.delete()
                messages.error(request, f'Недостатня кількість товару "{variation.name}". Доступно: {variation.quantity}.')
                return redirect('order_create')
            
            # Створюємо елемент замовлення
            item_price = variation.price
            item_total = quantity * item_price
            total_sum += item_total
            
            OrderItem.objects.create(
                order=order,
                product_variation=variation,
                quantity=quantity,
                price=item_price,
                total_price=item_total
            )
            
            # Зменшуємо кількість товару на складі
            variation.quantity -= quantity
            variation.save()
        
        # Оновлюємо загальну суму замовлення
        order.total_price = total_sum
        order.save()
        
        # Очищаємо дані замовлення з сесії
        if 'order_items' in request.session:
            del request.session['order_items']
        if 'order_comment' in request.session:
            del request.session['order_comment']
        
        messages.success(request, f'Замовлення №{order.id} успішно створено!')
        return redirect('order_detail', pk=order.id)
        
    except json.JSONDecodeError:
        messages.error(request, 'Помилка при обробці даних замовлення.')
        return redirect('order_create')
    except Exception as e:
        messages.error(request, f'Помилка при створенні замовлення: {str(e)}')
        return redirect('order_create') 
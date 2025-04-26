from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.urls import reverse
from ..models import Culture, Order, OrderItem, Product, ProductVariation
from ..forms import OrderForm, OrderItemFormSet, AddToCartForm, CartItemForm, CheckoutForm, ProductVariationFilterForm
import json
from django.db.models import Q

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
    """View to display details of a specific order."""
    order = get_object_or_404(Order, pk=pk)
    
    # Ensure users can only view their own orders (except for staff)
    if not request.user.is_staff and order.user != request.user:
        messages.error(request, 'У вас немає доступу до цього замовлення.')
        return redirect('order_list')
    
    context = {
        'order': order,
    }
    
    return render(request, 'warehouse/order/order_detail.html', context)

@login_required
def order_create(request):
    """View to create a new order directly."""
    if request.method == 'POST':
        # Перевіряємо, чи є дані про товари
        items_json = request.POST.get('items_json', '')
        if items_json:
            try:
                selected_items = json.loads(items_json)
                
                # Перевіряємо наявність товарів перед створенням замовлення
                for item in selected_items:
                    variation = get_object_or_404(ProductVariation, id=item['id'])
                    quantity = int(item['quantity'])
                    
                    # Перевіряємо наявність товару
                    if quantity > variation.quantity:
                        messages.error(request, f'Недостатня кількість товару "{variation.name}". Доступно: {variation.quantity}.')
                        return redirect('order_create')
                
                # Зберігаємо дані в сесії для використання при підтвердженні
                request.session['order_items'] = items_json
                request.session['order_comment'] = request.POST.get('comment', '')
                
                # Перенаправляємо на сторінку підтвердження
                return redirect('order_confirm')
                
            except json.JSONDecodeError:
                messages.error(request, 'Помилка при обробці даних замовлення.')
        else:
            messages.error(request, 'Не вибрано жодного товару.')
    
    if request.method == 'GET':
        filter_form = ProductVariationFilterForm(request.GET)
        if filter_form.is_valid():
            filter_kwargs = {}
            if filter_form.cleaned_data['culture']:
                filter_kwargs['parent_product__culture'] = filter_form.cleaned_data['culture']
            if filter_form.cleaned_data['real_name']:
                filter_kwargs['real_name__icontains'] = filter_form.cleaned_data['real_name']
            if filter_form.cleaned_data['name']:
                filter_kwargs['import_name__icontains'] = filter_form.cleaned_data['name']
            if filter_form.cleaned_data['lot_number']:
                filter_kwargs['lot_number__icontains'] = filter_form.cleaned_data['lot_number']
            if filter_form.cleaned_data['measurement_unit']:
                filter_kwargs['measurement_unit'] = filter_form.cleaned_data['measurement_unit']
            if filter_form.cleaned_data['package_type']:
                filter_kwargs['package_type'] = filter_form.cleaned_data['package_type']

            variations = ProductVariation.objects.filter(**filter_kwargs)
    else:
        variations = ProductVariation.objects.filter(quantity__gt=0)
    cultures = Culture.objects.all()
    context = {
        'variations': variations,
        'filter_form': filter_form,
        'cultures': cultures,
    }
    
    return render(request, 'warehouse/order/order_form.html', context)

@login_required
def order_confirm(request):
    """View to confirm an order."""
    if request.method == 'POST':
        # Отримуємо дані про вибрані товари
        items_json = request.POST.get('items_json', '[]')
        try:
            selected_items = json.loads(items_json)
            
            # Перевіряємо, чи є вибрані товари
            if not selected_items:
                messages.error(request, 'Не вибрано жодного товару.')
                return redirect('order_create')
            
            # Отримуємо інформацію про кожен товар
            order_items = []
            total_sum = 0
            
            for item in selected_items:
                variation = get_object_or_404(ProductVariation, id=item['id'])
                quantity = int(item['quantity'])
                
                # Перевіряємо наявність товару
                if quantity > variation.quantity:
                    messages.error(request, f'Недостатня кількість товару "{variation.name}". Доступно: {variation.quantity}.')
                    return redirect('order_create')
                
                item_total = quantity * variation.price
                total_sum += item_total
                
                order_items.append({
                    'variation': variation,
                    'quantity': quantity,
                    'item_total': item_total,
                })
            
            context = {
                'order_items': order_items,
                'total_sum': total_sum,
                'items_json': items_json,
                'comment': request.POST.get('comment', ''),
            }
            
            return render(request, 'warehouse/order/order_confirm.html', context)
            
        except json.JSONDecodeError:
            messages.error(request, 'Помилка при обробці даних замовлення.')
            return redirect('order_create')
    
    # Якщо запит GET, показуємо сторінку підтвердження з даними з сесії
    items_json = request.session.get('order_items', '[]')
    try:
        selected_items = json.loads(items_json)
        
        # Перевіряємо, чи є вибрані товари
        if not selected_items:
            messages.error(request, 'Не вибрано жодного товару.')
            return redirect('order_create')
        
        # Отримуємо інформацію про кожен товар
        order_items = []
        total_sum = 0
        
        for item in selected_items:
            variation = get_object_or_404(ProductVariation, id=item['id'])
            quantity = int(item['quantity'])
            
            item_total = quantity * variation.price
            total_sum += item_total
            
            order_items.append({
                'variation': variation,
                'quantity': quantity,
                'item_total': item_total,
            })
        
        context = {
            'order_items': order_items,
            'total_sum': total_sum,
            'items_json': items_json,
            'comment': request.session.get('order_comment', ''),
        }
        
        return render(request, 'warehouse/order/order_confirm.html', context)
        
    except json.JSONDecodeError:
        messages.error(request, 'Помилка при обробці даних замовлення.')
        return redirect('order_create')

@login_required
def order_cancel(request, pk):
    """View to cancel an order."""
    order = get_object_or_404(Order, pk=pk)
    
    # Ensure users can only cancel their own orders (except for staff)
    if not request.user.is_staff and order.user != request.user:
        messages.error(request, 'У вас немає доступу для скасування цього замовлення.')
        return redirect('order_list')
    
    if request.method == 'POST':
        order.status = 'canceled'
        for item in order.items.all():
            item.product.quantity += item.quantity
            item.product.save()
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
            user=request.user,
            status='successful',  # Статус "очікує обробки"
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
            # Перевіряємо структуру моделі OrderItem і використовуємо правильні назви полів
            OrderItem.objects.create(
                order=order,
                product=variation,  # Змінено з product на product_variation
                quantity=quantity,
                price=item_price,
                total_price=item_total  # Змінено з total на total_price
            )
            
            # Зменшуємо кількість товару на складі
            variation.quantity -= quantity
            variation.save()
        
        # Оновлюємо загальну суму замовлення
        order.total_price = total_sum  # Змінено з total_amount на total_price
        order.save()
        
        # Очищаємо дані замовлення з сесії
        if 'order_items' in request.session:
            del request.session['order_items']
        if 'order_comment' in request.session:
            del request.session['order_comment']
        
        messages.success(request, f'Замовлення №{order.id} успішно створено!')
        return redirect('order_detail', pk=order.id)  # Змінено з order_id на pk
        
    except json.JSONDecodeError:
        print(False)
        messages.error(request, 'Помилка при обробці даних замовлення.')
        return redirect('order_create')
    except Exception as e:
        messages.error(request, f'Помилка при створенні замовлення: {str(e)}')
        return redirect('order_create') 
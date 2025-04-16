from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.urls import reverse
from ..models import Order, OrderItem, Product
from ..forms import OrderForm, OrderItemFormSet, AddToCartForm, CartItemForm, CheckoutForm

@login_required
def order_list(request):
    """View to display the list of orders."""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    # Filter by status if provided
    status = request.GET.get('status', '')
    if status:
        orders = orders.filter(status=status)
    
    # Paginate results
    paginator = Paginator(orders, 10)  # Show 10 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate total items for the current page
    total_items = 0
    for order in page_obj:
        for item in order.items.all():
            total_items += item.quantity
    
    context = {
        'page_obj': page_obj,
        'current_status': status,
        'total_items': total_items,
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
    """View to create a new order directly (admin functionality)."""
    if request.method == 'POST':
        form = OrderForm(request.POST)
        formset = OrderItemFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()
            
            formset.instance = order
            items = formset.save()
            
            # Calculate total price
            total_price = sum(item.price * item.quantity for item in items)
            order.total_price = total_price
            order.save()
            
            messages.success(request, f'Замовлення #{order.id} успішно створено.')
            return redirect('order_detail', pk=order.pk)
    else:
        form = OrderForm()
        formset = OrderItemFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'title': 'Створити нове замовлення',
    }
    
    return render(request, 'warehouse/order/order_form.html', context)

@login_required
def order_update(request, pk):
    """View to update an existing order."""
    order = get_object_or_404(Order, pk=pk)
    
    # Ensure users can only update their own orders (except for staff)
    if not request.user.is_staff and order.user != request.user:
        messages.error(request, 'У вас немає доступу для редагування цього замовлення.')
        return redirect('order_list')
    
    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        formset = OrderItemFormSet(request.POST, instance=order)
        
        if form.is_valid() and formset.is_valid():
            order = form.save()
            items = formset.save()
            
            # Recalculate total price
            total_price = sum(item.price * item.quantity for item in order.items.all())
            order.total_price = total_price
            order.save()
            
            messages.success(request, f'Замовлення #{order.id} успішно оновлено.')
            return redirect('order_detail', pk=order.pk)
    else:
        form = OrderForm(instance=order)
        formset = OrderItemFormSet(instance=order)
    
    context = {
        'form': form,
        'formset': formset,
        'order': order,
        'title': f'Редагувати замовлення #{order.id}',
    }
    
    return render(request, 'warehouse/order/order_form.html', context)

@login_required
def order_cancel(request, pk):
    """View to cancel an order."""
    order = get_object_or_404(Order, pk=pk)
    
    # Ensure users can only cancel their own orders (except for staff)
    if not request.user.is_staff and order.user != request.user:
        messages.error(request, 'У вас немає доступу для скасування цього замовлення.')
        return redirect('order_list')
    
    # Only allow cancelling pending or processing orders
    if order.status not in ['pending', 'processing']:
        messages.error(request, 'Можна скасувати лише замовлення в обробці або ті, що обробляються.')
        return redirect('order_detail', pk=order.pk)
    
    if request.method == 'POST':
        order.status = 'canceled'
        order.save()
        messages.success(request, f'Замовлення #{order.id} успішно скасовано.')
        return redirect('order_list')
    
    context = {
        'order': order,
    }
    
    return render(request, 'warehouse/order/order_confirm_cancel.html', context)

@login_required
def add_to_cart(request, product_id):
    """View to add a product to the cart."""
    product = get_object_or_404(Product, pk=product_id)
    
    if request.method == 'POST':
        form = AddToCartForm(request.POST)
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            
            # Check if product is available
            if not product.is_available:
                messages.error(request, f'Товар "{product.name}" недоступний.')
                return redirect('product_detail', pk=product_id)
            
            # Check if quantity is available
            if quantity > product.quantity:
                messages.error(
                    request, 
                    f'Недостатня кількість товару. Доступно: {product.quantity} {product.measurement_unit}.'
                )
                return redirect('product_detail', pk=product_id)
            
            # Get or create cart in session
            cart = request.session.get('cart', {})
            
            # Add/update product in cart
            product_key = str(product_id)
            if product_key in cart:
                cart[product_key]['quantity'] += quantity
            else:
                cart[product_key] = {
                    'quantity': quantity,
                    'name': product.name,
                    'price': float(product.price),
                }
            
            request.session['cart'] = cart
            messages.success(request, f'Товар "{product.name}" додано до кошика.')
            
            # Redirect to cart or continue shopping
            if request.POST.get('checkout', ''):
                return redirect('view_cart')
            else:
                return redirect('product_list')
    else:
        form = AddToCartForm(initial={'product_id': product_id})
    
    context = {
        'product': product,
        'form': form,
    }
    
    return render(request, 'warehouse/order/add_to_cart.html', context)

@login_required
def view_cart(request):
    """View to display the cart contents."""
    cart = request.session.get('cart', {})
    cart_items = []
    total_price = 0
    
    # Process cart items
    for product_id, item_data in cart.items():
        try:
            product = Product.objects.get(pk=int(product_id))
            quantity = item_data['quantity']
            price = float(item_data['price'])
            item_total = quantity * price
            
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'price': price,
                'total': item_total,
            })
            
            total_price += item_total
        except Product.DoesNotExist:
            # Remove non-existent products from cart
            cart.pop(product_id, None)
            request.session['cart'] = cart
    
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }
    
    return render(request, 'warehouse/order/cart.html', context)

@login_required
def update_cart(request):
    """View to update cart contents."""
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        action = request.POST.get('action')
        
        # Process each cart item
        for key in cart.keys():
            quantity_key = f'quantity_{key}'
            if quantity_key in request.POST:
                try:
                    new_quantity = int(request.POST[quantity_key])
                    if new_quantity > 0:
                        cart[key]['quantity'] = new_quantity
                    else:
                        # Remove item if quantity is 0
                        cart.pop(key, None)
                except (ValueError, TypeError):
                    pass
        
        request.session['cart'] = cart
        
        if action == 'checkout':
            return redirect('checkout')
        else:
            messages.success(request, 'Кошик успішно оновлено.')
            return redirect('view_cart')
    
    return redirect('view_cart')

@login_required
def clear_cart(request):
    """View to clear the cart."""
    if 'cart' in request.session:
        del request.session['cart']
        messages.success(request, 'Кошик успішно очищено.')
    
    return redirect('view_cart')

@login_required
def checkout(request):
    """View to process the checkout."""
    cart = request.session.get('cart', {})
    
    if not cart:
        messages.error(request, 'Ваш кошик порожній.')
        return redirect('product_list')
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Create new order
            order = Order(
                user=request.user,
                status='pending',
                comment=form.cleaned_data.get('comment', ''),
                total_price=0,
            )
            order.save()
            
            total_price = 0
            
            # Create order items from cart
            for product_id, item_data in cart.items():
                try:
                    product = Product.objects.get(pk=int(product_id))
                    quantity = item_data['quantity']
                    price = product.price
                    
                    # Check if quantity is available
                    if quantity > product.quantity:
                        messages.error(
                            request, 
                            f'Недостатня кількість товару "{product.name}". Доступно: {product.quantity}.'
                        )
                        order.delete()  # Rollback order creation
                        return redirect('view_cart')
                    
                    # Create order item
                    order_item = OrderItem(
                        order=order,
                        product=product,
                        quantity=quantity,
                        price=price,
                        total_price=price * quantity,
                    )
                    order_item.save()
                    
                    # Update product quantity
                    product.quantity -= quantity
                    product.save()
                    
                    total_price += price * quantity
                    
                except Product.DoesNotExist:
                    # Skip non-existent products
                    continue
            
            # Update order total price
            order.total_price = total_price
            order.save()
            
            # Clear cart after successful checkout
            del request.session['cart']
            
            messages.success(request, f'Замовлення #{order.id} успішно створено.')
            return redirect('order_detail', pk=order.pk)
    else:
        form = CheckoutForm()
    
    # Calculate cart totals
    cart_items = []
    total_price = 0
    
    for product_id, item_data in cart.items():
        try:
            product = Product.objects.get(pk=int(product_id))
            quantity = item_data['quantity']
            price = float(product.price)
            item_total = quantity * price
            
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'price': price,
                'total': item_total,
            })
            
            total_price += item_total
        except Product.DoesNotExist:
            # Remove non-existent products from cart
            cart.pop(product_id, None)
            request.session['cart'] = cart
    
    context = {
        'form': form,
        'cart_items': cart_items,
        'total_price': total_price,
    }
    
    return render(request, 'warehouse/order/checkout.html', context) 
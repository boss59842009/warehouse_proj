from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from ..models import ProductMovement, Product
from ..forms import ProductMovementForm

@login_required
def movement_list(request):
    """View to display a list of all product movements."""
    movements = ProductMovement.objects.all().order_by('-date')
    
    # Filter by movement type if provided
    movement_type = request.GET.get('type', '')
    if movement_type:
        movements = movements.filter(movement_type=movement_type)
    
    # Filter by product if provided
    product_id = request.GET.get('product', '')
    if product_id:
        try:
            product = Product.objects.get(pk=int(product_id))
            movements = movements.filter(product=product)
        except (Product.DoesNotExist, ValueError):
            pass
    
    # Search by document number or comment
    search = request.GET.get('search', '')
    if search:
        movements = movements.filter(
            Q(document_number__icontains=search) | 
            Q(comment__icontains=search) |
            Q(product__name__icontains=search)
        )
    
    # Paginate results
    paginator = Paginator(movements, 20)  # Show 20 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all products for filter dropdown
    products = Product.objects.all().order_by('name')
    
    context = {
        'page_obj': page_obj,
        'products': products,
        'movement_types': dict(ProductMovement.MOVEMENT_TYPES),
        'current_type': movement_type,
        'current_product': product_id,
        'search': search,
    }
    
    return render(request, 'warehouse/movement/movement_list.html', context)

@login_required
def movement_detail(request, pk):
    """View to display details of a specific product movement."""
    movement = get_object_or_404(ProductMovement, pk=pk)
    
    context = {
        'movement': movement,
    }
    
    return render(request, 'warehouse/movement/movement_detail.html', context)

@login_required
def movement_create(request):
    """View to create a new product movement."""
    if request.method == 'POST':
        form = ProductMovementForm(request.POST)
        
        if form.is_valid():
            movement = form.save(commit=False)
            movement.performed_by = request.user
            
            # Update product quantity based on movement type
            product = movement.product
            quantity = movement.quantity
            
            if movement.movement_type == 'incoming':
                product.quantity += quantity
                product.save()
                messages.success(request, f'Додано {quantity} одиниць товару "{product.name}".')
            
            elif movement.movement_type == 'outgoing':
                if product.quantity >= quantity:
                    product.quantity -= quantity
                    product.save()
                    messages.success(request, f'Видано {quantity} одиниць товару "{product.name}".')
                else:
                    messages.error(
                        request, 
                        f'Недостатня кількість товару. Доступно: {product.quantity} одиниць.'
                    )
                    return render(request, 'warehouse/movement/movement_form.html', {'form': form})
            
            elif movement.movement_type == 'return':
                product.quantity += quantity
                product.save()
                messages.success(request, f'Повернуто {quantity} одиниць товару "{product.name}".')
            
            elif movement.movement_type == 'write_off':
                if product.quantity >= quantity:
                    product.quantity -= quantity
                    product.save()
                    messages.success(request, f'Списано {quantity} одиниць товару "{product.name}".')
                else:
                    messages.error(
                        request, 
                        f'Недостатня кількість товару. Доступно: {product.quantity} одиниць.'
                    )
                    return render(request, 'warehouse/movement/movement_form.html', {'form': form})
            
            movement.save()
            return redirect('movement_detail', pk=movement.pk)
    else:
        # Pre-select product if provided in URL
        product_id = request.GET.get('product', '')
        initial = {}
        
        if product_id:
            try:
                product = Product.objects.get(pk=int(product_id))
                initial = {'product': product}
            except (Product.DoesNotExist, ValueError):
                pass
                
        form = ProductMovementForm(initial=initial)
    
    context = {
        'form': form,
        'title': 'Створити новий рух товару',
    }
    
    return render(request, 'warehouse/movement/movement_form.html', context)

@login_required
def incoming_movement(request):
    """View to create a new incoming product movement."""
    if request.method == 'POST':
        form = ProductMovementForm(request.POST)
        
        if form.is_valid():
            movement = form.save(commit=False)
            movement.movement_type = 'incoming'
            movement.performed_by = request.user
            
            # Update product quantity
            product = movement.product
            quantity = movement.quantity
            product.quantity += quantity
            product.save()
            
            movement.save()
            messages.success(request, f'Додано {quantity} одиниць товару "{product.name}".')
            return redirect('movement_detail', pk=movement.pk)
    else:
        form = ProductMovementForm(initial={'movement_type': 'incoming'})
    
    context = {
        'form': form,
        'title': 'Створити прибуткову накладну',
    }
    
    return render(request, 'warehouse/movement/movement_form.html', context)

@login_required
def outgoing_movement(request):
    """View to create a new outgoing product movement."""
    if request.method == 'POST':
        form = ProductMovementForm(request.POST)
        
        if form.is_valid():
            movement = form.save(commit=False)
            movement.movement_type = 'outgoing'
            movement.performed_by = request.user
            
            # Check and update product quantity
            product = movement.product
            quantity = movement.quantity
            
            if product.quantity >= quantity:
                product.quantity -= quantity
                product.save()
                
                movement.save()
                messages.success(request, f'Видано {quantity} одиниць товару "{product.name}".')
                return redirect('movement_detail', pk=movement.pk)
            else:
                messages.error(
                    request, 
                    f'Недостатня кількість товару. Доступно: {product.quantity} одиниць.'
                )
    else:
        form = ProductMovementForm(initial={'movement_type': 'outgoing'})
    
    context = {
        'form': form,
        'title': 'Створити видаткову накладну',
    }
    
    return render(request, 'warehouse/movement/movement_form.html', context)

@login_required
def product_movements(request, product_id):
    """View to display all movements for a specific product."""
    product = get_object_or_404(Product, pk=product_id)
    movements = ProductMovement.objects.filter(product=product).order_by('-date')
    
    # Paginate results
    paginator = Paginator(movements, 20)  # Show 20 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'product': product,
        'page_obj': page_obj,
    }
    
    return render(request, 'warehouse/movement/product_movements.html', context) 
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from ..models import ProductIncome, Product, Culture, ProductVariation
from ..forms import InventoryForm, ProductFilterForm, ProductIncomeItemForm, ProductIncomeItemFormSet, ProductIncomeForm, ProductIncomeFilterForm

@login_required
def movement_list(request):
    """View to display a list of all product movements."""
    movements = ProductIncome.objects.all().order_by('-created_at')
    movement_filter_form = ProductIncomeFilterForm()
    # if request.method == 'GET':
    #     movement_filter_form = ProductIncomeFilterForm(request.GET)
    #     if movement_filter_form.is_valid():
    #         movements = movements.filter(
    #             Q(culture__name__icontains=movement_filter_form.cleaned_data['culture']) |
    #             Q(real_name__icontains=movement_filter_form.cleaned_data['real_name']) |
    #             Q(name__icontains=movement_filter_form.cleaned_data['name']) |
    #             Q(lot_number__icontains=movement_filter_form.cleaned_data['lot_number']) |
    #             Q(measurement_unit__name__icontains=movement_filter_form.cleaned_data['measurement_unit']) |
    #             Q(package_type__name__icontains=movement_filter_form.cleaned_data['package_type'])
    #         )

    
     # Filter by status if provided
    movement_type = request.GET.get('movement_type', '')
    if movement_type:
        movements = movements.filter(movement_type=movement_type)

    created_at_from = request.GET.get('created_at_from', '')
    if created_at_from:
        movements = movements.filter(created_at__gte=created_at_from)
    # # Filter by product if provided
    # product_id = request.GET.get('product', '')
    # if product_id:
    #     try:
    #         product = Product.objects.get(pk=int(product_id))
    #         movements = movements.filter(product=product)
    #     except (Product.DoesNotExist, ValueError):
    #         pass
    
    # # Search by document number or comment
    # search = request.GET.get('search', '')
    # if search:
    #     movements = movements.filter(
    #         Q(document_number__icontains=search) | 
    #         Q(comment__icontains=search) |
    #         Q(product__name__icontains=search)
    #     )
    
    # Paginate results
    paginator = Paginator(movements, 20)  # Show 20 items per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all products for filter dropdown
    products = Product.objects.all().order_by('name')
    
    context = {
        'page_obj': page_obj,
        'products': products,
        'movement_filter_form': movement_filter_form,
    }
    
    return render(request, 'warehouse/movement/movement_list.html', context)

@login_required
def product_income_create(request):
    products = Product.objects.all().prefetch_related('variations', 'productimage_set')
    cultures = Culture.objects.all().order_by('name')
    
    # Створюємо формсет
    formset = ProductIncomeItemFormSet(request.POST or None)
    
    # Додаємо атрибути data- до опцій select для product_variation
    for form in formset:
        product_variation_field = form.fields['product_variation']
        for i, choice in enumerate(product_variation_field.widget.choices):
            if choice[0]:  # Пропускаємо порожній варіант
                try:
                    product_variation = ProductVariation.objects.select_related('culture').get(pk=choice[0])
                    # Додаємо атрибути data- до опції
                    attrs = {
                        'data-culture': product_variation.culture.name if product_variation.culture else '',
                        'data-real-name': product_variation.real_name or '',
                        'data-name': product_variation.name or ''
                    }
                    product_variation_field.widget.choices[i] = (
                        choice[0],
                        choice[1],
                        attrs
                    )
                except ProductVariation.DoesNotExist:
                    pass
    
    if request.method == 'POST':
        if formset.is_valid():
            # Зберігаємо основну форму
            income = ProductIncome.objects.create(
                movement_type = 'incoming',
                performed_by = request.user
            )
            
            # Перевіряємо, що всі елементи мають product_variation
            valid_items = []
            for form in formset:
                print(form.cleaned_data)
                if form.is_valid() and not form.cleaned_data.get('DELETE'):
                    if form.cleaned_data.get('product_variation'):
                        valid_items.append(form)
            
            # Зберігаємо тільки валідні елементи
            for form in valid_items:
                item = form.save(commit=False)
                item.income = income
                item.save()
            
            # Оновлюємо загальну кількість та кількість упаковок
            income.total_quantity = sum(item.quantity for item in income.productincomeitem_set.all())
            income.total_packages_count = sum(item.packages_count for item in income.productincomeitem_set.all())
            income.save()
            
            return redirect('movement_list')
    
    context = {
        'formset': formset,
        'products': products,
        'cultures': cultures,
    }
    
    return render(request, 'warehouse/movement/income_create_form.html', context)
# @login_required
# def inventory_create(request):
#     """View to create a new inventory."""
#     if request.method == 'POST':
#         form = InventoryForm(request.POST)  
        
#         if form.is_valid():
#             form.save()
#             messages.success(request, 'Інвентаризація товару створена успішно.')
#             return redirect('movement_list')
#     else:
#         form = InventoryForm()  
#     context = {
#         'form': form,
#         'title': 'Створити інвентаризацію товару',
#     }

#     return render(request, 'warehouse/movement/inventory_form.html', context)


# # @login_required
# # def movement_detail(request, pk):
# #     """View to display details of a specific product movement."""
# #     movement = get_object_or_404(ProductIncome, pk=pk)
    
# #     context = {
# #         'movement': movement,
# #     }
    
# #     return render(request, 'warehouse/movement/movement_detail.html', context)

# @login_required
# def movement_create(request):
#     """View to create a new product movement."""
#     if request.method == 'POST':
#         form = ProductIncomeItemForm(request.POST)
        
#         if form.is_valid():
#             movement = form.save(commit=False)
#             movement.performed_by = request.user
            
#             # Update product quantity based on movement type
#             product = movement.product
#             quantity = movement.quantity
            
#             if movement.movement_type == 'incoming':
#                 product.quantity += quantity
#                 product.save()
#                 messages.success(request, f'Додано {quantity} одиниць товару "{product.name}".')
            
#             elif movement.movement_type == 'outgoing':
#                 if product.quantity >= quantity:
#                     product.quantity -= quantity
#                     product.save()
#                     messages.success(request, f'Видано {quantity} одиниць товару "{product.name}".')
#                 else:
#                     messages.error(
#                         request, 
#                         f'Недостатня кількість товару. Доступно: {product.quantity} одиниць.'
#                     )
#                     return render(request, 'warehouse/movement/movement_form.html', {'form': form})
            
#             elif movement.movement_type == 'return':
#                 product.quantity += quantity
#                 product.save()
#                 messages.success(request, f'Повернуто {quantity} одиниць товару "{product.name}".')
            
#             elif movement.movement_type == 'write_off':
#                 if product.quantity >= quantity:
#                     product.quantity -= quantity
#                     product.save()
#                     messages.success(request, f'Списано {quantity} одиниць товару "{product.name}".')
#                 else:
#                     messages.error(
#                         request, 
#                         f'Недостатня кількість товару. Доступно: {product.quantity} одиниць.'
#                     )
#                     return render(request, 'warehouse/movement/movement_form.html', {'form': form})
            
#             movement.save()
#             return redirect('movement_detail', pk=movement.pk)
#     else:
#         # Pre-select product if provided in URL
#         product_id = request.GET.get('product', '')
#         initial = {}
        
#         if product_id:
#             try:
#                 product = Product.objects.get(pk=int(product_id))
#                 initial = {'product': product}
#             except (Product.DoesNotExist, ValueError):
#                 pass
                
#         form = ProductIncomeItemForm(initial=initial)
    
#     context = {
#         'form': form,
#         'title': 'Створити новий рух товару',
#     }
    
#     return render(request, 'warehouse/movement/movement_form.html', context)

# @login_required
# def incoming_movement(request):
#     """View to create a new incoming product movement."""
#     if request.method == 'POST':
#         form = ProductIncomeForm(request.POST)
        
#         if form.is_valid():
#             movement = form.save(commit=False)
#             movement.movement_type = 'incoming'
#             movement.performed_by = request.user
            
#             # Update product quantity
#             product = movement.product
#             quantity = movement.quantity
#             product.quantity += quantity
#             product.save()
            
#             movement.save()
#             messages.success(request, f'Додано {quantity} одиниць товару "{product.name}".')
#             return redirect('movement_detail', pk=movement.pk)
#     else:
#         form = ProductIncomeForm(initial={'movement_type': 'incoming'})
    
#     context = {
#         'form': form,
#         'title': 'Створити прибуткову накладну',
#     }
    
#     return render(request, 'warehouse/movement/movement_form.html', context)

# @login_required
# def outgoing_movement(request):
#     """View to create a new outgoing product movement."""
#     if request.method == 'POST':
#         form = ProductIncomeForm(request.POST)
        
#         if form.is_valid():
#             movement = form.save(commit=False)
#             movement.movement_type = 'outgoing'
#             movement.performed_by = request.user
            
#             # Check and update product quantity
#             product = movement.product
#             quantity = movement.quantity
            
#             if product.quantity >= quantity:
#                 product.quantity -= quantity
#                 product.save()
                
#                 movement.save()
#                 messages.success(request, f'Видано {quantity} одиниць товару "{product.name}".')
#                 return redirect('movement_detail', pk=movement.pk)
#             else:
#                 messages.error(
#                     request, 
#                     f'Недостатня кількість товару. Доступно: {product.quantity} одиниць.'
#                 )
#     else:
#         form = ProductIncomeForm(initial={'movement_type': 'outgoing'})
    
#     context = {
#         'form': form,
#         'title': 'Створити видаткову накладну',
#     }
    
#     return render(request, 'warehouse/movement/movement_form.html', context)

# @login_required
# def product_movements(request, product_id):
#     """View to display all movements for a specific product."""
#     product = get_object_or_404(Product, pk=product_id)
#     movements = ProductIncome.objects.filter(product=product).order_by('-date')
    
#     # Paginate results
#     paginator = Paginator(movements, 20)  # Show 20 items per page
#     page_number = request.GET.get('page')
#     page_obj = paginator.get_page(page_number)
    
#     context = {
#         'product': product,
#         'page_obj': page_obj,
#     }
    
#     return render(request, 'warehouse/movement/product_movements.html', context) 
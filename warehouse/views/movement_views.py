from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from ..models import ProductIncome, Product, Culture, ProductVariation, Inventory
from ..forms import InventoryForm, ProductFilterForm, ProductIncomeItemForm, ProductIncomeItemFormSet, ProductIncomeForm, ProductIncomeFilterForm
from itertools import chain
from django.db.models import Value, CharField

@login_required
def movement_list(request):
    """View to display a list of all product movements."""
    # Додаємо поле для ідентифікації типу моделі
    product_income_movements = ProductIncome.objects.all().annotate(
        model_type=Value('product_income', output_field=CharField())
    )
    inventory_movements = Inventory.objects.all().annotate(
        model_type=Value('inventory', output_field=CharField())
    )
    
    movement_filter_form = ProductIncomeFilterForm()
    
    # Фільтрація
    movement_type = request.GET.get('movement_type', '')
    if movement_type:
        product_income_movements = product_income_movements.filter(movement_type=movement_type)
        inventory_movements = inventory_movements.filter(movement_type=movement_type)

    created_at_from = request.GET.get('created_at_from', '')
    if created_at_from:
        product_income_movements = product_income_movements.filter(created_at__gte=created_at_from)
        inventory_movements = inventory_movements.filter(created_at__gte=created_at_from)
    
    # Об'єднуємо queryset за допомогою chain
    all_movements = list(chain(product_income_movements, inventory_movements))
    # Сортуємо об'єднаний список
    all_movements.sort(key=lambda x: x.created_at, reverse=True)
    
    # Пагінація
    paginator = Paginator(all_movements, 20)
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
                    # Convert the ModelChoiceIteratorValue to int - make sure we get the id value properly
                    choice_id = int(str(choice[0]))
                    product_variation = ProductVariation.objects.select_related('parent_product', 'parent_product__culture', 'package_type', 'measurement_unit').get(pk=choice_id)
                    # Додаємо атрибути data- до опції
                    attrs = {
                        'data-culture': product_variation.parent_product.culture.name if product_variation.parent_product and product_variation.parent_product.culture else '',
                        'data-real-name': product_variation.real_name or (product_variation.parent_product.real_name if product_variation.parent_product else ''),
                        'data-name': product_variation.name or '',
                        'data-lot-number': product_variation.lot_number or '',
                        'data-package-type': product_variation.package_type.id if product_variation.package_type else '',
                        'data-measurement-unit': product_variation.measurement_unit.id if product_variation.measurement_unit else '',
                    }
                    product_variation_field.widget.choices[i] = (
                        choice[0],
                        choice[1],
                        attrs
                    )
                except (ProductVariation.DoesNotExist, ValueError, TypeError, AttributeError) as e:
                    print(f"Error setting up choice attributes: {e}")
                    pass
    
    if request.method == 'POST':
        print("POST data:", request.POST)
        print("POST data keys:", request.POST.keys())
        
        # Check if product_variation fields are present
        product_variation_fields = [key for key in request.POST.keys() if 'product_variation' in key]
        print("Product variation fields:", product_variation_fields)
        print("Product variation values:", {key: request.POST.get(key) for key in product_variation_fields})
        
        formset = ProductIncomeItemFormSet(request.POST or None)
        print("Formset errors:", formset.errors)
        print("Formset non-form errors:", formset.non_form_errors())
        
        for i, form in enumerate(formset):
            print(f"Form {i} errors:", form.errors)
            
        if formset.is_valid():
            # Зберігаємо основну форму
            income = ProductIncome.objects.create(
                movement_type = 'incoming',
                performed_by = request.user
            )
            
            # Перевіряємо, що всі елементи мають product_variation
            valid_items = []
            for form in formset:
                print(f"Form cleaned data: {form.cleaned_data}")
                if form.is_valid() and not form.cleaned_data.get('DELETE'):
                    if form.cleaned_data.get('product_variation'):
                        valid_items.append(form)
            
            if not valid_items:
                messages.error(request, "Немає валідних товарів для додавання. Переконайтеся, що ви вибрали варіацію товару.")
                return redirect('product_income_create')
            
            # Зберігаємо тільки валідні елементи
            for form in valid_items:
                try:
                    item = form.save(commit=False)
                    item.product_income = income
                    
                    # Переконуємось, що product_variation існує
                    variation = form.cleaned_data.get('product_variation')
                    if variation:
                        # Перевіряємо чи потрібно оновити поля варіації з форми
                        if form.cleaned_data.get('lot_number') and not variation.lot_number:
                            variation.lot_number = form.cleaned_data.get('lot_number')
                        
                        if form.cleaned_data.get('package_type') and not variation.package_type:
                            variation.package_type = form.cleaned_data.get('package_type')
                            
                        if form.cleaned_data.get('measurement_unit') and not variation.measurement_unit:
                            variation.measurement_unit = form.cleaned_data.get('measurement_unit')
                        
                        # Зберігаємо варіацію з оновленими полями
                        variation.save()
                    
                    item.save()
                    print(f"Successfully saved item with product_variation: {item.product_variation_id}")
                except Exception as e:
                    print(f"Error saving form: {e}")
                    messages.error(request, f"Помилка збереження: {e}")
            
            # Оновлюємо загальну кількість та кількість упаковок
            income.total_quantity = sum(item.quantity for item in income.productincomeitem_set.all())
            income.total_packages_count = sum(item.packages_count for item in income.productincomeitem_set.all())
            income.save()
            
            messages.success(request, "Прибуткова накладна успішно створена.")
            return redirect('movement_list')
        else:
            print(f"Formset errors: {formset.errors}")
            for i, form in enumerate(formset):
                if form.errors:
                    print(f"Form {i} errors: {form.errors}")
            messages.error(request, "Будь ласка, перевірте правильність заповнення форми.")
    else:
        formset = ProductIncomeItemFormSet()
    
    context = {
        'formset': formset,
        'products': products,
        'cultures': cultures,
    }
    
    return render(request, 'warehouse/movement/income_create_form.html', context)


@login_required
def product_income_detail(request, pk):
    """View to display details of a specific product income."""
    product_income = get_object_or_404(ProductIncome, pk=pk)
    
    context = {
        'product_income': product_income,
    }
    
    return render(request, 'warehouse/movement/product_income_detail.html', context)

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
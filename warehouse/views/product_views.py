from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from ..models import Product, Culture, ProductImage, ProductVariation, PackageType, MeasurementUnit         
from ..forms import ProductForm, ProductImageFormSet, ProductVariationFormSet, ProductFilterForm

@login_required
def product_list(request):
    """View to display the list of products."""
    products = Product.objects.all().order_by('name')
    filter_form = ProductFilterForm(request.GET)
    
    # Apply filters if form is valid
    if filter_form.is_valid():
        culture = filter_form.cleaned_data.get('culture')
        available_only = filter_form.cleaned_data.get('available_only')
        search = filter_form.cleaned_data.get('search')
        
        if culture:
            products = products.filter(culture=culture)
        
        if available_only:
            products = products.filter(is_available=True)
        
        if search:
            products = products.filter(
                Q(name__icontains=search) | 
                Q(real_name__icontains=search) | 
                Q(import_name__icontains=search)
            )
    
    # Paginate results
    paginator = Paginator(products, 10)  # Show 10 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
    }
    
    return render(request, 'warehouse/product/product_list.html', context)

@login_required
def product_detail(request, pk):
    """View to display details of a specific product."""
    product = get_object_or_404(Product, pk=pk)
    
    # Get related products (same category)
    related_products = Product.objects.filter(
        culture=product.culture
    ).exclude(id=product.id)[:4]

    # Get all variations of the product
    variations = ProductVariation.objects.filter(parent_product=product).order_by('id')
    # Paginate results
    paginator = Paginator(variations, 10)  # Show 10 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'product': product,
        'related_products': related_products,
        'variations': page_obj,
    }    
    return render(request, 'warehouse/product/product_detail.html', context)

@login_required
def product_create(request):
    """View to create a new product."""
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        print(request.FILES)
        
        # Ініціалізуємо формсети з правильними префіксами
        formset = ProductImageFormSet(request.POST, request.FILES, prefix='images')
        variations_formset = ProductVariationFormSet(request.POST, prefix='variations')
        
        has_variations = request.POST.get('has_variations') == 'on'
        
        if form.is_valid() and formset.is_valid() and (not has_variations or variations_formset.is_valid()):
            # Зберігаємо товар
            product = form.save()
            
            # Зберігаємо зображення з формсету
            image_instances = formset.save(commit=False)
            for image in image_instances:
                image.product = product
                image.save()
            
            # Видаляємо позначені для видалення зображення
            for obj in formset.deleted_objects:
                obj.delete()
            
            # Обробка динамічно доданих зображень
            for key, value in request.FILES.items():
                if key.startswith('images-') and key.endswith('-image'):
                    # Перевіряємо, чи це зображення не входить у формсет
                    form_index = key.split('-')[1]
                    if not any(img.id for img in image_instances if f'images-{form_index}-' in key):
                        # Створюємо нове зображення
                        new_image = ProductImage(product=product, image=value)
                        new_image.save()
            
            # Зберігаємо варіації, якщо вони є
            if has_variations:
                variation_instances = variations_formset.save(commit=False)
                for variation in variation_instances:
                    variation.parent_product = product
                    variation.culture = product.culture
                    variation.save()
                
                # Видаляємо позначені для видалення варіації
                for obj in variations_formset.deleted_objects:
                    obj.delete()
            
            messages.success(request, f'Товар "{product.real_name}" успішно створено.')
            return redirect('product_detail', pk=product.pk)
        else:
            print(form.errors)
            print(formset.errors)
            print(variations_formset.errors)
    else:
        form = ProductForm()
        formset = ProductImageFormSet(prefix='images')
        variations_formset = ProductVariationFormSet(prefix='variations')
    
    # Отримуємо всі типи упаковок
    package_types = PackageType.objects.all()
    measurement_units = MeasurementUnit.objects.all()

    # Передаємо queryset для поля package_type у порожній формі
    variations_formset.empty_form.fields['package_type'].queryset = package_types
    variations_formset.empty_form.fields['measurement_unit'].queryset = measurement_units
    # Також для всіх форм у формсеті
    for form in variations_formset.forms:
        form.fields['package_type'].queryset = package_types
        form.fields['measurement_unit'].queryset = measurement_units

    context = {
        'form': form,
        'formset': formset,
        'variations_formset': variations_formset,
        'package_types': package_types,
        'measurement_units': measurement_units,
        'title': 'Створення нового товару',
    }
    
    return render(request, 'warehouse/product/product_form.html', context)

@login_required
def product_update(request, pk):
    """View to update an existing product."""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        print(request.FILES)
        # Ініціалізуємо формсети з правильними префіксами
        formset = ProductImageFormSet(request.POST, request.FILES, instance=product, prefix='images')
        variations_formset = ProductVariationFormSet(request.POST, instance=product, prefix='variations')

        
        has_variations = request.POST.get('has_variations') == 'on'
        
        if form.is_valid() and formset.is_valid() and (not has_variations or variations_formset.is_valid()):
            # Зберігаємо товар
            product = form.save()
            
            # Явно видаляємо зображення, позначені для видалення
            for form_item in formset:
                if form_item.cleaned_data and form_item.cleaned_data.get('DELETE', False):
                    if form_item.instance and form_item.instance.pk:
                        print(f"Видаляємо зображення з ID: {form_item.instance.pk}")
                        form_item.instance.image.delete(save=False)  # Видаляємо файл
                        form_item.instance.delete()  # Видаляємо запис з БД
            
            # Зберігаємо зображення з формсету
            image_instances = formset.save(commit=False)
            for image in image_instances:
                image.product = product
                image.save()
            
            # Обробка динамічно доданих зображень
            for key, value in request.FILES.items():
                if key.startswith('images-') and key.endswith('-image'):
                    # Перевіряємо, чи це зображення не входить у формсет
                    form_index = key.split('-')[1]
                    if not any(img.id for img in image_instances if f'images-{form_index}-' in key):
                        # Створюємо нове зображення
                        new_image = ProductImage(product=product, image=value)
                        new_image.save()
            
            # Зберігаємо варіації, якщо вони є
            if has_variations:
                # Перевіряємо, які варіації позначені для видалення
                for form_item in variations_formset:
                    if form_item.cleaned_data and form_item.cleaned_data.get('DELETE', False):
                        if form_item.instance and form_item.instance.pk:
                            form_item.instance.delete()
                
                variation_instances = variations_formset.save(commit=False)
                print(variation_instances)
                for variation in variation_instances:
                    variation.parent_product = product
                    variation.culture = product.culture
                    print(variation.culture)
                    variation.save()
            else:
                # Якщо варіації не використовуються, видаляємо всі існуючі
                ProductVariation.objects.filter(parent_product=product).delete()
            
            messages.success(request, f'Товар "{product.real_name}" успішно оновлено.')
            return redirect('product_detail', pk=product.pk)
        else:
            print(form.errors)
            print(formset.errors)
            print(variations_formset.errors)
    else:
        form = ProductForm(instance=product)
        formset = ProductImageFormSet(instance=product, prefix='images')
        variations_formset = ProductVariationFormSet(instance=product, prefix='variations')
        # Встановлюємо чекбокс, якщо є варіації
        has_variations = ProductVariation.objects.filter(parent_product=product).exists()
    
    # Отримуємо всі типи упаковок
    package_types = PackageType.objects.all()
    measurement_units = MeasurementUnit.objects.all()

    # Передаємо queryset для поля package_type у порожній формі
    variations_formset.empty_form.fields['package_type'].queryset = package_types
    variations_formset.empty_form.fields['measurement_unit'].queryset = measurement_units
    # Також для всіх форм у формсеті

    for variation_form in variations_formset.forms:
        variation_form.fields['package_type'].queryset = package_types
        variation_form.fields['measurement_unit'].queryset = measurement_units
    print(variations_formset)
    context = {
        'form': form,
        'formset': formset,
        'variations_formset': variations_formset,
        'product': product,
        'has_variations': has_variations,
        'package_types': package_types,
        'measurement_units': measurement_units,
        'title': f'Редагування товару: {product.real_name}',
    }
    
    return render(request, 'warehouse/product/product_form.html', context)

@login_required
def product_delete(request, pk):
    """View to delete a product."""
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Товар "{product_name}" успішно видалено.')
        return redirect('product_list')
    return redirect('product_detail', pk=product.pk)

@login_required
def category_products(request, category_id):
    """View to display products filtered by category."""
    category = get_object_or_404(Culture, pk=category_id)
    products = Product.objects.filter(category=category).order_by('name')
    
    # Paginate results
    paginator = Paginator(products, 10)  # Show 10 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj,
    }
    
    return render(request, 'warehouse/product/category_products.html', context)

@login_required
def culture_products(request, culture_id):
    """View to display products filtered by culture."""
    culture = get_object_or_404(Culture, pk=culture_id)
    products = Product.objects.filter(culture=culture).order_by('name')
    
    # Paginate results
    paginator = Paginator(products, 10)  # Show 10 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'culture': culture,
        'page_obj': page_obj,
    }
    
    return render(request, 'warehouse/product/culture_products.html', context)

@login_required
def variation_product_detail(request, pk):
    """View to display details of a specific product variation."""
    variation_product = get_object_or_404(
        ProductVariation.objects.select_related('parent_product', 'parent_product__culture', 'package_type', 'measurement_unit'), 
        pk=pk
    )
    
    # Get related variations (same parent product)
    related_products = ProductVariation.objects.filter(
        parent_product=variation_product.parent_product
    ).exclude(id=variation_product.id)[:4]
    
    context = {
        'variation_product': variation_product,
        'related_products': related_products,
    }
    
    return render(request, 'warehouse/product/variation_product_detail.html', context)

@login_required
def variation_product_delete(request, pk):
    """View to delete a product variation."""
    variation = get_object_or_404(ProductVariation, pk=pk)
    parent_product = variation.parent_product
    
    if request.method == 'POST':
        variation_name = variation.name or variation.parent_product.real_name
        variation.delete()
        messages.success(request, f'Варіацію товару "{variation_name}" успішно видалено.')
        return redirect('product_detail', pk=parent_product.pk)
    return redirect('product_detail', pk=parent_product.pk) 
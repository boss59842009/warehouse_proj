from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from ..models import Product, ProductVariation, Culture, ProductVariationImage
from ..forms import ProductForm, ProductImageFormSet, ProductFilterForm, ProductVariationForm, ProductVariationImageFormSet


@login_required
def variation_product_detail(request, pk):
    """View to display details of a specific product."""
    variation_product = get_object_or_404(ProductVariation, pk=pk)
    
    # Get related products (same category)
    related_products = ProductVariation.objects.filter(
        culture=variation_product.culture
    ).exclude(id=variation_product.id)[:4]
    
    context = {
        'variation_product': variation_product,
        'related_products': related_products,
    }    
    return render(request, 'warehouse/product/variation_product_detail.html', context)

@login_required
def variation_product_create(request, product_id):
    """View to create a new product.""" 
    product = get_object_or_404(Product, pk=product_id)
    if request.method == 'POST':
        form = ProductVariationForm(request.POST, request.FILES)
        formset = ProductVariationImageFormSet(request.POST, request.FILES, instance=None, prefix='images')
        
        if form.is_valid() and formset.is_valid():
            # Спочатку зберігаємо товар без коміту
            variation_product = form.save(commit=False)
            # Встановлюємо батьківський продукт
            variation_product.parent_product = product
            # Встановлюємо культуру
            variation_product.culture = product.culture
            # Зберігаємо варіацію
            variation_product.save()
            
            # Прив'язуємо формсет до створеного товару
            formset.instance = variation_product
            
            # Зберігаємо зображення
            image_instances = formset.save(commit=False)
            for image in image_instances:
                image.variation_product = variation_product  # Явно встановлюємо зв'язок
                image.save()
            
            # Видаляємо позначені для видалення зображення
            for obj in formset.deleted_objects:
                obj.delete()
            
            messages.success(request, f'Варіація товару "{variation_product.name}" успішно створено.')
            return redirect('variation_product_detail', pk=variation_product.pk)
    else:
        form = ProductVariationForm()
        formset = ProductVariationImageFormSet(prefix='images')
    
    context = {
        'form': form,
        'formset': formset,
        'title': 'Створення нової варіації товару',
        'product': product,
    }
    
    return render(request, 'warehouse/product/variation_product_form.html', context)

@login_required
def variation_product_update(request, pk):
    """View to update an existing product."""
    variation_product = get_object_or_404(ProductVariation, pk=pk)
    
    if request.method == 'POST':
        form = ProductVariationForm(request.POST, request.FILES, instance=variation_product)
        formset = ProductVariationImageFormSet(request.POST, request.FILES, instance=variation_product, prefix='images')
        
        if form.is_valid() and formset.is_valid():
            variation_product = form.save()
            # Зберігаємо формсет
            formset.save()
            messages.success(request, f'Товар "{variation_product.real_name}" успішно оновлено.')
            return redirect('variation_product_detail', pk=variation_product.pk)
    else:
        form = ProductVariationForm(instance=variation_product)
        formset = ProductVariationImageFormSet(instance=variation_product, prefix='images')
    
    context = {
        'form': form,
        'formset': formset,
        'variation_product': variation_product,
        'title': f'Редагування товару: {variation_product.real_name}',
    }
    
    return render(request, 'warehouse/product/variation_product_form.html', context)

@login_required
def variation_product_delete(request, pk):
    """View to delete a product."""
    product = get_object_or_404(ProductVariation, pk=pk)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Варіація товару "{product_name}" успішно видалено.')
        return redirect('product_detail', pk=product.parent_product.pk)
    return redirect('variation_product_detail', pk=product.pk)
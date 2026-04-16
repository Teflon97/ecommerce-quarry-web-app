from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product

@login_required
def product_list(request):
    products = Product.objects.all()
    return render(request, 'admin/portal/products/list.html', {'products': products})

@login_required
def product_create(request):
    if request.method == 'POST':
        # Handle product creation
        name = request.POST.get('name')
        description = request.POST.get('description')
        price = request.POST.get('price')
        
        if name and price:
            product = Product.objects.create(
                name=name,
                description=description,
                short_description=request.POST.get('short_description', ''),
                price=price,
                stock_quantity=request.POST.get('stock_quantity', 0),
                created_by=request.user
            )
            messages.success(request, f'Product "{name}" created successfully!')
            return redirect('product_detail', pk=product.id)
    
    return render(request, 'admin/portal/products/form.html')

@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'admin/portal/products/detail.html', {'product': product})

@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        # Handle product update
        product.name = request.POST.get('name', product.name)
        product.description = request.POST.get('description', product.description)
        product.price = request.POST.get('price', product.price)
        product.stock_quantity = request.POST.get('stock_quantity', product.stock_quantity)
        product.save()
        messages.success(request, f'Product "{product.name}" updated successfully!')
        return redirect('product_detail', pk=product.id)
    
    return render(request, 'admin/portal/products/form.html', {'product': product})

@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product "{product_name}" deleted successfully!')
        return redirect('product_list')
    
    return render(request, 'admin/portal/products/delete.html', {'product': product})
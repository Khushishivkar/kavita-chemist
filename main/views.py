from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, F, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (CategoryForm, ContactForm, LoginForm, ProductForm,
                    RegisterForm, StockForm)
from .models import (EXPIRY_WARNING_DAYS, Category, ContactMessage, Product,
                     StockTransaction)

staff_required = user_passes_test(lambda u: u.is_staff, login_url='login')


# ---------------------------------------------------------------
# PUBLIC PAGES
# ---------------------------------------------------------------
def home(request):
    return render(request, 'main/home.html')


def about(request):
    return render(request, 'main/about.html')


def features(request):
    return render(request, 'main/features.html')


def contact(request):
    form = ContactForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Thank you! Your message has been sent. We will reply soon.')
        return redirect('contact')
    return render(request, 'main/contact.html', {'form': form})


# ---------------------------------------------------------------
# AUTH
# ---------------------------------------------------------------
class SiteLoginView(LoginView):
    template_name = 'main/login.html'
    authentication_form = LoginForm
    redirect_authenticated_user = True


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f'Welcome, {user.username}! Your account is ready.')
        return redirect('dashboard')
    return render(request, 'main/register.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


# ---------------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------------
@login_required
def dashboard(request):
    today = timezone.localdate()
    soon = today + timedelta(days=EXPIRY_WARNING_DAYS)
    products = Product.objects.all()

    low = products.filter(quantity__gt=0, quantity__lte=F('reorder_level'))
    out = products.filter(quantity=0)
    expiring = products.filter(expiry_date__isnull=False, expiry_date__lte=soon).order_by('expiry_date')
    expired_count = products.filter(expiry_date__lt=today).count()
    total_value = sum((p.price * p.quantity for p in products), 0)

    # chart data
    top = list(products.order_by('-quantity')[:8])
    cat_rows = Category.objects.annotate(units=Sum('products__quantity')).filter(units__gt=0)
    ok_count = products.count() - low.count() - out.count()

    charts = {
        'topLabels': [p.name for p in top],
        'topValues': [p.quantity for p in top],
        'statusLabels': ['Healthy', 'Low stock', 'Out of stock'],
        'statusValues': [max(ok_count, 0), low.count(), out.count()],
        'catLabels': [c.name for c in cat_rows],
        'catValues': [c.units for c in cat_rows],
    }

    context = {
        'total_products': products.count(),
        'total_categories': Category.objects.count(),
        'low_count': low.count(),
        'out_count': out.count(),
        'expiring_count': expiring.count(),
        'expired_count': expired_count,
        'total_value': total_value,
        'low_items': low.order_by('quantity')[:6],
        'expiring_items': expiring[:6],
        'recent_products': products.select_related('category').order_by('-created_at')[:6],
        'recent_txns': StockTransaction.objects.select_related('product')[:7],
        'unread_messages': ContactMessage.objects.filter(is_read=False).count() if request.user.is_staff else 0,
        'charts': charts,
    }
    return render(request, 'main/dashboard.html', context)


# ---------------------------------------------------------------
# PRODUCTS
# ---------------------------------------------------------------
@login_required
def product_list(request):
    today = timezone.localdate()
    soon = today + timedelta(days=EXPIRY_WARNING_DAYS)
    qs = Product.objects.select_related('category')

    q = request.GET.get('q', '').strip()
    cat = request.GET.get('category', '')
    status = request.GET.get('status', '')

    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(brand__icontains=q))
    if cat.isdigit():
        qs = qs.filter(category_id=cat)
    if status == 'low':
        qs = qs.filter(quantity__gt=0, quantity__lte=F('reorder_level'))
    elif status == 'out':
        qs = qs.filter(quantity=0)
    elif status == 'expiring':
        qs = qs.filter(expiry_date__gte=today, expiry_date__lte=soon)
    elif status == 'expired':
        qs = qs.filter(expiry_date__lt=today)

    page = Paginator(qs, 10).get_page(request.GET.get('page'))
    params = request.GET.copy()
    params.pop('page', None)
    return render(request, 'main/product_list.html', {
        'page': page,
        'categories': Category.objects.all(),
        'q': q, 'sel_category': cat, 'sel_status': status,
        'querystring': params.urlencode(),
    })


@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product.objects.select_related('category'), pk=pk)
    return render(request, 'main/product_detail.html', {
        'product': product,
        'txns': product.transactions.select_related('created_by')[:10],
    })


@login_required
def product_create(request):
    form = ProductForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        product = form.save()
        if product.quantity:
            StockTransaction.objects.create(
                product=product, kind=StockTransaction.IN, quantity=product.quantity,
                notes='Opening stock', created_by=request.user)
        messages.success(request, f'"{product.name}" added to inventory.')
        return redirect('product_detail', pk=product.pk)
    return render(request, 'main/product_form.html', {'form': form, 'title': 'Add medicine'})


@login_required
def product_edit(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = ProductForm(request.POST or None, instance=product)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f'"{product.name}" updated.')
        return redirect('product_detail', pk=product.pk)
    return render(request, 'main/product_form.html', {'form': form, 'title': 'Edit medicine', 'product': product})


@login_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f'"{name}" deleted.')
        return redirect('product_list')
    return render(request, 'main/confirm_delete.html', {
        'object_name': product.name, 'kind': 'medicine', 'cancel_url': product.get_absolute_url(),
        'warning': 'Its stock history will be deleted too.'})


@login_required
def product_stock(request, pk):
    product = get_object_or_404(Product, pk=pk)
    form = StockForm(request.POST or None, product=product)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            product = Product.objects.select_for_update().get(pk=pk)
            txn = form.save(commit=False)
            txn.product, txn.created_by = product, request.user
            if txn.kind == StockTransaction.IN:
                product.quantity += txn.quantity
            elif txn.kind == StockTransaction.OUT:
                product.quantity = max(product.quantity - txn.quantity, 0)
            else:
                product.quantity = txn.quantity
            product.save(update_fields=['quantity', 'updated_at'])
            txn.save()
        messages.success(request, f'Stock updated. "{product.name}" now has {product.quantity} units.')
        return redirect('product_detail', pk=pk)
    return render(request, 'main/stock_form.html', {'form': form, 'product': product})


# ---------------------------------------------------------------
# CATEGORIES
# ---------------------------------------------------------------
@login_required
def category_list(request):
    cats = Category.objects.annotate(count=Count('products'))
    return render(request, 'main/category_list.html', {'categories': cats})


@login_required
def category_create(request):
    form = CategoryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Category added.')
        return redirect('category_list')
    return render(request, 'main/category_form.html', {'form': form, 'title': 'Add category'})


@login_required
def category_edit(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    form = CategoryForm(request.POST or None, instance=cat)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Category updated.')
        return redirect('category_list')
    return render(request, 'main/category_form.html', {'form': form, 'title': 'Edit category'})


@login_required
def category_delete(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        cat.delete()
        messages.success(request, 'Category deleted.')
        return redirect('category_list')
    return render(request, 'main/confirm_delete.html', {
        'object_name': cat.name, 'kind': 'category', 'cancel_url': reverse('category_list'),
        'warning': 'Medicines in it will stay but become uncategorised.'})


# ---------------------------------------------------------------
# CONTACT INBOX (staff only)
# ---------------------------------------------------------------
@login_required
@staff_required
def inbox(request):
    return render(request, 'main/inbox.html', {'items': ContactMessage.objects.all()})


@login_required
@staff_required
@require_POST
def inbox_toggle(request, pk):
    msg = get_object_or_404(ContactMessage, pk=pk)
    msg.is_read = not msg.is_read
    msg.save(update_fields=['is_read'])
    return redirect('inbox')

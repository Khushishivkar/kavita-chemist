from datetime import timedelta

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

EXPIRY_WARNING_DAYS = 60


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=150)
    brand = models.CharField(max_length=100, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=10, help_text='Alert when stock falls to this number')
    expiry_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product_detail', args=[self.pk])

    @property
    def is_out_of_stock(self):
        return self.quantity == 0

    @property
    def is_low_stock(self):
        return 0 < self.quantity <= self.reorder_level

    @property
    def is_expired(self):
        return bool(self.expiry_date and self.expiry_date < timezone.localdate())

    @property
    def is_expiring_soon(self):
        if not self.expiry_date or self.is_expired:
            return False
        return self.expiry_date <= timezone.localdate() + timedelta(days=EXPIRY_WARNING_DAYS)

    @property
    def status_label(self):
        if self.is_expired:
            return 'Expired'
        if self.is_out_of_stock:
            return 'Out of stock'
        if self.is_low_stock:
            return 'Low stock'
        if self.is_expiring_soon:
            return 'Expiring soon'
        return 'In stock'

    @property
    def status_colour(self):
        if self.is_expired or self.is_out_of_stock:
            return 'red'
        if self.is_low_stock or self.is_expiring_soon:
            return 'orange'
        return 'green'

    @property
    def stock_value(self):
        return self.price * self.quantity


class StockTransaction(models.Model):
    IN, OUT, ADJUST = 'in', 'out', 'adjust'
    TYPE_CHOICES = [(IN, 'Stock in'), (OUT, 'Stock out / sold'), (ADJUST, 'Set exact quantity')]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='transactions')
    kind = models.CharField(max_length=10, choices=TYPE_CHOICES)
    quantity = models.PositiveIntegerField()
    notes = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_kind_display()} {self.quantity} x {self.product}'

    @property
    def colour(self):
        return {self.IN: 'green', self.OUT: 'orange', self.ADJUST: 'blue'}[self.kind]

    @property
    def icon(self):
        return {self.IN: 'fa-arrow-down', self.OUT: 'fa-arrow-up', self.ADJUST: 'fa-sliders'}[self.kind]

    @property
    def sign(self):
        return {self.IN: '+', self.OUT: '-', self.ADJUST: '='}[self.kind]


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=150, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name}: {self.subject or self.message[:30]}'

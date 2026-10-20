from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from main.models import Category, Product, StockTransaction


class Command(BaseCommand):
    help = 'Fill the database with sample pharmacy data (safe to run once).'

    def handle(self, *args, **options):
        if Product.objects.exists():
            self.stdout.write('Products already exist - nothing to do.')
            return
        today = timezone.localdate()
        cats = {n: Category.objects.get_or_create(name=n, defaults={'description': d})[0] for n, d in [
            ('Pain Relief', 'Analgesics and anti-inflammatory tablets'),
            ('Antibiotics', 'Prescription antibiotics'),
            ('Vitamins', 'Supplements and multivitamins'),
            ('Cold & Cough', 'Syrups, lozenges and decongestants'),
            ('First Aid', 'Bandages, antiseptics and dressings'),
            ('Diabetes Care', 'Insulin, strips and monitors'),
        ]}
        rows = [
            ('Paracetamol 500mg', 'Crocin', 'Pain Relief', 25, 240, 50, 400),
            ('Ibuprofen 400mg', 'Brufen', 'Pain Relief', 32, 8, 20, 300),
            ('Amoxicillin 500mg', 'Mox', 'Antibiotics', 85, 60, 25, 25),
            ('Azithromycin 500mg', 'Azee', 'Antibiotics', 118, 0, 20, 200),
            ('Vitamin C 500mg', 'Celin', 'Vitamins', 45, 150, 40, 500),
            ('Multivitamin Daily', 'Revital H', 'Vitamins', 320, 35, 15, 700),
            ('Cough Syrup 100ml', 'Benadryl', 'Cold & Cough', 110, 12, 15, 45),
            ('Cetirizine 10mg', 'Okacet', 'Cold & Cough', 28, 90, 30, 600),
            ('Antiseptic Liquid 250ml', 'Dettol', 'First Aid', 145, 40, 10, 800),
            ('Adhesive Bandage (pack)', 'Band-Aid', 'First Aid', 60, 6, 15, 900),
            ('Glucose Test Strips (50)', 'Accu-Chek', 'Diabetes Care', 950, 22, 10, 300),
            ('Metformin 500mg', 'Glycomet', 'Diabetes Care', 40, 130, 40, 20),
        ]
        for name, brand, cat, price, qty, reorder, days in rows:
            p = Product.objects.create(
                name=name, brand=brand, category=cats[cat], price=price, quantity=qty,
                reorder_level=reorder, expiry_date=today + timedelta(days=days),
                description=f'{name} by {brand}. Store in a cool, dry place.')
            if qty:
                StockTransaction.objects.create(product=p, kind='in', quantity=qty, notes='Opening stock')
        self.stdout.write(self.style.SUCCESS('Demo data added: 6 categories, 12 medicines.'))

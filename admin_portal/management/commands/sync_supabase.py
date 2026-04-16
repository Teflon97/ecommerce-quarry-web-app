from django.core.management.base import BaseCommand
from supabase import create_client
import os
from dotenv import load_dotenv
from apps.products.models import Product
from apps.orders.models import Order, OrderItem

class Command(BaseCommand):
    help = 'Sync data from Supabase to Django models'
    
    def handle(self, *args, **options):
        load_dotenv()
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not supabase_url or not supabase_key:
            self.stdout.write(self.style.ERROR('Supabase credentials not found in .env file'))
            return
        
        supabase = create_client(supabase_url, supabase_key)
        
        # Sync products
        self.stdout.write('Syncing products...')
        products_data = supabase.table('products').select('*').execute()
        
        for item in products_data.data:
            product, created = Product.objects.update_or_create(
                id=item.get('id'),
                defaults={
                    'name': item.get('name'),
                    'description': item.get('description'),
                    'short_description': item.get('short_description'),
                    'price': item.get('price'),
                    'sale_price': item.get('sale_price'),
                    'stock_quantity': item.get('stock_quantity', 0),
                    'status': item.get('status', 'active'),
                    'image_url': item.get('image_url', ''),
                }
            )
            if created:
                self.stdout.write(f'  Created product: {product.name}')
            else:
                self.stdout.write(f'  Updated product: {product.name}')
        
        # Sync orders
        self.stdout.write('Syncing orders...')
        orders_data = supabase.table('orders').select('*').execute()
        
        for item in orders_data.data:
            order, created = Order.objects.update_or_create(
                id=item.get('id'),
                defaults={
                    'order_number': item.get('order_number'),
                    'customer_name': item.get('customer_name'),
                    'customer_email': item.get('customer_email'),
                    'customer_phone': item.get('customer_phone'),
                    'customer_address': item.get('customer_address'),
                    'total_amount': item.get('total_amount'),
                    'status': item.get('status', 'pending'),
                    'payment_status': item.get('payment_status', 'pending'),
                    'created_at': item.get('created_at'),
                }
            )
            if created:
                self.stdout.write(f'  Created order: {order.order_number}')
            else:
                self.stdout.write(f'  Updated order: {order.order_number}')
        
        self.stdout.write(self.style.SUCCESS('Successfully synced data from Supabase'))
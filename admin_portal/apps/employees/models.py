from django.db import models
import uuid

class Employee(models.Model):
    DEPARTMENT_CHOICES = [
        ('Sales', 'Sales'),
        ('Accounting', 'Accounting'),
        ('Finance', 'Finance'),
        ('Delivery', 'Delivery'),
        ('Warehouse', 'Warehouse'),
        ('Management', 'Management'),
    ]
    
    ROLE_CHOICES = [
        ('Admin', 'Admin'),
        ('Manager', 'Manager'),
        ('Sales Rep', 'Sales Rep'),
        ('Accountant', 'Accountant'),
        ('Finance Officer', 'Finance Officer'),
        ('Driver', 'Driver'),
        ('Warehouse Staff', 'Warehouse Staff'),
        ('Dispatcher', 'Dispatcher'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee_id = models.CharField(max_length=50, unique=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True)
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    hire_date = models.DateField(auto_now_add=True)
    driver_license_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    max_load_capacity_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    available_for_delivery = models.BooleanField(default=True)
    last_latitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    last_longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    last_location_update = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'employees'
        ordering = ['first_name', 'last_name']
    
    def save(self, *args, **kwargs):
        if not self.employee_id:
            prefix = {
                'Admin': 'ADM',
                'Manager': 'MGR',
                'Driver': 'DRV',
                'Sales Rep': 'SAL',
                'Accountant': 'ACC',
                'Finance Officer': 'FIN',
                'Warehouse Staff': 'WRH',
                'Dispatcher': 'DSP'
            }.get(self.role, 'EMP')
            count = Employee.objects.filter(role=self.role).count() + 1
            self.employee_id = f"{prefix}{count:03d}"
        super().save(*args, **kwargs)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def __str__(self):
        return f"{self.full_name} - {self.role}"

class Truck(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    truck_number = models.CharField(max_length=50, unique=True)
    license_plate = models.CharField(max_length=50, unique=True)
    capacity_kg = models.DecimalField(max_digits=10, decimal_places=2)
    current_load_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    model = models.CharField(max_length=100, blank=True)
    year = models.IntegerField(null=True, blank=True)
    assigned_driver_email = models.EmailField(max_length=255, blank=True, default='')
    is_available = models.BooleanField(default=True)
    is_operational = models.BooleanField(default=True)
    last_known_latitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    last_known_longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'trucks'
        ordering = ['truck_number']
    
    @property
    def available_capacity(self):
        return self.capacity_kg - self.current_load_kg
    
    def __str__(self):
        return f"{self.truck_number} - {self.capacity_kg}kg"

class Delivery(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('accepted', 'Accepted'),
        ('loading', 'Loading'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delivery_number = models.CharField(max_length=50, unique=True, blank=True)
    order_id = models.CharField(max_length=255)
    truck_id = models.UUIDField(null=True, blank=True)
    driver_id = models.UUIDField(null=True, blank=True)
    dispatcher_id = models.UUIDField(null=True, blank=True)
    total_weight_kg = models.DecimalField(max_digits=10, decimal_places=2)
    pickup_location = models.TextField(blank=True)
    delivery_address = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    distance_km = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estimated_delivery_time = models.DateTimeField(null=True, blank=True)
    actual_delivery_time = models.DateTimeField(null=True, blank=True)
    current_latitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    current_longitude = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    assigned_to = models.UUIDField(null=True, blank=True)  # Driver ID
    assignment_id = models.CharField(max_length=255, unique=True, blank=True, default=uuid.uuid4)  # Renamed from delivery_photo
    delivery_notes = models.TextField(blank=True)
    failure_reason = models.TextField(blank=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    loaded_up_at = models.DateTimeField(null=True, blank=True)  # Renamed from picked_up_at
    in_transit_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'deliveries'
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        if not self.delivery_number:
            self.delivery_number = f"DLV-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
        if not self.assignment_id:
            self.assignment_id = str(uuid.uuid4())
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Delivery {self.delivery_number} - {self.status}"
from django.db import models
import uuid

class Report(models.Model):
    REPORT_TYPES = [
        ('orders', 'Orders Report'),
        ('products', 'Products Report'),
        ('employees', 'Employees Report'),
        ('deliveries', 'Deliveries Report'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    report_type = models.CharField(max_length=50, choices=REPORT_TYPES)
    file_path = models.CharField(max_length=500, blank=True)
    generated_by_email = models.EmailField(max_length=255)
    generated_at = models.DateTimeField(auto_now_add=True)
    parameters = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'reports'
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"{self.report_type} - {self.generated_at}"
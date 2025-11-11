"""
Signals for POS Management
Auto-update inventory when distributions are created
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Distribution, ClientInventory


@receiver(post_save, sender=Distribution)
def update_client_inventory_on_distribution(sender, instance, created, **kwargs):
    """
    Automatically update client inventory when a distribution is created
    """
    if created and instance.status in ['new', 'waiting_visit']:
        # Get or create inventory record for this client-product combination
        inventory, inv_created = ClientInventory.objects.get_or_create(
            client=instance.client,
            product=instance.product,
            defaults={
                'current_quantity': 0,
                'minimum_quantity': 0,
                'maximum_quantity': 100,
                'last_updated_by': instance.created_by,
                'last_distribution': instance
            }
        )
        
        # Add the distributed quantity to inventory
        inventory.add_stock(
            quantity=instance.quantity,
            distribution=instance,
            user=instance.created_by
        )

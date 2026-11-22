import os
import django
from unittest.mock import patch

# 1. Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from admin_app.models import Admin, JournalActivite
from admin_app.services.moderation_service import ModerationService

# 2. Get your superuser (replace with your actual email!)
admin_user = Admin.objects.first() 
if not admin_user:
    print("Create a superuser first!")
    exit()

print(f"Testing with admin: {admin_user.email}")

# 3. THE MAGIC: We patch (fake) the EventClient's method
# Whenever the code calls update_event_status, it will just return (True, {})
with patch('admin_app.clients.event_client.EventClient.update_event_status') as mock_update:
    mock_update.return_value = (True, {"message": "Fake Event Service Success"})
    
    print("--- Testing Approve Event ---")
    service = ModerationService(admin_user=admin_user)
    success, message = service.approve_event(event_id=42)
    
    print(f"Success: {success}")
    print(f"Message: {message}")
    
    # Check if the Journal was written
    log = JournalActivite.objects.filter(target_id=42).first()
    if log:
        print(f"✅ Journal created! Action: {log.action}, Admin: {log.admin.email}")
    else:
        print("❌ Journal NOT created!")
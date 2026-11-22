from rest_framework import serializers
from .models import Admin, JournalActivite

class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin
        fields = ['id', 'email', 'first_name', 'last_name', 'is_active', 'date_joined']
        # Notice: 'password' is NOT in the fields list. It will never be sent in JSON.
        # We also don't include is_superuser so a frontend cannot accidentally make someone a superuser.

class JournalActiviteSerializer(serializers.ModelSerializer):
    # To make the journal readable, we fetch the admin's email instead of just the ID
    admin_email = serializers.ReadOnlyField(source='admin.email')

    class Meta:
        model = JournalActivite
        fields = ['id', 'admin_email', 'action', 'target_type', 'target_id', 'details', 'date_action']
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

class AdminManager(BaseUserManager):
    """
    Custom manager to handle user creation using email instead of username.
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class Admin(AbstractUser):
    username = None 
    email = models.EmailField(unique=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = AdminManager()

    def __str__(self):
        return self.email

    class Meta:
        db_table = 'admins'


class JournalActivite(models.Model):
    """
    Audit log for all moderation actions.
    """
    # Choices for the action field to prevent typos and keep data clean
    ACTION_CHOICES = (
        ('VALIDATE_ORGANIZER', 'Validate Organizer'),
        ('SUSPEND_ORGANIZER', 'Suspend Organizer'),
        ('REACTIVATE_ORGANIZER', 'Reactivate Organizer'),
        ('APPROVE_EVENT', 'Approve Event'),
        ('REJECT_EVENT', 'Reject Event'),
    )

    TARGET_CHOICES = (
        ('ORGANIZER', 'Organizer'),
        ('EVENT', 'Event'),
    )

    # 1. The Admin who performed the action (Internal ForeignKey - Allowed!)
    admin = models.ForeignKey(Admin, on_delete=models.CASCADE, related_name='journal_entries')
    
    # 2. What action was taken (e.g., APPROVE_EVENT)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    
    # 3. What was the target (ORGANIZER or EVENT)
    target_type = models.CharField(max_length=20, choices=TARGET_CHOICES)
    
    # 4. The ID of the Organizer or Event (External ID - NO ForeignKey!)
    target_id = models.IntegerField()
    
    # 5. The details (e.g., "Admin approved event 'Tech Talk'")
    details = models.TextField(blank=True, null=True)
    
    # 6. When it happened (UML: dateAction)
    date_action = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.admin.email} - {self.action} - {self.target_type} {self.target_id}"

    class Meta:
        db_table = 'journal_activite'
        ordering = ['-date_action'] # Newest actions first
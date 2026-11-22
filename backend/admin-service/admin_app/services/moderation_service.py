from ..models import JournalActivite
from ..clients.organizer_client import OrganizerClient
from ..clients.event_client import EventClient

class ModerationService:
    def __init__(self, admin_user):
        self.admin = admin_user
        self.organizer_client = OrganizerClient()
        self.event_client = EventClient()

    def approve_event(self, event_id):
        # 1. Call the Event Service
        success, response_data = self.event_client.update_event_status(event_id, "APPROUVEE")
        
        # 2. If it fails, stop here and return the error
        if not success:
            return False, f"Event Service error: {response_data}"

        # 3. If it succeeds, log the action in our Journal
        self._log_action(
            action='APPROVE_EVENT',
            target_type='EVENT',
            target_id=event_id,
            details=f"Approved event {event_id}"
        )
        return True, "Event approved successfully"

    def reject_event(self, event_id):
        success, response_data = self.event_client.update_event_status(event_id, "REJETEE")
        if not success:
            return False, f"Event Service error: {response_data}"

        self._log_action(
            action='REJECT_EVENT',
            target_type='EVENT',
            target_id=event_id,
            details=f"Rejected event {event_id}"
        )
        return True, "Event rejected successfully"

    def validate_organizer(self, organizer_id):
        success, response_data = self.organizer_client.update_organizer_status(organizer_id, "VALIDE")
        if not success:
            return False, f"Organizer Service error: {response_data}"

        self._log_action(
            action='VALIDATE_ORGANIZER',
            target_type='ORGANIZER',
            target_id=organizer_id,
            details=f"Validated organizer {organizer_id}"
        )
        return True, "Organizer validated successfully"

    def suspend_organizer(self, organizer_id):
        success, response_data = self.organizer_client.update_organizer_status(organizer_id, "SUSPENDU")
        if not success:
            return False, f"Organizer Service error: {response_data}"

        self._log_action(
            action='SUSPEND_ORGANIZER',
            target_type='ORGANIZER',
            target_id=organizer_id,
            details=f"Suspended organizer {organizer_id}"
        )
        return True, "Organizer suspended successfully"

    def reactivate_organizer(self, organizer_id):
        success, response_data = self.organizer_client.update_organizer_status(organizer_id, "ACTIF")
        if not success:
            return False, f"Organizer Service error: {response_data}"

        self._log_action(
            action='REACTIVATE_ORGANIZER',
            target_type='ORGANIZER',
            target_id=organizer_id,
            details=f"Reactivated organizer {organizer_id}"
        )
        return True, "Organizer reactivated successfully"

    def _log_action(self, action, target_type, target_id, details):
        """Helper method to write to the database."""
        JournalActivite.objects.create(
            admin=self.admin,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details
        )
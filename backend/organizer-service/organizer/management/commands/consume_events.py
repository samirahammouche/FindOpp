"""python manage.py consume_events

Worker that listens to RabbitMQ (run it in a second terminal / container):
    organizer.registered        (Auth service)  -> create the organizer profile
    organizer.verified          (Admin service) -> profile becomes "verified" / "rejected"
    publication.status_changed  (Admin service) -> approve / reject a publication
"""
import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from organizer import services
from organizer.messaging import EXCHANGE
from organizer.models import Organization, Publication
from organizer.serializers import OrganizationRegistrationSerializer, StatusUpdateSerializer

QUEUE = "organizer-service"
ROUTING_KEYS = ["organizer.registered", "organizer.verified", "publication.status_changed"]


def handle_event(routing_key, data):
    if routing_key == "organizer.registered":
        serializer = OrganizationRegistrationSerializer(data=data)
        serializer.fields["user_id"].validators = []
        serializer.is_valid(raise_exception=True)
        organization, _ = services.register_organization(serializer.validated_data)
        return f"profile ready for {organization.name}"

    if routing_key == "organizer.verified":
        status = data.get("status", Organization.Verification.VERIFIED)
        Organization.objects.filter(user_id=data["user_id"]).update(verification_status=status)
        return f"organizer {data['user_id']} -> {status}"

    if routing_key == "publication.status_changed":
        publication = Publication.objects.get(pk=data["publication_id"])
        serializer = StatusUpdateSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        if publication.status != Publication.Status.PENDING:
            return f"ignored: publication {publication.pk} is {publication.status}"
        services.apply_moderation_decision(
            publication, serializer.validated_data["status"], serializer.validated_data.get("reason", "")
        )
        return f"publication {publication.pk} -> {publication.status}"

    return "ignored"


class Command(BaseCommand):
    help = "Consume the FindOpp events sent to the Organizer service (RabbitMQ)."

    def handle(self, *args, **options):
        if not settings.RABBITMQ_URL:
            raise CommandError("Set RABBITMQ_URL, e.g. amqp://guest:guest@localhost:5672/")
        import pika

        connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
        channel = connection.channel()
        channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
        channel.queue_declare(queue=QUEUE, durable=True)
        for key in ROUTING_KEYS:
            channel.queue_bind(queue=QUEUE, exchange=EXCHANGE, routing_key=key)
        channel.basic_qos(prefetch_count=1)

        def callback(ch, method, properties, body):
            try:
                message = json.loads(body)
                result = handle_event(method.routing_key, message.get("data", message))
                self.stdout.write(self.style.SUCCESS(f"[{method.routing_key}] {result}"))
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as error:  # bad message: do not block the queue
                self.stderr.write(f"[{method.routing_key}] error: {error}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        channel.basic_consume(queue=QUEUE, on_message_callback=callback)
        self.stdout.write(f"Waiting for events on queue '{QUEUE}' ({', '.join(ROUTING_KEYS)})...")
        try:
            channel.start_consuming()
        except KeyboardInterrupt:
            channel.stop_consuming()
        connection.close()

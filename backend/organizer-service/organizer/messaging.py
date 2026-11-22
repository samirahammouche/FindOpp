"""RabbitMQ (asynchronous communication between microservices).

All FindOpp services use one "topic" exchange called `findopp`.

Events SENT by this service:
    publication.submitted   -> the Admin service puts it in "Publications to review"
    publication.updated     -> a published opportunity was edited (back to review)
    publication.deleted

Events RECEIVED by this service (see `python manage.py consume_events`):
    organizer.registered      <- Auth service, after "Create account"
    publication.status_changed <- Admin service, after Approve / Reject
    organizer.verified         <- Admin service, after the organizer is verified

If RABBITMQ_URL is empty (local development), events are only written in the logs.
"""
import json
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

EXCHANGE = "findopp"


def publish_event(routing_key, payload):
    message = json.dumps({"event": routing_key, "source": "organizer-service", "data": payload}, default=str)
    if not settings.RABBITMQ_URL:
        logger.info("[event not sent, RABBITMQ_URL empty] %s %s", routing_key, message)
        return False
    try:
        import pika

        connection = pika.BlockingConnection(pika.URLParameters(settings.RABBITMQ_URL))
        channel = connection.channel()
        channel.exchange_declare(exchange=EXCHANGE, exchange_type="topic", durable=True)
        channel.basic_publish(
            exchange=EXCHANGE,
            routing_key=routing_key,
            body=message,
            properties=pika.BasicProperties(content_type="application/json", delivery_mode=2),
        )
        connection.close()
        return True
    except Exception:  # the API must keep working even if RabbitMQ is down
        logger.exception("Could not publish event %s", routing_key)
        return False


def publication_payload(publication):
    return {
        "publication_id": publication.id,
        "organization_id": publication.organization_id,
        "organization_name": publication.organization.name,
        "title": publication.title,
        "category": publication.category,
        "status": publication.status,
        "application_deadline": publication.application_deadline,
    }

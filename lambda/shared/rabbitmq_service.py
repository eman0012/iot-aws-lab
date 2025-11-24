import json
import logging
import ssl
import pika
from .config import get_config

logger = logging.getLogger()

class RabbitMQService:
    def __init__(self):
        config = get_config()
        self.host = config["RABBITMQ_HOST"]
        self.port = config["RABBITMQ_PORT"]
        self.username = config["RABBITMQ_USERNAME"]
        self.password = config["RABBITMQ_PASSWORD"]
        self.queue_name = config["QUEUE_NAME"]

    def _get_connection(self):
        credentials = pika.PlainCredentials(self.username, self.password)

        # Amazon MQ requires TLS
        ssl_context = ssl.create_default_context()

        parameters = pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            virtual_host="/",
            credentials=credentials,
            ssl_options=pika.SSLOptions(ssl_context),
            heartbeat=30,
            blocked_connection_timeout=300
        )

        return pika.BlockingConnection(parameters)

    def declare_queue(self, queue_name: str = None):
        """Declare a queue (creates if doesn't exist)"""
        queue = queue_name or self.queue_name
        connection = self._get_connection()
        channel = connection.channel()

        channel.queue_declare(
            queue=queue,
            durable=True,
            arguments={
                'x-dead-letter-exchange': '',
                'x-dead-letter-routing-key': f'{queue}-dlq',
                'x-message-ttl': 86400000  # 24 hours
            }
        )

        # Also declare dead letter queue
        channel.queue_declare(queue=f'{queue}-dlq', durable=True)

        connection.close()
        logger.info(f"Queue '{queue}' declared successfully")

    def send_message(self, message: dict, queue_name: str = None):
        """Send a message to RabbitMQ queue"""
        queue = queue_name or self.queue_name

        try:
            connection = self._get_connection()
            channel = connection.channel()

            channel.queue_declare(queue=queue, durable=True)

            channel.basic_publish(
                exchange='',
                routing_key=queue,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Persistent
                    content_type='application/json'
                )
            )

            logger.info(f"Message sent to queue '{queue}'")
            connection.close()
            return True

        except Exception as e:
            logger.exception(f"Failed to send message to RabbitMQ: {str(e)}")
            raise

    def receive_messages(self, max_messages: int = 10, queue_name: str = None) -> list:
        """Receive messages from queue (for polling-based consumption)"""
        queue = queue_name or self.queue_name
        messages = []

        try:
            connection = self._get_connection()
            channel = connection.channel()

            channel.queue_declare(queue=queue, durable=True)

            for _ in range(max_messages):
                method, properties, body = channel.basic_get(queue=queue, auto_ack=False)

                if body:
                    messages.append({
                        'delivery_tag': method.delivery_tag,
                        'body': json.loads(body)
                    })
                else:
                    break

            # Acknowledge all messages
            for msg in messages:
                channel.basic_ack(delivery_tag=msg['delivery_tag'])

            connection.close()
            return [m['body'] for m in messages]

        except Exception as e:
            logger.exception(f"Failed to receive messages from RabbitMQ: {str(e)}")
            raise

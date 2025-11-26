"""
RabbitMQ Consumer Lambda
========================
Processes telemetry messages from RabbitMQ queue:
1. Stores telemetry data to PostgreSQL
2. Evaluates alert conditions
3. Creates alert logs for triggered conditions

Triggered by: CloudWatch Events (scheduled polling) or direct invocation
"""

import json
import logging
from datetime import datetime, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)

import sys
sys.path.insert(0, '/opt/python')

from shared.db_service import DatabaseService
from shared.rabbitmq_service import RabbitMQService


def main(event, context):
    """
    Main handler - processes messages from RabbitMQ telemetry queue.
    Can be triggered by CloudWatch Events for scheduled polling.
    """
    logger.info("Starting RabbitMQ consumer...")

    try:
        rabbitmq = RabbitMQService()
        db = DatabaseService()

        # Receive messages from queue (batch of up to 10)
        messages = rabbitmq.receive_messages(max_messages=10)

        if not messages:
            logger.info("No messages in queue")
            return {
                "statusCode": 200,
                "body": json.dumps({"processed": 0, "message": "No messages to process"})
            }

        processed = 0
        alerts_triggered = 0
        errors = []

        for message in messages:
            try:
                result = process_message(message, db)
                processed += 1
                alerts_triggered += result.get('alerts_triggered', 0)
            except Exception as e:
                logger.exception(f"Error processing message: {e}")
                errors.append(str(e))

        logger.info(f"Processed {processed} messages, triggered {alerts_triggered} alerts")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "processed": processed,
                "alerts_triggered": alerts_triggered,
                "errors": errors if errors else None
            })
        }

    except Exception as e:
        logger.exception(f"Consumer error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }


def process_message(message: dict, db: DatabaseService) -> dict:
    """
    Process a single telemetry message:
    1. Store telemetry to DB
    2. Evaluate conditions
    3. Create alerts if needed
    """
    message_type = message.get('type')

    if message_type != 'telemetry':
        logger.warning(f"Unknown message type: {message_type}")
        return {"alerts_triggered": 0}

    data = message.get('data', {})
    user_id = message.get('userId')

    # 1. Store telemetry to database
    telemetry_record = store_telemetry(data, user_id, db)
    logger.info(f"Stored telemetry: {telemetry_record.get('eventId')}")

    # 2. Evaluate conditions and create alerts
    alerts = evaluate_conditions(data, user_id, db)

    return {
        "telemetry_id": telemetry_record.get('eventId'),
        "alerts_triggered": len(alerts)
    }


def store_telemetry(data: dict, user_id: str, db: DatabaseService) -> dict:
    """Store telemetry data to PostgreSQL"""

    # Build values array from telemetry data (Azure format)
    values = []

    sensor_mappings = {
        'temperature': 'temperature',
        'humidity': 'humidity',
        'pressure': 'pressure',
        'light_level': 'light',
        'motion_detected': 'motion',
        'sound_level': 'sound',
        'air_quality': 'airQuality',
        'battery_level': 'battery'
    }

    for field, value_type in sensor_mappings.items():
        if data.get(field) is not None:
            values.append({
                "valueType": value_type,
                "value": data[field]
            })

    telemetry_data = {
        'eventId': data.get('id'),
        'deviceId': data.get('device_id'),
        'userId': user_id,
        'event_date': data.get('timestamp', datetime.now(timezone.utc).isoformat()),
        'values': values,
        'imageUrl': data.get('image_url')
    }

    return db.insert_telemetry(telemetry_data)


def evaluate_conditions(data: dict, user_id: str, db: DatabaseService) -> list:
    """
    Evaluate alert conditions against telemetry data.
    Creates alert logs for any triggered conditions.

    Azure logic: Check conditions by valueType, compare against min/max/exact values
    """
    alerts = []
    device_id = data.get('device_id')

    # Map telemetry fields to value types
    sensor_mappings = {
        'temperature': 'temperature',
        'humidity': 'humidity',
        'pressure': 'pressure',
        'light_level': 'light',
        'motion_detected': 'motion',
        'sound_level': 'sound',
        'air_quality': 'airQuality',
        'battery_level': 'battery'
    }

    for field, value_type in sensor_mappings.items():
        value = data.get(field)
        if value is None:
            continue

        # Get conditions for this value type
        conditions = db.get_conditions_by_value_type(value_type)

        for condition in conditions:
            # Check if condition applies to this device or all devices (scope)
            cond_device_id = condition.get('deviceId')
            scope = condition.get('scope', 'device')

            if scope == 'device' and cond_device_id and cond_device_id != device_id:
                continue

            # Check if condition is triggered
            triggered, message = check_condition(condition, value, value_type)

            if triggered:
                logger.info(f"Condition triggered: {condition.get('conditionId')} - {message}")

                # Create alert log
                alert = db.create_alert_log({
                    'deviceId': device_id,
                    'userId': user_id,
                    'message': message,
                    'condition': condition,
                    'telemetryData': {
                        'valueType': value_type,
                        'value': value,
                        'timestamp': data.get('timestamp')
                    }
                })
                alerts.append(alert)

    return alerts


def check_condition(condition: dict, value, value_type: str) -> tuple:
    """
    Check if a condition is triggered.

    Azure condition structure:
    - minValue: trigger if value < minValue
    - maxValue: trigger if value > maxValue
    - exactValue: trigger if value == exactValue

    Returns: (triggered: bool, message: str)
    """
    min_value = condition.get('minValue')
    max_value = condition.get('maxValue')
    exact_value = condition.get('exactValue')
    condition_name = condition.get('conditionName', 'Unnamed condition')

    try:
        # Convert to float for comparison (except for motion which is boolean)
        if value_type == 'motion':
            # Motion is boolean - check exact match
            if exact_value is not None and value == exact_value:
                return True, f"{condition_name}: Motion detected = {value}"
        else:
            numeric_value = float(value)

            if min_value is not None and numeric_value < float(min_value):
                return True, f"{condition_name}: {value_type} ({numeric_value}) below minimum ({min_value})"

            if max_value is not None and numeric_value > float(max_value):
                return True, f"{condition_name}: {value_type} ({numeric_value}) above maximum ({max_value})"

            if exact_value is not None and numeric_value == float(exact_value):
                return True, f"{condition_name}: {value_type} ({numeric_value}) equals threshold ({exact_value})"

    except (ValueError, TypeError) as e:
        logger.warning(f"Error comparing values: {e}")

    return False, ""

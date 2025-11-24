# EventBridge event bus for IoT events
resource "aws_cloudwatch_event_bus" "main" {
  name = "${var.project_name}-${var.environment}-event-bus"
}

# Rule to catch IoT device events
resource "aws_cloudwatch_event_rule" "iot_telemetry" {
  name           = "${var.project_name}-${var.environment}-iot-telemetry"
  event_bus_name = aws_cloudwatch_event_bus.main.name

  event_pattern = jsonencode({
    source      = ["iot.telemetry"]
    detail-type = ["IoT Device Telemetry"]
  })
}

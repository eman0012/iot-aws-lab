# IoT Platform CLI

A Go-based command-line tool for testing and managing the IoT Platform API.

## Installation

```bash
cd go-cli
go mod download
go build -o iot-cli cmd/main.go
```

## Usage

### Set API URL

```bash
export IOT_API_URL="https://your-api-gateway-url.execute-api.ca-central-1.amazonaws.com"
```

### Commands

#### Health Check
```bash
./iot-cli health
```

#### Login
```bash
./iot-cli login --email user@example.com --password yourpassword
```

This will output a token. Export it:
```bash
export IOT_TOKEN="your-jwt-token"
```

#### List Devices
```bash
./iot-cli devices list
```

#### Send Telemetry
```bash
./iot-cli telemetry send --device DEVICE_ID --temp 25.5 --humidity 60.0
```

#### Load Test
```bash
./iot-cli loadtest --device DEVICE_ID --requests 1000 --concurrency 50
```

### Global Flags

- `--api, -a`: API Gateway URL (overrides IOT_API_URL env)
- `--token, -t`: JWT token (overrides IOT_TOKEN env)
- `--verbose, -v`: Verbose output

## Examples

```bash
# Full workflow
export IOT_API_URL="https://xyz.execute-api.ca-central-1.amazonaws.com"

# Login
./iot-cli login -e admin@example.com -p admin123
export IOT_TOKEN="eyJhbG..."

# Check health
./iot-cli health

# List devices
./iot-cli devices list

# Send telemetry
./iot-cli telemetry send -d device-001 -T 22.5 -H 55.0

# Run load test
./iot-cli loadtest -d device-001 -n 100 -c 10
```

## Build for Distribution

```bash
# Build for current platform
go build -o iot-cli cmd/main.go

# Build for Linux
GOOS=linux GOARCH=amd64 go build -o iot-cli-linux cmd/main.go

# Build for macOS
GOOS=darwin GOARCH=amd64 go build -o iot-cli-macos cmd/main.go

# Build for Windows
GOOS=windows GOARCH=amd64 go build -o iot-cli.exe cmd/main.go
```

# AZURE_PROJECT_REFERENCE.md

**Source Project:** `/Users/cory/School/Cloud DevOps Grad Cert Courses/CST8922-450/IoTAccessability`

This document provides complete implementation details of the Azure IoT Accessibility platform for AWS migration reference.

---

## 1. DIRECTORY STRUCTURE

```
IoTAccessability/
├── AGENTS.md
├── IoTAccessability/ (iOS Mobile App - Swift/SwiftUI)
│   ├── Application/
│   │   ├── IoTAccessabilityApp.swift
│   │   ├── AppDelegate.swift
│   │   └── SceneDelegate.swift
│   ├── Core/
│   │   ├── Models/ (User, Device, TelemetryData, NotificationModel)
│   │   ├── Services/ (AuthService, NetworkService, DeviceService, TelemetryService, NotificationService)
│   │   └── Utilities/ (Constants, Extensions, Helpers)
│   ├── Features/
│   │   ├── Authentication/ (LoginView, ViewModels, Components)
│   │   ├── Dashboard/ (DashboardView, ViewModels, Components)
│   │   ├── DeviceManagement/ (DeviceListView, DeviceDetailView, AddDeviceView)
│   │   ├── HealthMonitoring/
│   │   ├── Profile/
│   │   └── Accessibility/
│   └── Resources/ (Assets.xcassets, Preview Content)
├── IoTAccessability.xcodeproj/
├── IoTAccessibility_Documentation/
│   ├── Backend_Codebase/ (Python Azure Functions)
│   │   ├── function_app.py (Main HTTP trigger entry point)
│   │   ├── host.json (Azure Functions host config)
│   │   ├── local.settings.json (Environment variables)
│   │   ├── requirements.txt (Python dependencies)
│   │   ├── azure_services/
│   │   │   ├── CosmosdbService.py
│   │   │   ├── ServicebusService.py
│   │   │   ├── IothubService.py
│   │   │   ├── BlobstorageService.py
│   │   │   ├── NotificationService.py
│   │   │   ├── VisionService.py
│   │   │   ├── CommunicationService.py
│   │   │   └── EventtopicService.py
│   │   ├── config/
│   │   │   ├── azure_config.py (Environment variable loading)
│   │   │   ├── jwt_utils.py (JWT creation/validation)
│   │   │   ├── password_utils.py (bcrypt hashing)
│   │   │   └── sas_utils.py (SAS token generation)
│   │   ├── functions/
│   │   │   ├── user_functions.py (User CRUD + login)
│   │   │   ├── device_functions.py (Device CRUD)
│   │   │   ├── telemetry_functions.py (Telemetry CRUD)
│   │   │   ├── condition_functions.py (Alert rules CRUD)
│   │   │   ├── alertlogs.py (Alert logs CRUD)
│   │   │   └── admin_functions.py (Admin operations)
│   │   ├── listeners/
│   │   │   ├── servicebus_listener.py (Process queued telemetry)
│   │   │   └── blobstorage_listener.py (Image analysis trigger)
│   │   ├── scheduled/
│   │   │   └── trigger_functions.py (Daily cleanup cron)
│   │   ├── swagger/
│   │   │   └── swagger.yaml (OpenAPI 3.0.1 spec)
│   │   └── json_data/ (Sample data files)
│   └── karate-tests/ (API testing framework)
├── infra/ (Bicep Infrastructure as Code)
│   ├── main.bicep (Main orchestrator)
│   ├── parameters.dev.json
│   └── modules/ (13 module files for each Azure resource)
└── prepare_kv.sh (Key Vault setup script)
```

---

## 2. BACKEND FUNCTIONS - COMPLETE REFERENCE

### 2.1 Main Entry Point
**File:** `function_app.py`

**All HTTP Routes:**

| Method | Route | Function | Auth Required |
|--------|-------|----------|---------------|
| GET | `/ping` | Health check | No |
| GET | `/swagger` | Return swagger.yaml | No |
| GET | `/swagger-ui` | Swagger UI HTML | No |
| POST | `/user` | Register user | No |
| GET | `/user` | Get user profile | Yes |
| PUT | `/user` | Update user profile | Yes |
| PATCH | `/user` | Change password | No (requires old password) |
| DELETE | `/user` | Delete user account | Yes |
| POST | `/user/login` | User authentication | No |
| POST | `/device` | Register device | Yes |
| GET | `/devices` | List/filter devices | Yes |
| PUT/PATCH | `/device` | Update device | Yes |
| DELETE | `/device` | Delete device | Yes |
| POST | `/telemetry` | Submit telemetry data | No (device auth via deviceId) |
| GET | `/telemetry` | Query telemetry data | Yes |
| DELETE | `/telemetry` | Delete telemetry event | Yes |
| POST | `/conditions` | Create alert rule | Yes |
| GET | `/conditions` | List alert rules | Yes |
| PUT | `/conditions` | Update alert rule | Yes |
| DELETE | `/conditions` | Delete alert rule | Yes |
| GET | `/alertlogs` | List alert history | Yes |
| DELETE | `/alertlogs` | Delete alert log | Yes |
| GET | `/manage/users` | List all users (admin) | Yes (admin) |
| PUT | `/manage/change-user-type` | Change user role (admin) | Yes (admin) |
| POST | `/manage/create-admin` | Create admin user | No |
| GET | `/manage/processed-images` | List/get images (admin) | Yes (admin) |
| POST | `/manage/transfer-device` | Transfer device ownership (admin) | Yes (admin) |

**Triggered Functions:**
- **ServiceBusListenerFunction**: Service Bus Queue trigger on `cst8922servicebusqueue`
- **BlobTriggerListener**: Blob trigger on `telemetry-images` container
- **ScheduledCleanup**: Timer trigger `0 0 0 * * *` (daily at midnight UTC)

---

### 2.2 User Functions
**File:** `functions/user_functions.py`

**Functions:**
```python
def register_user(req: HttpRequest) -> HttpResponse:
    """
    POST /user - Register new user
    Required fields: username, name, surname, email, password
    Optional: address, phone, emergencyContact
    Returns: 201 with JWT token and userId
    Creates user with bcrypt hashed password and embedded empty Devices array
    """

def login_user(req: HttpRequest) -> HttpResponse:
    """
    POST /user/login - Authenticate user
    Required: email, password
    Returns: 200 with JWT token
    Verifies password with bcrypt, generates JWT with 1-hour expiry
    """

def get_user(req: HttpRequest) -> HttpResponse:
    """
    GET /user - Get user profile
    Auth: Bearer JWT
    Returns: User object (password excluded)
    """

def update_user(req: HttpRequest) -> HttpResponse:
    """
    PUT /user - Update user profile
    Auth: Bearer JWT
    Query param: userId (optional, admin only to update other users)
    Returns: 200 on success
    Uses MongoDB $set operator
    """

def change_password(req: HttpRequest) -> HttpResponse:
    """
    PATCH /user - Change password
    Required: email, oldPassword, newPassword
    No JWT required but validates old password
    Returns: 200 on success
    """

def delete_user(req: HttpRequest) -> HttpResponse:
    """
    DELETE /user - Delete user account
    Auth: Bearer JWT
    Query param: userId (optional, admin only)
    Side effect: Deletes all user's devices from Azure IoT Hub
    Returns: 200 on success
    """
```

**Database Operations:**
- `cosmos_service.insert_document(user_data)` - Create user
- `cosmos_service.find_document({"email": email})` - Login lookup
- `cosmos_service.find_document({"_id": user_id})` - Get user
- `cosmos_service.update_document({"_id": user_id}, {"$set": {...}})` - Update user
- `cosmos_service.delete_document({"_id": user_id})` - Delete user

**IoT Hub Integration:**
- `iothub_service.delete_device_from_iot_hub([device_ids])` - Bulk device deletion on user delete

---

### 2.3 Device Functions
**File:** `functions/device_functions.py`

**Functions:**
```python
def register_device(req: HttpRequest) -> HttpResponse:
    """
    POST /device - Register device
    Auth: Bearer JWT
    Required: deviceId, deviceName, sensorType, location.name
    Optional: location.longitude, location.latitude, telemetryData, status
    Side effects:
    - Registers device in Azure IoT Hub with SAS authentication
    - Adds device to user's Devices array in Cosmos DB
    Returns: 201 on success
    """

def get_devices(req: HttpRequest) -> HttpResponse:
    """
    GET /devices - Get user's devices
    Auth: Bearer JWT
    Query params (optional): deviceId, deviceName, sensorType, location
    Returns: Array of devices or single device if deviceId specified
    Uses projection to filter devices array by query params
    """

def update_device(req: HttpRequest) -> HttpResponse:
    """
    PUT/PATCH /device?deviceId=xxx - Update device
    Auth: Bearer JWT
    Query param: deviceId (required)
    Updatable fields: deviceName, sensorType, location, status
    Uses MongoDB $set with positional operator: {"Devices.$": updated_device}
    Returns: 200 on success
    """

def delete_device(req: HttpRequest) -> HttpResponse:
    """
    DELETE /device - Delete device
    Auth: Bearer JWT
    Required: deviceId in body
    Side effects:
    - Deletes device from Azure IoT Hub
    - Removes device from user's Devices array using $pull
    Returns: 200 on success
    """
```

**Database Operations:**
- `cosmos_service.update_document({"_id": user_id}, {"$push": {"Devices": device}})` - Add device
- `cosmos_service.find_document({"_id": user_id})` - Get user with devices
- `cosmos_service.update_document({"_id": user_id, "Devices.deviceId": device_id}, {"$set": {"Devices.$": updated}})` - Update device
- `cosmos_service.update_document({"_id": user_id}, {"$pull": {"Devices": {"deviceId": device_id}}})` - Delete device

**IoT Hub Integration:**
- `iothub_service.register_device_in_iot_hub(device_data)` - Register device
- `iothub_service.delete_device_from_iot_hub(device_id)` - Delete device

---

### 2.4 Telemetry Functions
**File:** `functions/telemetry_functions.py`

**Functions:**
```python
def post_telemetry(req: HttpRequest) -> HttpResponse:
    """
    POST /telemetry - Submit telemetry data
    No JWT auth (devices post directly)
    Content-Type: multipart/form-data OR application/json

    Multipart fields:
    - deviceId: string (optional if in values)
    - values: JSON string array
    - image: binary file (optional)

    JSON body (single or array):
    {
        "deviceId": "string",
        "values": [{"valueType": "string", "value": number, ...}]
    }

    Process:
    1. Validate deviceId exists in database
    2. Generate eventId (UUID)
    3. Upload image to Blob Storage if provided (filename: {event_date}_{event_id}_{device_id}.ext)
    4. Send telemetry message to Service Bus Queue for async processing
    5. Return 202 Accepted immediately

    Returns: 202 with eventId and imageUrl (if uploaded)
    """

def get_telemetry(req: HttpRequest) -> HttpResponse:
    """
    GET /telemetry?deviceId=xxx - Get telemetry history
    Auth: Bearer JWT
    Query params: deviceId (required), eventId, sensorType, eventDate (optional filters)
    Returns: Array of telemetry objects from user's Devices[].telemetryData
    """

def delete_telemetry(req: HttpRequest) -> HttpResponse:
    """
    DELETE /telemetry - Delete telemetry event
    Auth: Bearer JWT
    Required: eventId in body
    Uses $pull to remove from Devices.$.telemetryData array
    Returns: 200 on success
    """
```

**Service Bus Operations:**
```python
# Message format sent to queue
message = {
    "deviceId": device_id,
    "userId": user_id,
    "eventId": event_id,
    "event_date": datetime.now(timezone.utc).isoformat(),
    "values": [
        {
            "valueType": "temperature",
            "value": 25.5,
            "longitude": "optional",
            "latitude": "optional"
        }
    ]
}
servicebus_service.send_message("cst8922servicebusqueue", json.dumps(message))
```

**Blob Storage Operations:**
```python
# Upload image
image_filename = f"{event_date}_{event_id}_{device_id}.{extension}"
blob_service.upload_image(image_data, image_filename)
```

---

### 2.5 Condition Functions
**File:** `functions/condition_functions.py`

**Functions:**
```python
def get_conditions(req: HttpRequest) -> HttpResponse:
    """
    GET /conditions - List alert rules
    Auth: Bearer JWT
    Optional body: {"deviceId": "string"} to filter
    Returns conditions where:
    - scope="general" (userId="" and deviceId="")
    - scope="user" (userId=current, deviceId="")
    - scope="device" (deviceId=specified)
    """

def create_condition(req: HttpRequest) -> HttpResponse:
    """
    POST /conditions - Create alert rule
    Auth: Bearer JWT
    Required: valueType
    Optional: minValue, maxValue, exactValue, unit, conditionType, notificationMethods
    Accepts single object or array
    Validates at least one threshold (min/max/exact) exists
    Stores in Conditions collection with scope logic:
    - conditionType="general" → userId="", deviceId=""
    - conditionType="user" → userId=current, deviceId=""
    - conditionType="device" → userId="", deviceId=from_request
    Returns: 201 with created conditions
    """

def update_condition(req: HttpRequest) -> HttpResponse:
    """
    PUT /conditions - Update alert rule
    Auth: Bearer JWT
    Required: conditionId (ObjectId)
    Updatable: valueType, minValue, maxValue, exactValue, unit, notificationMethods
    Uses $set operator
    Returns: 200 on success
    """

def delete_condition(req: HttpRequest) -> HttpResponse:
    """
    DELETE /conditions - Delete alert rule
    Auth: Bearer JWT
    Required: conditionId (ObjectId)
    Authorization: Admins can delete any, users can only delete own or global conditions
    Returns: 200 on success
    """
```

**Database Operations:**
```python
# Query conditions
cosmos_service.find_documents(
    {
        "$or": [
            {"scope": "general"},
            {"userId": user_id, "scope": "user"},
            {"deviceId": device_id, "scope": "device"}
        ]
    },
    "Conditions"
)

# Create condition
cosmos_service.insert_document(condition_data, "Conditions")

# Update condition
cosmos_service.update_document(
    {"_id": ObjectId(condition_id)},
    {"$set": update_fields},
    "Conditions"
)

# Delete condition
cosmos_service.delete_document({"_id": ObjectId(condition_id)}, "Conditions")
```

---

### 2.6 Alert Log Functions
**File:** `functions/alertlogs.py`

**Functions:**
```python
def get_alertlogs(req: HttpRequest) -> HttpResponse:
    """
    GET /alertlogs - Get alert history
    Auth: Bearer JWT
    Query param: deviceId (optional filter)
    Returns: Array of alert logs for current user
    Query: {"user_id": user_id} or {"user_id": user_id, "deviceId": device_id}
    """

def delete_alertlog(req: HttpRequest) -> HttpResponse:
    """
    DELETE /alertlogs - Delete alert log
    Auth: Bearer JWT
    Required: alertLogId (ObjectId)
    Returns: 200 on success
    """
```

**Database Operations:**
```python
# Query alert logs
cosmos_service.find_documents({"user_id": user_id}, "AlertLogs")

# Delete alert log
cosmos_service.delete_document({"_id": ObjectId(alert_log_id)}, "AlertLogs")
```

---

### 2.7 Admin Functions
**File:** `functions/admin_functions.py`

**Functions:**
```python
def get_all_users(req: HttpRequest) -> HttpResponse:
    """
    GET /manage/users - List all users (admin only)
    Auth: Bearer JWT (admin)
    Query params: userId, username, email, phone (optional filters)
    Returns: Array of users with passwords removed
    """

def change_user_type(req: HttpRequest) -> HttpResponse:
    """
    PUT /manage/change-user-type?userId=xxx&userType=admin - Change user role
    Auth: Bearer JWT (admin)
    Query params: userId, userType ("user" or "admin")
    Uses $set to update type field
    Returns: 200 on success
    """

def create_admin_user(req: HttpRequest) -> HttpResponse:
    """
    POST /manage/create-admin - Create admin user
    No auth required (for initial setup)
    Same as register_user but sets type="admin"
    Returns: 201 with JWT token
    """

def get_processed_images(req: HttpRequest) -> HttpResponse:
    """
    GET /manage/processed-images - List or get specific image (admin only)
    Auth: Bearer JWT (admin)
    Query params: prefix, imageName, imageUrl, deviceId
    Modes:
    - No params: List all blobs in processed-images container
    - prefix: List blobs with prefix
    - imageName: Get specific blob with SAS URL
    - imageUrl: Extract blob name and return SAS URL
    - deviceId: List images for device (prefix=deviceId/)
    Returns: {"files": [...], "directories": [...]} or {"imageUrl": "SAS URL"}
    """

def transfer_device(req: HttpRequest) -> HttpResponse:
    """
    POST /manage/transfer-device?deviceId=xxx&newUserId=yyy - Transfer device ownership
    Auth: Bearer JWT (admin)
    Query params: deviceId, newUserId
    Process:
    1. Find device in old user's Devices array
    2. Remove from old user using $pull
    3. Add to new user using $push
    Returns: 200 with deviceId, oldUserId, newUserId
    """
```

---

### 2.8 Service Bus Listener (Event-Driven)
**File:** `listeners/servicebus_listener.py`

**Trigger:** Service Bus Queue `cst8922servicebusqueue`

```python
@app.service_bus_queue_trigger(
    arg_name="msg",
    queue_name="cst8922servicebusqueue",
    connection="SERVICE_BUS_CONNECTION_STRING"
)
def ServiceBusListenerFunction(msg: func.ServiceBusMessage):
    """
    Processes telemetry messages from Service Bus Queue

    Message format:
    {
        "deviceId": "string",
        "userId": "UUID",
        "eventId": "UUID",
        "event_date": "ISO 8601",
        "values": [{"valueType": "string", "value": number, ...}]
    }

    Process:
    1. Parse message body
    2. Find user in Cosmos DB
    3. Update user's Devices.$.telemetryData array (MongoDB $push)
    4. Query all conditions from Conditions collection
    5. For each value in telemetry:
        a. Filter conditions by valueType
        b. Apply scope filtering (general/user/device)
        c. Check thresholds (minValue, maxValue, exactValue)
        d. If violated: notify_user()
    6. Forward telemetry to IoT Hub Event Grid

    notify_user():
    - For each notificationMethods in condition:
        - "Log": Insert into AlertLogs collection
        - "Email": Send via CommunicationService
        - "Notification": Send via NotificationService (currently commented out)
        - "SMS": Not implemented
    """
```

**Key Logic:**
```python
# Condition evaluation
for value in telemetry["values"]:
    value_type = value["valueType"]
    value_data = int(value["value"])

    conditions = cosmos_service.find_documents(
        {"valueType": value_type},
        "Conditions"
    )

    for condition in conditions:
        # Apply scope filtering
        if condition["scope"] == "user" and condition["userId"] != user["userId"]:
            continue
        if condition["scope"] == "device" and condition["deviceId"] != device_id:
            continue

        # Check thresholds
        if condition.get("minValue") and value_data < condition["minValue"]:
            notify_user(condition, message, user, device_id, telemetry["values"])

        if condition.get("maxValue") and value_data > condition["maxValue"]:
            notify_user(condition, message, user, device_id, telemetry["values"])

        if condition.get("exactValue") and value_data != condition["exactValue"]:
            notify_user(condition, message, user, device_id, telemetry["values"])
```

---

### 2.9 Blob Storage Listener (Event-Driven)
**File:** `listeners/blobstorage_listener.py`

**Trigger:** Blob uploads to `telemetry-images` container

```python
@app.blob_trigger(
    arg_name="blob",
    path="telemetry-images/{name}",
    connection="AZURE_STORAGE_CONNECTION_STRING"
)
async def BlobTriggerListener(blob: func.InputStream):
    """
    Processes uploaded images with Computer Vision

    Blob name format: {event_date}_{event_id}_{device_id}.{ext}

    Process:
    1. Generate SAS URL for blob
    2. Call VisionService.analyze_image(sas_url)
    3. If content detected (fire, animal, human, flood, thunder):
        a. Move blob to processed-images/{deviceId}/ container
        b. Update telemetry in Cosmos DB with imageUrl field (retry 5 times with exponential backoff)
        c. Query user by deviceId
        d. Send email alert with detection details and image link
    4. Return analysis result

    Detection categories:
    - fire: High severity
    - flood: High severity
    - thunder: Medium severity
    - animal: Low severity
    - human: Low severity
    - other: Not alerted

    Email format:
    - Subject: "{content_type} Alert Detected!"
    - Body: HTML with event details, severity, instructions, image URL
    """
```

**Retry Logic:**
```python
max_retries = 5
retry_delay = 2  # seconds

for attempt in range(max_retries):
    try:
        cosmos_service.update_document(
            {
                "_id": user_id,
                "Devices.telemetryData.eventId": event_id
            },
            {
                "$set": {
                    "Devices.$[].telemetryData.$[elem].imageUrl": processed_blob_name
                }
            },
            array_filters=[{"elem.eventId": event_id}]
        )
        break
    except Exception:
        if attempt < max_retries - 1:
            time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
```

---

### 2.10 Scheduled Cleanup
**File:** `scheduled/trigger_functions.py`

**Trigger:** Timer `0 0 0 * * *` (daily at midnight UTC)

```python
@app.timer_trigger(
    arg_name="timer_info",
    schedule="0 0 0 * * *",
    run_on_startup=False
)
def scheduled_cleanup(timer_info):
    """
    Daily cleanup of old uploaded images

    Process:
    1. Query all users from Cosmos DB
    2. For each user's uploadedImages array:
        a. Parse upload date from blob name format
        b. Calculate age
        c. If older than 24 hours:
            - Delete blob from storage
            - Remove from uploadedImages array
    3. Update user document with remaining images

    Purpose: Manage storage costs by removing old images
    Note: Processed images are not cleaned up
    """
```

---

## 3. SERVICE CLASSES - COMPLETE API

### 3.1 CosmosDBService
**File:** `azure_services/CosmosdbService.py`

**Connection:**
```python
class CosmosDBService:
    def __init__(self):
        connection_string = COSMOS_DB_CONNECTION_STRING
        client = MongoClient(
            connection_string,
            tls=True,
            tlsAllowInvalidCertificates=True,
            maxPoolSize=50,
            retryWrites=False,  # Cosmos DB limitation
            serverSelectionTimeoutMS=30000
        )
        self.db = client[COSMOS_DB_NAME]
        self.default_collection = COSMOS_USERS_COLLECTION
```

**Methods:**
```python
def insert_document(self, document: dict, collection_name: str = None) -> InsertOneResult:
    """Insert single document. Returns InsertOneResult with inserted_id."""
    collection = self.db[collection_name or self.default_collection]
    return collection.insert_one(document)

def find_document(self, query: dict, collection_name: str = None) -> dict | None:
    """Find single document matching query. Returns dict or None."""
    collection = self.db[collection_name or self.default_collection]
    return collection.find_one(query)

def update_document(self, query: dict, update: dict, collection_name: str = None) -> UpdateResult:
    """
    Update document using MongoDB operators.
    Examples:
    - {"$set": {"field": "value"}}
    - {"$push": {"Devices": device_obj}}
    - {"$pull": {"Devices": {"deviceId": "123"}}}
    Returns UpdateResult with matched_count, modified_count.
    """
    collection = self.db[collection_name or self.default_collection]
    return collection.update_one(query, update)

def delete_document(self, query: dict, collection_name: str = None) -> DeleteResult:
    """Delete single document. Returns DeleteResult with deleted_count."""
    collection = self.db[collection_name or self.default_collection]
    return collection.delete_one(query)

def find_documents(self, query: dict, collection_name: str = None) -> list[dict]:
    """Find multiple documents. Returns list of dicts."""
    collection = self.db[collection_name or self.default_collection]
    return list(collection.find(query))
```

**Collections Used:**
- `Users` (default) - User documents with embedded Devices array
- `Conditions` - Alert condition rules
- `AlertLogs` - Alert history
- `Logs` - System logs

---

### 3.2 ServiceBusService
**File:** `azure_services/ServicebusService.py`

```python
class ServiceBusService:
    def __init__(self):
        self.client = ServiceBusClient.from_connection_string(
            SERVICE_BUS_CONNECTION_STRING
        )

    def send_message(self, queue_name: str, message_body: str):
        """
        Send message to queue.
        Args:
            queue_name: "cst8922servicebusqueue"
            message_body: JSON string
        """
        with self.client:
            sender = self.client.get_queue_sender(queue_name)
            with sender:
                message = ServiceBusMessage(message_body)
                sender.send_messages(message)

    def receive_messages(self, queue_name: str, max_message_count: int = 1) -> list[str]:
        """
        Receive and complete messages from queue.
        Returns: List of message bodies (JSON strings)
        """
        with self.client:
            receiver = self.client.get_queue_receiver(queue_name)
            with receiver:
                messages = receiver.receive_messages(
                    max_message_count=max_message_count,
                    max_wait_time=5
                )
                for msg in messages:
                    receiver.complete_message(msg)
                return [str(msg) for msg in messages]
```

---

### 3.3 IoTHubService
**File:** `azure_services/IothubService.py`

```python
class IoTHubService:
    def __init__(self):
        self.registry_manager = IoTHubRegistryManager.from_connection_string(
            IOTHUB_CONNECTION_STRING
        )

    def register_device_in_iot_hub(self, device_data: dict) -> dict:
        """
        Register device with SAS authentication.
        Args:
            device_data: {"deviceId": "string", ...}
        Returns: {"message": "Device registered" or "already exists"}
        """
        device_id = device_data["deviceId"]

        try:
            # Check if exists
            self.registry_manager.get_device(device_id)
            return {"message": "Device already registered in IoT Hub"}
        except:
            # Create device
            device = Device(
                device_id=device_id,
                authentication=AuthenticationMechanism(type="sas")
            )
            self.registry_manager.create_device(device)
            return {"message": "Device registered in IoT Hub"}

    def delete_device_from_iot_hub(self, device_id: str | list) -> dict:
        """
        Delete device(s) from IoT Hub.
        Args:
            device_id: Single device ID string or list of device IDs
        Returns: {"deleted": [...], "failed": [...]}
        """
        if isinstance(device_id, list):
            deleted = []
            failed = []
            for dev_id in device_id:
                try:
                    self.registry_manager.delete_device(dev_id)
                    deleted.append(dev_id)
                except Exception as e:
                    failed.append({"deviceId": dev_id, "error": str(e)})
            return {"deleted": deleted, "failed": failed}
        else:
            self.registry_manager.delete_device(device_id)
            return {"deleted": [device_id]}

    def send_telemetry_to_event_hub(self, device_id: str, telemetry_data: dict):
        """Forward telemetry to Event Grid via EventtopicService."""
        forward_event(telemetry_data)
```

---

### 3.4 BlobStorageService
**File:** `azure_services/BlobstorageService.py`

```python
class BlobStorageService:
    def __init__(self):
        self.blob_service_client = BlobServiceClient.from_connection_string(
            AZURE_STORAGE_CONNECTION_STRING
        )
        self.container_name = BLOB_CONTAINER_NAME  # "telemetry-images"

    def upload_image(self, image_data: bytes, blob_path: str):
        """
        Upload image to Blob Storage.
        Args:
            image_data: Binary image data
            blob_path: Filename in container (e.g., "2024-01-15_uuid_device123.jpg")
        """
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob_path
        )
        blob_client.upload_blob(image_data, overwrite=True)

    def generate_sas_url(self, container_or_path: str, blob_name: str = None) -> str:
        """
        Generate SAS URL with read permission.
        Args:
            container_or_path: Container name or full blob path
            blob_name: Blob name if container_or_path is container
        Returns: Full URL with SAS token (valid for 1 hour)
        """
        if blob_name:
            blob_client = self.blob_service_client.get_blob_client(
                container=container_or_path,
                blob=blob_name
            )
        else:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=container_or_path
            )

        sas_token = generate_blob_sas(
            account_name=AZURE_STORAGE_ACCOUNT_NAME,
            container_name=blob_client.container_name,
            blob_name=blob_client.blob_name,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.utcnow() + timedelta(hours=1)
        )

        return f"{blob_client.url}?{sas_token}"
```

**Containers:**
- `telemetry-images` - Incoming images from devices
- `processed-images` - Images after Computer Vision analysis (organized by deviceId/)

---

### 3.5 NotificationService
**File:** `azure_services/NotificationService.py`

```python
class NotificationService:
    def __init__(self):
        # Parse Notification Hub connection string
        conn_parts = NOTIFICATION_HUB_CONNECTION_STRING.split(";")
        self.endpoint = None
        self.sas_key_name = None
        self.sas_key_value = None

        for part in conn_parts:
            if "Endpoint=" in part:
                self.endpoint = part.split("=", 1)[1]
            elif "SharedAccessKeyName=" in part:
                self.sas_key_name = part.split("=", 1)[1]
            elif "SharedAccessKey=" in part:
                self.sas_key_value = part.split("=", 1)[1]

    def send_notification(self, message: str, device_id: str = None, values: list = None):
        """
        Send Apple Push Notification.
        Args:
            message: Alert message text
            device_id: Device ID (optional)
            values: Telemetry values (optional)
        Format: {"aps": {"alert": "...", "sound": "default"}, "deviceId": "...", "message": "..."}
        """
        payload = {
            "aps": {
                "alert": message,
                "sound": "default"
            },
            "deviceId": device_id,
            "message": message,
            "values": values
        }

        sas_token = self._generate_sas_token()
        url = f"{self.endpoint}{NOTIFICATION_HUB_NAMESPACE}/messages/?api-version=2015-01"

        headers = {
            "Authorization": sas_token,
            "Content-Type": "application/json;charset=utf-8",
            "ServiceBusNotification-Format": "apple"
        }

        requests.post(url, headers=headers, data=json.dumps(payload))

    def _generate_sas_token(self) -> str:
        """Generate SharedAccessSignature for Notification Hub (valid 5 minutes)."""
        uri = f"{self.endpoint}{NOTIFICATION_HUB_NAMESPACE}/messages"
        expiry = int(time.time() + 3000)  # 3000 seconds

        string_to_sign = f"{uri}\n{expiry}"
        signature = hmac.new(
            self.sas_key_value.encode(),
            string_to_sign.encode(),
            hashlib.sha256
        ).digest()
        signature_b64 = base64.b64encode(signature).decode()

        return f"SharedAccessSignature sr={uri}&sig={signature_b64}&se={expiry}&skn={self.sas_key_name}"
```

---

### 3.6 VisionService (Computer Vision)
**File:** `azure_services/VisionService.py`

```python
class VisionService:
    def __init__(self):
        self.client = ComputerVisionClient(
            COGNITIVE_SERVICE_ENDPOINT,
            CognitiveServicesCredentials(COGNITIVE_SERVICE_KEY)
        )

    async def analyze_image(self, image_url: str) -> dict:
        """
        Analyze image with Computer Vision API.
        Args:
            image_url: Blob SAS URL
        Returns: {
            "content_type": "fire" | "animal" | "human" | "flood" | "thunder" | "other",
            "confidence": float (0-1),
            "description": "string"
        }
        """
        features = [VisualFeatureTypes.tags, VisualFeatureTypes.description]
        analysis = self.client.analyze_image(image_url, visual_features=features)

        return await self.detect_image_content(analysis)

    async def detect_image_content(self, analysis_result) -> dict:
        """
        Detect specific content types from CV results.

        Detection keywords:
        - fire: ["fire", "flame", "smoke", "burning", "blaze"]
        - animal: ["animal", "dog", "cat", "bird", "wildlife", "pet", "horse", "cow", "sheep", "lion", "tiger"]
        - human: ["person", "people", "human", "man", "woman", "child", "face", "portrait"]
        - flood: ["flood", "flooding", "water", "submerged", "inundation"]
        - thunder: ["lightning", "thunder", "storm", "thunderstorm", "electrical storm"]

        Minimum confidence: 0.5
        Priority order: fire > flood > thunder > animal > human > other
        """
        # Check tags
        for tag in analysis_result.tags:
            if tag.confidence > 0.5:
                tag_name = tag.name.lower()

                if any(kw in tag_name for kw in ["fire", "flame", "smoke", "burning", "blaze"]):
                    return {"content_type": "fire", "confidence": tag.confidence, "description": analysis_result.description.captions[0].text}

                # ... similar checks for other types

        # Fallback to description
        if analysis_result.description.captions:
            description = analysis_result.description.captions[0].text.lower()
            # ... keyword checks in description

        return {"content_type": "other", "confidence": 0.0, "description": "No specific content detected"}
```

---

### 3.7 CommunicationService (Email)
**File:** `azure_services/CommunicationService.py`

```python
class CommunicationService:
    def __init__(self):
        self.email_client = EmailClient.from_connection_string(
            COMMUNICATION_SERVICE_CONNECTION_STRING
        )

    def send_email(self, recipient_email: str, subject: str, body: str, html_body: str = None):
        """
        Send email via Azure Communication Services.
        Args:
            recipient_email: Recipient email address
            subject: Email subject
            body: Plain text body
            html_body: HTML body (optional)
        Returns: Result with message_id
        """
        # Validate email
        if not recipient_email or "@" not in recipient_email:
            raise ValueError("Invalid recipient email")

        message = {
            "content": {
                "subject": subject,
                "plainText": body,
                "html": html_body or body
            },
            "recipients": {
                "to": [{"address": recipient_email}]
            },
            "senderAddress": COMMUNICATION_SERVICE_SENDER_EMAIL
        }

        poller = self.email_client.begin_send(message)
        result = poller.result()
        return result
```

---

### 3.8 EventTopicService (Event Grid)
**File:** `azure_services/EventtopicService.py`

```python
def forward_event(event_data: dict):
    """
    Publish event to Event Grid Topic.
    Args:
        event_data: Telemetry data dict
    Event structure:
        - subject: "Device/{device_id}"
        - event_type: "IoT.DeviceTelemetry"
        - data_version: "1.0"
        - data: event_data
    """
    credential = AzureKeyCredential(EVENTGRID_TOPIC_KEY)
    client = EventGridPublisherClient(EVENTGRID_TOPIC_ENDPOINT, credential)

    event = EventGridEvent(
        subject=f"Device/{event_data.get('deviceId', 'unknown')}",
        event_type="IoT.DeviceTelemetry",
        data=event_data,
        data_version="1.0"
    )

    client.send(event)
```

---

## 4. CONFIGURATION & ENVIRONMENT VARIABLES

**File:** `config/azure_config.py`

**Required Environment Variables:**
```python
SERVICE_BUS_CONNECTION_STRING          # Format: Endpoint=sb://...;SharedAccessKeyName=...;SharedAccessKey=...
COSMOS_DB_CONNECTION_STRING            # Format: mongodb://...?ssl=true&...
COMMUNICATION_SERVICE_CONNECTION_STRING # Format: endpoint=https://...;accesskey=...
COMMUNICATION_SERVICE_SENDER_EMAIL     # Example: DoNotReply@xxx.azurecomm.net
IOTHUB_CONNECTION_STRING               # Format: HostName=...;SharedAccessKeyName=...;SharedAccessKey=...
EVENTGRID_TOPIC_ENDPOINT               # Format: https://...eventgrid.azure.net/api/events
EVENTGRID_TOPIC_KEY                    # Access key for Event Grid
NOTIFICATION_HUB_CONNECTION_STRING     # Format: Endpoint=sb://...;SharedAccessKeyName=...;SharedAccessKey=...
JWT_SECRET                             # Secret key for JWT signing (any string)
COGNITIVE_SERVICE_ENDPOINT             # Format: https://...cognitiveservices.azure.com/
COGNITIVE_SERVICE_KEY                  # Access key for Computer Vision
AZURE_STORAGE_CONNECTION_STRING        # Format: DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...
AZURE_STORAGE_ACCOUNT_NAME             # Storage account name (for SAS generation)
```

**Optional (with defaults):**
```python
SERVICE_BUS_QUEUE_NAME = "cst8922servicebusqueue"
COSMOS_DB_NAME = "TelemetryDB"
COSMOS_USERS_COLLECTION = "Users"
COSMOS_CONDITIONS_COLLECTION = "Conditions"
COSMOS_ALERT_COLLECTION = "AlertLogs"
COSMOS_LOGS_COLLECTION = "Logs"
NOTIFICATION_HUB_NAMESPACE = "telemetryns"
NOTIFICATION_HUB_NAME = "telemetryhub"
JWT_ALGORITHM = "HS256"
BLOB_CONTAINER_NAME = "telemetry-images"
BLOB_CONTAINER_PROCESSED_IMAGES = "processed-images"
```

**JWT Configuration:**
```python
# File: config/jwt_utils.py
JWT_EXPIRY_HOURS = 1  # Tokens expire after 1 hour

def create_token(user_id: str) -> str:
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def authenticate_user(req: HttpRequest, return_http_response: bool = True):
    # Extracts "Authorization: Bearer <token>" header
    # Decodes JWT with JWT_SECRET
    # Returns user_id or 401 HttpResponse
```

**Password Configuration:**
```python
# File: config/password_utils.py
# Uses bcrypt with auto-generated salt

def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
```

---

## 5. DATA MODELS - COMPLETE SCHEMAS

### 5.1 Users Collection (Cosmos DB)
**Collection:** `Users` (default collection)

```json
{
    "_id": "UUID (userId)",
    "userId": "UUID",
    "username": "string (unique, required)",
    "name": "string (required)",
    "surname": "string (required)",
    "address": "string (optional)",
    "phone": "string (optional)",
    "email": "string (unique, required)",
    "emergencyContact": "string (optional)",
    "password": "bcrypt hashed string (required)",
    "authToken": "JWT string (generated on login/register)",
    "type": "user" | "admin" (default: "user")",
    "Devices": [
        {
            "deviceId": "string (unique in IoT Hub)",
            "deviceName": "string",
            "sensorType": "string",
            "location": {
                "name": "string (required)",
                "longitude": "string (optional)",
                "latitude": "string (optional)"
            },
            "registrationDate": "ISO 8601 timestamp",
            "telemetryData": [
                {
                    "deviceId": "string",
                    "userId": "string (UUID)",
                    "eventId": "UUID (unique)",
                    "event_date": "ISO 8601 timestamp",
                    "values": [
                        {
                            "valueType": "string (e.g., temperature, humidity)",
                            "value": "number",
                            "longitude": "string (optional)",
                            "latitude": "string (optional)"
                        }
                    ],
                    "imageUrl": "string (blob filename, added by Blob Listener)"
                }
            ],
            "status": [
                {
                    "valueType": "string",
                    "value": "number"
                }
            ]
        }
    ],
    "uploadedImages": ["string (blob filenames, cleaned up after 24 hours)"]
}
```

**Indexes:**
- Primary: `_id` (shard key = userId)
- Unique: `username`, `email`
- Query: `Devices.deviceId` (for lookup by device)

---

### 5.2 Conditions Collection
**Collection:** `Conditions`

```json
{
    "_id": "MongoDB ObjectId",
    "type": "condition" (constant value),
    "userId": "UUID or empty string",
    "deviceId": "string or empty string",
    "valueType": "string (e.g., temperature, humidity)",
    "minValue": "number (optional)",
    "maxValue": "number (optional)",
    "exactValue": "number (optional)",
    "unit": "string (e.g., Celsius, %, optional)",
    "scope": "general" | "user" | "device",
    "notificationMethods": ["Log", "Notification", "Email", "SMS"]
}
```

**Scope Logic:**
- `scope="general"`: Applies to all telemetry (userId="" and deviceId="")
- `scope="user"`: Applies to all devices of a user (userId=UUID, deviceId="")
- `scope="device"`: Applies to specific device (userId="", deviceId="string")

**Validation:**
- At least one threshold (minValue, maxValue, exactValue) must be present
- valueType is required

---

### 5.3 AlertLogs Collection
**Collection:** `AlertLogs`

```json
{
    "_id": "MongoDB ObjectId",
    "deviceId": "string",
    "user_id": "UUID",
    "message": "string (human-readable alert description)",
    "condition": {
        "_id": "ObjectId",
        "type": "condition",
        "userId": "string",
        "deviceId": "string",
        "valueType": "string",
        "minValue": "number",
        "maxValue": "number",
        "exactValue": "number (optional)",
        "unit": "string",
        "scope": "string",
        "notificationMethods": ["string"]
    },
    "telemetry_data": [
        {
            "valueType": "string",
            "value": "number",
            "longitude": "string (optional)",
            "latitude": "string (optional)"
        }
    ],
    "timestamp": "ISO 8601 timestamp"
}
```

**Created By:** Service Bus Listener when condition violated and "Log" in notificationMethods

---

## 6. API CONTRACTS - COMPLETE REFERENCE

### 6.1 User Authentication

#### POST `/user/login`
**Auth:** None
**Request:**
```json
{
    "email": "user@example.com",
    "password": "plaintext"
}
```
**Response (200):**
```json
{
    "message": "Login successful",
    "token": "JWT string (1-hour expiry)"
}
```
**Errors:**
- 400: Missing email or password
- 401: Invalid credentials
- 404: User not found

#### POST `/user` (Register)
**Auth:** None
**Request:**
```json
{
    "username": "string (required)",
    "name": "string (required)",
    "surname": "string (required)",
    "address": "string (optional)",
    "phone": "string (optional)",
    "email": "string (required)",
    "emergencyContact": "string (optional)",
    "password": "string (required)"
}
```
**Response (201):**
```json
{
    "message": "User created successfully",
    "token": "JWT string",
    "userId": "UUID"
}
```
**Errors:**
- 400: Missing required fields
- 409: Username or email already exists

---

### 6.2 User Profile Management

#### GET `/user`
**Auth:** Bearer JWT
**Response (200):** User object (password excluded, authToken excluded)

#### PUT `/user`
**Auth:** Bearer JWT
**Query Params:** `userId` (optional, admin only)
**Request:** Any user fields to update (cannot update userId, password, type unless admin)
**Response (200):**
```json
{"message": "User updated successfully"}
```

#### PATCH `/user` (Change Password)
**Auth:** None (validates old password)
**Request:**
```json
{
    "email": "user@example.com",
    "oldPassword": "string",
    "newPassword": "string"
}
```
**Response (200):**
```json
{"message": "Password updated successfully"}
```

#### DELETE `/user`
**Auth:** Bearer JWT
**Query Params:** `userId` (optional, admin only)
**Side Effect:** Deletes all user's devices from Azure IoT Hub
**Response (200):**
```json
{"message": "User deleted successfully"}
```

---

### 6.3 Device Management

#### POST `/device`
**Auth:** Bearer JWT
**Request:**
```json
{
    "deviceId": "string (required)",
    "deviceName": "string (required)",
    "sensorType": "string (required)",
    "location": {
        "name": "string (required)",
        "longitude": "string (optional)",
        "latitude": "string (optional)"
    },
    "telemetryData": [] (optional),
    "status": [] (optional)
}
```
**Side Effect:** Registers device in Azure IoT Hub
**Response (201):**
```json
{"message": "Device registered successfully"}
```

#### GET `/devices`
**Auth:** Bearer JWT
**Query Params:** `deviceId`, `deviceName`, `sensorType`, `location` (optional)
**Response (200):**
```json
{
    "devices": [...],
    "count": 5,
    "userId": "UUID",
    "filters": {...},
    "timestamp": "ISO 8601"
}
```
Or for single device:
```json
{"device": {...}}
```

#### PUT/PATCH `/device?deviceId=xxx`
**Auth:** Bearer JWT
**Request:** Fields to update (deviceName, sensorType, location, status)
**Response (200):**
```json
{"message": "Device updated successfully"}
```

#### DELETE `/device`
**Auth:** Bearer JWT
**Request:**
```json
{"deviceId": "string"}
```
**Side Effect:** Deletes device from Azure IoT Hub
**Response (200):**
```json
{"message": "Device deleted successfully"}
```

---

### 6.4 Telemetry Management

#### POST `/telemetry`
**Auth:** None (validates deviceId exists)
**Content-Type:** `multipart/form-data` OR `application/json`

**Multipart:**
```
deviceId: string (optional if in values)
values: JSON string array
image: binary file (optional)
```

**JSON (single):**
```json
{
    "deviceId": "string",
    "values": [
        {
            "valueType": "string",
            "value": number,
            "longitude": "string (optional)",
            "latitude": "string (optional)"
        }
    ]
}
```

**JSON (batch):**
```json
[
    {"deviceId": "string", "values": [...]},
    ...
]
```

**Response (202 Accepted):**
```json
{
    "message": "Telemetry data sent to Service Bus Queue successfully",
    "processed": 5,
    "details": [
        {
            "status": "success",
            "message": "Telemetry data sent to queue",
            "deviceId": "string",
            "eventId": "UUID"
        }
    ],
    "eventId": "UUID (for single item)",
    "imageUrl": "blob filename (if image uploaded)"
}
```

**Process:**
1. Validate deviceId
2. Generate eventId
3. Upload image to `telemetry-images` (if provided)
4. Send message to Service Bus Queue
5. Return 202 immediately

#### GET `/telemetry?deviceId=xxx`
**Auth:** Bearer JWT
**Query Params:** `deviceId` (required), `eventId`, `sensorType`, `eventDate` (optional)
**Response (200):** Array of telemetry objects from user's Devices[].telemetryData

#### DELETE `/telemetry`
**Auth:** Bearer JWT
**Request:**
```json
{"eventId": "UUID"}
```
**Response (200):**
```json
{"message": "Telemetry data deleted successfully"}
```

---

### 6.5 Conditions (Alert Rules)

#### GET `/conditions`
**Auth:** Bearer JWT
**Request (optional):**
```json
{"deviceId": "string"}
```
**Response (200):**
```json
{
    "conditions": [
        {
            "_id": "ObjectId",
            "type": "condition",
            "userId": "string",
            "deviceId": "string",
            "valueType": "string",
            "minValue": number,
            "maxValue": number,
            "exactValue": number,
            "unit": "string",
            "scope": "general|user|device",
            "notificationMethods": ["Log", "Email", "SMS", "Notification"]
        }
    ]
}
```

#### POST `/conditions`
**Auth:** Bearer JWT
**Request (single or array):**
```json
{
    "deviceId": "string (optional, for device-level conditions)",
    "valueType": "string (required)",
    "minValue": number (optional),
    "maxValue": number (optional),
    "exactValue": number (optional),
    "unit": "string (optional)",
    "conditionType": "general" | "user" | "device",
    "notificationMethods": ["Log", "Email", "SMS", "Notification"]
}
```
**Response (201):**
```json
{
    "created_conditions": [...],
    "errors": [...] (if any)
}
```

#### PUT `/conditions`
**Auth:** Bearer JWT
**Request:**
```json
{
    "conditionId": "ObjectId (required)",
    ...fields to update
}
```
**Response (200):**
```json
{"message": "Condition updated successfully"}
```

#### DELETE `/conditions`
**Auth:** Bearer JWT
**Request:**
```json
{"conditionId": "ObjectId"}
```
**Authorization:** Admins can delete any; users can delete own or global
**Response (200):**
```json
{"message": "Condition deleted successfully"}
```

---

### 6.6 Alert Logs

#### GET `/alertlogs`
**Auth:** Bearer JWT
**Query Params:** `deviceId` (optional)
**Response (200):**
```json
{
    "alert_logs": [
        {
            "_id": "ObjectId",
            "deviceId": "string",
            "user_id": "UUID",
            "message": "string",
            "condition": {...},
            "telemetry_data": [...],
            "timestamp": "ISO 8601"
        }
    ]
}
```

#### DELETE `/alertlogs`
**Auth:** Bearer JWT
**Request:**
```json
{"alertLogId": "ObjectId"}
```
**Response (200):**
```json
{"message": "Alert log deleted successfully"}
```

---

### 6.7 Admin Functions

#### GET `/manage/users`
**Auth:** Bearer JWT (admin)
**Query Params:** `userId`, `username`, `email`, `phone` (optional)
**Response (200):** Array of users (passwords removed)

#### PUT `/manage/change-user-type?userId=xxx&userType=admin`
**Auth:** Bearer JWT (admin)
**Response (200):**
```json
{"message": "User type changed to admin successfully"}
```

#### POST `/manage/create-admin`
**Auth:** None
**Request:** Same as POST `/user`
**Response (201):** Same as POST `/user` with type="admin"

#### GET `/manage/processed-images`
**Auth:** Bearer JWT (admin)
**Query Params:** `prefix`, `imageName`, `imageUrl`, `deviceId`
**Modes:**
- No params: List all blobs in processed-images
- prefix: List blobs with prefix
- imageName: Get specific blob with SAS URL
- deviceId: List images for device

#### POST `/manage/transfer-device?deviceId=xxx&newUserId=yyy`
**Auth:** Bearer JWT (admin)
**Response (200):**
```json
{
    "message": "Device transferred successfully",
    "deviceId": "string",
    "oldUserId": "UUID",
    "newUserId": "UUID"
}
```

---

## 7. MOBILE APP (iOS - Swift/SwiftUI)

**Platform:** iOS 14+
**Language:** Swift 5+
**Framework:** SwiftUI
**Architecture:** MVVM

**Base API URL:** `https://iotaccessdev-func.azurewebsites.net/api`

### API Integration
**Endpoints Called:**
- POST `/user/login`
- GET `/user`
- PUT `/user`
- GET `/devices`
- POST `/device`
- DELETE `/device`
- POST `/telemetry` (with multipart image upload)
- GET `/telemetry`
- GET `/conditions`
- POST `/conditions`
- GET `/alertlogs`

**Authentication:**
- JWT stored in iOS Keychain via KeychainSwift library
- Added to requests as `Authorization: Bearer {token}`
- Token refresh handled on 401 responses

**Services:**
- AuthService: Login, logout, token management
- NetworkService: Base HTTP client with authentication
- DeviceService: Device CRUD operations
- TelemetryService: Telemetry submission with image upload
- NotificationService: APNs registration and handling

**Data Models:**
All conform to Codable:
- User: Maps to backend User schema
- Device: Maps to backend Device schema
- TelemetryData: Maps to telemetry object
- Condition: Maps to condition schema
- AlertLog: Maps to alert log schema

---

## 8. INFRASTRUCTURE AS CODE (Bicep)

**File:** `infra/main.bicep`

**Parameters:**
- `location`: Azure region (default: resourceGroup().location)
- `namePrefix`: Resource name prefix (e.g., "iotaccessdev")
- `environment`: Environment name (e.g., "dev")
- `functionPythonVersion`: Python runtime version (default: "3.10")

**Modules Deployed (13 total):**

| Module | Resource | Output Name |
|--------|----------|-------------|
| storage | Storage Account | accountId, accountName, primaryConnectionString |
| appInsights | Application Insights | instrumentationKey |
| keyVault | Key Vault | vaultName, vaultUri |
| function | Function App (Python) | functionAppName, principalId |
| cosmos | Cosmos DB (MongoDB API) | connectionString |
| serviceBus | Service Bus Namespace + Queue | queueConnectionString |
| eventGrid | Event Grid Topic | topicEndpoint, topicKey |
| notification | Notification Hub | fullAccessConnection |
| iot | IoT Hub | connectionString |
| blob | Blob Containers | (uses storage account) |
| vision | Computer Vision | endpoint, primaryKey |
| comms | Communication Services | connectionString |
| eventhub | Event Hub (optional) | connectionString |

**Resource Naming Convention:**
- `{namePrefix}-stg` - Storage Account
- `{namePrefix}-ai` - Application Insights
- `{namePrefix}-kv` - Key Vault
- `{namePrefix}-func` - Function App
- `{namePrefix}-cosmos` - Cosmos DB
- `{namePrefix}-sb` - Service Bus
- `{namePrefix}-eg` - Event Grid
- `{namePrefix}-nh` - Notification Hub
- `{namePrefix}-iot` - IoT Hub
- `{namePrefix}-vision` - Computer Vision
- `{namePrefix}-comms` - Communication Services

**Deployment:**
```bash
az deployment group create \
  --resource-group <rg-name> \
  --template-file infra/main.bicep \
  --parameters infra/parameters.dev.json
```

---

## 9. DATA FLOW & BUSINESS LOGIC

### Telemetry Processing Flow
```
1. Device/App → POST /telemetry (multipart or JSON)
   ├─ function_app.py validates deviceId exists
   ├─ Generates eventId (UUID)
   ├─ Uploads image to "telemetry-images" blob (if provided)
   └─ Sends message to Service Bus Queue "cst8922servicebusqueue"

2. Service Bus Listener (Azure Function Trigger)
   ├─ Receives message from queue
   ├─ Finds user by deviceId in Cosmos DB
   ├─ Updates user.Devices.$.telemetryData array (MongoDB $push)
   ├─ Queries Conditions collection
   ├─ For each telemetry value:
   │   ├─ Filters conditions by valueType
   │   ├─ Applies scope filtering (general/user/device)
   │   ├─ Checks thresholds (min/max/exact)
   │   └─ If violated: notify_user()
   └─ Forwards to IoT Hub Event Grid

3. If Image Uploaded:
   └─ Blob Trigger Listener (Azure Function)
      ├─ Generates SAS URL for blob
      ├─ Calls Computer Vision API
      ├─ Analyzes for: fire, animal, human, flood, thunder
      ├─ If detected (confidence > 0.5):
      │   ├─ Moves blob to "processed-images/{deviceId}/"
      │   ├─ Updates telemetry.imageUrl in Cosmos DB (retry 5 times)
      │   ├─ Queries user by deviceId
      │   └─ Sends email alert with severity and instructions
      └─ Returns analysis result
```

### Condition Evaluation Logic
**Triggered:** Service Bus Listener after receiving telemetry message

```python
# For each value in telemetry
for value in telemetry["values"]:
    value_type = value["valueType"]
    value_data = int(value["value"])

    # Query all conditions for this valueType
    conditions = cosmos_service.find_documents(
        {"valueType": value_type},
        "Conditions"
    )

    for condition in conditions:
        # Apply scope filtering
        if condition["scope"] == "user":
            if condition["userId"] != user["userId"]:
                continue
        elif condition["scope"] == "device":
            if condition["deviceId"] != device_id:
                continue
        # scope == "general" applies to all

        # Check thresholds
        violated = False
        if condition.get("minValue") and value_data < condition["minValue"]:
            violated = True
        if condition.get("maxValue") and value_data > condition["maxValue"]:
            violated = True
        if condition.get("exactValue") and value_data != condition["exactValue"]:
            violated = True

        if violated:
            notify_user(condition, message, user, device_id, values)
```

### Notification Logic
**Methods:** `["Log", "Notification", "Email", "SMS"]`

```python
def notify_user(condition, message, user, device_id, values):
    for method in condition["notificationMethods"]:
        if method == "Log":
            # Insert into AlertLogs collection
            alert_document = {
                "deviceId": device_id,
                "user_id": user["userId"],
                "message": message,
                "condition": condition,
                "telemetry_data": values,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            cosmos_service.insert_document(alert_document, "AlertLogs")

        elif method == "Email":
            communication_service.send_email(
                recipient_email=user["email"],
                subject="Alert Notification",
                body=message
            )

        elif method == "Notification":
            # Send Apple Push Notification
            notification_service.send_notification(message, device_id, values)

        elif method == "SMS":
            # Not implemented (requires Azure Communication Services SMS)
            pass
```

---

## 10. AZURE-TO-AWS SERVICE MAPPING

| Azure Service | Current Usage | AWS Equivalent | Notes |
|---------------|---------------|----------------|-------|
| Azure Functions | HTTP triggers + Service Bus/Blob/Timer | AWS Lambda | Lambda needs separate triggers per type |
| Cosmos DB (MongoDB API) | Document storage with MongoDB queries | Amazon DocumentDB or DynamoDB | DocumentDB is MongoDB compatible |
| Service Bus Queue | Message queue for async telemetry processing | Amazon SQS | SQS has different message retention (14 days vs 7 days) |
| Azure IoT Hub | Device registry and management | AWS IoT Core | Similar device registry + MQTT broker |
| Blob Storage | Image storage with containers | Amazon S3 | S3 uses buckets + folders instead of containers |
| Event Grid | Event routing from IoT Hub | Amazon EventBridge | EventBridge has different event schema |
| Notification Hub | Apple Push Notifications | Amazon SNS | SNS supports mobile push directly |
| Computer Vision | Image analysis (tags, descriptions) | Amazon Rekognition | Rekognition Custom Labels for custom detection |
| Communication Services | Email sending | Amazon SES | SES requires domain verification |
| Application Insights | Logging and monitoring | CloudWatch | CloudWatch Logs + CloudWatch Metrics |
| Key Vault | Secret management | AWS Secrets Manager | Similar secret storage and rotation |

---

## 11. CRITICAL MIGRATION CONSIDERATIONS

### Authentication
- JWT with 1-hour expiry, HS256 algorithm
- Bearer token in Authorization header
- Token includes only user_id and expiry (no roles/claims)
- bcrypt for password hashing (12 rounds)

### Database Patterns
- User document with **embedded** Devices array (not separate collection)
- Telemetry **embedded** in Device.telemetryData array (not separate collection)
- Conditions and AlertLogs are separate collections
- MongoDB update operators: `$set`, `$push`, `$pull`, positional `$`
- Nested array queries: `{"Devices.deviceId": "xxx"}`

### Async Processing
- Telemetry POST returns 202 immediately after queuing
- Service Bus processes asynchronously
- Blob processing is event-driven (on upload)
- Eventual consistency between queue and database

### Blob/Image Processing
- Upload trigger activates Computer Vision
- Results determine if moved to processed-images
- Device-specific folders: `processed-images/{deviceId}/`
- SAS URLs with 1-hour expiry
- Retry logic for updating telemetry (5 attempts, exponential backoff)

### Error Handling
- Specific HTTP status codes (400, 401, 403, 404, 409, 500)
- Validation before database operations
- Try-catch with logging throughout
- Partial success for batch operations (telemetry)

### Condition Scopes
- `general` (userId="" and deviceId=""): Applies to ALL telemetry
- `user` (userId=UUID, deviceId=""): Applies to ALL user's devices
- `device` (userId="", deviceId="xxx"): Applies to ONE device
- Evaluation happens in Service Bus Listener, not on POST

### Image Detection Keywords
- **Fire:** fire, flame, smoke, burning, blaze
- **Animal:** animal, dog, cat, bird, wildlife, pet, horse, cow, sheep, lion, tiger
- **Human:** person, people, human, man, woman, child, face, portrait
- **Flood:** flood, flooding, water, submerged, inundation
- **Thunder:** lightning, thunder, storm, thunderstorm, electrical storm
- Minimum confidence: 0.5
- Priority: fire > flood > thunder > animal > human > other

### Scheduled Operations
- Daily cleanup at midnight UTC (cron: `0 0 0 * * *`)
- Deletes images older than 24 hours from uploadedImages array
- Does NOT delete processed-images

---

## 12. PYTHON DEPENDENCIES

**File:** `requirements.txt`

```
azure-functions
pymongo
bcrypt
PyJWT
requests
Pillow
aiohttp
uamqp==1.6.1
certifi>=2023.7.22
azure-storage-blob
azure-servicebus
azure-communication-email
azure-identity
azure-core
azure-eventgrid
dnspython
azure-eventhub
azure-iot-hub
azure-mgmt-iothub
azure-cognitiveservices-vision-computervision
azure-cognitiveservices-vision-customvision
```

---

**END OF AZURE PROJECT REFERENCE**

This document contains complete implementation details for AWS migration. All API contracts, data models, business logic, and Azure service dependencies have been documented for feature parity validation.

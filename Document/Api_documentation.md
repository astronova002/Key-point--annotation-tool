# API Documentation
## Keypoint Annotation Tool - REST API Reference

## Base URL
- Development: `http://localhost:8000/api/`
- Production: `https://your-domain.com/api/`

## Authentication
All API endpoints (except registration and login) require JWT authentication.

### Headers
```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

## API Endpoints

### Authentication Endpoints

#### POST /auth/register/
Register a new user account.

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string",
  "role": "ANNOTATOR|VERIFIER"
}
```

**Response (201):**
```json
{
  "message": "User registered successfully. Awaiting admin approval.",
  "user_id": "integer"
}
```

#### POST /auth/login/
Authenticate user and get tokens.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200):**
```json
{
  "access": "jwt_token",
  "refresh": "refresh_token",
  "user": {
    "id": "integer",
    "username": "string",
    "email": "string",
    "role": "string",
    "is_approved": "boolean"
  }
}
```

### Image & Batch Management

#### POST /batches/
Create a new image batch.

**Request Body:**
```json
{
  "batch_name": "string",
  "description": "string",
  "keypoint_schema_id": "integer",
  "total_images": "integer"
}
```

#### POST /batches/{batch_id}/upload/
Upload images to a batch.

**Request:** Multipart form data with image files

**Response (200):**
```json
{
  "uploaded_count": "integer",
  "failed_count": "integer",
  "processing_status": "string"
}
```

### Annotation Workflow

#### GET /assignments/
Get assigned batches for the current annotator.

**Response (200):**
```json
{
  "assignments": [
    {
      "id": "integer",
      "batch": {
        "id": "integer",
        "name": "string",
        "total_images": "integer"
      },
      "status": "string",
      "progress_percentage": "number",
      "due_date": "datetime"
    }
  ]
}
```

#### POST /annotations/
Submit an annotation.

**Request Body:**
```json
{
  "image_id": "integer",
  "refined_keypoints": {
    "keypoints": [
      {
        "id": "integer",
        "name": "string",
        "x": "number",
        "y": "number",
        "confidence": "number",
        "visible": "integer"
      }
    ]
  },
  "time_spent_seconds": "integer",
  "difficulty_rating": "string",
  "notes": "string"
}
```

### Verification Process

#### GET /verifications/queue/
Get pending annotations for verification.

**Response (200):**
```json
{
  "queue": [
    {
      "annotation_id": "integer",
      "image": {
        "id": "integer",
        "filename": "string",
        "width": "integer",
        "height": "integer"
      },
      "annotator": {
        "username": "string"
      },
      "submitted_at": "datetime"
    }
  ]
}
```

#### POST /verifications/
Submit verification decision.

**Request Body:**
```json
{
  "annotation_id": "integer",
  "decision": "APPROVED|APPROVED_WITH_CORRECTIONS|REJECTED",
  "corrected_keypoints": "object|null",
  "feedback": "string",
  "quality_score": "integer",
  "rejection_reason": "string|null"
}
```

### Analytics & Reporting

#### GET /analytics/performance/
Get user performance metrics.

**Response (200):**
```json
{
  "current_period": {
    "images_processed": "integer",
    "avg_time_per_image": "number",
    "accuracy_score": "number",
    "quality_rating": "number"
  },
  "trends": {
    "productivity_trend": "number",
    "accuracy_trend": "number"
  },
  "peer_comparison": {
    "percentile": "integer",
    "rank": "integer"
  }
}
```

## Error Responses

### Standard Error Format
```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": "object|null"
  }
}
```

### Common HTTP Status Codes
- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

## Rate Limiting
- Authentication endpoints: 10 requests per minute
- File upload endpoints: 100 requests per hour
- Other endpoints: 1000 requests per hour

## WebSocket Events

### Connection
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/notifications/');
```

### Event Types
- `batch_processing_complete`: Batch YOLO processing finished
- `assignment_received`: New batch assigned
- `verification_completed`: Annotation verified
- `system_notification`: System-wide announcements
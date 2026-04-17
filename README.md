# Loyalty Points API

Redemption service for Walmart's customer loyalty program.

**Team:** Customer Loyalty  
**Tech Stack:** Python 3.11, Flask  
**Port:** 8080

## API Endpoints

### Health Check

```
GET /health
```

Returns service health status.

**Response:**
```json
{
  "status": "UP",
  "service": "loyalty-points-api"
}
```

### List Redemptions

```
GET /api/v1/redemption?limit=20&offset=0
```

Returns paginated list of redemptions.

**Query Parameters:**
- `limit` (optional): Items per page, 1-100, default 20
- `offset` (optional): Starting index, default 0

**Response:**
```json
{
  "items": [
    {
      "id": "1",
      "name": "$10 Store Credit",
      "value": 1000
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

### Create Redemption

```
POST /api/v1/redemption
Content-Type: application/json
```

Creates a new redemption option.

**Request Body:**
```json
{
  "name": "$25 Gift Card",
  "value": 2500
}
```

**Validation Rules:**
- `name`: Required, non-empty string, max 200 characters
- `value`: Required, positive number, max 1,000,000

**Response (201 Created):**
```json
{
  "id": "2",
  "name": "$25 Gift Card",
  "value": 2500
}
```

**Error Response (400 Bad Request):**
```json
{
  "errors": [
    "name is required and must be a string",
    "value must be a positive number"
  ]
}
```

### Get Redemption

```
GET /api/v1/redemption/{id}
```

Returns a single redemption by ID.

**Response (200 OK):**
```json
{
  "id": "1",
  "name": "$10 Store Credit",
  "value": 1000
}
```

**Error Response (404 Not Found):**
```json
{
  "error": "not found"
}
```

## Local Development

### Prerequisites

- Python 3.11+
- pip

### Setup

```bash
# Install dependencies
pip install flask

# Run the service
python app.py
```

Service will be available at `http://localhost:8080`.

### Testing

```bash
# Health check
curl http://localhost:8080/health

# Create redemption
curl -X POST http://localhost:8080/api/v1/redemption \
  -H "Content-Type: application/json" \
  -d '{"name": "$10 Credit", "value": 1000}'

# List redemptions
curl http://localhost:8080/api/v1/redemption
```

## Architecture

### Current Implementation

- **Storage:** In-memory store (`_redemptions` list)
- **ID Generation:** Sequential integer counter
- **Request Limits:** 1 MB max payload size

### Production Considerations

This service uses in-memory storage for simplicity. Production deployment requires:

- Database backend (PostgreSQL recommended)
- Persistent ID generation (UUIDs or database sequences)
- Authentication/authorization
- Rate limiting
- Caching layer for read-heavy operations

### Design Decisions

- **Points as integers:** Value stored in point units (e.g., 1000 = $10) to avoid floating-point precision issues
- **Strict validation:** Prevents invalid redemption options from entering the system
- **Pagination defaults:** 20-item limit balances performance and usability

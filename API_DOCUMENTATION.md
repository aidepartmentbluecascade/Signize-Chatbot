# Signize Chatbot API Documentation

## Overview

The Signize Chatbot API is a single-endpoint service that provides all chatbot functionality through a simple REST API. You only need a **session ID** to access all features.

## Base URL
```
http://localhost:5000/api/chatbot
```

## Authentication
No authentication required. All data is isolated by session ID.

## Session Management

### Session ID Generation
- **Auto-generated**: If no session ID provided, one is automatically created
- **Format**: `session_{timestamp}_{random_string}`
- **Example**: `session_1755500136604_hzfe6e5jd`

### Session Persistence
- Sessions persist until server restart
- Each session is completely isolated
- Multiple users can use the API simultaneously

## API Endpoints

### Main Endpoint: `/api/chatbot`

**Method**: `POST`

**Content-Type**: `application/json`

## Request Format

```json
{
    "session_id": "optional_session_id",
    "action": "chat|upload|quote|get_quote",
    "message": "user message",
    "email": "user@example.com",
    "files": [...],
    "quote_data": {...}
}
```

## Actions

### 1. Chat Action

Send messages and get AI responses.

**Required Fields:**
- `action`: `"chat"`
- `message`: User's message

**Optional Fields:**
- `session_id`: Existing session ID (auto-generated if not provided)
- `email`: User's email address

**Example Request:**
```json
{
    "action": "chat",
    "message": "Hi, I need help with a sign",
    "email": "user@example.com"
}
```

**Example Response:**
```json
{
    "session_id": "session_1755500136604_hzfe6e5jd",
    "response": "Hello! I'd be happy to help you with your sign needs. First, could you please provide your email address so I can save your information and follow up with you?",
    "quote_form_triggered": false,
    "message_count": 2,
    "email": "user@example.com"
}
```

### 2. Upload Action

Upload logo files to Dropbox.

**Required Fields:**
- `action`: `"upload"`
- `session_id`: Existing session ID
- `files`: Array of file objects

**File Object Format:**
```json
{
    "filename": "logo.png",
    "data": "base64_encoded_file_data"
}
```

**Example Request:**
```json
{
    "action": "upload",
    "session_id": "session_1755500136604_hzfe6e5jd",
    "files": [
        {
            "filename": "logo1.png",
            "data": "iVBORw0KGgoAAAANSUhEUgAA..."
        },
        {
            "filename": "logo2.pdf",
            "data": "JVBERi0xLjQKJcOkw7zDtsO..."
        }
    ]
}
```

**Example Response:**
```json
{
    "session_id": "session_1755500136604_hzfe6e5jd",
    "uploaded_files": [
        {
            "filename": "logo1.png",
            "url": "https://dl.dropboxusercontent.com/s/abc123/logo1.png?dl=1",
            "upload_time": "2025-01-18T11:56:10.123456"
        }
    ],
    "total_logos": 1
}
```

### 3. Quote Action

Submit quote form data.

**Required Fields:**
- `action`: `"quote"`
- `session_id`: Existing session ID
- `quote_data`: Quote form data

**Quote Data Format:**
```json
{
    "size": "2x3 feet",
    "material": "3D metal",
    "illumination": "LED backlit",
    "installation": "Brick wall",
    "location": "New York, NY",
    "budget": "$1000-2000",
    "deadline": "Standard (15-17 business days)",
    "notes": "Additional requirements..."
}
```

**Example Request:**
```json
{
    "action": "quote",
    "session_id": "session_1755500136604_hzfe6e5jd",
    "quote_data": {
        "size": "2x3 feet",
        "material": "3D metal",
        "illumination": "LED backlit",
        "installation": "Brick wall",
        "location": "New York, NY",
        "budget": "$1000-2000",
        "deadline": "Standard (15-17 business days)"
    }
}
```

**Example Response:**
```json
{
    "session_id": "session_1755500136604_hzfe6e5jd",
    "message": "Quote saved successfully",
    "quote_id": "session_1755500136604_hzfe6e5jd"
}
```

### 4. Get Quote Action

Retrieve existing quote data.

**Required Fields:**
- `action`: `"get_quote"`
- `session_id`: Existing session ID

**Example Request:**
```json
{
    "action": "get_quote",
    "session_id": "session_1755500136604_hzfe6e5jd"
}
```

**Example Response:**
```json
{
    "session_id": "session_1755500136604_hzfe6e5jd",
    "quote_data": {
        "size": "2x3 feet",
        "material": "3D metal",
        "illumination": "LED backlit",
        "installation": "Brick wall",
        "location": "New York, NY",
        "budget": "$1000-2000",
        "deadline": "Standard (15-17 business days)"
    },
    "status": "new"
}
```

## Error Responses

**400 Bad Request:**
```json
{
    "error": "Message is required for chat action"
}
```

**500 Internal Server Error:**
```json
{
    "error": "API call failed"
}
```

## Complete Workflow Example

### Step 1: Start Conversation
```bash
curl -X POST http://localhost:5000/api/chatbot \
  -H "Content-Type: application/json" \
  -d '{
    "action": "chat",
    "message": "Hi, I need help with a sign"
  }'
```

**Response:**
```json
{
    "session_id": "session_1755500136604_hzfe6e5jd",
    "response": "Hello! I'd be happy to help you with your sign needs. First, could you please provide your email address so I can save your information and follow up with you?",
    "quote_form_triggered": false,
    "message_count": 2,
    "email": null
}
```

### Step 2: Provide Email
```bash
curl -X POST http://localhost:5000/api/chatbot \
  -H "Content-Type: application/json" \
  -d '{
    "action": "chat",
    "session_id": "session_1755500136604_hzfe6e5jd",
    "message": "My email is user@example.com",
    "email": "user@example.com"
  }'
```

### Step 3: Request Quote
```bash
curl -X POST http://localhost:5000/api/chatbot \
  -H "Content-Type: application/json" \
  -d '{
    "action": "chat",
    "session_id": "session_1755500136604_hzfe6e5jd",
    "message": "I want a mockup and quote for a 3D metal sign"
  }'
```

### Step 4: Upload Logo Files
```bash
curl -X POST http://localhost:5000/api/chatbot \
  -H "Content-Type: application/json" \
  -d '{
    "action": "upload",
    "session_id": "session_1755500136604_hzfe6e5jd",
    "files": [
        {
            "filename": "logo.png",
            "data": "base64_encoded_data_here"
        }
    ]
  }'
```

### Step 5: Submit Quote
```bash
curl -X POST http://localhost:5000/api/chatbot \
  -H "Content-Type: application/json" \
  -d '{
    "action": "quote",
    "session_id": "session_1755500136604_hzfe6e5jd",
    "quote_data": {
        "size": "2x3 feet",
        "material": "3D metal",
        "illumination": "LED backlit",
        "installation": "Brick wall",
        "location": "New York, NY",
        "budget": "$1000-2000",
        "deadline": "Standard (15-17 business days)"
    }
  }'
```

## Client Libraries

### Python Client
```python
import requests

class SignizeChatbotClient:
    def __init__(self, base_url="http://localhost:5000/api"):
        self.base_url = f"{base_url}/chatbot"
        self.session_id = None
    
    def chat(self, message, email=None):
        payload = {
            "action": "chat",
            "message": message
        }
        if self.session_id:
            payload["session_id"] = self.session_id
        if email:
            payload["email"] = email
        
        response = requests.post(self.base_url, json=payload)
        data = response.json()
        
        if "session_id" in data:
            self.session_id = data["session_id"]
        
        return data

# Usage
client = SignizeChatbotClient()
response = client.chat("Hi, I need help with a sign")
print(response["response"])
```

### JavaScript Client
```javascript
class SignizeChatbotClient {
    constructor(baseUrl = 'http://localhost:5000/api') {
        this.baseUrl = `${baseUrl}/chatbot`;
        this.sessionId = null;
    }
    
    async chat(message, email = null) {
        const payload = {
            action: 'chat',
            message: message
        };
        
        if (this.sessionId) {
            payload.session_id = this.sessionId;
        }
        
        if (email) {
            payload.email = email;
        }
        
        const response = await fetch(this.baseUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        const data = await response.json();
        
        if (data.session_id) {
            this.sessionId = data.session_id;
        }
        
        return data;
    }
}

// Usage
const client = new SignizeChatbotClient();
client.chat("Hi, I need help with a sign").then(response => {
    console.log(response.response);
});
```

## Data Storage

### Google Sheets
- **Purpose**: Conversation history and session tracking
- **Columns**: Session ID, Email, Timestamp, Message Count, Conversation, Status
- **Access**: Read-only for viewing conversations

### MongoDB
- **Purpose**: Quote form data storage
- **Collection**: `quotes`
- **Index**: `session_id` (unique)

### Dropbox
- **Purpose**: Logo file storage
- **Structure**: `/logos/{session_id}/{filename}`
- **Access**: Public URLs for file access

## Rate Limits

Currently no rate limits implemented. For production use, consider:
- Rate limiting per session ID
- Request throttling
- API key authentication

## Security Considerations

- **Data Isolation**: Each session is completely isolated
- **No Authentication**: Anyone can access the API
- **File Upload**: Validate file types and sizes
- **Input Validation**: Sanitize all user inputs

## Deployment

### Requirements
- Python 3.8+
- Flask
- OpenAI API key
- Dropbox API token
- MongoDB connection
- Google Sheets API credentials

### Environment Variables
```bash
OPENAI_API_KEY=your_openai_key
DROPBOX_ACCESS_TOKEN=your_dropbox_token
MONGODB_URI=your_mongodb_uri
GOOGLE_SHEETS_ID=your_sheets_id
```

### Running the API
```bash
python api_service.py
```

The API will be available at `http://localhost:5000/api/chatbot`

## Support

For questions or issues:
1. Check the health endpoint: `GET /api/health`
2. Review error messages in API responses
3. Check server logs for detailed error information

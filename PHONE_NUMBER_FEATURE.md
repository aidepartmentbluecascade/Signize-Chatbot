# Phone Number Collection Feature

## Overview
The ChromaBot now includes a phone number collection feature that allows users to provide their phone numbers when they need to speak with a human representative or get a call back. This replaces the previous email-only approach for customer service requests.

## Features

### 1. Automatic Phone Number Collection
- **Trigger Phrases**: The AI automatically detects when users want to speak with someone
- **Smart Detection**: Recognizes phrases like:
  - "call me"
  - "speak to someone"
  - "talk to someone"
  - "human"
  - "representative"
  - "expert"
  - "agent"
  - "I need to speak with a sign expert"

### 2. User Interface
- **Phone Number Popup**: Clean, user-friendly popup similar to email collection
- **Input Validation**: Accepts various phone number formats
- **Real-time Feedback**: Shows validation status and success messages

### 3. Data Persistence
- **Database Storage**: Phone numbers are saved to MongoDB
- **Session Management**: Phone numbers persist throughout the chat session
- **Fallback Storage**: Local JSON storage if MongoDB is unavailable

## Technical Implementation

### Backend Changes

#### New API Endpoints
```python
# Save phone number
POST /save-phone
{
    "session_id": "string",
    "phone_number": "string"
}

# Get phone number
GET /get-phone/<session_id>
```

#### Database Schema Updates
- Added `phone_number` field to chat sessions
- Phone numbers are stored in both MongoDB and local JSON files
- Phone numbers are included in session retrieval responses

#### AI Prompt Updates
- Enhanced system prompt to detect phone number requests
- Added `[PHONE_NUMBER_TRIGGER]` marker for frontend detection
- Phone number context is injected into AI conversations

### Frontend Changes

#### New UI Elements
```html
<!-- Phone Number Field -->
<div class="phone-field-container" id="phoneFieldContainer" style="display: none;">
    <div class="phone-input-wrapper">
        <input type="tel" id="phoneInput" placeholder="Enter your phone number..." class="phone-input">
        <button id="phoneSubmitBtn" class="phone-submit-btn">
            <i class="fas fa-check"></i>
        </button>
    </div>
    <div class="phone-validation" id="phoneValidation"></div>
</div>
```

#### JavaScript Functions
```javascript
// Phone number validation and submission
async function validateAndSubmitPhone()

// Show/hide phone number field
function showPhoneField()
function hidePhoneField()

// Phone number validation display
function showPhoneValidation(message, isValid)
```

#### CSS Styling
- Phone field styles mirror email field styles
- Consistent with existing design system
- Responsive and accessible

## Usage Flow

### 1. User Requests Human Contact
```
User: "I need to speak with someone about my sign order"
AI: "I'd be happy to have someone call you! Could you please provide your phone number so I can have a sign expert reach out to you?"
```

### 2. Phone Number Collection
- Phone number popup appears
- User enters phone number
- System validates and saves the number
- Confirmation message is sent to the bot

### 3. Session Continuation
- Phone number is stored in the session
- User can continue chatting normally
- Phone number is available for future reference

## Configuration

### Environment Variables
No additional environment variables are required. The feature uses existing MongoDB and session management infrastructure.

### Database Requirements
- MongoDB: Phone numbers are stored in the `quotes` collection
- Local Storage: Phone numbers are stored in JSON files in the `chat_sessions` directory

## Testing

### Manual Testing
1. Start a chat session
2. Ask to speak with someone: "I need to speak with a human"
3. Verify phone number popup appears
4. Enter a valid phone number
5. Confirm the number is saved and session continues

### Automated Testing
Run the test script:
```bash
python test_phone_functionality.py
```

### Webhook Testing
Test the n8n webhook connection:
```bash
curl -X GET http://localhost:5000/test-webhook
```

Or visit in browser:
```
http://localhost:5000/test-webhook
```

This will send a test payload to verify the webhook connection and authentication are working correctly.

## Error Handling

### Validation Errors
- Empty phone number input
- Invalid phone number format
- Database connection failures

### Fallback Mechanisms
- Local storage if MongoDB is unavailable
- Graceful degradation of functionality
- User-friendly error messages

## Security Considerations

### Data Protection
- Phone numbers are stored securely in the database
- No phone number data is logged to console
- Input validation prevents malicious input

### Privacy
- Phone numbers are only collected when explicitly requested
- Users can choose not to provide phone numbers
- Phone numbers are only used for requested callbacks

## Future Enhancements

### Potential Improvements
1. **SMS Verification**: Send verification codes via SMS
2. **Call Scheduling**: Allow users to schedule call times
3. **Integration**: Connect with CRM systems for call management
4. **Analytics**: Track phone number collection success rates

### API Extensions
- Phone number format validation endpoints
- International phone number support
- Phone number update functionality

## Troubleshooting

### Common Issues

#### Phone Number Popup Not Appearing
- Check browser console for JavaScript errors
- Verify AI response contains phone number trigger
- Ensure phone number hasn't already been collected

#### Phone Number Not Saving
- Check MongoDB connection status
- Verify session ID is valid
- Check browser network tab for API errors

#### Validation Errors
- Ensure phone number format is valid
- Check for special characters or formatting
- Verify input field is properly initialized

### Debug Information
- Enable browser developer tools
- Check network requests to `/save-phone` endpoint
- Review MongoDB logs for database errors

## Support

For technical support or questions about the phone number feature:
1. Check the application logs
2. Review the browser console
3. Test with the provided test script
4. Contact the development team

---

**Version**: 1.0.0  
**Last Updated**: December 2024  
**Compatibility**: ChromaBot v2.0+

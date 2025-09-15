# Sign-nize Customer Support Chatbot

A modern AI-powered customer support chatbot for Signize, specializing in custom sign design and production. The chatbot gathers customer requirements through natural conversation and saves data to Google Sheets.

## Features

- 🤖 **AI-Powered Conversations**: Uses OpenAI GPT-4 for natural, contextual conversations
- 📧 **Email Collection**: Collects customer email addresses with validation
- 📊 **Google Sheets Integration**: Automatically saves conversation data to Google Sheets
- 🎨 **Modern UI**: Beautiful, responsive chat interface with animations
- 📱 **Mobile Responsive**: Works perfectly on desktop and mobile devices
- 🔒 **Secure**: No hardcoded credentials, uses environment variables

## Prerequisites

- Python 3.8 or higher
- Google Cloud Platform account
- OpenAI API key
- Google Sheets API enabled

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/aidepartmentbluecascade/Signize-Chatbot.git
   cd Signize-Chatbot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. **Set up Google Sheets integration**
   
   a. Go to [Google Cloud Console](https://console.cloud.google.com/)
   
   b. Create a new project or select an existing one
   
   c. Enable the Google Sheets API
   
   d. Create a Service Account:
      - Go to "IAM & Admin" > "Service Accounts"
      - Click "Create Service Account"
      - Give it a name (e.g., "signize-chatbot")
      - Grant "Editor" role
      - Create and download the JSON key file
   
   e. Rename the downloaded file to `credentials.json` and place it in the root directory
   
   f. Create a Google Sheet and share it with the service account email (found in credentials.json)
   
   g. Update the `SPREADSHEET_ID` in `app.py` with your Google Sheet ID

## Usage

1. **Start the application**
   ```bash
   python app.py
   ```

2. **Open your browser**
   Navigate to `http://localhost:5000`

3. **Start chatting**
   The chatbot will guide customers through the sign design process, collecting:
   - Email address
   - Sign requirements (size, material, installation surface, etc.)
   - Timeline and budget
   - Logo/design preferences

## Configuration

### Google Sheets Setup
- The application automatically saves conversation data to Google Sheets
- Each conversation creates one row with all details
- Make sure your service account has "Editor" access to the Google Sheet

### Customization
- Modify `SIGN_NIZE_SYSTEM_PROMPT` in `app.py` to change conversation flow
- Update UI styling in `static/style.css`
- Customize chat behavior in `static/script.js`

## File Structure

```
├── app.py                 # Main Flask application
├── environment.py         # Environment variable loader
├── requirements.txt       # Python dependencies
├── credentials.json       # Google Service Account credentials (not in repo)
├── credentials_template.json # Template for credentials
├── .env                   # Environment variables (not in repo)
├── .gitignore            # Git ignore rules
├── README.md             # This file
├── static/               # Static files (CSS, JS, images)
│   ├── style.css         # Main stylesheet
│   ├── script.js         # Frontend JavaScript
│   └── images/           # Images and logos
├── templates/            # HTML templates
│   └── index.html        # Main chat interface
└── chat_sessions/        # Local session storage (optional)
```

## Security Notes

- Never commit `credentials.json` or `.env` files to version control
- The application is configured to only use credentials from files, not hardcoded values
- All sensitive data is stored locally or in Google Sheets with proper access controls

## Troubleshooting

### Google Sheets Connection Issues
- Ensure the service account has "Editor" access to the Google Sheet
- Verify the `SPREADSHEET_ID` is correct
- Check that the Google Sheets API is enabled in your Google Cloud project

### OpenAI API Issues
- Verify your OpenAI API key is correct and has sufficient credits
- Check that the API key is properly set in the `.env` file

### Email Validation Issues
- The application validates email format before accepting
- Invalid emails will show an error message

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support or questions, please contact the development team or create an issue in the GitHub repository.

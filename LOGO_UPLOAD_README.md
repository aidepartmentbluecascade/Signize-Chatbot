# Logo Upload & Dropbox Integration

## Overview

The ChromaBot application has been enhanced with Dropbox integration for logo file uploads and a redesigned quote form with optional fields. This allows users to upload multiple logo files directly through the web interface, which are then stored in Dropbox for easy access by the design team.

## New Features

### 1. Multiple Logo Upload
- **Drag & Drop Interface**: Users can drag and drop multiple logo files onto the upload area
- **Click to Upload**: Traditional file picker interface for selecting files
- **File Type Support**: JPG, PNG, PDF, AI, EPS files (up to 10MB each)
- **Real-time Preview**: Shows uploaded files with status indicators
- **Progress Tracking**: Visual progress bars for upload status
- **Remove Files**: Users can remove uploaded files before submission

### 2. Dropbox Integration
- **Automatic Upload**: Files are uploaded to Dropbox immediately upon selection
- **Shared Links**: Each uploaded file gets a public Dropbox link
- **Organized Storage**: Files are organized by session ID in Dropbox
- **Backup Storage**: Files are also stored locally as backup

### 3. Optional Form Fields
- **All Fields Optional**: Users can submit quotes with minimal information
- **Flexible Dimensions**: Width and height are optional
- **Enhanced UX**: Better user experience for partial submissions

## Technical Implementation

### Backend Changes

#### 1. Dropbox Integration (`app.py`)
```python
# Dropbox configuration
DROPBOX_ACCESS_TOKEN = "your-dropbox-token"

def upload_to_dropbox(local_file_path, dropbox_path):
    """Upload file to Dropbox and return public link"""
    dbx = dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)
    # Upload file and create shared link
    return url
```

#### 2. Enhanced Upload Route
```python
@app.route("/upload-logo", methods=["POST"])
def upload_logo():
    # Handle file upload
    # Upload to Dropbox
    # Store in session
    # Return success with Dropbox URL
```

### Frontend Changes

#### 1. HTML Structure (`templates/index.html`)
```html
<!-- Logo Upload Section -->
<div class="form-group">
    <label for="logoUploads">Logo Files (Optional)</label>
    <div class="logo-upload-container">
        <div class="logo-upload-area" id="logoUploadArea">
            <!-- Upload interface -->
        </div>
        <div class="logo-preview-container" id="logoPreviewContainer">
            <!-- Preview uploaded files -->
        </div>
    </div>
</div>
```

#### 2. JavaScript Functionality (`static/script.js`)
```javascript
// Logo upload functions
function handleLogoFileSelect(event) { /* Handle file selection */ }
function uploadLogoFile(file) { /* Upload to server */ }
function addLogoPreviewItem(logoId, file, status) { /* Show preview */ }
```

#### 3. CSS Styling (`static/style.css`)
```css
/* Logo upload styles */
.logo-upload-area { /* Upload area styling */ }
.logo-preview-item { /* Preview item styling */ }
.logo-upload-progress { /* Progress bar styling */ }
```

## Setup Instructions

### 1. Install Dependencies
```bash
pip install dropbox
```

### 2. Configure Dropbox
1. Create a Dropbox app at https://www.dropbox.com/developers
2. Generate an access token
3. Update the `DROPBOX_ACCESS_TOKEN` in `app.py`

### 3. Test Integration
```bash
python test_dropbox.py
```

## Usage

### For Users
1. **Start Quote Process**: Trigger the quote form through the chat
2. **Upload Logos**: Drag and drop or click to select logo files
3. **Fill Form**: Complete any desired fields (all optional)
4. **Submit**: Form includes logo information automatically

### For Developers
1. **File Storage**: Files are stored in `/logos/{session_id}/` in Dropbox
2. **Session Management**: Logo information is stored in session data
3. **Database Integration**: Logo URLs are included in quote submissions

## File Structure

```
ChromaBot/
├── app.py                    # Main application with Dropbox integration
├── templates/
│   └── index.html           # Updated form with logo upload
├── static/
│   ├── style.css            # Logo upload styles
│   └── script.js            # Logo upload JavaScript
├── data/
│   └── logos/               # Local backup storage
├── test_dropbox.py          # Dropbox integration test
└── requirements.txt         # Updated with dropbox dependency
```

## API Endpoints

### Upload Logo
- **POST** `/upload-logo`
- **Parameters**: `logo` (file), `session_id` (string)
- **Response**: `{success: true, dropbox_url: "url", logo_count: 1}`

### Get Session Logos
- **GET** `/session/{session_id}/logos`
- **Response**: `{logos: [{filename, dropbox_url, upload_time}]}`

## Error Handling

- **File Validation**: Checks file type and size before upload
- **Upload Failures**: Shows error status in preview
- **Network Issues**: Graceful fallback to local storage
- **Dropbox Errors**: Comprehensive error logging

## Security Considerations

- **File Size Limits**: 10MB maximum per file
- **File Type Validation**: Only allowed formats accepted
- **Session Isolation**: Files organized by session ID
- **Access Control**: Dropbox links are public but organized

## Future Enhancements

1. **Image Compression**: Automatic image optimization
2. **Batch Processing**: Upload multiple files simultaneously
3. **File Management**: Edit/rename uploaded files
4. **Cloud Storage**: Additional cloud providers (Google Drive, OneDrive)
5. **Version Control**: Track file versions and changes

## Troubleshooting

### Common Issues

1. **Upload Fails**
   - Check Dropbox token validity
   - Verify file size and type
   - Check network connectivity

2. **Preview Not Showing**
   - Ensure JavaScript is enabled
   - Check browser console for errors
   - Verify file input element exists

3. **Dropbox Connection Issues**
   - Run `python test_dropbox.py` to diagnose
   - Check token permissions
   - Verify Dropbox API status

### Debug Commands

```javascript
// Test logo upload functionality
window.testLogoUpload = function() {
    console.log('Uploaded logos:', uploadedLogos);
    console.log('Preview container:', logoPreviewContainer);
};

// Test Dropbox connection
window.testDropboxConnection = function() {
    fetch('/test-mongodb')
        .then(response => response.json())
        .then(data => console.log('Connection test:', data));
};
```

## Support

For technical support or questions about the logo upload functionality, please refer to the main project documentation or contact the development team.

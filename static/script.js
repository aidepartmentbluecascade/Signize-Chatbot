// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const fabBtn = document.getElementById('fabBtn');
const minimizeBtn = document.getElementById('minimizeBtn');
const closeBtn = document.getElementById('closeBtn');
const quickActionBtns = document.querySelectorAll('.quick-action-btn');
const emailFieldContainer = document.getElementById('emailFieldContainer');
const emailInput = document.getElementById('emailInput');
const emailSubmitBtn = document.getElementById('emailSubmitBtn');
const emailValidation = document.getElementById('emailValidation');

// Logo Upload Elements
const logoUploadArea = document.getElementById('logoUploadArea');
const logoFileInput = document.getElementById('logoFileInput');
const logoPreviewContainer = document.getElementById('logoPreviewContainer');
const logoPreviewList = document.getElementById('logoPreviewList');

// Quote Form Elements
const quoteModal = document.getElementById('quoteModal');
const quoteSummaryModal = document.getElementById('quoteSummaryModal');
const quoteForm = document.getElementById('quoteForm');
const closeQuoteModal = document.getElementById('closeQuoteModal');
const closeQuoteSummaryModal = document.getElementById('closeQuoteSummaryModal');
const cancelQuote = document.getElementById('cancelQuote');
const requestChanges = document.getElementById('requestChanges');
const closeSummary = document.getElementById('closeSummary');
const quoteSummaryContent = document.getElementById('quoteSummaryContent');

// Session Management
let sessionId = generateSessionId();
let isTyping = false;
let userEmail = '';
let emailCollected = false;

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    focusInput();
});

// Generate unique session ID
function generateSessionId() {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

// Initialize event listeners
function initializeEventListeners() {
    // Send message on button click
    sendBtn.addEventListener('click', sendMessage);
    
    // Send message on Enter key
    messageInput.addEventListener('keypress', function(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });
    
    // Email validation and submission
    emailSubmitBtn.addEventListener('click', validateAndSubmitEmail);
    emailInput.addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            validateAndSubmitEmail();
        }
    });
    
    // Logo upload functionality
    if (logoUploadArea && logoFileInput) {
        logoUploadArea.addEventListener('click', () => logoFileInput.click());
        
        logoFileInput.addEventListener('change', handleLogoFileSelect);
        
        // Drag and drop functionality
        logoUploadArea.addEventListener('dragover', handleDragOver);
        logoUploadArea.addEventListener('dragleave', handleDragLeave);
        logoUploadArea.addEventListener('drop', handleDrop);
    }
    
    // Input focus and typing indicators
    messageInput.addEventListener('focus', function() {
        this.parentElement.classList.add('focused');
    });
    
    messageInput.addEventListener('blur', function() {
        this.parentElement.classList.remove('focused');
    });
    
    // Quick action buttons
    quickActionBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const action = this.dataset.action;
            handleQuickAction(action);
        });
    });
    
    // Control buttons
    minimizeBtn.addEventListener('click', minimizeChat);
    closeBtn.addEventListener('click', closeChat);
    fabBtn.addEventListener('click', toggleChat);
    
    // Quote form event listeners
    closeQuoteModal.addEventListener('click', closeQuoteForm);
    closeQuoteSummaryModal.addEventListener('click', closeQuoteSummary);
    cancelQuote.addEventListener('click', closeQuoteForm);
    requestChanges.addEventListener('click', requestQuoteChanges);
    closeSummary.addEventListener('click', closeQuoteSummary);
    quoteForm.addEventListener('submit', handleQuoteSubmit);
    
    // Start fresh button
    const startFreshBtn = document.getElementById('startFreshBtn');
    if (startFreshBtn) {
        startFreshBtn.addEventListener('click', startFreshQuote);
    }
    
    // Close modals when clicking overlay
    quoteModal.addEventListener('click', function(e) {
        if (e.target === quoteModal) closeQuoteForm();
    });
    
    // ESC key to close quote form
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            if (quoteModal.classList.contains('show')) {
                closeQuoteForm();
            }
            if (quoteSummaryModal.classList.contains('show')) {
                closeQuoteSummary();
            }
        }
    });
    
    // Unit button functionality for dimensions
    const unitButtons = document.querySelectorAll('.unit-btn');
    unitButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            const field = this.dataset.field;
            const unit = this.dataset.unit;
            
            console.log(`Unit button clicked: ${field} - ${unit}`);
            
            // Remove active class from all buttons in this field group
            const fieldGroup = this.closest('.input-with-unit');
            fieldGroup.querySelectorAll('.unit-btn').forEach(b => b.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            // Update the corresponding input field with unit info
            const input = fieldGroup.querySelector('input');
            if (input) {
                input.dataset.unit = unit;
                console.log(`Updated ${field} input unit to: ${unit}`);
            }
        });
    });
    
    quoteSummaryModal.addEventListener('click', function(e) {
        if (e.target === quoteSummaryModal) closeQuoteSummary();
    });
    
    // Auto-resize input
    messageInput.addEventListener('input', autoResizeInput);
}

// Email validation and submission
async function validateAndSubmitEmail() {
    const email = emailInput.value.trim();
    if (!email) {
        showEmailValidation('Please enter an email address', false);
        return;
    }
    
    try {
        const response = await fetch('/validate-email', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email: email })
        });
        
        const data = await response.json();
        
        if (data.valid) {
            userEmail = email;
            emailCollected = true;
            showEmailValidation('Email saved successfully!', true);
            hideEmailField();
            
            // Send a message to the bot indicating email was collected
            setTimeout(() => {
                addMessage('user', `My email is ${email}`);
                sendMessageToBot(`My email is ${email}`);
            }, 1000);
        } else {
            showEmailValidation(data.message, false);
        }
    } catch (error) {
        console.error('Email validation error:', error);
        showEmailValidation('Email validation failed', false);
    }
}

function showEmailValidation(message, isValid) {
    emailValidation.textContent = message;
    emailValidation.className = `email-validation ${isValid ? 'valid' : 'invalid'}`;
}

function hideEmailField() {
    emailFieldContainer.style.display = 'none';
    // Enable chat input when email field is hidden
    enableChatInput();
}

function showEmailField() {
    emailFieldContainer.style.display = 'block';
    emailInput.focus();
    // Disable chat input when email field is shown
    disableChatInput();
}

// Chat input control functions
function disableChatInput() {
    messageInput.disabled = true;
    messageInput.placeholder = 'Please enter your email first...';
    sendBtn.disabled = true;
    messageInput.classList.add('disabled');
    sendBtn.classList.add('disabled');
    
    // Also disable quick action buttons
    quickActionBtns.forEach(btn => {
        btn.disabled = true;
        btn.classList.add('disabled');
    });
}

function enableChatInput() {
    messageInput.disabled = false;
    messageInput.placeholder = 'Type your message here...';
    sendBtn.disabled = false;
    messageInput.classList.remove('disabled');
    sendBtn.classList.remove('disabled');
    
    // Also enable quick action buttons
    quickActionBtns.forEach(btn => {
        btn.disabled = false;
        btn.classList.remove('disabled');
    });
}

// Logo Upload Functions
let uploadedLogos = [];

function handleLogoFileSelect(event) {
    const files = Array.from(event.target.files);
    handleLogoFiles(files);
}

function handleDragOver(event) {
    event.preventDefault();
    logoUploadArea.classList.add('dragover');
}

function handleDragLeave(event) {
    event.preventDefault();
    logoUploadArea.classList.remove('dragover');
}

function handleDrop(event) {
    event.preventDefault();
    logoUploadArea.classList.remove('dragover');
    const files = Array.from(event.dataTransfer.files);
    handleLogoFiles(files);
}

function handleLogoFiles(files) {
    files.forEach(file => {
        if (isValidLogoFile(file)) {
            uploadLogoFile(file);
        } else {
            alert(`Invalid file: ${file.name}. Please upload JPG, PNG, PDF, AI, or EPS files under 10MB.`);
        }
    });
}

function isValidLogoFile(file) {
    const validTypes = ['image/jpeg', 'image/png', 'application/pdf', 'application/postscript'];
    const validExtensions = ['.jpg', '.jpeg', '.png', '.pdf', '.ai', '.eps'];
    const maxSize = 10 * 1024 * 1024; // 10MB
    
    const hasValidType = validTypes.includes(file.type);
    const hasValidExtension = validExtensions.some(ext => 
        file.name.toLowerCase().endsWith(ext)
    );
    const hasValidSize = file.size <= maxSize;
    
    return (hasValidType || hasValidExtension) && hasValidSize;
}

async function uploadLogoFile(file) {
    const logoId = 'logo_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    
    // Add preview item
    addLogoPreviewItem(logoId, file, 'uploading');
    
    try {
        const formData = new FormData();
        formData.append('logo', file);
        formData.append('session_id', sessionId);
        
        const response = await fetch('/upload-logo', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            updateLogoPreviewItem(logoId, 'success', data.dropbox_url);
            uploadedLogos.push({
                id: logoId,
                filename: file.name,
                dropbox_url: data.dropbox_url
            });
        } else {
            updateLogoPreviewItem(logoId, 'error');
            console.error('Upload failed:', data.message);
        }
    } catch (error) {
        updateLogoPreviewItem(logoId, 'error');
        console.error('Upload error:', error);
    }
}

function addLogoPreviewItem(logoId, file, status) {
    const previewItem = document.createElement('div');
    previewItem.className = 'logo-preview-item';
    previewItem.id = logoId;
    
    const isImage = file.type.startsWith('image/');
    const previewContent = isImage ? 
        `<img src="${URL.createObjectURL(file)}" alt="${file.name}">` :
        `<i class="fas fa-file" style="font-size: 48px; color: var(--text-light); margin-bottom: 8px;"></i>`;
    
    previewItem.innerHTML = `
        ${previewContent}
        <div class="logo-name">${file.name}</div>
        <div class="logo-status ${status}">${status}</div>
        <button class="remove-logo" onclick="removeLogo('${logoId}')">
            <i class="fas fa-times"></i>
        </button>
        <div class="logo-upload-progress">
            <div class="logo-upload-progress-bar" style="width: ${status === 'uploading' ? '50%' : '100%'}"></div>
        </div>
    `;
    
    logoPreviewList.appendChild(previewItem);
    logoPreviewContainer.style.display = 'block';
}

function updateLogoPreviewItem(logoId, status, dropboxUrl = null) {
    const previewItem = document.getElementById(logoId);
    if (previewItem) {
        const statusElement = previewItem.querySelector('.logo-status');
        const progressBar = previewItem.querySelector('.logo-upload-progress-bar');
        
        statusElement.className = `logo-status ${status}`;
        statusElement.textContent = status;
        
        if (status === 'success') {
            progressBar.style.width = '100%';
            progressBar.style.background = 'var(--success-color)';
        } else if (status === 'error') {
            progressBar.style.background = 'var(--error-color)';
        }
    }
}

function removeLogo(logoId) {
    const previewItem = document.getElementById(logoId);
    if (previewItem) {
        previewItem.remove();
        uploadedLogos = uploadedLogos.filter(logo => logo.id !== logoId);
        
        if (uploadedLogos.length === 0) {
            logoPreviewContainer.style.display = 'none';
        }
    }
}

// Show uploaded logos
async function showUploadedLogos() {
    try {
        const response = await fetch(`/session/${sessionId}/logos`);
        const data = await response.json();
        
        if (data.logos && data.logos.length > 0) {
            const logoList = data.logos.map(logo => 
                `• ${logo.filename} (${logo.dropbox_url || logo.public_url})`
            ).join('\n');
            
            addMessage('ai', `Here are the logos you've uploaded:\n${logoList}`);
        } else {
            addMessage('ai', "You haven't uploaded any logos yet.");
        }
    } catch (error) {
        console.error('Error fetching logos:', error);
        addMessage('ai', "Sorry, I couldn't retrieve your uploaded logos.");
    }
}

// Send message function
async function sendMessage() {
    const message = messageInput.value.trim();
    if (!message || isTyping) return;
    
    // Add user message to chat
    addMessage('user', message);
    messageInput.value = '';
    autoResizeInput();
    
    // Send message to bot
    await sendMessageToBot(message);
}

// Send message to bot
async function sendMessageToBot(message) {
    // Show typing indicator for AI response
    addTypingIndicator();
    isTyping = true;
    
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                message: message,
                session_id: sessionId,
                email: userEmail
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Add AI response to chat
            addMessage('ai', data.message);
            
            // Check if quote form should be triggered (only if email is collected)
            if (data.quote_form_triggered && emailCollected) {
                setTimeout(() => {
                    showQuoteForm();
                }, 1000);
            }
            
            // Check if the bot is asking for email
            if (data.message.toLowerCase().includes('email') && !emailCollected) {
                showEmailField();
            }
            
            // REMOVED: Logo upload functionality - not needed
            
            // Check if the bot is asking about uploaded logos
            // Note: showUploadedLogos function is commented out, so we'll skip this for now
            // if (data.message.toLowerCase().includes('logo') && (data.message.toLowerCase().includes('uploaded') || data.message.toLowerCase().includes('have'))) {
            //     showUploadedLogos();
            // }
        } else {
            throw new Error(data.message || 'Failed to send message');
        }
    } catch (error) {
        console.error('Error:', error);
        addMessage('ai', 'Sorry, I encountered an error. Please try again.');
    } finally {
        isTyping = false;
        focusInput();
    }
}

// Quote Form Functions
function debugFormFields() {
    console.log('🔍 Debugging form fields...');
    console.log('Form element:', quoteForm);
    
    // List all form elements
    const formElements = quoteForm.elements;
    console.log('Available form elements:');
    for (let i = 0; i < formElements.length; i++) {
        const element = formElements[i];
        if (element.name) {
            console.log(`- ${element.name}: ${element.type} (current value: "${element.value}")`);
        }
    }
    
    // Check specific fields we need
    const requiredFields = ['width', 'height', 'materialPreference', 'illumination', 'installationSurface', 'cityState', 'budget', 'placement', 'deadline', 'additionalNotes'];
    requiredFields.forEach(field => {
        const element = quoteForm.elements[field];
        if (element) {
            console.log(`✅ Field ${field} found: ${element.type}`);
        } else {
            console.log(`❌ Field ${field} NOT found`);
        }
    });
}

function showQuoteForm() {
    quoteModal.classList.add('show');
    
    // Debug form fields first
    debugFormFields();
    
    // Check if we have a session ID before trying to load data
    if (sessionId) {
        console.log('🔄 Session ID found, attempting to load existing data...');
        // Always try to load existing data and restore unit buttons
        // The loadExistingQuoteData function will handle unit button restoration
        loadExistingQuoteData();
    } else {
        console.log('⚠️  No session ID found, using default form state');
        resetUnitButtons();
    }
}

function closeQuoteForm() {
    quoteModal.classList.remove('show');
    quoteForm.reset();
    // Clear uploaded logos
    uploadedLogos = [];
    logoPreviewList.innerHTML = '';
    logoPreviewContainer.style.display = 'none';
    // Don't reset unit buttons - preserve user selections for next time
    // resetUnitButtons();
}

function closeQuoteSummary() {
    quoteSummaryModal.classList.remove('show');
}

function resetUnitButtons() {
    // Reset all unit buttons to inches (default)
    const unitButtons = document.querySelectorAll('.unit-btn');
    unitButtons.forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.unit === 'inches') {
            btn.classList.add('active');
        }
        // Reset dataset unit on inputs
        const fieldGroup = btn.closest('.input-with-unit');
        const input = fieldGroup.querySelector('input');
        if (input) {
            input.dataset.unit = 'inches';
        }
    });
}

function clearStoredQuoteData() {
    // Clear any stored data in memory (not localStorage)
    console.log('Cleared stored quote data from memory');
}

function startFreshQuote() {
    clearStoredQuoteData();
    resetUnitButtons();
    quoteForm.reset();
    // Clear uploaded logos
    uploadedLogos = [];
    logoPreviewList.innerHTML = '';
    logoPreviewContainer.style.display = 'none';
}

async function handleQuoteSubmit(event) {
    event.preventDefault();
    
    if (!userEmail) {
        alert('Please provide your email address first.');
        return;
    }
    
    // Validate dimensions if provided
    const widthInput = document.getElementById('width');
    const heightInput = document.getElementById('height');
    const width = widthInput.value.trim();
    const height = heightInput.value.trim();
    
    // Only validate if both dimensions are provided
    if (width || height) {
        if (!width || !height) {
            alert('Please enter both width and height dimensions, or leave both empty.');
            return;
        }
        
        if (isNaN(width) || isNaN(height) || parseFloat(width) <= 0 || parseFloat(height) <= 0) {
            alert('Please enter valid positive numbers for dimensions.');
            return;
        }
    }
    
    const formData = new FormData(quoteForm);
    const quoteData = {};
    
    // Convert FormData to object
    for (let [key, value] of formData.entries()) {
        quoteData[key] = value;
    }
    
    // Handle dimensions with units
    const widthUnit = widthInput.dataset.unit || 'inches';
    const heightUnit = heightInput.dataset.unit || 'inches';
    
    console.log('📝 Form submission - Units:', { widthUnit, heightUnit });
    console.log('📝 Form submission - Dimensions:', { width, height });
    
    // Create formatted dimensions string
    if (width && height) {
        quoteData.sizeDimensions = `${width} ${widthUnit} × ${height} ${heightUnit}`;
        quoteData.width = width;
        quoteData.height = height;
        quoteData.widthUnit = widthUnit;
        quoteData.heightUnit = heightUnit;
        
        console.log('📐 Formatted dimensions:', quoteData.sizeDimensions);
    }
    
    // Add logo information
    quoteData.uploadedLogos = uploadedLogos;
    quoteData.logoCount = uploadedLogos.length;
    
    console.log('📤 Submitting quote data:', quoteData);
    
    try {
        const response = await fetch('/save-quote', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId,
                email: userEmail,
                form_data: quoteData
            })
        });
        
        const data = await response.json();
        console.log('📥 Save quote response:', data);
        
        if (data.success) {
            console.log('✅ Quote saved successfully, closing form and showing summary');
            closeQuoteForm();
            showQuoteSummary(quoteData);
            
            // Send a message to the bot
            addMessage('user', 'I have submitted my quote request with all the details.');
            sendMessageToBot('I have submitted my quote request with all the details.');
        } else {
            console.error('❌ Quote save failed:', data.error);
            alert('Error saving quote: ' + data.error);
        }
    } catch (error) {
        console.error('❌ Error submitting quote:', error);
        alert('Error submitting quote. Please try again.');
    }
}

function showQuoteSummary(quoteData) {
    const logoSection = quoteData.uploadedLogos && quoteData.uploadedLogos.length > 0 ? `
        <div class="quote-summary-item">
            <span class="quote-summary-label">Logo Files:</span>
            <span class="quote-summary-value">${quoteData.uploadedLogos.length} file(s) uploaded</span>
        </div>
    ` : '';
    
    const summaryHTML = `
        <div class="quote-summary">
            <h3>Your Quote Request Details</h3>
            ${logoSection}
            <div class="quote-summary-item">
                <span class="quote-summary-label">Size & Dimensions:</span>
                <span class="quote-summary-value">${quoteData.sizeDimensions || 'Not specified'}</span>
            </div>
            <div class="quote-summary-item">
                <span class="quote-summary-label">Material:</span>
                <span class="quote-summary-value">${quoteData.materialPreference || 'Not specified'}</span>
            </div>
            <div class="quote-summary-item">
                <span class="quote-summary-label">Illumination:</span>
                <span class="quote-summary-value">${quoteData.illumination || 'Not specified'}</span>
            </div>
            <div class="quote-summary-item">
                <span class="quote-summary-label">Installation Surface:</span>
                <span class="quote-summary-value">${quoteData.installationSurface || 'Not specified'}</span>
            </div>
            <div class="quote-summary-item">
                <span class="quote-summary-label">Location:</span>
                <span class="quote-summary-value">${quoteData.cityState || 'Not specified'}</span>
            </div>
            <div class="quote-summary-item">
                <span class="quote-summary-label">Budget:</span>
                <span class="quote-summary-value">${quoteData.budget || 'Not specified'}</span>
            </div>
            <div class="quote-summary-item">
                <span class="quote-summary-label">Placement:</span>
                <span class="quote-summary-value">${quoteData.placement || 'Not specified'}</span>
            </div>
            <div class="quote-summary-item">
                <span class="quote-summary-label">Deadline:</span>
                <span class="quote-summary-value">${quoteData.deadline || 'Not specified'}</span>
            </div>
            ${quoteData.additionalNotes ? `
            <div class="quote-summary-item">
                <span class="quote-summary-label">Additional Notes:</span>
                <span class="quote-summary-value">${quoteData.additionalNotes}</span>
            </div>
            ` : ''}
        </div>
        <p><strong>Next Steps:</strong></p>
        ${quoteData.uploadedLogos && quoteData.uploadedLogos.length > 0 ? 
            '<p>✅ Your logo files have been uploaded successfully and are ready for our designers to work with.</p>' : 
            '<p>Please email your logo files to <a href="mailto:info@signize.us">info@signize.us</a> so our designers can work with your brand assets.</p>'
        }
        <p>Our team will review your requirements and get back to you with a mockup and quote within a few hours.</p>
    `;
    
    quoteSummaryContent.innerHTML = summaryHTML;
    quoteSummaryModal.classList.add('show');
}

async function loadExistingQuoteData() {
    try {
        console.log('🔄 Starting to load existing quote data...');
        console.log('Session ID:', sessionId);
        
        const response = await fetch(`/get-quote/${sessionId}`);
        console.log('📡 API Response status:', response.status);
        
        if (response.ok) {
            const data = await response.json();
            console.log('📊 Raw API response data:', data);
            
            if (data.form_data && Object.keys(data.form_data).length > 0) {
                console.log('📋 Found form data with keys:', Object.keys(data.form_data));
                console.log('📋 Form data values:', data.form_data);
                
                // Wait for form to be fully ready
                await waitForFormReady();
                
                // Pre-fill the form with existing data
                let filledCount = 0;
                Object.keys(data.form_data).forEach(key => {
                    let element = quoteForm.elements[key];
                    
                    // Handle field name variations
                    if (!element) {
                        // Try alternative field names
                        const fieldMappings = {
                            'width': 'width',
                            'height': 'height',
                            'materialPreference': 'materialPreference',
                            'illumination': 'illumination',
                            'installationSurface': 'installationSurface',
                            'cityState': 'cityState',
                            'budget': 'budget',
                            'placement': 'placement',
                            'deadline': 'deadline',
                            'additionalNotes': 'additionalNotes'
                        };
                        
                        if (fieldMappings[key]) {
                            element = quoteForm.elements[fieldMappings[key]];
                        }
                    }
                    
                    if (element) {
                        element.value = data.form_data[key];
                        console.log(`✅ Filled field ${key} with value: "${data.form_data[key]}"`);
                        filledCount++;
                    } else {
                        console.log(`❌ Field ${key} not found in form`);
                    }
                });
                
                console.log(`📝 Filled ${filledCount} out of ${Object.keys(data.form_data).length} fields`);
                
                // Restore unit buttons if we have unit data
                if (data.form_data.widthUnit || data.form_data.heightUnit) {
                    console.log('🔧 Restoring unit buttons from form data:', {
                        widthUnit: data.form_data.widthUnit,
                        heightUnit: data.form_data.heightUnit
                    });
                    restoreUnitButtonsFromData(data.form_data);
                } else {
                    console.log('🔧 No unit data found in form data, using defaults');
                    resetUnitButtons();
                }
                
                console.log('✅ Form successfully loaded with existing data');
            } else {
                console.log('⚠️  No form_data found or form_data is empty');
                console.log('Data structure:', data);
                resetUnitButtons();
            }
        } else {
            console.log('❌ API response not OK:', response.status, response.statusText);
        }
    } catch (error) {
        console.error('❌ Error loading existing quote data:', error);
        resetUnitButtons();
    }
}

function waitForFormReady() {
    return new Promise((resolve) => {
        let attempts = 0;
        const maxAttempts = 50; // 5 seconds max wait
        
        const checkForm = () => {
            attempts++;
            console.log(`🔄 Checking if form is ready (attempt ${attempts})...`);
            
            // Check if key form elements exist
            const widthField = quoteForm.elements['width'];
            const materialField = quoteForm.elements['materialPreference'];
            
            if (widthField && materialField) {
                console.log('✅ Form is ready, proceeding with data loading');
                resolve();
            } else if (attempts >= maxAttempts) {
                console.log('⚠️  Form not ready after maximum attempts, proceeding anyway');
                resolve();
            } else {
                console.log('⏳ Form not ready yet, waiting...');
                setTimeout(checkForm, 100);
            }
        };
        
        checkForm();
    });
}

function restoreUnitButtonsFromData(formData) {
    try {
        console.log('Restoring unit buttons from data:', formData);
        
        if (formData.widthUnit) {
            // Restore width unit
            const widthButtons = document.querySelectorAll('[data-field="width"].unit-btn');
            console.log(`Found ${widthButtons.length} width unit buttons`);
            
            widthButtons.forEach(btn => {
                btn.classList.remove('active');
                if (btn.dataset.unit === formData.widthUnit) {
                    btn.classList.add('active');
                    console.log(`Activated width button: ${formData.widthUnit}`);
                }
            });
            
            // Update input dataset unit
            const widthInput = document.getElementById('width');
            if (widthInput) {
                widthInput.dataset.unit = formData.widthUnit;
                console.log(`Set width input unit to: ${formData.widthUnit}`);
            }
        }
        
        if (formData.heightUnit) {
            // Restore height unit
            const heightButtons = document.querySelectorAll('[data-field="height"].unit-btn');
            console.log(`Found ${heightButtons.length} height unit buttons`);
            
            heightButtons.forEach(btn => {
                btn.classList.remove('active');
                if (btn.dataset.unit === formData.heightUnit) {
                    btn.classList.add('active');
                    console.log(`Activated height button: ${formData.heightUnit}`);
                }
            });
            
            // Update input dataset unit
            const heightInput = document.getElementById('height');
            if (heightInput) {
                heightInput.dataset.unit = formData.heightUnit;
                console.log(`Set height input unit to: ${formData.heightUnit}`);
            }
        }
        
        console.log(`Successfully restored units: Width=${formData.widthUnit}, Height=${formData.heightUnit}`);
    } catch (error) {
        console.error('Error restoring unit buttons from form data:', error);
        // Fall back to default if there's an error
        resetUnitButtons();
    }
}

function requestQuoteChanges() {
    closeQuoteSummary();
    showQuoteForm();
}

// Add message to chat
function addMessage(sender, content) {
    // Remove typing indicator if it exists
    removeTypingIndicator();
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message slide-up`;
    
    const currentTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    
    messageDiv.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-${sender === 'ai' ? 'robot' : 'user'}"></i>
        </div>
        <div class="message-content">
            <div class="message-bubble">
                <p>${formatMessage(content)}</p>
            </div>
            <div class="message-time">${currentTime}</div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

// Format message content (handle links, code blocks, etc.)
function formatMessage(content) {
    // Convert URLs to clickable links
    content = content.replace(
        /(https?:\/\/[^\s]+)/g, 
        '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
    );
    
    // Convert line breaks to <br> tags
    content = content.replace(/\n/g, '<br>');
    
    return content;
}

// Add typing indicator
function addTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message ai-message typing-indicator';
    typingDiv.id = 'typing-indicator';
    
    typingDiv.innerHTML = `
        <div class="message-avatar">
            <i class="fas fa-robot"></i>
        </div>
        <div class="message-content">
            <div class="message-bubble">
                <div class="typing-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            </div>
        </div>
    `;
    
    chatMessages.appendChild(typingDiv);
    scrollToBottom();
}

// Remove typing indicator
function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Handle quick actions
function handleQuickAction(action) {
    let message = '';
    
    switch (action) {
        case 'start-design':
            message = "I'd like to start designing a custom sign. Can you help me with the process?";
            break;
        case 'get-quote':
            message = "I want a mockup and quote for a custom sign.";
            break;
        case 'view-portfolio':
            message = "Can you show me some examples of your previous work or portfolio?";
            break;
        default:
            return;
    }
    
    // Set the message in input and send it
    messageInput.value = message;
    sendMessage();
}



// Scroll to bottom of chat
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Focus on input
function focusInput() {
    messageInput.focus();
}

// Auto-resize input
function autoResizeInput() {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
}

// Minimize chat
function minimizeChat() {
    const chatContainer = document.querySelector('.chat-container');
    chatContainer.classList.toggle('minimized');
    
    if (chatContainer.classList.contains('minimized')) {
        minimizeBtn.innerHTML = '<i class="fas fa-expand"></i>';
    } else {
        minimizeBtn.innerHTML = '<i class="fas fa-minus"></i>';
    }
}

// Close chat
function closeChat() {
    const chatContainer = document.querySelector('.chat-container');
    chatContainer.classList.add('hidden');
    
    // Show FAB
    fabBtn.style.display = 'flex';
}

// Toggle chat visibility
function toggleChat() {
    const chatContainer = document.querySelector('.chat-container');
    chatContainer.classList.remove('hidden');
    chatContainer.classList.remove('minimized');
    
    // Hide FAB
    fabBtn.style.display = 'none';
    
    // Focus on input
    focusInput();
}

// Utility function to debounce
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Add CSS for typing indicator
const typingStyles = `
    .typing-indicator .message-bubble {
        background: var(--bg-tertiary);
        border: 1px solid var(--border-color);
    }
    
    .typing-dots {
        display: flex;
        gap: 4px;
        align-items: center;
        padding: 8px 0;
    }
    
    .typing-dots span {
        width: 8px;
        height: 8px;
        background: var(--text-light);
        border-radius: 50%;
        animation: typing 1.4s infinite ease-in-out;
    }
    
    .typing-dots span:nth-child(1) {
        animation-delay: -0.32s;
    }
    
    .typing-dots span:nth-child(2) {
        animation-delay: -0.16s;
    }
    
    @keyframes typing {
        0%, 80%, 100% {
            transform: scale(0.8);
            opacity: 0.5;
        }
        40% {
            transform: scale(1);
            opacity: 1;
        }
    }
    
    .chat-container.minimized {
        position: fixed;
        bottom: 0;
        right: 0;
        width: 400px;
        transform: none;
        z-index: 1000;
    }
    
    .chat-container.minimized .chat-messages,
    .chat-container.minimized .chat-input-container {
        display: none;
    }
    
    .chat-container.minimized .chat-header {
        border-radius: var(--border-radius-lg);
    }
    
    @media (max-width: 768px) {
        .chat-container.minimized {
            width: 100%;
            right: 0;
        }
    }
    
    .fab {
        display: none;
    }
    
    .input-wrapper.focused {
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    .message a {
        color: var(--primary-color);
        text-decoration: none;
        font-weight: 500;
    }
    
    .message a:hover {
        text-decoration: underline;
    }
    
    .user-message .message a {
        color: white;
        text-decoration: underline;
    }
`;

// Inject typing styles
const styleSheet = document.createElement('style');
styleSheet.textContent = typingStyles;
document.head.appendChild(styleSheet);

// Export functions for potential external use
window.SignNizeChat = {
    sendMessage,
    addMessage,
    handleQuickAction,
    toggleChat,
    minimizeChat,
    closeChat
};

function testUnitButtons() {
    console.log('Testing unit button functionality...');
    
    // Check if unit buttons exist
    const widthButtons = document.querySelectorAll('[data-field="width"].unit-btn');
    const heightButtons = document.querySelectorAll('[data-field="height"].unit-btn');
    
    console.log(`Found ${widthButtons.length} width buttons and ${heightButtons.length} height buttons`);
    
    // Check current active states
    widthButtons.forEach(btn => {
        console.log(`Width button ${btn.dataset.unit}: ${btn.classList.contains('active') ? 'active' : 'inactive'}`);
    });
    
    heightButtons.forEach(btn => {
        console.log(`Height button ${btn.dataset.unit}: ${btn.classList.contains('active') ? 'active' : 'inactive'}`);
    });
    
    // Check input dataset units
    const widthInput = document.getElementById('width');
    const heightInput = document.getElementById('height');
    
    console.log('Input dataset units:', {
        width: widthInput?.dataset.unit || 'not set',
        height: heightInput?.dataset.unit || 'not set'
    });
}

function testLoadQuoteData() {
    console.log('🧪 Testing quote data loading...');
    console.log('Session ID:', sessionId);
    
    // Test the API endpoint directly
    fetch(`/get-quote/${sessionId}`)
        .then(response => response.json())
        .then(data => {
            console.log('📊 Raw API response:', data);
            
            if (data.form_data) {
                console.log('📋 Form data keys:', Object.keys(data.form_data));
                console.log('📋 Form data values:', data.form_data);
                
                // Check if we can fill the form
                Object.keys(data.form_data).forEach(key => {
                    const element = quoteForm.elements[key];
                    if (element) {
                        console.log(`✅ Can fill ${key}: ${element.type}`);
                    } else {
                        console.log(`❌ Cannot fill ${key}: field not found`);
                    }
                });
            } else {
                console.log('⚠️  No form_data in response');
            }
        })
        .catch(error => {
            console.error('❌ Error testing quote data:', error);
        });
}

function testDatabaseConnection() {
    console.log('🧪 Testing database connection...');
    
    // Test the MongoDB status endpoint
    fetch('/mongodb-status')
        .then(response => response.json())
        .then(data => {
            console.log('📊 MongoDB Status:', data);
        })
        .catch(error => {
            console.error('❌ Error checking MongoDB status:', error);
        });
    
    // Test the test-mongodb endpoint
    fetch('/test-mongodb')
        .then(response => response.json())
        .then(data => {
            console.log('📊 MongoDB Connection Test:', data);
        })
        .catch(error => {
            console.error('❌ Error testing MongoDB connection:', error);
        });
}

function testQuoteDataStorage() {
    console.log('🧪 Testing quote data storage...');
    
    // Test saving some data
    const testData = {
        session_id: sessionId,
        email: 'test@example.com',
        form_data: {
            width: '24',
            height: '36',
            widthUnit: 'inches',
            heightUnit: 'inches',
            materialPreference: 'metal',
            illumination: 'led-backlit',
            installationSurface: 'brick-wall',
            cityState: 'New York, NY',
            budget: '1000-2500',
            placement: 'outdoor',
            deadline: 'standard',
            additionalNotes: 'Test data for debugging'
        }
    };
    
    fetch('/save-quote', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(testData)
    })
    .then(response => response.json())
    .then(data => {
        console.log('📊 Save Quote Response:', data);
        
        if (data.success) {
            console.log('✅ Test data saved successfully, now testing retrieval...');
            // Test retrieving the data
            setTimeout(() => {
                testLoadQuoteData();
            }, 1000);
        }
    })
    .catch(error => {
        console.error('❌ Error saving test data:', error);
    });
}

// Add to global scope for testing
window.testLoadQuoteData = testLoadQuoteData;
window.testDatabaseConnection = testDatabaseConnection;
window.testQuoteDataStorage = testQuoteDataStorage;

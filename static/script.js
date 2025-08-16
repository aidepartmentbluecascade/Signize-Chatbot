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
// REMOVED: Logo upload elements - not needed

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
    
    // REMOVED: Logo upload functionality - not needed
    
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

// REMOVED: All logo upload functions - not needed

// Show uploaded logos
// async function showUploadedLogos() {
//     try {
//         const response = await fetch(`/session/${sessionId}/logos`);
//         const data = await response.json();
        
//         if (data.logos && data.logos.length > 0) {
//             const logoList = data.logos.map(logo => 
//                 `• ${logo.filename} (${logo.public_url})`
//             ).join('\n');
            
//             addMessage('ai', `Here are the logos you've uploaded:\n${logoList}`);
//         } else {
//             addMessage('ai', "You haven't uploaded any logos yet.");
//         }
//     } catch (error) {
//         console.error('Error fetching logos:', error);
//         addMessage('ai', "Sorry, I couldn't retrieve your uploaded logos.");
//     }
// }

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
function showQuoteForm() {
    quoteModal.classList.add('show');
    // Initialize unit buttons to default state only if no previous data
    if (!hasPreviousQuoteData()) {
        resetUnitButtons();
    } else {
        // Restore previous unit selections from database
        restoreUnitButtonsFromDatabase();
    }
    // Pre-fill form if we have existing data
    loadExistingQuoteData();
}

function closeQuoteForm() {
    quoteModal.classList.remove('show');
    quoteForm.reset();
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
}

function restoreUnitButtonsFromDatabase() {
    // This will be called after loadExistingQuoteData loads the data
    // The unit buttons will be restored in loadExistingQuoteData
    console.log('Will restore unit buttons from database data');
}

async function handleQuoteSubmit(event) {
    event.preventDefault();
    
    if (!userEmail) {
        alert('Please provide your email address first.');
        return;
    }
    
    // Validate dimensions
    const widthInput = document.getElementById('width');
    const heightInput = document.getElementById('height');
    const width = widthInput.value.trim();
    const height = heightInput.value.trim();
    
    if (!width || !height) {
        alert('Please enter both width and height dimensions.');
        return;
    }
    
    if (isNaN(width) || isNaN(height) || parseFloat(width) <= 0 || parseFloat(height) <= 0) {
        alert('Please enter valid positive numbers for dimensions.');
        return;
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
    
    console.log('Form submission - Units:', { widthUnit, heightUnit });
    
    // Create formatted dimensions string
    if (width && height) {
        quoteData.sizeDimensions = `${width} ${widthUnit} × ${height} ${heightUnit}`;
        quoteData.width = width;
        quoteData.height = height;
        quoteData.widthUnit = widthUnit;
        quoteData.heightUnit = heightUnit;
        
        console.log('Formatted dimensions:', quoteData.sizeDimensions);
    }
    
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
        
        if (data.success) {
            closeQuoteForm();
            showQuoteSummary(quoteData);
            
            // Send a message to the bot
            addMessage('user', 'I have submitted my quote request with all the details.');
            sendMessageToBot('I have submitted my quote request with all the details.');
        } else {
            alert('Error saving quote: ' + data.error);
        }
    } catch (error) {
        console.error('Error submitting quote:', error);
        alert('Error submitting quote. Please try again.');
    }
}

function showQuoteSummary(quoteData) {
    const summaryHTML = `
        <div class="quote-summary">
            <h3>Your Quote Request Details</h3>
            <div class="quote-summary-item">
                <span class="quote-summary-label">Size & Dimensions:</span>
                <span class="quote-summary-value">${quoteData.sizeDimensions || 'Not specified'}</span>
            </div>
            <div class="quote-summary-item">
                <span class="quote-summary-label">Material:</span>
                <span class="quote-summary-value">${quoteData.materialPreference}</span>
            </div>
            <div class="quote-summary-item">
                <span class="quote-summary-label">Illumination:</span>
                <span class="quote-summary-value">${quoteData.illumination}</span>
            </div>
            <div class="quote-summary-item">
                <span class="quote-summary-label">Installation Surface:</span>
                <span class="quote-summary-value">${quoteData.installationSurface}</span>
            </div>
            <div class="quote-summary-item">
                <span class="quote-summary-label">Location:</span>
                <span class="quote-summary-value">${quoteData.cityState}</span>
            </div>
            <div class="quote-summary-item">
                <span class="quote-summary-label">Budget:</span>
                <span class="quote-summary-value">${quoteData.budget}</span>
            </div>
            <div class="quote-summary-item">
                <span class="quote-summary-label">Placement:</span>
                <span class="quote-summary-value">${quoteData.placement}</span>
            </div>
            <div class="quote-summary-item">
                <span class="quote-summary-label">Deadline:</span>
                <span class="quote-summary-value">${quoteData.deadline}</span>
            </div>
            ${quoteData.additionalNotes ? `
            <div class="quote-summary-item">
                <span class="quote-summary-label">Additional Notes:</span>
                <span class="quote-summary-value">${quoteData.additionalNotes}</span>
            </div>
            ` : ''}
        </div>
        <p><strong>Next Steps:</strong></p>
        <p>Please email your logo files to <a href="mailto:info@signize.us">info@signize.us</a> so our designers can work with your brand assets.</p>
        <p>Our team will review your requirements and get back to you with a mockup and quote within a few hours.</p>
    `;
    
    quoteSummaryContent.innerHTML = summaryHTML;
    quoteSummaryModal.classList.add('show');
}

async function loadExistingQuoteData() {
    try {
        const response = await fetch(`/get-quote/${sessionId}`);
        if (response.ok) {
            const data = await response.json();
            console.log('Loaded existing quote data:', data);
            
            if (data.form_data) {
                // Pre-fill the form with existing data
                Object.keys(data.form_data).forEach(key => {
                    const element = quoteForm.elements[key];
                    if (element) {
                        element.value = data.form_data[key];
                    }
                });
                
                // Restore unit buttons if we have unit data
                if (data.form_data.widthUnit || data.form_data.heightUnit) {
                    console.log('Restoring unit buttons from form data:', {
                        widthUnit: data.form_data.widthUnit,
                        heightUnit: data.form_data.heightUnit
                    });
                    restoreUnitButtonsFromData(data.form_data);
                } else {
                    console.log('No unit data found in form data, using defaults');
                    resetUnitButtons();
                }
            } else {
                console.log('No existing form data found');
                resetUnitButtons();
            }
        }
    } catch (error) {
        console.error('Error loading existing quote data:', error);
        resetUnitButtons();
    }
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

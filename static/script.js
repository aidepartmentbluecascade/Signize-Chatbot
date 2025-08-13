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
const logoUploadContainer = document.getElementById('logoUploadContainer');
const logoFile = document.getElementById('logoFile');
const logoUploadBtn = document.getElementById('logoUploadBtn');
const logoUploadStatus = document.getElementById('logoUploadStatus');

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
    logoFile.addEventListener('change', handleLogoFileSelect);
    logoUploadBtn.addEventListener('click', uploadLogo);
    
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

// Logo upload functions
function handleLogoFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        logoUploadBtn.disabled = false;
        showLogoUploadStatus('File selected: ' + file.name, 'uploading');
    } else {
        logoUploadBtn.disabled = true;
        hideLogoUploadStatus();
    }
}

async function uploadLogo() {
    const file = logoFile.files[0];
    if (!file) {
        showLogoUploadStatus('Please select a file first', 'error');
        return;
    }
    
    const formData = new FormData();
    formData.append('logo', file);
    formData.append('session_id', sessionId);
    
    showLogoUploadStatus('Uploading logo...', 'uploading');
    logoUploadBtn.disabled = true;
    
    try {
        const response = await fetch('/upload-logo', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            showLogoUploadStatus(`${data.message} (${data.logo_count} total logos)`, 'success');
            
            // Clear the file input for next upload but keep container visible
            logoFile.value = '';
            logoUploadBtn.disabled = true;
            
            // Hide the upload container after successful upload to prevent confusion
            setTimeout(() => {
                hideLogoUploadContainer();
            }, 2000);
            
            // Send a message to the bot indicating logo was uploaded
            setTimeout(() => {
                addMessage('user', `I've uploaded my logo: ${file.name}`);
                sendMessageToBot(`I've uploaded my logo: ${file.name}`);
            }, 1000);
            
            // Hide success message after 3 seconds
            setTimeout(() => {
                hideLogoUploadStatus();
            }, 3000);
        } else {
            showLogoUploadStatus(data.message, 'error');
            logoUploadBtn.disabled = false;
        }
    } catch (error) {
        console.error('Logo upload error:', error);
        showLogoUploadStatus('Upload failed', 'error');
        logoUploadBtn.disabled = false;
    }
}

function showLogoUploadContainer() {
    logoUploadContainer.style.display = 'block';
}

function hideLogoUploadContainer() {
    logoUploadContainer.style.display = 'none';
    // Clear file input when hiding
    logoFile.value = '';
    logoUploadBtn.disabled = true;
    hideLogoUploadStatus();
}

function showLogoUploadStatus(message, type) {
    logoUploadStatus.textContent = message;
    logoUploadStatus.className = `logo-upload-status ${type}`;
}

function hideLogoUploadStatus() {
    logoUploadStatus.style.display = 'none';
}

// Check if logos have been uploaded
async function checkIfLogosUploaded() {
    try {
        const response = await fetch(`/session/${sessionId}/logos`);
        const data = await response.json();
        return data.logos && data.logos.length > 0;
    } catch (error) {
        console.error('Error checking logos:', error);
        return false;
    }
}

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
            
            // Check if the bot is asking for email
            if (data.message.toLowerCase().includes('email') && !emailCollected) {
                showEmailField();
            }
            
            // Check if the bot is asking for logo upload (only show if not already uploaded)
            if (data.message.toLowerCase().includes('logo') && data.message.toLowerCase().includes('upload')) {
                // Check if we have uploaded logos before showing the container
                const hasUploadedLogos = await checkIfLogosUploaded();
                if (!hasUploadedLogos) {
                    showLogoUploadContainer();
                } else {
                    // If logos are already uploaded, hide the upload container and don't show upload prompt
                    hideLogoUploadContainer();
                    // Don't trigger any additional logo-related actions
                    return;
                }
            }
            
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
            message = "I'm interested in getting a quote for a custom sign. What information do you need?";
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

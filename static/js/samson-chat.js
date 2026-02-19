/**
 * Samson AI Chat Widget
 * Floating chat assistant powered by AI
 */

(function() {
    'use strict';

    // DOM Elements
    const toggleButton = document.getElementById('samson-chat-toggle');
    const chatPanel = document.getElementById('samson-chat-panel');
    const closeButton = document.getElementById('samson-chat-close');
    const chatForm = document.getElementById('samson-chat-form');
    const chatInput = document.getElementById('samson-input');
    const messagesContainer = document.getElementById('samson-messages');

    // State
    let isOpen = false;
    let isLoading = false;

    // Toggle chat panel
    function toggleChat() {
        isOpen = !isOpen;
        if (isOpen) {
            chatPanel.classList.remove('hidden');
            chatInput.focus();
        } else {
            chatPanel.classList.add('hidden');
        }
    }

    // Close chat panel
    function closeChat() {
        isOpen = false;
        chatPanel.classList.add('hidden');
    }

    // Add message to chat
    function addMessage(text, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `samson-message ${isUser ? 'samson-message-user' : 'samson-message-bot'}`;
        
        const paragraph = document.createElement('p');
        paragraph.textContent = text;
        messageDiv.appendChild(paragraph);
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Show typing indicator
    function showTyping() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'samson-typing';
        typingDiv.id = 'samson-typing';
        
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('div');
            dot.className = 'samson-typing-dot';
            typingDiv.appendChild(dot);
        }
        
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    // Remove typing indicator
    function hideTyping() {
        const typingDiv = document.getElementById('samson-typing');
        if (typingDiv) {
            typingDiv.remove();
        }
    }

    // Send message to AI
    async function sendMessage(message) {
        if (isLoading) return;
        
        isLoading = true;
        showTyping();
        
        try {
            // Call the AI chat API
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    context: window.location.pathname,
                }),
            });
            
            hideTyping();
            
            if (response.ok) {
                const data = await response.json();
                addMessage(data.response || data.message || "I'm not sure how to help with that.");
            } else {
                addMessage("Sorry, I'm having trouble connecting right now. Please try again.");
            }
        } catch (error) {
            hideTyping();
            console.error('Chat error:', error);
            addMessage("Sorry, I encountered an error. Please try again.");
        } finally {
            isLoading = false;
        }
    }

    // Handle form submission
    function handleSubmit(event) {
        event.preventDefault();
        
        const message = chatInput.value.trim();
        if (!message) return;
        
        // Add user message
        addMessage(message, true);
        
        // Clear input
        chatInput.value = '';
        
        // Send to AI
        sendMessage(message);
    }

    // Event Listeners
    toggleButton.addEventListener('click', toggleChat);
    closeButton.addEventListener('click', closeChat);
    chatForm.addEventListener('submit', handleSubmit);

    // Keyboard shortcut (Escape to close)
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && isOpen) {
            closeChat();
        }
    });

    // Initialize
    console.log('Samson AI Chat Widget initialized');
})();

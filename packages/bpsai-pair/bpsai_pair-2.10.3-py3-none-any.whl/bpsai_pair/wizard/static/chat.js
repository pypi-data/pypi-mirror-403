/**
 * Chat UI component for the PairCoder Guided Setup wizard.
 *
 * Provides message bubbles, text input, typing indicator,
 * auto-scroll, quick-reply buttons, and basic markdown rendering.
 */

/**
 * @param {Object} opts
 * @param {HTMLElement} opts.messagesContainer
 * @param {HTMLTextAreaElement} opts.inputField
 * @param {HTMLElement} opts.sendButton
 * @param {HTMLElement} opts.typingIndicator
 * @param {HTMLElement} opts.quickReplies
 * @param {HTMLElement} [opts.actionsContainer]
 * @param {HTMLElement} [opts.createButton]
 * @param {HTMLElement} [opts.customizeButton]
 * @param {HTMLElement} [opts.startOverButton]
 */
function ChatUI(opts) {
    this.messages = opts.messagesContainer;
    this.input = opts.inputField;
    this.sendBtn = opts.sendButton;
    this.typingEl = opts.typingIndicator;
    this.quickRepliesEl = opts.quickReplies;
    this.actionsEl = opts.actionsContainer || null;
    this.createBtn = opts.createButton || null;
    this.customizeBtn = opts.customizeButton || null;
    this.startOverBtn = opts.startOverButton || null;
    this._abortController = null;

    this._bindEvents();
}

/**
 * Bind DOM event listeners.
 */
ChatUI.prototype._bindEvents = function() {
    var self = this;

    this.sendBtn.addEventListener('click', function() {
        self._handleSend();
    });

    this.input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            self._handleSend();
        }
    });

    // Auto-resize textarea
    this.input.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });

    // Quick reply buttons
    if (this.quickRepliesEl) {
        var buttons = this.quickRepliesEl.querySelectorAll('.quick-reply-btn');
        buttons.forEach(function(btn) {
            btn.addEventListener('click', function() {
                var reply = this.getAttribute('data-reply');
                if (reply) {
                    self.input.value = reply;
                    self._handleSend();
                }
            });
        });
    }

    // Action buttons (Create / Customize / Start over)
    if (this.createBtn) {
        this.createBtn.addEventListener('click', function() {
            self._handleCreate();
        });
    }
    if (this.customizeBtn) {
        this.customizeBtn.addEventListener('click', function() {
            self._handleCustomize();
        });
    }
    if (this.startOverBtn) {
        this.startOverBtn.addEventListener('click', function() {
            self._handleStartOver();
        });
    }
};

/**
 * Handle sending a message from the input field.
 */
ChatUI.prototype._handleSend = function() {
    var text = this.input.value.trim();
    if (!text) return;

    this.input.value = '';
    this.input.style.height = 'auto';
    this.sendMessage(text);
};

/**
 * Add a message bubble to the chat.
 * @param {string} role - 'user' or 'assistant'
 * @param {string} content - Message text (may contain markdown)
 */
ChatUI.prototype.addMessage = function(role, content) {
    var wrapper = document.createElement('div');
    wrapper.className = 'chat-message ' + role;

    var avatar = document.createElement('div');
    avatar.className = 'chat-avatar';
    avatar.textContent = role === 'assistant' ? 'PC' : 'You';

    var bubble = document.createElement('div');
    bubble.className = 'chat-bubble ' + role;
    bubble.innerHTML = this.renderMarkdown(content);

    wrapper.appendChild(avatar);
    wrapper.appendChild(bubble);

    // Insert before the typing indicator
    if (this.typingEl && this.typingEl.parentNode === this.messages) {
        this.messages.insertBefore(wrapper, this.typingEl);
    } else {
        this.messages.appendChild(wrapper);
    }

    this.scrollToBottom();

    // Hide quick replies after first user message
    if (role === 'user' && this.quickRepliesEl) {
        this.quickRepliesEl.classList.add('hidden');
    }
};

/**
 * Show the typing indicator.
 */
ChatUI.prototype.showTypingIndicator = function() {
    if (this.typingEl) {
        this.typingEl.classList.remove('hidden');
        this.scrollToBottom();
    }
};

/**
 * Hide the typing indicator.
 */
ChatUI.prototype.hideTypingIndicator = function() {
    if (this.typingEl) {
        this.typingEl.classList.add('hidden');
    }
};

/**
 * Scroll the messages container to the bottom.
 */
ChatUI.prototype.scrollToBottom = function() {
    if (this.messages) {
        this.messages.scrollTop = this.messages.scrollHeight;
    }
};

/**
 * Render basic markdown to HTML.
 * Supports: bold, italic, inline code, code blocks, links.
 * @param {string} text - Raw markdown text
 * @returns {string} HTML string
 */
ChatUI.prototype.renderMarkdown = function(text) {
    if (!text) return '';

    // Escape HTML
    var html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');

    // Code blocks (``` ... ```)
    html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');

    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // Italic
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

    // Links (only allow http/https/relative URLs to prevent javascript: XSS)
    html = html.replace(
        /\[([^\]]+)\]\(([^)]+)\)/g,
        function(_match, text, url) {
            if (/^(https?:\/\/|\/)/.test(url)) {
                return '<a href="' + url + '" target="_blank" rel="noopener">' + text + '</a>';
            }
            return text;
        }
    );

    // Line breaks
    html = html.replace(/\n/g, '<br>');

    return html;
};

/**
 * Send a user message and stream the assistant response via SSE.
 * @param {string} text - The user's message
 */
ChatUI.prototype.sendMessage = function(text) {
    this.addMessage('user', text);
    this.showTypingIndicator();

    var self = this;
    this._abortController = new AbortController();
    this._activeBubble = null;
    this._collectedText = '';

    fetch('/api/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream',
        },
        body: JSON.stringify({ message: text }),
        signal: this._abortController.signal,
    })
        .then(function(response) {
            if (!response.ok) {
                return response.json().then(function(data) {
                    throw new Error(data.error || 'Request failed');
                });
            }
            return self._readSSEStream(response);
        })
        .catch(function(err) {
            self.hideTypingIndicator();
            if (err.name !== 'AbortError') {
                self.addMessage('assistant',
                    'Sorry, something went wrong. Please try again.');
            }
        })
        .finally(function() {
            self._abortController = null;
            self._activeBubble = null;
        });
};

/**
 * Read and process an SSE stream from a fetch response.
 * @param {Response} response - The fetch Response object
 */
ChatUI.prototype._readSSEStream = function(response) {
    var self = this;
    var reader = response.body.getReader();
    var decoder = new TextDecoder();
    var buffer = '';
    var currentEvent = 'message';

    function processChunk() {
        return reader.read().then(function(result) {
            // Process data even on final chunk
            if (result.value) {
                buffer += decoder.decode(result.value, { stream: true });
            }

            var lines = buffer.split('\n');
            buffer = lines.pop() || '';

            for (var i = 0; i < lines.length; i++) {
                var line = lines[i].trim();
                if (line.startsWith('event: ')) {
                    currentEvent = line.substring(7);
                } else if (line.startsWith('data: ')) {
                    var data = line.substring(6);
                    self._handleSSEEvent(currentEvent, data);
                    currentEvent = 'message';
                }
            }

            // Check done AFTER processing
            if (result.done) {
                // Process any remaining buffer content
                if (buffer.trim().length > 0) {
                    var remainingLines = buffer.split('\n');
                    for (var j = 0; j < remainingLines.length; j++) {
                        var remainingLine = remainingLines[j].trim();
                        if (remainingLine.startsWith('event: ')) {
                            currentEvent = remainingLine.substring(7);
                        } else if (remainingLine.startsWith('data: ')) {
                            self._handleSSEEvent(currentEvent, remainingLine.substring(6));
                        }
                    }
                }
                self.hideTypingIndicator();
                return;
            }

            return processChunk();
        });
    }

    return processChunk();
};

/**
 * Handle a single SSE event.
 * @param {string} eventType - The event name (token, done, error)
 * @param {string} data - The event data (JSON-encoded for tokens)
 */
ChatUI.prototype._handleSSEEvent = function(eventType, data) {
    if (eventType === 'token') {
        this.hideTypingIndicator();
        // Token data is JSON-encoded to preserve special characters
        try {
            var token = JSON.parse(data);
            this._appendToken(token);
        } catch (e) {
            // Fallback: use raw data if JSON parsing fails
            this._appendToken(data);
        }
    } else if (eventType === 'done') {
        this.hideTypingIndicator();
        this._showActions();  // Always show buttons after response completes
    } else if (eventType === 'error') {
        this.hideTypingIndicator();
        this.addMessage('assistant',
            'Sorry, something went wrong: ' + data);
    }
};

/**
 * Append a token to the active assistant bubble, creating it if needed.
 * @param {string} token - The text token to append
 */
ChatUI.prototype._appendToken = function(token) {
    this._collectedText += token;

    if (!this._activeBubble) {
        var wrapper = document.createElement('div');
        wrapper.className = 'chat-message assistant';

        var avatar = document.createElement('div');
        avatar.className = 'chat-avatar';
        avatar.textContent = 'PC';

        var bubble = document.createElement('div');
        bubble.className = 'chat-bubble assistant';

        wrapper.appendChild(avatar);
        wrapper.appendChild(bubble);

        if (this.typingEl && this.typingEl.parentNode === this.messages) {
            this.messages.insertBefore(wrapper, this.typingEl);
        } else {
            this.messages.appendChild(wrapper);
        }

        this._activeBubble = bubble;
    }

    this._activeBubble.innerHTML = this.renderMarkdown(this._collectedText);
    this.scrollToBottom();
};

/**
 * Check if the latest assistant response contains a paircoder_config XML block.
 * If found, show the action buttons (Create / Customize / Start over).
 * Uses multiple detection strategies in case of character dropping during SSE streaming.
 */
ChatUI.prototype._checkForConfig = function() {
    if (!this._collectedText) return;

    var text = this._collectedText;

    // Primary detection: full opening tag
    if (text.indexOf('<paircoder_config>') !== -1) {
        this._showActions();
        return;
    }

    // Fallback 1: Case-insensitive check
    if (text.toLowerCase().indexOf('<paircoder_config>') !== -1) {
        this._showActions();
        return;
    }

    // Fallback 2: Check for partial patterns (in case < is dropped)
    // Look for "paircoder_config" followed by project_name patterns
    if (text.indexOf('paircoder_config') !== -1 &&
        (text.indexOf('project_name') !== -1 || text.indexOf('Project Name') !== -1)) {
        this._showActions();
        return;
    }

    // Fallback 3: Look for the structured summary format
    if (text.indexOf('**Project Name:**') !== -1 &&
        text.indexOf('**Description:**') !== -1) {
        this._showActions();
        return;
    }

    // Fallback 4: JSON config format
    if (text.indexOf('"project_name"') !== -1 ||
        text.indexOf('"projectName"') !== -1) {
        this._showActions();
        return;
    }
};

/**
 * Show the action buttons panel.
 */
ChatUI.prototype._showActions = function() {
    if (this.actionsEl) {
        this.actionsEl.classList.remove('hidden');
        this.scrollToBottom();
    }
};

/**
 * Hide the action buttons panel.
 */
ChatUI.prototype._hideActions = function() {
    if (this.actionsEl) {
        this.actionsEl.classList.add('hidden');
    }
};

/**
 * Handle "Create it!" — send config to server and redirect to Review.
 */
ChatUI.prototype._handleCreate = function() {
    var self = this;
    fetch('/api/chat/create', { method: 'POST' })
        .then(function(response) { return response.json(); })
        .then(function(data) {
            if (data.success && data.next_url) {
                window.location.href = data.next_url;
            } else {
                self.addMessage('assistant',
                    'Could not create project: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(function() {
            self.addMessage('assistant',
                'Sorry, something went wrong. Please try again.');
        });
};

/**
 * Handle "Customize" — pre-fill and switch to Quick Setup.
 */
ChatUI.prototype._handleCustomize = function() {
    var self = this;
    fetch('/api/chat/customize', { method: 'POST' })
        .then(function(response) { return response.json(); })
        .then(function(data) {
            if (data.success && data.next_url) {
                window.location.href = data.next_url;
            } else {
                self.addMessage('assistant',
                    'Could not switch to Quick Setup: ' + (data.error || 'Unknown error'));
            }
        })
        .catch(function() {
            self.addMessage('assistant',
                'Sorry, something went wrong. Please try again.');
        });
};

/**
 * Handle "Start over" — clear history and reset the chat.
 */
ChatUI.prototype._handleStartOver = function() {
    var self = this;
    fetch('/api/chat/reset', { method: 'POST' })
        .then(function(response) { return response.json(); })
        .then(function(data) {
            if (data.success) {
                self._hideActions();
                // Clear all message bubbles except the initial one
                var bubbles = self.messages.querySelectorAll('.chat-message:not(.typing-indicator)');
                for (var i = 1; i < bubbles.length; i++) {
                    bubbles[i].remove();
                }
                self._collectedText = '';
                self._activeBubble = null;
                // Show quick replies again
                if (self.quickRepliesEl) {
                    self.quickRepliesEl.classList.remove('hidden');
                }
            }
        })
        .catch(function() {
            self.addMessage('assistant',
                'Sorry, could not reset. Please try again.');
        });
};

/**
 * Cancel an in-progress generation request.
 */
ChatUI.prototype.cancelGeneration = function() {
    if (this._abortController) {
        this._abortController.abort();
        this._abortController = null;
        this.hideTypingIndicator();

        // Notify the server to stop generation
        fetch('/api/chat/cancel', { method: 'POST' })
            .catch(function() { /* ignore cancel errors */ });
    }
};

/**
 * Show dynamic quick reply buttons.
 * @param {string[]} replies - Array of quick reply labels
 */
ChatUI.prototype._showQuickReplies = function(replies) {
    if (!this.quickRepliesEl) return;

    this.quickRepliesEl.innerHTML = '';
    var self = this;

    replies.forEach(function(label) {
        var btn = document.createElement('button');
        btn.className = 'quick-reply-btn';
        btn.setAttribute('data-reply', label);
        btn.textContent = label;
        btn.addEventListener('click', function() {
            self.input.value = label;
            self._handleSend();
        });
        self.quickRepliesEl.appendChild(btn);
    });

    this.quickRepliesEl.classList.remove('hidden');
};

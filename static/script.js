// static/script.js
document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatBox = document.getElementById('chat-box');


    sessionId = generateSessionId();

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = userInput.value.trim();
        if (!message) return;

        appendMessage('user', message);
        userInput.value = '';

        try {
            const response = await fetch('/surf-ai', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    session_chat_history: getChatHistory(),
                    user_id: 'user123', 
                }),
            });

            const data = await response.json();

            if (response.ok) {
                if (typeof data.assistant === 'string') {
                    appendMessage('assistant', data.assistant);
                } else {
                    appendMessage('assistant', JSON.stringify(data.assistant));
                    console.warn('assistant is not a string:', data.assistant);
                }
            } else {
                appendMessage('assistant', `Error: ${data.error}`);
                console.error('Backend Error:', data.error);
            }
        } catch (error) {
            appendMessage('assistant', `Error: ${error.message}`);
            console.error('Fetch Error:', error);
        }
    });

    function appendMessage(role, message) {
        const msgDiv = document.createElement('div');
        msgDiv.classList.add('message', role);

        if (role === 'assistant') {
            if (message) {
                const rawHtml = marked.parse(message);
                const cleanHtml = DOMPurify.sanitize(rawHtml);
                msgDiv.innerHTML = cleanHtml;
            } else {
                msgDiv.textContent = "No message received.";
            }
        } else {
            msgDiv.textContent = message;
        }


        chatBox.appendChild(msgDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function getChatHistory() {
        const messages = chatBox.querySelectorAll('.message');
        const history = [];
        messages.forEach(msg => {
            const role = msg.classList.contains('user') ? 'user' : 'assistant';
            const message = role === 'user' ? msg.textContent : msg.innerText;
            history.push({ role, content: message });
        });
        return history;
    }

    function generateSessionId() {
        return 'session_' + Math.random().toString(36).substr(2, 9);
    }
});

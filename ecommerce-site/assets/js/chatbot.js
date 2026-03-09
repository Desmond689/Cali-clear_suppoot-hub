// WhatsApp-style chat widget
let chatEmail = null;
let chatName = null;
let chatPollInterval = null;

function initChat() {
  const bubble = document.getElementById('chat-bubble');
  const panel = document.getElementById('chat-panel');
  const input = document.getElementById('chat-input');
  const messages = document.getElementById('chat-messages');

  if (!bubble || !panel || !input || !messages) {
    console.warn('Chat elements not found');
    return;
  }

  bubble.addEventListener('click', () => {
    const isHidden = panel.classList.contains('hidden');
    panel.classList.toggle('hidden');
    
    if (!isHidden) {
      // Chat is being closed
      if (chatPollInterval) {
        clearInterval(chatPollInterval);
        chatPollInterval = null;
      }
    } else {
      // Chat is being opened
      loadChatHistory();
      // Poll for new messages every 2 seconds
      chatPollInterval = setInterval(loadChatHistory, 2000);
      input.focus();
    }
  });

  input.addEventListener('keydown', e => {
    if (e.key !== 'Enter') return;
    const text = e.target.value.trim();
    if (!text) return;
    
    // Get or prompt for email
    if (!chatEmail) {
      chatEmail = localStorage.getItem('user_email') || prompt('Please enter your email:') || 'anonymous@example.com';
      chatName = localStorage.getItem('user_name') || prompt('What is your name?') || 'Guest';
    }
    
    // Display user message immediately
    messages.innerHTML += `<div class="chat-message user-message" style="text-align:right;margin:8px 0;">
      <div style="background:#ff6f61;color:#fff;padding:8px 12px;border-radius:12px;display:inline-block;max-width:70%;word-wrap:break-word;">${escapeHtml(text)}</div>
    </div>`;
    messages.scrollTop = messages.scrollHeight;
    
    // Send message to backend
    fetch('/api/messages', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: chatEmail, name: chatName, message: text })
    })
      .then(res => res.json())
      .then(json => {
        if (json.status !== 'success') {
          messages.innerHTML += `<div class="chat-message admin-message" style="margin:8px 0;">
            <div style="background:#333;color:#ccc;padding:8px 12px;border-radius:12px;display:inline-block;max-width:70%;word-wrap:break-word;">Error sending message</div>
          </div>`;
          messages.scrollTop = messages.scrollHeight;
        }
      })
      .catch(err => {
        console.error('Chat error:', err);
        messages.innerHTML += `<div class="chat-message admin-message" style="margin:8px 0;">
          <div style="background:#333;color:#ccc;padding:8px 12px;border-radius:12px;display:inline-block;max-width:70%;word-wrap:break-word;">Network error</div>
        </div>`;
        messages.scrollTop = messages.scrollHeight;
      });
    
    e.target.value = '';
  });
}

async function loadChatHistory() {
  if (!chatEmail) return;
  
  const messages = document.getElementById('chat-messages');
  if (!messages) return;
  
  try {
    const res = await fetch(`/api/messages/thread?email=${encodeURIComponent(chatEmail)}`);
    const json = await res.json();
    
    if (json.status !== 'success') return;
    
    const thread = json.data || [];
    
    // Render conversation
    let html = '';
    thread.forEach(msg => {
      // User message
      html += `<div class="chat-message user-message" style="text-align:right;margin:8px 0;">
        <div style="background:#ff6f61;color:#fff;padding:8px 12px;border-radius:12px;display:inline-block;max-width:70%;word-wrap:break-word;">${escapeHtml(msg.message)}</div>
        <div style="font-size:11px;color:#999;margin-top:4px;">${formatChatTime(msg.created_at)}</div>
      </div>`;
      
      // Admin reply (if exists)
      if (msg.admin_reply) {
        html += `<div class="chat-message admin-message" style="margin:8px 0;">
          <div style="background:#e0e0e0;color:#333;padding:8px 12px;border-radius:12px;display:inline-block;max-width:70%;word-wrap:break-word;">${escapeHtml(msg.admin_reply)}</div>
          <div style="font-size:11px;color:#999;margin-top:4px;">${formatChatTime(msg.replied_at)}</div>
        </div>`;
      }
    });
    
    // Only update if content changed to avoid flicker
    if (messages.innerHTML !== html) {
      messages.innerHTML = html;
      messages.scrollTop = messages.scrollHeight;
    }
  } catch (err) {
    console.error('Error loading chat history:', err);
  }
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function formatChatTime(isoString) {
  if (!isoString) return '';
  const date = new Date(isoString);
  const hours = String(date.getHours()).padStart(2, '0');
  const mins = String(date.getMinutes()).padStart(2, '0');
  return `${hours}:${mins}`;
}

// Initialize immediately since script is at end of page
initChat();

// Also try on DOMContentLoaded as backup
document.addEventListener('DOMContentLoaded', initChat);

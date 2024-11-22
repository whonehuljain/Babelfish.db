document.addEventListener('DOMContentLoaded', () => {
  const userInput = document.getElementById('user-message');
  const sendBtn = document.getElementById('send-btn');
  const chatHistory = document.getElementById('chat-history');
  const themeToggle = document.getElementById('theme-toggle');
  const body = document.body;
  const connectLink = document.getElementById('connect-link');
  

   // Get connection information from data attributes
   const chatWrapper = document.querySelector('.chat-wrapper');
   const connectionType = chatWrapper.dataset.connectionType;
   const hasConnection = chatWrapper.dataset.connectionStatus !== '';

   // Update connection status
   function updateDBStatus(isConnected, dbType = '') {
    const dbStatusDot = document.getElementById('status-dot');
    const dbStatusText = document.querySelector('.status-text');
    
    if (isConnected) {
        dbStatusDot.classList.remove('red-dot');
        dbStatusDot.classList.add('green-dot');
        dbStatusText.innerHTML = `Connected to ${dbType}`;
    } else {
        dbStatusDot.classList.remove('green-dot');
        dbStatusDot.classList.add('red-dot');
        dbStatusText.innerHTML = `DB Not Connected, <a href="#" id="connect-link" class="text-primary">Connect Database</a>`;
        
        // Re-attach event listener for connect link
        const connectLink = document.getElementById('connect-link');
        if (connectLink) {
            connectLink.addEventListener('click', (e) => {
                e.preventDefault();
                window.location.href = '/';  // or wherever your connection page is
            });
        }
    }
}

    // Update status on page load
    const dbType = connectionType === 'mysql' ? 'MySQL' : 
    connectionType === 'mongodb' ? 'MongoDB' : '';
    updateDBStatus(hasConnection, dbType);



  // Theme Toggle Functionality (Previous implementation remains the same)
  themeToggle.addEventListener('click', () => {
      body.classList.toggle('dark-theme');
      body.classList.toggle('light-theme');
      
      const currentTheme = body.classList.contains('dark-theme') ? 'dark' : 'light';
      localStorage.setItem('theme', currentTheme);
  });

  // Check and Apply Saved Theme on Load (Previous implementation remains the same)
  const savedTheme = localStorage.getItem('theme');
  if (savedTheme === 'light') {
      body.classList.remove('dark-theme');
      body.classList.add('light-theme');
  }

//   // DB Connection Status (Previous implementation remains the same)
//   function updateDBStatus(isConnected, dbName = '') {
//       if (isConnected) {
//           dbStatusDot.classList.remove('red-dot');
//           dbStatusDot.classList.add('green-dot');
//           dbStatusText.innerHTML = `Connected to ${dbName || 'Database'}`;
//       } else {
//           dbStatusDot.classList.remove('green-dot');
//           dbStatusDot.classList.add('red-dot');
//           dbStatusText.innerHTML = `DB Not Connected, <a href="#" id="connect-link" class="text-primary">Connect Database</a>`;
//       }
//   }

//   // Simulated initial state
//   updateDBStatus(false);

  // Connect Link Event (Previous implementation remains the same)
  connectLink.addEventListener('click', (e) => {
      e.preventDefault();
      window.location.href = '/connect-database/';
  });

  // Create Profile Icon
  function createProfileIcon(type) {
      const icon = document.createElement('div');
      icon.classList.add('profile-icon');
      
      if (type === 'user') {
          icon.classList.add('user-profile');
          icon.textContent = 'U';
      } else {
          icon.classList.add('bot-profile');
          icon.textContent = 'AI';
      }
      
      return icon;
  }

  // Send user message
  async function sendMessage() {
      const message = userInput.value.trim();
      if (!message) return;

      addMessage('user', message);

      try {
          const response = await fetch('/chat/', {
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json',
                  'X-CSRFToken': getCsrfToken()
              },
              body: JSON.stringify({ prompt: message })
          });

          if (response.ok) {
              const data = await response.json();
              addMessage('bot', data.reply || 'No response');
          } else {
              addMessage('bot', 'Error: Unable to process request');
          }
      } catch (error) {
          console.error('Error sending message:', error);
          addMessage('bot', 'Error: Server not reachable');
      }

      userInput.value = '';
  }

  // Send message on button click and Enter keypress (Previous implementation remains the same)
  sendBtn.addEventListener('click', sendMessage);
  userInput.addEventListener('keypress', (event) => {
      if (event.key === 'Enter') {
          event.preventDefault();
          sendMessage();
      }
  });

  // Add message to chat history with profile icon
  function addMessage(sender, message) {
      // Create message container
      const messageContainer = document.createElement('div');
      messageContainer.classList.add('chat-message-container', sender);

      // Create profile icon
      const profileIcon = createProfileIcon(sender);

      // Create message bubble
      const bubble = document.createElement('div');
      bubble.className = `chat-bubble ${sender}`;
      bubble.innerText = message;

      // Append profile icon and message bubble to container
      messageContainer.appendChild(profileIcon);
      messageContainer.appendChild(bubble);

      // Add to chat history
      chatHistory.appendChild(messageContainer);
      chatHistory.scrollTop = chatHistory.scrollHeight;
  }

  // Function to get CSRF token from cookie (Previous implementation remains the same)
  function getCsrfToken() {
      const cookies = document.cookie.split(';');
      for (let cookie of cookies) {
          const [name, value] = cookie.trim().split('=');
          if (name === 'csrftoken') return value;
      }
      return '';
  }
});
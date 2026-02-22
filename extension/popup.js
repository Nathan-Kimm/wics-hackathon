// Fetch current track from Flask backend
async function updateCurrentTrack() {
    try {
        const response = await fetch('http://127.0.0.1:5000/current_track', {
            credentials: 'include' 
        });

        if (!response.ok) {
            if (response.status === 401) {
                showError('Not authenticated. Please visit http://127.0.0.1:5000/login');
                return;
            }
            if (response.status === 404) {
                showError('No track currently playing');
                return;
            }
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        // Update track name
        document.getElementById('track-name').textContent = data.track;

        // Update artist name
        document.getElementById('artist-name').textContent = data.artist;

        // Update album cover
        const albumImage = document.getElementById('album-image');
        albumImage.src = data.album_cover;
        albumImage.style.display = 'block';

    } catch (error) {
        console.error('Error fetching track:', error);
        showError('Failed to connect to Spotify API');
    }
}

function showError(message) {
    document.getElementById('track-name').textContent = message;
    document.getElementById('artist-name').textContent = '';
    document.getElementById('album-image').style.display = 'none';
}

// Update track info when popup opens
document.addEventListener('DOMContentLoaded', () => {
    updateCurrentTrack();

    // Optionally refresh every 3 seconds
    setInterval(updateCurrentTrack, 3000);

    // ── Chat ──
    const input = document.getElementById('chat-input');
    const sendBtn = document.getElementById('chat-send');

    function appendBubble(text, role) {
        const messages = document.getElementById('chat-messages');
        const bubble = document.createElement('div');
        bubble.classList.add('chat-bubble', role);
        bubble.textContent = text;
        messages.appendChild(bubble);
        messages.scrollTop = messages.scrollHeight;
    }

    async function sendMessage() {
        const text = input.value.trim();
        if (!text) return;
        input.value = '';
        appendBubble(text, 'user');

        // Show a thinking indicator
        const messages = document.getElementById('chat-messages');
        const thinking = document.createElement('div');
        thinking.classList.add('chat-bubble', 'bot');
        thinking.textContent = 'Thinking...';
        messages.appendChild(thinking);
        messages.scrollTop = messages.scrollHeight;

        try {
            // Grab currently displayed track & artist
            const trackName = document.getElementById('track-name').textContent || '';
            const artistName = document.getElementById('artist-name').textContent || '';

            const response = await fetch('http://127.0.0.1:5000/chat', {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text,
                    current_track: trackName,
                    current_artist: artistName
                })
            });

            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            thinking.remove();
            appendBubble(data.reply || data.error || JSON.stringify(data), 'bot');
        } catch (err) {
            thinking.remove();
            appendBubble('Error: ' + err.message, 'bot');
        }
    }

    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') sendMessage();
    });
});

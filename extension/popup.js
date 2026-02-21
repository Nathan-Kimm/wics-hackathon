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
});

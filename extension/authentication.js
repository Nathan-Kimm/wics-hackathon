document.addEventListener('DOMContentLoaded', function() {
    const loginBtn = document.getElementById('login-btn');
    const statusMessage = document.getElementById('status-message');

    checkAuthStatus();

    loginBtn.addEventListener('click', function() {
        chrome.tabs.create({
            url: 'http://127.0.0.1:5000/login'
        });
        statusMessage.textContent = 'Please complete authentication in the new tab...';
    });

    function checkAuthStatus() {
        fetch('http://127.0.0.1:5000/current_track')
            .then(response => {
                if (response.ok) {
                    window.location.href = 'popup.html';
                } else {
                    statusMessage.textContent = 'Ready to connect';
                }
            })
    }

    setInterval(checkAuthStatus, 3000);
});

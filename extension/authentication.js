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
                console.log(response);
                if (response.status == "404" || response.ok) {
                    window.location.href = 'popup.html';
                }
            })
            .catch(error => {
                console.log('Backend not running or authenticated');
                statusMessage.textContent = 'Make sure backend is running';
            });
    }

    setInterval(checkAuthStatus, 3000);
});

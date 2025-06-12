// Progress indicator functionality
function updateProgress(progress, message) {
    const progressBar = document.getElementById('progressBar');
    const statusMessage = document.getElementById('statusMessage');
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    // Show overlay if not already shown
    if (loadingOverlay && loadingOverlay.style.display === 'none') {
        loadingOverlay.style.display = 'flex';
    }
    
    if (progressBar) {
        progressBar.style.width = progress + '%';
    }
    
    if (statusMessage) {
        statusMessage.textContent = message;
        statusMessage.style.display = 'block';
        statusMessage.className = 'status-message info';
    }
}

function showError(message) {
    const statusMessage = document.getElementById('statusMessage');
    if (statusMessage) {
        statusMessage.textContent = message;
        statusMessage.className = 'status-message error';
        statusMessage.style.display = 'block';
    }
}

function hideProgress() {
    const loadingOverlay = document.getElementById('loadingOverlay');
    if (loadingOverlay) {
        loadingOverlay.style.display = 'none';
    }
}

// Export functions for use in other modules
window.progressIndicator = {
    update: updateProgress,
    error: showError,
    hide: hideProgress
};

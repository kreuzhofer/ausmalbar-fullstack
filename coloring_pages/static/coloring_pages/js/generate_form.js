function updateProgress(progress, message) {
    const progressBar = document.getElementById('progressBar');
    const statusMessage = document.getElementById('statusMessage');
    
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

function handleFormSubmit(event) {
    event.preventDefault();
    
    const form = event.target;
    const formData = new FormData(form);
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    // Show loading overlay
    if (loadingOverlay) {
        loadingOverlay.style.display = 'flex';
    }
    
    // Update progress
    updateProgress(10, 'Starting image generation...');
    
    // Start progress simulation
    let progress = 10;
    const maxProgress = 90;
    const progressInterval = setInterval(() => {
        if (progress < maxProgress) {
            progress += 5;
            updateProgress(progress, 'Generating your coloring page... (This may take a minute)');
        }
    }, 2000);
    
    // Submit form via AJAX
    fetch(form.action, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
    })
    .then(response => {
        clearInterval(progressInterval);
        
        if (!response.ok) {
            return response.json().then(err => {
                throw new Error(err.error || 'Network response was not ok');
            });
        }
        return response.json();
    })
    .then(data => {
        if (data.redirect) {
            // If we got a redirect URL, navigate to it
            updateProgress(100, 'Image generated successfully! Redirecting...');
            setTimeout(() => {
                window.location.href = data.redirect;
            }, 1000);
        } else if (data.error) {
            throw new Error(data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showError('Error: ' + (error.message || 'Failed to generate image. Please try again.'));
        
        // Hide loading overlay after a delay
        setTimeout(() => {
            if (loadingOverlay) {
                loadingOverlay.style.display = 'none';
            }
        }, 5000);
    });
    
    return false;
}

// Add event listener when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('coloringpage_form');
    if (form) {
        form.onsubmit = handleFormSubmit;
    }
});

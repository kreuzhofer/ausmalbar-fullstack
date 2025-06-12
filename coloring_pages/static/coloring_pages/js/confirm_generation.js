document.addEventListener('DOMContentLoaded', function() {
    // Get form and action buttons
    const form = document.getElementById('confirm-form');
    const regenerateBtn = document.getElementById('regenerate_btn');
    const confirmBtn = document.querySelector('button[value="confirm"]');
    const rejectBtn = document.querySelector('button[value="reject"]');
    const promptField = document.getElementById('prompt');
    const hiddenPrompt = document.getElementById('hidden_prompt');
    const systemPromptSelect = document.getElementById('system_prompt_select');
    const systemPromptInput = document.getElementById('system_prompt_input');
    const formAction = document.getElementById('form_action');
    
    // Function to handle form submission
    function submitForm(action) {
        // Update the hidden prompt with the current value
        if (promptField && hiddenPrompt) {
            hiddenPrompt.value = promptField.value.trim();
        }
        
        // Update the system prompt input with the selected value
        if (systemPromptSelect && systemPromptInput) {
            systemPromptInput.value = systemPromptSelect.value;
        }
        
        // Set the form action
        if (formAction) {
            formAction.value = action;
        }
        
        // Show loading indicator
        const message = action === 'regenerate' ? 'Regenerating image...' : 
                       action === 'confirm' ? 'Saving coloring page...' : 
                       'Deleting generated content...';
        
        window.progressIndicator.update(0, message);
        
        // For regenerate action, we need to handle the response differently
        if (action === 'regenerate') {
            // Create form data and add the action
            const formData = new FormData(form);
            formData.set('action', 'regenerate');
            
            // Show loading indicator
            window.progressIndicator.update(0, 'Regenerating image...');
            
            // Show loading overlay
            const loadingOverlay = document.getElementById('loadingOverlay');
            if (loadingOverlay) {
                loadingOverlay.style.display = 'flex';
            }
            
            // Start progress simulation
            let progress = 10;
            const maxProgress = 90;
            const progressInterval = setInterval(() => {
                if (progress < maxProgress) {
                    progress += 5;
                    window.progressIndicator.update(progress, 'Regenerating your coloring page... (This may take a minute)');
                }
            }, 2000);
            
            // Submit the form via fetch
            fetch('', {  // Use empty string to submit to current URL
                method: 'POST',
                body: formData,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-Action': 'regenerate',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                credentials: 'same-origin'  // Include CSRF token
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
                if (data.success && data.thumb_data) {
                    // Update progress to 100%
                    window.progressIndicator.update(100, 'Image regenerated successfully!');
                    
                    // Update the preview image
                    const previewImg = document.querySelector('.preview-thumbnail');
                    if (previewImg) {
                        previewImg.src = data.thumb_data;
                    } else {
                        // If preview image doesn't exist, create it
                        const previewContainer = document.querySelector('.preview-container');
                        if (previewContainer) {
                            const img = document.createElement('img');
                            img.src = data.thumb_data;
                            img.className = 'preview-thumbnail';
                            img.alt = 'Preview';
                            previewContainer.innerHTML = '';
                            previewContainer.appendChild(img);
                        }
                    }
                    
                    // Update the title and description fields
                    if (data.title_en) {
                        const titleEnField = document.querySelector('.preview-field:nth-child(1) .value');
                        if (titleEnField) titleEnField.textContent = data.title_en;
                    }
                    if (data.title_de) {
                        const titleDeField = document.querySelector('.preview-field:nth-child(3) .value');
                        if (titleDeField) titleDeField.textContent = data.title_de;
                    }
                    if (data.description_en) {
                        const descEnField = document.querySelector('.preview-field:nth-child(2) .value');
                        if (descEnField) descEnField.textContent = data.description_en;
                    }
                    if (data.description_de) {
                        const descDeField = document.querySelector('.preview-field:nth-child(4) .value');
                        if (descDeField) descDeField.textContent = data.description_de;
                    }
                    
                    // Update the prompt field
                    if (data.prompt && promptField) {
                        promptField.value = data.prompt;
                    }
                    
                    // Hide the progress indicator after a delay
                    setTimeout(() => {
                        window.progressIndicator.hide();
                    }, 1000);
                } else if (data.redirect) {
                    window.location.href = data.redirect;
                } else {
                    throw new Error('Invalid response from server');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                window.progressIndicator.error(error.message || 'An error occurred while regenerating. Please try again.');
                
                // Hide loading overlay after a delay
                setTimeout(() => {
                    if (loadingOverlay) {
                        loadingOverlay.style.display = 'none';
                    }
                }, 5000);
            });
        } else if (action === 'reject') {
            // For reject action, show confirmation dialog
            if (confirm('Are you sure you want to reject this coloring page? This action cannot be undone.')) {
                form.submit();
            } else {
                window.progressIndicator.hide();
            }
        } else {
            // For confirm action, just submit the form
            form.submit();
        }
    }
    
    // Handle form submission for confirm and reject buttons
    if (form) {
        form.addEventListener('submit', function(e) {
            // Only prevent default for buttons with name='action'
            if (e.submitter && e.submitter.name === 'action') {
                e.preventDefault();
                const action = e.submitter.value;
                submitForm(action);
            }
        });
    }
    
    // Handle regenerate button click
    if (regenerateBtn) {
        regenerateBtn.addEventListener('click', function(e) {
            e.preventDefault();
            submitForm('regenerate');
        });
    }
});

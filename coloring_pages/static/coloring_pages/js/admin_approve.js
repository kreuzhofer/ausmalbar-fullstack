/* Adds an "Approve & Publish" button next to the status dropdown on the
 * ColoringPage change form. Only shown when current status is "draft".
 */
(function() {
    document.addEventListener('DOMContentLoaded', function() {
        var statusSelect = document.getElementById('id_status');
        if (!statusSelect) return;

        // Only show the button if current value is draft
        if (statusSelect.value !== 'draft') return;

        var btn = document.createElement('button');
        btn.type = 'button';
        btn.textContent = 'Approve & Publish';
        btn.className = 'button';
        btn.style.cssText = 'margin-left: 10px; background-color: #4a9c5d; color: white; padding: 6px 14px; border: none; border-radius: 4px; cursor: pointer;';

        btn.addEventListener('click', function() {
            // Set status to published
            statusSelect.value = 'published';

            // Find and click the default Save button (returns to changelist)
            var saveBtn = document.querySelector('.submit-row input[name="_save"]');
            if (saveBtn) {
                saveBtn.click();
            } else {
                // Fallback: submit the form directly
                statusSelect.form.submit();
            }
        });

        statusSelect.parentNode.appendChild(btn);
    });
})();

/**
 * PairCoder Setup Wizard JavaScript
 */

/**
 * Show the upgrade modal with optional feature name
 * @param {string} featureName - The name of the feature requiring upgrade
 */
function showUpgradeModal(featureName) {
    const modal = document.getElementById('upgrade-modal');
    if (modal) {
        // Update the feature title if provided
        const featureTitle = document.getElementById('modal-feature-title');
        if (featureTitle && featureName) {
            featureTitle.textContent = featureName;
        } else if (featureTitle) {
            featureTitle.textContent = 'Pro Features';
        }
        modal.classList.remove('hidden');
        // Focus the close button for accessibility
        const closeBtn = modal.querySelector('.modal-close');
        if (closeBtn) {
            closeBtn.focus();
        }
    }
}

/**
 * Hide the upgrade modal
 */
function hideUpgradeModal() {
    const modal = document.getElementById('upgrade-modal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

/**
 * Show license install modal
 */
function showLicenseInstall() {
    hideUpgradeModal();
    const modal = document.getElementById('license-install-modal');
    if (modal) {
        modal.classList.remove('hidden');
        // Clear any previous state
        clearLicenseForm();
        // Focus the file input
        const fileInput = document.getElementById('license-file');
        if (fileInput) {
            fileInput.focus();
        }
    }
}

/**
 * Hide license install modal
 */
function hideLicenseInstall() {
    const modal = document.getElementById('license-install-modal');
    if (modal) {
        modal.classList.add('hidden');
        clearLicenseForm();
    }
}

/**
 * Clear the license install form
 */
function clearLicenseForm() {
    const fileInput = document.getElementById('license-file');
    const jsonInput = document.getElementById('license-json');
    const fileName = document.getElementById('file-name');
    const statusDiv = document.getElementById('license-install-status');

    if (fileInput) fileInput.value = '';
    if (jsonInput) jsonInput.value = '';
    if (fileName) fileName.textContent = 'No file selected';
    if (statusDiv) {
        statusDiv.classList.add('hidden');
        statusDiv.textContent = '';
        statusDiv.className = 'status-message hidden';
    }
}

/**
 * Handle file selection for license upload
 * @param {Event} event - The file input change event
 */
function handleFileSelect(event) {
    const file = event.target.files[0];
    const fileName = document.getElementById('file-name');

    if (file) {
        if (fileName) fileName.textContent = file.name;

        // Read the file content
        const reader = new FileReader();
        reader.onload = function(e) {
            const jsonInput = document.getElementById('license-json');
            if (jsonInput) {
                jsonInput.value = e.target.result;
            }
        };
        reader.onerror = function() {
            showLicenseError('Failed to read file');
        };
        reader.readAsText(file);
    } else {
        if (fileName) fileName.textContent = 'No file selected';
    }
}

/**
 * Submit license installation
 * @param {Event} event - The form submit event
 */
function submitLicenseInstall(event) {
    event.preventDefault();

    const jsonInput = document.getElementById('license-json');
    const licenseJson = jsonInput ? jsonInput.value.trim() : '';

    if (!licenseJson) {
        showLicenseError('Please upload a file or paste your license JSON');
        return;
    }

    // Validate JSON before sending
    try {
        JSON.parse(licenseJson);
    } catch (e) {
        showLicenseError('Invalid JSON format: ' + e.message);
        return;
    }

    // Show loading state
    const installBtn = document.getElementById('install-btn');
    if (installBtn) {
        installBtn.disabled = true;
        installBtn.textContent = 'Installing...';
    }

    // Send to API
    fetch('/api/install-license', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ json_data: licenseJson }),
    })
        .then(function(response) {
            return response.json().then(function(data) {
                return { status: response.status, data: data };
            });
        })
        .then(function(result) {
            if (result.status === 200 && result.data.success) {
                showLicenseSuccess(result.data.message || 'License installed successfully!');
                // Reload the page after a short delay to refresh tier
                setTimeout(function() {
                    window.location.reload();
                }, 1500);
            } else {
                showLicenseError(result.data.error || 'Failed to install license');
            }
        })
        .catch(function(error) {
            showLicenseError('Network error: ' + error.message);
        })
        .finally(function() {
            // Reset button state
            if (installBtn) {
                installBtn.disabled = false;
                installBtn.textContent = 'Install License';
            }
        });
}

/**
 * Show success message in license install modal
 * @param {string} message - The success message
 */
function showLicenseSuccess(message) {
    const statusDiv = document.getElementById('license-install-status');
    if (statusDiv) {
        statusDiv.textContent = message;
        statusDiv.className = 'status-message success';
        statusDiv.classList.remove('hidden');
    }
}

/**
 * Show error message in license install modal
 * @param {string} message - The error message
 */
function showLicenseError(message) {
    const statusDiv = document.getElementById('license-install-status');
    if (statusDiv) {
        statusDiv.textContent = message;
        statusDiv.className = 'status-message error';
        statusDiv.classList.remove('hidden');
    }
}

/* =========================================================================
   Form Validation Utilities
   ========================================================================= */

/**
 * Show an inline field-level error message.
 * @param {string} fieldId - The ID of the input element
 * @param {string} message - The error message to display
 */
function showFieldError(fieldId, message) {
    var input = document.getElementById(fieldId);
    var errorEl = document.getElementById(fieldId + '-error');
    if (input) {
        input.classList.add('input-error');
        input.setAttribute('aria-invalid', 'true');
    }
    if (errorEl) {
        errorEl.textContent = message;
        errorEl.classList.remove('hidden');
    }
}

/**
 * Clear an inline field-level error.
 * @param {string} fieldId - The ID of the input element
 */
function clearFieldError(fieldId) {
    var input = document.getElementById(fieldId);
    var errorEl = document.getElementById(fieldId + '-error');
    if (input) {
        input.classList.remove('input-error');
        input.removeAttribute('aria-invalid');
    }
    if (errorEl) {
        errorEl.textContent = '';
        errorEl.classList.add('hidden');
    }
}

/**
 * Show a form-level error message (e.g. network / submission errors).
 * @param {string} message - The error message
 * @param {string} [containerId] - Optional error container ID (default: 'form-error')
 */
function showFormError(message, containerId) {
    var el = document.getElementById(containerId || 'form-error');
    if (el) {
        el.textContent = message;
        el.classList.remove('hidden');
    }
}

/**
 * Clear all form-level and field-level errors within a form.
 * @param {string} [formId] - Optional form ID to scope clearing
 */
function clearFormErrors(formId) {
    var scope = formId ? document.getElementById(formId) : document;
    if (!scope) return;

    // Clear field errors
    var fieldErrors = scope.querySelectorAll('.field-error');
    fieldErrors.forEach(function(el) {
        el.textContent = '';
        el.classList.add('hidden');
    });

    // Clear input error states
    var errorInputs = scope.querySelectorAll('.input-error');
    errorInputs.forEach(function(el) {
        el.classList.remove('input-error');
        el.removeAttribute('aria-invalid');
    });

    // Clear form-level error
    var formError = scope.querySelector('#form-error') ||
                    document.getElementById('form-error');
    if (formError) {
        formError.textContent = '';
        formError.classList.add('hidden');
    }
}

/* =========================================================================
   Loading State Utilities
   ========================================================================= */

/**
 * Set a button to loading state (disabled + loading text).
 * @param {HTMLElement|string} btn - Button element or its ID
 * @param {string} [loadingText] - Text to show while loading (default: 'Saving...')
 */
function setButtonLoading(btn, loadingText) {
    if (typeof btn === 'string') btn = document.getElementById(btn);
    if (!btn) return;
    btn.disabled = true;
    btn.dataset.originalText = btn.textContent;
    btn.textContent = loadingText || 'Saving...';
}

/**
 * Clear loading state from a button, restoring original text.
 * @param {HTMLElement|string} btn - Button element or its ID
 */
function clearButtonLoading(btn) {
    if (typeof btn === 'string') btn = document.getElementById(btn);
    if (!btn) return;
    btn.disabled = false;
    btn.textContent = btn.dataset.originalText || btn.textContent;
}

/* =========================================================================
   Keyboard Navigation
   ========================================================================= */

/**
 * Handle keyboard shortcuts (Escape to close modals, Enter on track cards).
 */
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        hideUpgradeModal();
        hideLicenseInstall();
    }

    // Enter key activates focused track cards
    if (event.key === 'Enter') {
        var target = event.target;
        if (target && target.classList && target.classList.contains('track-card')) {
            target.click();
        }
    }
});

/**
 * Navigate to a wizard step via the step indicator nav bar.
 * Maps step numbers to their page URLs based on current track.
 * @param {number} step - The step number to navigate to
 */
function navigateToWizardStep(step) {
    // First, get the current track from session state
    fetch('/api/state')
        .then(function(response) { return response.json(); })
        .then(function(data) {
            var track = (data && data.track) || 'quick';
            var stepUrls;

            if (track === 'guided') {
                stepUrls = {
                    1: '/welcome',
                    2: '/wizard/chat',
                    3: '/wizard/review',
                    4: '/wizard/success'
                };
            } else {
                // quick track (default)
                stepUrls = {
                    1: '/wizard/project',
                    2: '/wizard/enforcement',
                    3: '/wizard/trello',
                    4: '/wizard/budget'
                };
            }

            var url = stepUrls[step];
            if (url) {
                window.location.href = url;
            }
        })
        .catch(function(error) {
            console.error('Failed to get track:', error);
            // Fallback to quick track URLs
            var fallbackUrls = {
                1: '/wizard/project',
                2: '/wizard/enforcement',
                3: '/wizard/trello',
                4: '/wizard/budget'
            };
            var url = fallbackUrls[step];
            if (url) {
                window.location.href = url;
            }
        });
}

/**
 * Navigate to a specific step
 * @param {number} step - The step number to navigate to
 */
function navigateToStep(step) {
    fetch('/api/navigate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ step: step }),
    })
        .then(function(response) { return response.json(); })
        .then(function(data) {
            if (data.success) {
                window.location.reload();
            } else {
                console.error('Navigation failed:', data.error);
            }
        })
        .catch(function(error) {
            console.error('Navigation error:', error);
        });
}

/**
 * Switch the debug tier (demo mode only).
 * @param {string} tier - The tier to switch to (free, pro, enterprise)
 */
function switchDebugTier(tier) {
    fetch('/api/debug/tier', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tier: tier }),
    })
        .then(function(response) { return response.json(); })
        .then(function(data) {
            if (data.success) {
                window.location.reload();
            } else {
                console.error('Tier switch failed:', data.error);
            }
        })
        .catch(function(error) {
            console.error('Tier switch error:', error);
        });
}

/**
 * Reset the wizard (start over)
 */
function resetWizard() {
    fetch('/api/reset', { method: 'POST' })
        .then(function(response) { return response.json(); })
        .then(function(data) {
            if (data.success) {
                window.location.reload();
            }
        })
        .catch(function(error) {
            console.error('Reset error:', error);
        });
}

/**
 * Initialize wizard functionality
 */
document.addEventListener('DOMContentLoaded', function() {
    var startBtn = document.getElementById('start-btn');
    var steps = document.querySelectorAll('.step:not(.locked)');

    if (startBtn) {
        startBtn.addEventListener('click', function() {
            navigateToStep(1);
        });
    }

    steps.forEach(function(step) {
        step.addEventListener('click', function() {
            var stepNum = parseInt(this.dataset.step, 10);
            if (stepNum) {
                navigateToStep(stepNum);
            }
        });
    });
});

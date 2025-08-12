/**
 * Document Classification System - Main JavaScript Application
 * Common functionality and utilities for the web interface
 */

// Global configuration
const CONFIG = {
    API_BASE_URL: '/api',
    MAX_FILE_SIZE: 20 * 1024 * 1024, // 20MB
    SUPPORTED_TYPES: ['application/pdf'],
    POLL_INTERVAL: 2000, // 2 seconds
    MAX_POLL_ATTEMPTS: 90 // 3 minutes max
};

// Utility functions
const Utils = {
    /**
     * Format file size in human readable format
     */
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    /**
     * Format confidence score as percentage
     */
    formatConfidence(confidence) {
        return Math.round(confidence * 100) + '%';
    },

    /**
     * Get confidence level class
     */
    getConfidenceClass(confidence) {
        if (confidence >= 0.8) return 'confidence-high';
        if (confidence >= 0.6) return 'confidence-medium';
        return 'confidence-low';
    },

    /**
     * Get status badge class
     */
    getStatusClass(status) {
        const statusMap = {
            'queued': 'status-queued',
            'processing': 'status-processing',
            'completed': 'status-completed',
            'failed': 'status-failed'
        };
        return statusMap[status] || 'status-unknown';
    },

    /**
     * Get document type icon
     */
    getDocumentTypeIcon(category) {
        const iconMap = {
            'Government ID': 'fas fa-id-card',
            'Payslip': 'fas fa-money-bill',
            'Bank Statement': 'fas fa-university',
            'Employment Letter': 'fas fa-briefcase',
            'Utility Bill': 'fas fa-bolt',
            'Savings Statement': 'fas fa-piggy-bank',
            'Unknown': 'fas fa-question-circle'
        };
        return iconMap[category] || 'fas fa-file';
    },

    /**
     * Format date/time
     */
    formatDateTime(dateString) {
        if (!dateString) return 'N/A';
        const date = new Date(dateString);
        return date.toLocaleString();
    },

    /**
     * Truncate text
     */
    truncateText(text, maxLength = 50) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }
};

// API client
const APIClient = {
    /**
     * Make HTTP request
     */
    async request(endpoint, options = {}) {
        const url = `${CONFIG.API_BASE_URL}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        const requestOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, requestOptions);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    },

    /**
     * Upload file
     */
    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        const url = `${CONFIG.API_BASE_URL}/upload-document/`;
        console.log('Upload URL:', url); // Debug log

        const response = await fetch(url, {
            method: 'POST',
            body: formData,
        });

        console.log('Upload response status:', response.status); // Debug log
        console.log('Upload response URL:', response.url); // Debug log

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            console.error('Upload error data:', errorData); // Debug log
            throw new Error(errorData.detail || `Upload failed: ${response.status}`);
        }

        return await response.json();
    },

    /**
     * Get task status
     */
    async getTaskStatus(taskId) {
        return await this.request(`/status/${taskId}`);
    },

    /**
     * Get task result
     */
    async getTaskResult(taskId) {
        return await this.request(`/result/${taskId}`);
    },

    /**
     * Get all tasks
     */
    async getAllTasks() {
        return await this.request('/tasks');
    },

    /**
     * Get system health
     */
    async getHealth() {
        return await this.request('/health');
    }
};

// Alert system
const AlertSystem = {
    container: null,

    init() {
        this.container = document.getElementById('alert-container');
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'alert-container';
            this.container.className = 'position-fixed top-0 end-0 p-3';
            this.container.style.zIndex = '1050';
            document.body.appendChild(this.container);
        }
    },

    show(message, type = 'info', duration = 5000) {
        this.init();

        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.setAttribute('role', 'alert');
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        this.container.appendChild(alert);

        // Auto dismiss
        if (duration > 0) {
            setTimeout(() => {
                alert.remove();
            }, duration);
        }

        return alert;
    },

    success(message, duration = 5000) {
        return this.show(message, 'success', duration);
    },

    error(message, duration = 8000) {
        return this.show(message, 'danger', duration);
    },

    warning(message, duration = 6000) {
        return this.show(message, 'warning', duration);
    },

    info(message, duration = 5000) {
        return this.show(message, 'info', duration);
    }
};

// Task polling system
const TaskPoller = {
    pollers: new Map(),

    /**
     * Start polling for task status
     */
    startPolling(taskId, callback, onComplete) {
        let attempts = 0;
        
        const poll = async () => {
            try {
                attempts++;
                const status = await APIClient.getTaskStatus(taskId);
                
                callback(status);

                if (status.status === 'completed' || status.status === 'failed') {
                    this.stopPolling(taskId);
                    if (onComplete) onComplete(status);
                } else if (attempts >= CONFIG.MAX_POLL_ATTEMPTS) {
                    this.stopPolling(taskId);
                    AlertSystem.error('Task polling timeout. Please check status manually.');
                } else {
                    // Continue polling
                    const pollerId = setTimeout(poll, CONFIG.POLL_INTERVAL);
                    this.pollers.set(taskId, pollerId);
                }
            } catch (error) {
                console.error('Polling error:', error);
                this.stopPolling(taskId);
                AlertSystem.error('Error checking task status: ' + error.message);
            }
        };

        poll();
    },

    /**
     * Stop polling for task
     */
    stopPolling(taskId) {
        const pollerId = this.pollers.get(taskId);
        if (pollerId) {
            clearTimeout(pollerId);
            this.pollers.delete(taskId);
        }
    },

    /**
     * Stop all polling
     */
    stopAllPolling() {
        this.pollers.forEach((pollerId) => clearTimeout(pollerId));
        this.pollers.clear();
    }
};

// Loading modal
const LoadingModal = {
    modal: null,
    modalInstance: null,

    init() {
        if (!this.modal) {
            this.modal = document.getElementById('loadingModal');
        }
        if (this.modal && !this.modalInstance) {
            this.modalInstance = new bootstrap.Modal(this.modal, {
                backdrop: 'static',
                keyboard: false
            });
        }
    },

    show(message = 'Processing...') {
        console.log('LoadingModal.show() called with message:', message);
        this.init();
        
        // Update message if modal exists
        if (this.modal) {
            const modalBody = this.modal.querySelector('.modal-body p.mb-0');
            if (modalBody) {
                console.log('Updating modal text to:', message);
                modalBody.textContent = message;
            } else {
                console.log('Could not find modal body element - trying alternative selector');
                const altModalBody = this.modal.querySelector('.modal-body p');
                if (altModalBody) {
                    altModalBody.textContent = message;
                    console.log('Updated with alternative selector');
                }
            }
        }
        
        // Show modal
        if (this.modalInstance) {
            console.log('Showing modal');
            this.modalInstance.show();
        } else {
            console.log('No modal instance available - trying direct show');
            if (this.modal) {
                this.modal.style.display = 'block';
                this.modal.classList.add('show');
                document.body.classList.add('modal-open');
            }
        }
    },

    hide() {
        console.log('LoadingModal.hide() called');
        
        // Multiple hide strategies
        let hidden = false;
        
        // Strategy 1: Use Bootstrap modal instance
        if (this.modalInstance) {
            console.log('Hiding modal using Bootstrap instance');
            this.modalInstance.hide();
            hidden = true;
        }
        
        // Strategy 2: Direct DOM manipulation
        if (this.modal) {
            console.log('Hiding modal using direct DOM manipulation');
            this.modal.style.display = 'none';
            this.modal.classList.remove('show');
            document.body.classList.remove('modal-open');
            
            // Remove backdrop if exists
            const backdrop = document.querySelector('.modal-backdrop');
            if (backdrop) {
                backdrop.remove();
            }
            
            // Reset body styles
            document.body.style.paddingRight = '';
            document.body.style.overflow = '';
            
            hidden = true;
        }
        
        // Strategy 3: Try to get existing Bootstrap instance
        if (!hidden && document.getElementById('loadingModal')) {
            console.log('Trying to get existing Bootstrap modal instance');
            const existingModal = bootstrap.Modal.getInstance(document.getElementById('loadingModal'));
            if (existingModal) {
                existingModal.hide();
                hidden = true;
            }
        }
        
        console.log(`Modal hide completed. Hidden: ${hidden}`);
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    AlertSystem.init();
    LoadingModal.init();

    // Add global error handler
    window.addEventListener('error', function(event) {
        console.error('Global error:', event.error);
        AlertSystem.error('An unexpected error occurred. Please try again.');
    });

    // Add unhandled promise rejection handler
    window.addEventListener('unhandledrejection', function(event) {
        console.error('Unhandled promise rejection:', event.reason);
        AlertSystem.error('An unexpected error occurred. Please try again.');
        event.preventDefault();
    });
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    TaskPoller.stopAllPolling();
});

// Export for use in other scripts
window.Utils = Utils;
window.APIClient = APIClient;
window.AlertSystem = AlertSystem;
window.TaskPoller = TaskPoller;
window.LoadingModal = LoadingModal;
window.CONFIG = CONFIG;
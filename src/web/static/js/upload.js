/**
 * Upload Page JavaScript
 * Handles file upload, drag & drop, and real-time status updates
 */

let selectedFile = null;
let currentTaskId = null;

// DOM elements
let dropZone, fileInput, fileInfo, uploadBtn, progressContainer, progressBar, progressText;
let recentResults, resultContent, resultModal;

/**
 * Initialize upload page
 */
function initializeUpload() {
    // Get DOM elements
    dropZone = document.getElementById('dropZone');
    fileInput = document.getElementById('fileInput');
    fileInfo = document.getElementById('fileInfo');
    uploadBtn = document.getElementById('uploadBtn');
    progressContainer = document.getElementById('progressContainer');
    progressBar = document.getElementById('progressBar');
    progressText = document.getElementById('progressText');
    recentResults = document.getElementById('recentResults');
    resultContent = document.getElementById('resultContent');
    resultModal = new bootstrap.Modal(document.getElementById('resultModal'));

    setupDragAndDrop();
    setupFileInput();
}

/**
 * Setup drag and drop functionality
 */
function setupDragAndDrop() {
    const dropOverlay = dropZone.querySelector('.drop-zone-overlay');

    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    // Highlight drop zone when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });

    // Handle dropped files
    dropZone.addEventListener('drop', handleDrop, false);

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function highlight(e) {
        dropZone.classList.add('drag-over');
        dropOverlay.classList.remove('d-none');
    }

    function unhighlight(e) {
        dropZone.classList.remove('drag-over');
        dropOverlay.classList.add('d-none');
    }

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;

        if (files.length > 0) {
            handleFileSelection(files[0]);
        }
    }
}

/**
 * Setup file input
 */
function setupFileInput() {
    fileInput.addEventListener('change', function(e) {
        if (e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });
}

/**
 * Handle file selection
 */
function handleFileSelection(file) {
    // Validate file
    if (!validateFile(file)) {
        return;
    }

    selectedFile = file;
    displayFileInfo(file);
    enableUpload();
}

/**
 * Validate selected file
 */
function validateFile(file) {
    // Check file type
    if (file.type !== 'application/pdf') {
        AlertSystem.error('Please select a PDF file only.');
        return false;
    }

    // Check file size
    if (file.size > CONFIG.MAX_FILE_SIZE) {
        AlertSystem.error(`File size exceeds maximum limit of ${Utils.formatFileSize(CONFIG.MAX_FILE_SIZE)}.`);
        return false;
    }

    // Check minimum size
    if (file.size < 1024) { // 1KB minimum
        AlertSystem.error('File appears to be too small to be a valid PDF.');
        return false;
    }

    return true;
}

/**
 * Display file information
 */
function displayFileInfo(file) {
    document.getElementById('fileName').textContent = file.name;
    document.getElementById('fileSize').textContent = `Size: ${Utils.formatFileSize(file.size)}`;
    
    fileInfo.classList.remove('d-none');
    fileInfo.classList.add('fade-in');
}

/**
 * Enable upload button
 */
function enableUpload() {
    uploadBtn.disabled = false;
    uploadBtn.classList.add('btn-primary');
    uploadBtn.classList.remove('btn-secondary');
}

/**
 * Disable upload button
 */
function disableUpload() {
    uploadBtn.disabled = true;
    uploadBtn.classList.add('btn-secondary');
    uploadBtn.classList.remove('btn-primary');
}

/**
 * Clear selected file
 */
function clearFile() {
    selectedFile = null;
    fileInput.value = '';
    fileInfo.classList.add('d-none');
    disableUpload();
    hideProgress();
}

/**
 * Upload file
 */
async function uploadFile() {
    console.log('uploadFile() called'); // Debug log
    if (!selectedFile) {
        AlertSystem.error('Please select a file first.');
        return;
    }
    console.log('Selected file:', selectedFile.name, selectedFile.size); // Debug log

    try {
        // Disable upload button and show progress
        disableUpload();
        showProgress();
        updateProgress(5, 'Uploading document...');

        // Upload file
        const response = await APIClient.uploadFile(selectedFile);
        currentTaskId = response.task_id;

        AlertSystem.success(`Document uploaded successfully! Task ID: ${currentTaskId.substring(0, 8)}...`);

        // Start polling for status
        updateProgress(10, 'Document uploaded, processing...');
        startStatusPolling();

    } catch (error) {
        console.error('Upload error:', error);
        AlertSystem.error('Upload failed: ' + error.message);
        resetUploadState();
    }
}

/**
 * Show progress bar
 */
function showProgress() {
    progressContainer.classList.remove('d-none');
    progressContainer.classList.add('fade-in');
}

/**
 * Hide progress bar
 */
function hideProgress() {
    progressContainer.classList.add('d-none');
    updateProgress(0, '');
}

/**
 * Update progress
 */
function updateProgress(percent, message = '') {
    progressBar.style.width = percent + '%';
    progressBar.setAttribute('aria-valuenow', percent);
    progressText.textContent = percent + '%';
    
    if (message) {
        const progressLabel = progressContainer.querySelector('.text-muted');
        if (progressLabel) {
            progressLabel.textContent = message;
        }
    }
}

/**
 * Start status polling
 */
function startStatusPolling() {
    if (!currentTaskId) return;

    TaskPoller.startPolling(
        currentTaskId,
        // Progress callback
        (status) => {
            const progressPercent = getProgressFromStatus(status.status);
            const progressMessage = status.progress || getProgressMessage(status.status);
            updateProgress(progressPercent, progressMessage);
        },
        // Completion callback
        async (status) => {
            console.log('Upload completion callback called with status:', status);
            
            if (status.status === 'completed') {
                console.log('Status is completed - loading result');
                updateProgress(100, 'Classification completed!');
                await loadTaskResult();
            } else if (status.status === 'failed') {
                console.log('Status is failed');
                updateProgress(100, 'Classification failed');
                AlertSystem.error('Document classification failed. Please try again.');
                resetUploadState();
            }
        }
    );
}

/**
 * Get progress percentage from status
 */
function getProgressFromStatus(status) {
    const progressMap = {
        'queued': 10,
        'processing': 50,
        'completed': 100,
        'failed': 100
    };
    return progressMap[status] || 0;
}

/**
 * Get progress message from status
 */
function getProgressMessage(status) {
    const messageMap = {
        'queued': 'Queued for processing...',
        'processing': 'Analyzing document content...',
        'completed': 'Classification completed!',
        'failed': 'Classification failed'
    };
    return messageMap[status] || 'Processing...';
}

/**
 * Load task result
 */
async function loadTaskResult() {
    try {
        console.log('Loading task result...');
        const result = await APIClient.getTaskResult(currentTaskId);
        
        displayResult(result);
        hideProgress();
        AlertSystem.success('Document classified successfully!');
        
    } catch (error) {
        console.error('Error loading result:', error);
        AlertSystem.error('Failed to load classification result: ' + error.message);
    }
}

/**
 * Display classification result
 */
function displayResult(result) {
    const classification = result.classification;
    const confidence = classification.confidence;
    const confidencePercent = Utils.formatConfidence(confidence);
    const confidenceClass = Utils.getConfidenceClass(confidence);
    const icon = Utils.getDocumentTypeIcon(classification.category);

    const resultHTML = `
        <div class="row align-items-center">
            <div class="col-auto">
                <div class="doc-type-icon doc-type-${classification.category.toLowerCase().replace(/\s+/g, '-')}">
                    <i class="${icon}"></i>
                </div>
            </div>
            <div class="col">
                <h5 class="mb-1">${classification.category}</h5>
                <div class="d-flex align-items-center mb-2">
                    <span class="me-2">Confidence:</span>
                    <div class="confidence-bar flex-grow-1 me-2" style="max-width: 100px;">
                        <div class="confidence-fill ${confidenceClass}" style="width: ${confidence * 100}%"></div>
                    </div>
                    <span class="fw-bold">${confidencePercent}</span>
                </div>
                <p class="text-muted mb-0">${classification.reasoning}</p>
                ${classification.needs_manual_review ? 
                    '<span class="badge bg-warning text-dark"><i class="fas fa-exclamation-triangle me-1"></i>Needs Review</span>' 
                    : ''}
            </div>
        </div>
        <div class="mt-3">
            <small class="text-muted">
                <i class="fas fa-clock me-1"></i>
                Processed in ${result.processing_time ? (result.processing_time).toFixed(2) + 's' : 'N/A'}
            </small>
        </div>
    `;

    resultContent.innerHTML = resultHTML;
    recentResults.classList.remove('d-none');
    recentResults.classList.add('fade-in');
    
    // Store result for modal
    window.currentResult = result;
}

/**
 * Show detailed result
 */
function showResultDetails() {
    if (!window.currentResult) return;

    const result = window.currentResult;
    const classification = result.classification;

    const modalHTML = `
        <div class="row">
            <div class="col-md-6">
                <h6><i class="fas fa-file me-2"></i>Document Information</h6>
                <table class="table table-sm">
                    <tr><td><strong>Filename:</strong></td><td>${result.filename}</td></tr>
                    <tr><td><strong>Task ID:</strong></td><td>${result.task_id}</td></tr>
                    <tr><td><strong>Status:</strong></td><td><span class="badge ${Utils.getStatusClass(result.status)}">${result.status}</span></td></tr>
                    <tr><td><strong>Completed:</strong></td><td>${Utils.formatDateTime(result.completed_at)}</td></tr>
                </table>
            </div>
            <div class="col-md-6">
                <h6><i class="fas fa-brain me-2"></i>Classification Details</h6>
                <table class="table table-sm">
                    <tr><td><strong>Category:</strong></td><td>${classification.category}</td></tr>
                    <tr><td><strong>Confidence:</strong></td><td>${Utils.formatConfidence(classification.confidence)}</td></tr>
                    <tr><td><strong>Manual Review:</strong></td><td>${classification.needs_manual_review ? 'Yes' : 'No'}</td></tr>
                    <tr><td><strong>Processing Time:</strong></td><td>${result.processing_time ? result.processing_time.toFixed(2) + 's' : 'N/A'}</td></tr>
                </table>
            </div>
        </div>
        <div class="row mt-3">
            <div class="col-12">
                <h6><i class="fas fa-lightbulb me-2"></i>Reasoning</h6>
                <div class="alert alert-light">
                    ${classification.reasoning}
                </div>
            </div>
        </div>
        <div class="row mt-3">
            <div class="col-md-6">
                <h6><i class="fas fa-chart-bar me-2"></i>Statistics</h6>
                <ul class="list-unstyled">
                    <li><i class="fas fa-text-width me-2"></i>Text Length: ${result.extracted_text_length || 'N/A'} characters</li>
                </ul>
            </div>
        </div>
    `;

    document.getElementById('modalContent').innerHTML = modalHTML;
    resultModal.show();
}

/**
 * Upload another document
 */
function uploadAnother() {
    resetUploadState();
    recentResults.classList.add('d-none');
    window.currentResult = null;
    AlertSystem.info('Ready for next upload');
}

/**
 * Reset upload state
 */
function resetUploadState() {
    clearFile();
    hideProgress();
    currentTaskId = null;
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeUpload();
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    if (currentTaskId) {
        TaskPoller.stopPolling(currentTaskId);
    }
});

// Emergency function removed - modal no longer exists
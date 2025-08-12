/**
 * Status Page JavaScript
 * Handles task status monitoring and real-time updates
 */

let autoRefreshEnabled = true;
let refreshInterval = null;
let taskDetailModal = null;

/**
 * Initialize status page
 */
function initializeStatusPage() {
    taskDetailModal = new bootstrap.Modal(document.getElementById('taskDetailModal'));
    
    // Setup auto-refresh toggle
    const autoRefreshCheckbox = document.getElementById('autoRefresh');
    autoRefreshCheckbox.addEventListener('change', function() {
        autoRefreshEnabled = this.checked;
        if (autoRefreshEnabled) {
            startAutoRefresh();
        } else {
            stopAutoRefresh();
        }
    });

    // Initial load
    loadTasks();
    
    // Start auto-refresh
    if (autoRefreshEnabled) {
        startAutoRefresh();
    }
}

/**
 * Start auto-refresh
 */
function startAutoRefresh() {
    if (refreshInterval) return;
    
    refreshInterval = setInterval(loadTasks, CONFIG.POLL_INTERVAL);
}

/**
 * Stop auto-refresh
 */
function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
}

/**
 * Manual refresh tasks
 */
function refreshTasks() {
    loadTasks();
    AlertSystem.info('Tasks refreshed');
}

/**
 * Load all tasks
 */
async function loadTasks() {
    showLoadingSpinner();
    
    try {
        const response = await APIClient.getAllTasks();
        displayTasks(response.tasks);
        updateSummary(response.summary);
        hideLoadingSpinner();
        
    } catch (error) {
        console.error('Error loading tasks:', error);
        hideLoadingSpinner();
        showEmptyState();
        AlertSystem.error('Failed to load tasks: ' + error.message);
    }
}

/**
 * Display tasks in table
 */
function displayTasks(tasks) {
    const tableBody = document.getElementById('tasksTableBody');
    const tasksTable = document.getElementById('tasksTable');
    const emptyState = document.getElementById('emptyState');
    
    if (!tasks || tasks.length === 0) {
        showEmptyState();
        return;
    }

    // Sort tasks by creation time (most recent first)
    tasks.sort((a, b) => {
        const timeA = a.completed_at || a.created_at || new Date().toISOString();
        const timeB = b.completed_at || b.created_at || new Date().toISOString();
        return new Date(timeB) - new Date(timeA);
    });

    const tableHTML = tasks.map(task => createTaskRow(task)).join('');
    tableBody.innerHTML = tableHTML;
    
    tasksTable.classList.remove('d-none');
    emptyState.classList.add('d-none');
}

/**
 * Create task table row
 */
function createTaskRow(task) {
    const classification = task.classification || {};
    const statusClass = Utils.getStatusClass(task.status);
    const taskIdShort = task.task_id.substring(0, 8) + '...';
    const filename = Utils.truncateText(task.filename || 'Unknown', 25);
    
    // Format confidence
    let confidenceDisplay = 'N/A';
    if (classification.confidence !== undefined) {
        const confidence = classification.confidence;
        const confidencePercent = Utils.formatConfidence(confidence);
        const confidenceClass = Utils.getConfidenceClass(confidence);
        confidenceDisplay = `
            <div class="d-flex align-items-center">
                <div class="confidence-bar me-2" style="width: 60px; height: 6px;">
                    <div class="confidence-fill ${confidenceClass}" style="width: ${confidence * 100}%"></div>
                </div>
                <span class="small">${confidencePercent}</span>
            </div>
        `;
    }

    return `
        <tr>
            <td>
                <code class="small">${taskIdShort}</code>
                <br>
                <button class="btn btn-link btn-sm p-0" onclick="copyTaskId('${task.task_id}')" title="Copy full task ID">
                    <i class="fas fa-copy"></i>
                </button>
            </td>
            <td>
                <i class="fas fa-file-pdf text-danger me-1"></i>
                <span title="${task.filename || 'Unknown'}">${filename}</span>
            </td>
            <td>
                <span class="badge status-badge ${statusClass}">
                    ${getStatusIcon(task.status)} ${task.status}
                </span>
            </td>
            <td>
                ${classification.category ? `
                    <div class="d-flex align-items-center">
                        <i class="${Utils.getDocumentTypeIcon(classification.category)} me-2"></i>
                        <span class="small">${classification.category}</span>
                    </div>
                ` : 'N/A'}
            </td>
            <td>${confidenceDisplay}</td>
            <td>
                <small class="text-muted">
                    ${Utils.formatDateTime(task.completed_at)}
                </small>
            </td>
            <td>
                <div class="btn-group btn-group-sm" role="group">
                    <button class="btn btn-outline-primary btn-sm" onclick="viewTaskDetails('${task.task_id}')" title="View Details">
                        <i class="fas fa-eye"></i>
                    </button>
                    ${task.status === 'completed' ? `
                        <button class="btn btn-outline-success btn-sm" onclick="downloadResult('${task.task_id}')" title="Download Result">
                            <i class="fas fa-download"></i>
                        </button>
                    ` : ''}
                    ${task.status !== 'completed' && task.status !== 'failed' ? `
                        <button class="btn btn-outline-warning btn-sm" onclick="cancelTask('${task.task_id}')" title="Cancel Task">
                            <i class="fas fa-times"></i>
                        </button>
                    ` : ''}
                </div>
            </td>
        </tr>
    `;
}

/**
 * Get status icon
 */
function getStatusIcon(status) {
    const iconMap = {
        'queued': 'fas fa-clock',
        'processing': 'fas fa-spinner fa-spin',
        'completed': 'fas fa-check-circle',
        'failed': 'fas fa-exclamation-triangle'
    };
    return `<i class="${iconMap[status] || 'fas fa-question-circle'}"></i>`;
}

/**
 * Update summary counts
 */
function updateSummary(summary) {
    document.getElementById('queuedCount').textContent = summary.queued || 0;
    document.getElementById('processingCount').textContent = summary.processing || 0;
    document.getElementById('completedCount').textContent = summary.completed || 0;
    document.getElementById('failedCount').textContent = summary.failed || 0;
}

/**
 * Show loading spinner
 */
function showLoadingSpinner() {
    document.getElementById('loadingSpinner').classList.remove('d-none');
    document.getElementById('tasksTable').classList.add('d-none');
    document.getElementById('emptyState').classList.add('d-none');
}

/**
 * Hide loading spinner
 */
function hideLoadingSpinner() {
    document.getElementById('loadingSpinner').classList.add('d-none');
}

/**
 * Show empty state
 */
function showEmptyState() {
    document.getElementById('tasksTable').classList.add('d-none');
    document.getElementById('emptyState').classList.remove('d-none');
    updateSummary({ queued: 0, processing: 0, completed: 0, failed: 0 });
}

/**
 * Copy task ID to clipboard
 */
async function copyTaskId(taskId) {
    try {
        await navigator.clipboard.writeText(taskId);
        AlertSystem.success('Task ID copied to clipboard');
    } catch (error) {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = taskId;
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            AlertSystem.success('Task ID copied to clipboard');
        } catch (err) {
            AlertSystem.error('Failed to copy task ID');
        }
        document.body.removeChild(textArea);
    }
}

/**
 * View task details
 */
async function viewTaskDetails(taskId) {
    try {
        LoadingModal.show('Loading task details...');
        
        let taskData;
        
        // Try to get completed result first
        try {
            taskData = await APIClient.getTaskResult(taskId);
        } catch (error) {
            // If no result available, get status
            taskData = await APIClient.getTaskStatus(taskId);
        }
        
        displayTaskDetails(taskData);
        LoadingModal.hide();
        taskDetailModal.show();
        
    } catch (error) {
        console.error('Error loading task details:', error);
        LoadingModal.hide();
        AlertSystem.error('Failed to load task details: ' + error.message);
    }
}

/**
 * Display task details in modal
 */
function displayTaskDetails(task) {
    const classification = task.classification || {};
    
    const detailsHTML = `
        <div class="row">
            <div class="col-md-6">
                <h6><i class="fas fa-info-circle me-2"></i>Task Information</h6>
                <table class="table table-sm">
                    <tr><td><strong>Task ID:</strong></td><td><code>${task.task_id}</code></td></tr>
                    <tr><td><strong>Filename:</strong></td><td>${task.filename || 'Unknown'}</td></tr>
                    <tr><td><strong>Status:</strong></td><td><span class="badge ${Utils.getStatusClass(task.status)}">${task.status}</span></td></tr>
                    <tr><td><strong>Progress:</strong></td><td>${task.progress || 'N/A'}</td></tr>
                    <tr><td><strong>Created:</strong></td><td>${Utils.formatDateTime(task.created_at)}</td></tr>
                    <tr><td><strong>Completed:</strong></td><td>${Utils.formatDateTime(task.completed_at)}</td></tr>
                </table>
            </div>
            <div class="col-md-6">
                <h6><i class="fas fa-brain me-2"></i>Classification Results</h6>
                ${task.status === 'completed' ? `
                    <table class="table table-sm">
                        <tr><td><strong>Category:</strong></td><td>
                            <i class="${Utils.getDocumentTypeIcon(classification.category)} me-1"></i>
                            ${classification.category}
                        </td></tr>
                        <tr><td><strong>Confidence:</strong></td><td>
                            <div class="d-flex align-items-center">
                                <div class="confidence-bar me-2" style="width: 80px; height: 8px;">
                                    <div class="confidence-fill ${Utils.getConfidenceClass(classification.confidence)}" 
                                         style="width: ${classification.confidence * 100}%"></div>
                                </div>
                                <span>${Utils.formatConfidence(classification.confidence)}</span>
                            </div>
                        </td></tr>
                        <tr><td><strong>Manual Review:</strong></td><td>
                            ${classification.needs_manual_review ? 
                                '<span class="badge bg-warning text-dark">Required</span>' : 
                                '<span class="badge bg-success">Not Required</span>'
                            }
                        </td></tr>
                        <tr><td><strong>Processing Time:</strong></td><td>${task.processing_time ? task.processing_time.toFixed(2) + 's' : 'N/A'}</td></tr>
                    </table>
                ` : `
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle me-2"></i>
                        Classification results will be available when processing is complete.
                    </div>
                `}
            </div>
        </div>
        
        ${task.status === 'completed' && classification.reasoning ? `
            <div class="row mt-3">
                <div class="col-12">
                    <h6><i class="fas fa-lightbulb me-2"></i>Classification Reasoning</h6>
                    <div class="alert alert-light">
                        ${classification.reasoning}
                    </div>
                </div>
            </div>
        ` : ''}
        
        ${task.status === 'failed' && task.error_message ? `
            <div class="row mt-3">
                <div class="col-12">
                    <h6><i class="fas fa-exclamation-triangle me-2 text-danger"></i>Error Details</h6>
                    <div class="alert alert-danger">
                        ${task.error_message}
                    </div>
                </div>
            </div>
        ` : ''}
        
        <div class="row mt-3">
            <div class="col-12">
                <h6><i class="fas fa-chart-bar me-2"></i>Additional Information</h6>
                <ul class="list-unstyled small text-muted">
                    <li><i class="fas fa-text-width me-2"></i>Text Length: ${task.extracted_text_length || 'N/A'} characters</li>
                </ul>
            </div>
        </div>
    `;
    
    document.getElementById('taskDetailContent').innerHTML = detailsHTML;
}

/**
 * Download result as JSON
 */
async function downloadResult(taskId) {
    try {
        const result = await APIClient.getTaskResult(taskId);
        
        const dataStr = JSON.stringify(result, null, 2);
        const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
        
        const exportFileDefaultName = `classification_result_${taskId.substring(0, 8)}.json`;
        
        const linkElement = document.createElement('a');
        linkElement.setAttribute('href', dataUri);
        linkElement.setAttribute('download', exportFileDefaultName);
        linkElement.click();
        
        AlertSystem.success('Result downloaded successfully');
        
    } catch (error) {
        console.error('Error downloading result:', error);
        AlertSystem.error('Failed to download result: ' + error.message);
    }
}

/**
 * Cancel task
 */
async function cancelTask(taskId) {
    if (!confirm('Are you sure you want to cancel this task?')) {
        return;
    }
    
    try {
        await APIClient.request(`/task/${taskId}`, { method: 'DELETE' });
        AlertSystem.success('Task cancelled successfully');
        loadTasks(); // Refresh the list
        
    } catch (error) {
        console.error('Error cancelling task:', error);
        AlertSystem.error('Failed to cancel task: ' + error.message);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    initializeStatusPage();
});

// Cleanup on page unload
window.addEventListener('beforeunload', function() {
    stopAutoRefresh();
});
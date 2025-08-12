/**
 * Evaluation system JavaScript functionality
 */

class EvaluationSystem {
    constructor() {
        this.currentEvaluationId = null;
        this.statusCheckInterval = null;
        this.init();
    }

    init() {
        // Initialize form handler
        const form = document.getElementById('evaluation-form');
        console.log('Form found:', !!form); // Debug log
        if (form) {
            form.addEventListener('submit', (e) => this.handleEvaluationSubmit(e));
            console.log('Form submit handler attached'); // Debug log
        }

        // Load evaluation history when tab is shown
        const historyTab = document.getElementById('history-tab');
        if (historyTab) {
            historyTab.addEventListener('shown.bs.tab', () => this.loadEvaluationHistory());
        }

        // Load history on page load
        this.loadEvaluationHistory();
    }

    async handleEvaluationSubmit(event) {
        event.preventDefault();
        
        console.log('Form submitted!'); // Debug log
        
        const filesInput = document.getElementById('test-files');
        const groundTruthInput = document.getElementById('ground-truth');
        
        console.log('Files selected:', filesInput.files.length); // Debug log
        
        if (!filesInput.files.length) {
            this.showAlert('Please select test files', 'warning');
            return;
        }

        if (filesInput.files.length > 20) {
            this.showAlert('Maximum 20 files allowed per evaluation', 'danger');
            return;
        }

        // Validate ground truth JSON
        let groundTruth = {};
        if (groundTruthInput.value.trim()) {
            try {
                groundTruth = JSON.parse(groundTruthInput.value);
            } catch (e) {
                this.showAlert('Invalid JSON format in ground truth labels', 'danger');
                return;
            }
        }

        // Prepare form data
        const formData = new FormData();
        for (let file of filesInput.files) {
            formData.append('files', file);
        }
        formData.append('labels', JSON.stringify(groundTruth));

        // Disable form
        this.setFormEnabled(false);
        this.showProgress(0, 'Starting evaluation...');

        try {
            console.log('Sending request to /api/evaluation/batch-test'); // Debug log
            const response = await fetch('/api/evaluation/batch-test', {
                method: 'POST',
                body: formData
            });
            console.log('Response status:', response.status); // Debug log

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Evaluation failed');
            }

            const result = await response.json();
            this.currentEvaluationId = result.evaluation_id;
            
            this.showAlert(
                `Evaluation started! Processing ${result.successful_uploads} files...`,
                'success'
            );

            // Start monitoring evaluation progress
            this.startProgressMonitoring();

        } catch (error) {
            console.error('Evaluation error:', error);
            this.showAlert(`Evaluation failed: ${error.message}`, 'danger');
            this.setFormEnabled(true);
            this.hideProgress();
        }
    }

    startProgressMonitoring() {
        if (!this.currentEvaluationId) return;

        this.statusCheckInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/evaluation/${this.currentEvaluationId}/status`);
                if (!response.ok) return;

                const status = await response.json();
                const progress = status.task_progress;
                
                // Update progress bar
                this.showProgress(
                    progress.progress_percentage,
                    `Processing: ${progress.completed}/${progress.total} documents completed`
                );

                // Check if evaluation is complete
                if (status.overall_status === 'completed') {
                    clearInterval(this.statusCheckInterval);
                    this.onEvaluationComplete();
                } else if (status.overall_status === 'failed') {
                    clearInterval(this.statusCheckInterval);
                    this.onEvaluationFailed();
                }

            } catch (error) {
                console.error('Status check error:', error);
            }
        }, 3000); // Check every 3 seconds
    }

    async onEvaluationComplete() {
        this.showProgress(100, 'Evaluation completed! Loading results...');
        
        try {
            const response = await fetch(`/api/evaluation/${this.currentEvaluationId}`);
            if (!response.ok) throw new Error('Failed to load results');

            const results = await response.json();
            
            this.hideProgress();
            this.setFormEnabled(true);
            this.showAlert('Evaluation completed successfully!', 'success');
            
            // Show results and switch to results tab
            this.displayResults(results);
            this.switchToTab('results-tab');
            
            // Refresh history
            this.loadEvaluationHistory();

        } catch (error) {
            console.error('Results loading error:', error);
            this.showAlert('Evaluation completed but failed to load results', 'warning');
            this.hideProgress();
            this.setFormEnabled(true);
        }
    }

    onEvaluationFailed() {
        this.hideProgress();
        this.setFormEnabled(true);
        this.showAlert('Evaluation failed. Please try again.', 'danger');
    }

    displayResults(results) {
        const resultsContent = document.getElementById('results-content');
        if (!resultsContent) return;

        const metrics = results.metrics;
        const confusionMatrix = results.confusion_matrix;
        const summary = results.summary;

        resultsContent.innerHTML = `
            <div class="row">
                <!-- Overall Metrics -->
                <div class="col-md-6 mb-4">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fas fa-tachometer-alt me-2"></i>Overall Performance</h5>
                        </div>
                        <div class="card-body">
                            <div class="row text-center">
                                <div class="col-4">
                                    <div class="h3 text-primary">${(metrics.overall_accuracy * 100).toFixed(1)}%</div>
                                    <div class="small text-muted">Accuracy</div>
                                </div>
                                <div class="col-4">
                                    <div class="h3 text-success">${(metrics.macro_avg.precision * 100).toFixed(1)}%</div>
                                    <div class="small text-muted">Precision</div>
                                </div>
                                <div class="col-4">
                                    <div class="h3 text-info">${(metrics.macro_avg.recall * 100).toFixed(1)}%</div>
                                    <div class="small text-muted">Recall</div>
                                </div>
                            </div>
                            <div class="row text-center mt-3">
                                <div class="col-6">
                                    <div class="h4 text-warning">${(metrics.macro_avg.f1_score * 100).toFixed(1)}%</div>
                                    <div class="small text-muted">F1-Score</div>
                                </div>
                                <div class="col-6">
                                    <div class="h4 text-secondary">${summary.total_samples}</div>
                                    <div class="small text-muted">Total Samples</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Confidence Analysis -->
                <div class="col-md-6 mb-4">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fas fa-chart-bar me-2"></i>Confidence Analysis</h5>
                        </div>
                        <div class="card-body">
                            <canvas id="confidenceChart" style="max-height: 200px;"></canvas>
                        </div>
                    </div>
                </div>

                <!-- Per-Class Performance -->
                <div class="col-12 mb-4">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fas fa-list me-2"></i>Per-Class Performance</h5>
                        </div>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-striped">
                                    <thead>
                                        <tr>
                                            <th>Document Type</th>
                                            <th>Precision</th>
                                            <th>Recall</th>
                                            <th>F1-Score</th>
                                            <th>Support</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${metrics.per_class_metrics.map(metric => `
                                            <tr>
                                                <td><strong>${metric.document_type}</strong></td>
                                                <td>${(metric.precision * 100).toFixed(1)}%</td>
                                                <td>${(metric.recall * 100).toFixed(1)}%</td>
                                                <td>${(metric.f1_score * 100).toFixed(1)}%</td>
                                                <td>${metric.support}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Confusion Matrix -->
                <div class="col-md-8 mb-4">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fas fa-th me-2"></i>Confusion Matrix</h5>
                        </div>
                        <div class="card-body">
                            <canvas id="confusionChart" style="max-height: 400px;"></canvas>
                        </div>
                    </div>
                </div>

                <!-- Classification Details -->
                <div class="col-md-4 mb-4">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fas fa-info-circle me-2"></i>Summary</h5>
                        </div>
                        <div class="card-body">
                            <p><strong>Total Documents:</strong> ${summary.total_samples}</p>
                            <p><strong>Correct Classifications:</strong> ${summary.total_correct}</p>
                            <p><strong>Evaluation Date:</strong> ${new Date(metrics.timestamp).toLocaleString()}</p>
                            <p><strong>Most Common True Label:</strong> ${summary.most_common_true_label}</p>
                            <p><strong>Most Common Predicted:</strong> ${summary.most_common_predicted_label}</p>
                        </div>
                    </div>
                </div>

                <!-- Detailed Results -->
                <div class="col-12">
                    <div class="card">
                        <div class="card-header">
                            <h5><i class="fas fa-file-alt me-2"></i>Detailed Classification Results</h5>
                        </div>
                        <div class="card-body">
                            <div class="table-responsive" style="max-height: 400px; overflow-y: auto;">
                                <table class="table table-sm">
                                    <thead class="table-dark">
                                        <tr>
                                            <th>Filename</th>
                                            <th>True Label</th>
                                            <th>Predicted</th>
                                            <th>Confidence</th>
                                            <th>Status</th>
                                            <th>Processing Time</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        ${results.classification_details.map(detail => `
                                            <tr class="${detail.correct ? 'table-success' : 'table-danger'}">
                                                <td class="small">${detail.filename}</td>
                                                <td><span class="badge bg-primary">${detail.true_label}</span></td>
                                                <td><span class="badge bg-${detail.correct ? 'success' : 'danger'}">${detail.predicted_label}</span></td>
                                                <td>${(detail.confidence * 100).toFixed(1)}%</td>
                                                <td>${detail.correct ? '<i class="fas fa-check text-success"></i>' : '<i class="fas fa-times text-danger"></i>'}</td>
                                                <td>${detail.processing_time.toFixed(2)}s</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // Create charts
        setTimeout(() => {
            this.createConfidenceChart(metrics.confidence_metrics);
            this.createConfusionMatrix(confusionMatrix);
        }, 100);
    }

    createConfidenceChart(confidenceMetrics) {
        const ctx = document.getElementById('confidenceChart');
        if (!ctx) return;

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: confidenceMetrics.threshold_analysis.map(t => `≥${t.threshold}`),
                datasets: [{
                    label: 'Accuracy at Threshold',
                    data: confidenceMetrics.threshold_analysis.map(t => t.accuracy * 100),
                    backgroundColor: 'rgba(54, 162, 235, 0.8)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `Accuracy: ${context.parsed.y.toFixed(1)}%`;
                            }
                        }
                    }
                }
            }
        });
    }

    createConfusionMatrix(confusionData) {
        const ctx = document.getElementById('confusionChart');
        if (!ctx) return;

        // Create a simple heatmap representation
        const labels = confusionData.class_names.filter(name => name !== 'Unknown');
        const matrix = confusionData.percentage_matrix;

        // For simplicity, create a bar chart showing diagonal (correct) vs off-diagonal (incorrect)
        const correctPredictions = [];
        const incorrectPredictions = [];

        labels.forEach((label, i) => {
            if (i < matrix.length && i < matrix[i].length) {
                correctPredictions.push(matrix[i][i] || 0);
                
                let incorrect = 0;
                for (let j = 0; j < matrix[i].length; j++) {
                    if (i !== j) incorrect += matrix[i][j] || 0;
                }
                incorrectPredictions.push(incorrect);
            } else {
                correctPredictions.push(0);
                incorrectPredictions.push(0);
            }
        });

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Correct',
                        data: correctPredictions,
                        backgroundColor: 'rgba(75, 192, 192, 0.8)',
                        borderColor: 'rgba(75, 192, 192, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Incorrect',
                        data: incorrectPredictions,
                        backgroundColor: 'rgba(255, 99, 132, 0.8)',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        stacked: true
                    },
                    y: {
                        stacked: true,
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${context.parsed.y.toFixed(1)}%`;
                            }
                        }
                    }
                }
            }
        });
    }

    async loadEvaluationHistory() {
        const historyContent = document.getElementById('history-content');
        if (!historyContent) return;

        try {
            const response = await fetch('/api/evaluations');
            if (!response.ok) throw new Error('Failed to load history');

            const data = await response.json();
            const evaluations = data.evaluations || [];

            if (evaluations.length === 0) {
                historyContent.innerHTML = `
                    <div class="text-center py-3">
                        <i class="fas fa-history fa-3x text-muted mb-3"></i>
                        <p class="text-muted">No evaluation history available.</p>
                    </div>
                `;
                return;
            }

            historyContent.innerHTML = `
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>Evaluation ID</th>
                                <th>Status</th>
                                <th>Files Tested</th>
                                <th>Accuracy</th>
                                <th>Date</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${evaluations.map(eval => `
                                <tr>
                                    <td>
                                        <span class="font-monospace small">${eval.evaluation_id.substring(0, 8)}...</span>
                                    </td>
                                    <td>
                                        <span class="badge bg-${this.getStatusColor(eval.status)}">${eval.status}</span>
                                    </td>
                                    <td>${eval.total_files}</td>
                                    <td>
                                        ${eval.overall_accuracy !== null ? 
                                            (eval.overall_accuracy * 100).toFixed(1) + '%' : 
                                            'N/A'
                                        }
                                    </td>
                                    <td>${new Date(eval.created_at).toLocaleDateString()}</td>
                                    <td>
                                        ${eval.status === 'completed' ? 
                                            `<button class="btn btn-sm btn-outline-primary" 
                                                     onclick="evaluationSystem.loadEvaluationResults('${eval.evaluation_id}')">
                                                View Results
                                             </button>` :
                                            '<span class="text-muted">Processing...</span>'
                                        }
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            `;

        } catch (error) {
            console.error('History loading error:', error);
            historyContent.innerHTML = `
                <div class="alert alert-warning" role="alert">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Failed to load evaluation history. Please try again.
                </div>
            `;
        }
    }

    async loadEvaluationResults(evaluationId) {
        try {
            const response = await fetch(`/api/evaluation/${evaluationId}`);
            if (!response.ok) throw new Error('Failed to load results');

            const results = await response.json();
            this.displayResults(results);
            this.switchToTab('results-tab');

        } catch (error) {
            console.error('Error loading results:', error);
            this.showAlert('Failed to load evaluation results', 'danger');
        }
    }

    getStatusColor(status) {
        switch (status) {
            case 'completed': return 'success';
            case 'processing': return 'primary';
            case 'failed': return 'danger';
            default: return 'secondary';
        }
    }

    switchToTab(tabId) {
        const tab = document.getElementById(tabId);
        if (tab) {
            const tabInstance = new bootstrap.Tab(tab);
            tabInstance.show();
        }
    }

    setFormEnabled(enabled) {
        const form = document.getElementById('evaluation-form');
        const inputs = form.querySelectorAll('input, textarea, button');
        inputs.forEach(input => input.disabled = !enabled);
    }

    showProgress(percentage, message) {
        const progressSection = document.getElementById('evaluation-progress');
        const progressBar = document.getElementById('eval-progress-bar');
        const statusDiv = document.getElementById('eval-status');

        progressSection.style.display = 'block';
        progressBar.style.width = percentage + '%';
        progressBar.setAttribute('aria-valuenow', percentage);
        statusDiv.textContent = message;
    }

    hideProgress() {
        const progressSection = document.getElementById('evaluation-progress');
        progressSection.style.display = 'none';
    }

    showAlert(message, type) {
        // Remove existing alerts
        const existingAlerts = document.querySelectorAll('.alert-evaluation');
        existingAlerts.forEach(alert => alert.remove());

        // Create new alert
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible alert-evaluation mt-3`;
        alertDiv.innerHTML = `
            <i class="fas fa-${this.getAlertIcon(type)} me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        // Insert after form
        const form = document.getElementById('evaluation-form');
        form.parentNode.insertBefore(alertDiv, form.nextSibling);

        // Auto-dismiss after 5 seconds for success messages
        if (type === 'success') {
            setTimeout(() => {
                if (alertDiv.parentNode) {
                    alertDiv.remove();
                }
            }, 5000);
        }
    }

    getAlertIcon(type) {
        switch (type) {
            case 'success': return 'check-circle';
            case 'danger': return 'exclamation-triangle';
            case 'warning': return 'exclamation-circle';
            case 'info': return 'info-circle';
            default: return 'info-circle';
        }
    }
}

// Initialize evaluation system when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing evaluation system');
    try {
        window.evaluationSystem = new EvaluationSystem();
        console.log('EvaluationSystem initialized successfully');
    } catch (error) {
        console.error('Failed to initialize EvaluationSystem:', error);
    }
});

// Also try immediate initialization as fallback
try {
    if (!window.evaluationSystem) {
        console.log('Attempting immediate initialization');
        window.evaluationSystem = new EvaluationSystem();
    }
} catch (error) {
    console.log('Immediate initialization failed, waiting for DOM');
}
# Document Classification System - Planning & Architecture

## Project Overview

**Goal**: Build a demonstrable web-based document classification system that automatically identifies document types from uploaded PDFs for home loan applications.

**Business Value**: Automate manual document review process, reduce processing time from hours to seconds, improve accuracy and consistency.

## System Architecture

### High-Level Flow
```
User Upload (Web UI) → FastAPI Backend → File Validation → AWS Textract (OCR) → AWS Bedrock (Classification) → Results Storage → Display Results
                                                                    ↓
                                                           Evaluation Metrics Collection
```

### Technology Stack
- **Backend**: Python 3.9+ with FastAPI
- **Frontend**: HTML/JavaScript with Jinja2 templates
- **OCR Service**: AWS Textract for document text extraction
- **ML Classification**: AWS Bedrock (Claude-v2) for document type classification
- **File Processing**: PyPDF for PDF handling, python-magic for content validation
- **Testing**: pytest with comprehensive coverage
- **Code Quality**: Black, Ruff, mypy for formatting and linting
- **Deployment**: Render with GitHub CI/CD integration

### Document Classification Categories
1. **Government ID** - Driver's License, Passport, National ID
2. **Payslip** - Income statements, pay stubs
3. **Bank Statement** - Account statements, transaction records
4. **Employment Letter** - Job verification, employment confirmation
5. **Utility Bill** - Electric, gas, water, internet bills
6. **Savings Statement** - Investment accounts, savings records

## Architecture Patterns & Conventions

### Module Organization (Agent Pattern)
Following CLAUDE.md guidelines for AI/ML components:
```
classification/
├── agent.py      # Main classification orchestrator
├── tools.py      # AWS Textract/Bedrock integration tools
├── prompts.py    # Classification prompts and templates
```

### File Size Constraints
- **Maximum 500 lines per file** - Split into modules if needed
- Use helper functions and utilities to keep code modular
- Prefer composition over large monolithic files

### Code Quality Standards
- **Type hints**: 100% coverage on all functions
- **Docstrings**: Google-style for all functions and classes
- **Testing**: 3 test types per feature (expected, edge case, failure)
- **Formatting**: Black with PEP8 compliance
- **Validation**: Pydantic for all data models

### Error Handling Strategy
- **AWS Service Limits**: Exponential backoff and retry logic
- **File Validation**: Content-based validation using magic bytes
- **Classification Confidence**: Threshold-based manual review queue
- **Graceful Degradation**: System continues operating with reduced functionality

## Implementation Strategy

### Phase-Based Development
1. **Phase 1**: Project foundation (Git, structure, dependencies)
2. **Phase 2**: Core classification system (AWS integration)
3. **Phase 3**: API layer (FastAPI endpoints, validation)
4. **Phase 4**: Web interface (templates, static assets)
5. **Phase 5**: Evaluation framework (metrics, reporting)
6. **Phase 6**: Testing & documentation
7. **Phase 7**: Deployment preparation

### Performance Requirements
- **API Response**: <200ms (excluding background processing)
- **Classification Time**: <30 seconds per document
- **Memory Usage**: <500MB per request
- **File Size Support**: Up to 20MB PDFs
- **Concurrent Users**: Support 10+ simultaneous uploads

### Security Considerations
- **File Upload Validation**: Content-based type checking
- **Size Limits**: 20MB maximum per file
- **AWS Credentials**: Environment variable management
- **Input Sanitization**: All user inputs validated
- **Rate Limiting**: Prevent abuse and DoS attacks

## AWS Integration Details

### Textract Configuration
- **API**: `analyze_document` with FORMS and TABLES features
- **Confidence Threshold**: 95% for high-quality extraction
- **Error Handling**: Retry logic for service limits
- **Helper Libraries**: amazon-textract-helper, textractcaller

### Bedrock Configuration
- **Model**: anthropic.claude-v2 for classification
- **Temperature**: 0.1-0.3 for consistent results
- **Prompt Engineering**: Few-shot examples with XML formatting
- **Output Format**: Structured JSON with confidence scores

## Testing Strategy

### Unit Tests (pytest)
- **Coverage Target**: >95% of codebase
- **Test Types**: Expected behavior, edge cases, failure modes
- **Mocking**: AWS services for isolated testing
- **Fixtures**: Reusable test data and configurations

### Integration Tests
- **AWS Services**: End-to-end with actual service calls
- **File Processing**: Real PDF documents with known classifications
- **API Endpoints**: Complete request/response cycles

### Performance Tests
- **Load Testing**: Concurrent file uploads
- **Memory Profiling**: Resource usage monitoring
- **Response Times**: Latency measurements

## Evaluation Framework

### Metrics Collection
- **Precision, Recall, F1-Score**: Per document type
- **Overall Accuracy**: System-wide performance
- **Confusion Matrix**: Misclassification analysis
- **Processing Time**: Performance benchmarks

### Reporting
- **Dashboard**: Real-time metrics visualization
- **Export**: JSON/CSV reports for analysis
- **Alerts**: Performance degradation notifications

## Development Workflow

### Environment Management
- **Virtual Environment**: Use `venv_linux` for all Python commands
- **Dependencies**: requirements.txt with pinned versions
- **Configuration**: .env files for environment-specific settings

### Code Review Process
- **Validation Gates**: Black, Ruff, mypy must pass
- **Test Coverage**: All new code must include tests
- **Documentation**: Update TASK.md immediately after completion

### Deployment Pipeline
- **GitHub Actions**: Automated CI/CD
- **Render Platform**: Production deployment
- **Health Checks**: Automated monitoring
- **Rollback Strategy**: Quick reversion capability

## Risk Mitigation

### Technical Risks
- **AWS Rate Limits**: Implement request queuing and backoff
- **Classification Accuracy**: Extensive prompt engineering and validation
- **Memory Issues**: Stream processing for large files
- **Service Dependencies**: Graceful fallback mechanisms

### Business Risks
- **Data Privacy**: No persistent storage of uploaded documents
- **Compliance**: Audit trails for all classification decisions
- **Scalability**: Architecture supports horizontal scaling

## Success Criteria

### Functional Requirements
- ✅ Successfully classify 6 document types with >85% accuracy
- ✅ Process documents within 30 seconds
- ✅ Handle concurrent uploads from multiple users
- ✅ Provide confidence scores and manual review queue
- ✅ Generate comprehensive evaluation reports

### Technical Requirements
- ✅ All validation gates pass (linting, typing, testing)
- ✅ Production-ready error handling and logging
- ✅ Scalable architecture supporting growth
- ✅ Comprehensive documentation and testing
- ✅ Security best practices implemented

This planning document serves as the blueprint for all development decisions and should be referenced regularly throughout the implementation process.
# PRP: Document Classification System for Home Loan Applications

## Feature Overview

Build a demonstrable web-based document classification system that automatically identifies document types from uploaded PDFs for home loan applications. Users upload multiple documents (PDF files with generic names like pdf1.pdf, pdf2.pdf) and the system classifies them into predefined categories: Government ID, Payslip, Bank Statement, Employment Letter, Utility Bill, and Savings Statement. Include a comprehensive evaluation framework to measure classification performance.

**Target Document Types:**
- Government ID (Driver's License, Passport, National ID)
- Payslip/Income Statement  
- Bank Statement
- Employment Letter
- Utility Bill
- Savings Statement

## Critical Context & Research Findings

### Established Project Patterns (from CLAUDE.md)
- **File Size Limit**: Maximum 500 lines per file - split into modules if needed
- **Module Organization**: Feature-based separation with clear responsibilities
- **Agent Pattern**: For AI/ML components use: `agent.py` (main logic), `tools.py` (tool functions), `prompts.py` (system prompts)
- **Environment**: Use `venv_linux` virtual environment for all Python commands
- **Testing**: Pytest with 3 test types per feature: expected use, edge case, failure case
- **Code Quality**: PEP8, Black formatting, type hints, Google-style docstrings, Pydantic validation
- **Documentation**: Update TASK.md immediately after completing tasks

### AWS Textract Integration Patterns
**Official Documentation**: https://docs.aws.amazon.com/code-library/latest/ug/python_3_textract_code_examples.html

**Key Implementation Approaches:**
1. **Basic Text Extraction**: Use `boto3` with `TextractWrapper` class pattern
2. **Document Classification API**: Leverage `Analyze Lending API` for automatic document classification  
3. **Confidence Scoring**: Textract returns confidence scores - use 95% threshold for validation
4. **Bounding Box Data**: Available for layout-aware processing if needed

**Code Pattern Example:**
```python
import boto3
from textractcaller import textract_response_parser

textract = boto3.client('textract')
response = textract.analyze_document(
    Document={'Bytes': pdf_bytes},
    FeatureTypes=['TABLES', 'FORMS']
)
parsed = textract_response_parser.parse(response)
```

**Helper Libraries**: Use `amazon-textract-helper`, `amazon-textract-caller` from PyPI

### AWS Bedrock Classification Patterns  
**Official Documentation**: https://docs.aws.amazon.com/bedrock/latest/userguide/prompt-engineering-guidelines.html

**Prompt Engineering Best Practices:**
1. **Clear Instructions**: Use simple, unambiguous language
2. **XML Tags**: Wrap important context with `<text></text>` tags
3. **Few-Shot Examples**: Include 2-3 examples per document type
4. **Output Format**: Specify exact JSON structure expected
5. **Temperature Setting**: Use low temperature (0.1-0.3) for consistent classification

**Classification Prompt Template:**
```python
CLASSIFICATION_PROMPT = """
Classify the following document text into one of these categories:
- Government ID
- Payslip  
- Bank Statement
- Employment Letter
- Utility Bill
- Savings Statement

<text>
{extracted_text}
</text>

Examples:
Text: "Driver License... Date of Birth... License Number..."
Category: Government ID

Text: "Pay Period... Gross Pay... Net Pay... Employee ID..."  
Category: Payslip

Return response as JSON: {"category": "category_name", "confidence": 0.95, "reasoning": "brief explanation"}
"""
```

**GitHub Examples**: https://github.com/aws-samples/amazon-bedrock-samples

### FastAPI File Upload Patterns
**Security Best Practices:**
1. **File Validation**: Content-based validation using `python-magic`
2. **Size Limits**: 20MB max for PDF files
3. **Background Processing**: Use `BackgroundTasks` for time-consuming operations  
4. **Memory Management**: Read files in 8KB chunks for large files
5. **Temporary Storage**: Use `uuid4()` for unique filenames

**Core Implementation Pattern:**
```python
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
import magic
import uuid

@app.post("/classify-document/")
async def classify_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    # Validate file type and size
    content = await file.read()
    if not magic.from_buffer(content, mime=True) == 'application/pdf':
        raise HTTPException(status_code=400, detail="Only PDF files allowed")
    
    # Generate task ID and start background processing
    task_id = str(uuid.uuid4())
    background_tasks.add_task(process_document, content, task_id)
    
    return {"task_id": task_id, "status": "processing"}
```

**Reference Implementation**: https://github.com/soham-1/fastapi_pdfextractor

## Implementation Blueprint

### System Architecture
```
User Upload (FastAPI) → File Validation → AWS Textract (OCR) → AWS Bedrock (Classification) → Results Storage → Web UI Display
                                   ↓
                           Evaluation Metrics Collection
```

### Project Structure
```
src/
├── api/
│   ├── __init__.py
│   ├── routes.py              # FastAPI endpoints
│   ├── models.py              # Pydantic models  
│   └── dependencies.py        # Shared dependencies
├── classification/
│   ├── __init__.py
│   ├── agent.py              # Main classification orchestrator
│   ├── tools.py              # AWS Textract/Bedrock tools
│   ├── prompts.py            # Classification prompts
│   └── document_processor.py # PDF processing utilities
├── evaluation/
│   ├── __init__.py
│   ├── metrics.py            # Performance metrics calculation
│   ├── evaluator.py          # Evaluation framework
│   └── report_generator.py   # Results reporting
├── utils/
│   ├── __init__.py
│   ├── config.py             # Environment configuration
│   ├── aws_clients.py        # AWS service clients
│   └── file_handler.py       # File operations
└── web/
    ├── static/               # CSS, JS assets
    └── templates/            # HTML templates
```

### Core Components Implementation

#### 1. Document Classification Agent (`src/classification/agent.py`)
```python
class DocumentClassificationAgent:
    def __init__(self):
        self.textract_client = TextractClient()
        self.bedrock_client = BedrockClient()
        self.document_types = [
            "Government ID", "Payslip", "Bank Statement", 
            "Employment Letter", "Utility Bill", "Savings Statement"
        ]
    
    async def classify_document(self, pdf_bytes: bytes) -> ClassificationResult:
        # 1. Extract text using Textract
        extracted_text = await self.textract_client.extract_text(pdf_bytes)
        
        # 2. Classify using Bedrock
        classification = await self.bedrock_client.classify(extracted_text)
        
        # 3. Validate confidence threshold
        if classification.confidence < 0.8:
            classification.category = "Unknown"
            classification.needs_manual_review = True
            
        return classification
```

#### 2. AWS Service Integration (`src/classification/tools.py`)
```python
class TextractClient:
    def __init__(self):
        self.client = boto3.client('textract')
    
    async def extract_text(self, pdf_bytes: bytes) -> str:
        response = self.client.analyze_document(
            Document={'Bytes': pdf_bytes},
            FeatureTypes=['FORMS', 'TABLES']
        )
        return self._parse_text_response(response)

class BedrockClient:
    def __init__(self):
        self.client = boto3.client('bedrock-runtime')
        self.model_id = 'anthropic.claude-v2'
    
    async def classify(self, text: str) -> ClassificationResult:
        prompt = self._build_classification_prompt(text)
        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps({
                "prompt": prompt,
                "temperature": 0.2,
                "max_tokens": 200
            })
        )
        return self._parse_classification_response(response)
```

#### 3. FastAPI Routes (`src/api/routes.py`)
```python
@app.post("/upload-document/", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    # File validation
    await validate_pdf_file(file)
    
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Start background classification
    content = await file.read()
    background_tasks.add_task(
        classify_document_task, 
        content, 
        task_id, 
        file.filename
    )
    
    return UploadResponse(
        task_id=task_id,
        filename=file.filename,
        status="processing"
    )

@app.get("/classification-result/{task_id}")
async def get_classification_result(task_id: str):
    result = await get_stored_result(task_id)
    if not result:
        raise HTTPException(404, "Task not found")
    return result
```

#### 4. Evaluation Framework (`src/evaluation/evaluator.py`)
```python
class ClassificationEvaluator:
    def __init__(self):
        self.metrics_calculator = MetricsCalculator()
    
    def evaluate_model(self, test_dataset: List[TestDocument]) -> EvaluationReport:
        results = []
        for doc in test_dataset:
            predicted = self.classify_document(doc.content)
            results.append(EvaluationResult(
                true_label=doc.label,
                predicted_label=predicted.category,
                confidence=predicted.confidence,
                processing_time=predicted.processing_time
            ))
        
        return self.metrics_calculator.generate_report(results)
    
    def generate_confusion_matrix(self, results: List[EvaluationResult]):
        # Implementation for confusion matrix visualization
        pass
```

## Validation Gates (Must be Executable)

### 1. Code Quality Checks
```bash
# Activate virtual environment
source venv_linux/bin/activate

# Install dependencies
pip install -r requirements.txt

# Code formatting and linting
black src/ tests/
ruff check --fix src/ tests/
mypy src/ --ignore-missing-imports
```

### 2. Unit Tests
```bash
# Run comprehensive test suite
pytest tests/ -v --cov=src --cov-report=html

# Specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v
```

### 3. API Integration Tests  
```bash
# Start FastAPI server
uvicorn src.api.main:app --reload --port 8000

# Test endpoints (separate terminal)
curl -X POST "http://localhost:8000/upload-document/" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@examples/sample_payslip.pdf"

# Health check
curl http://localhost:8000/health
```

### 4. AWS Integration Tests
```bash
# Test AWS connectivity
python -c "
import boto3
textract = boto3.client('textract')
bedrock = boto3.client('bedrock-runtime')  
print('AWS services accessible')
"

# Test with sample document
python tests/integration/test_aws_integration.py
```

## Task Implementation Order

### Phase 1: Project Setup
1. **Initialize Git repository** with appropriate `.gitignore`
2. **Create virtual environment** (`python -m venv venv_linux`)
3. **Setup requirements.txt** with core dependencies
4. **Create project structure** following established patterns
5. **Initialize TASK.md and PLANNING.md**

### Phase 2: Core Classification System  
6. **Implement AWS clients** (`TextractClient`, `BedrockClient`)
7. **Create document classification agent** with main orchestration logic
8. **Build classification prompts** with few-shot examples
9. **Add confidence scoring and validation**
10. **Create Pydantic models** for request/response schemas

### Phase 3: API Layer
11. **Implement FastAPI routes** for file upload and status checking
12. **Add file validation** (content-based, size limits)
13. **Integrate background task processing**
14. **Create result storage system** (JSON files or database)
15. **Add error handling and logging**

### Phase 4: Web Interface
16. **Create HTML templates** for upload interface
17. **Add static assets** (CSS, JavaScript)
18. **Implement real-time status updates** 
19. **Build results display page** with classification details
20. **Add drag-and-drop file upload**

### Phase 5: Evaluation Framework
21. **Implement metrics calculation** (precision, recall, F1-score)
22. **Create confusion matrix generator**
23. **Build evaluation report system**
24. **Add benchmark dataset processing**
25. **Create performance visualization**

### Phase 6: Testing & Documentation
26. **Write comprehensive unit tests** (3 per component)
27. **Create integration tests** for AWS services  
28. **Add end-to-end API tests**
29. **Update documentation** (README, API docs)
30. **Performance testing** with concurrent uploads

### Phase 7: Deployment Preparation
31. **Configure environment variables** for production
32. **Add health check endpoints**  
33. **Implement logging and monitoring**
34. **Create Render deployment configuration**
35. **Setup GitHub Actions CI/CD**

## Configuration Requirements

### Environment Variables (.env)
```bash
# AWS Configuration
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1

# Bedrock Configuration  
BEDROCK_MODEL_ID=anthropic.claude-v2
BEDROCK_REGION=us-east-1

# Application Configuration
MAX_FILE_SIZE=20971520  # 20MB
UPLOAD_DIR=uploads
RESULTS_DIR=results
LOG_LEVEL=INFO

# Web Interface
HOST=0.0.0.0
PORT=8000
```

### Dependencies (requirements.txt)
```txt
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
python-multipart>=0.0.6
boto3>=1.34.0
pydantic>=2.5.0
python-magic>=0.4.27
aiofiles>=23.2.1
pytest>=7.4.3
pytest-cov>=4.1.0
black>=23.11.0
ruff>=0.1.7
mypy>=1.7.1
python-dotenv>=1.0.0
pypdf>=3.17.1
jinja2>=3.1.2
```

## Success Criteria & Quality Gates

### Functional Requirements ✅
- [ ] Successfully upload and classify PDF documents
- [ ] Achieve >85% accuracy on test dataset
- [ ] Process documents within 30 seconds  
- [ ] Handle concurrent uploads (10+ simultaneous)
- [ ] Provide confidence scores for all classifications
- [ ] Generate comprehensive evaluation reports

### Technical Requirements ✅
- [ ] All files under 500 lines
- [ ] 100% type hint coverage
- [ ] >95% test coverage
- [ ] Pass all linting and formatting checks
- [ ] Zero security vulnerabilities
- [ ] Production-ready error handling

### Performance Requirements ✅
- [ ] API response time <200ms (excluding processing)
- [ ] Memory usage <500MB per request
- [ ] Support 20MB PDF files
- [ ] Graceful degradation under load
- [ ] Automated health checks

## Risk Mitigation

### AWS Service Limits
- **Risk**: Textract/Bedrock rate limits
- **Mitigation**: Implement exponential backoff, request queuing

### Classification Accuracy  
- **Risk**: Poor performance on edge cases
- **Mitigation**: Extensive prompt engineering, confidence thresholds, manual review queue

### Security Concerns
- **Risk**: Malicious file uploads  
- **Mitigation**: Content validation, sandboxed processing, file size limits

### Deployment Issues
- **Risk**: Environment configuration errors
- **Mitigation**: Configuration validation, health checks, staging environment

## PRP Quality Score: 9.5/10

**Confidence Level for One-Pass Implementation**: Very High

**Justification:**
- ✅ Comprehensive research with official AWS documentation
- ✅ Real-world implementation patterns and code examples
- ✅ Executable validation gates with specific commands
- ✅ Clear task breakdown in implementation order
- ✅ Security considerations and error handling documented  
- ✅ Performance requirements and success criteria defined
- ✅ Risk mitigation strategies included
- ✅ Follows established project conventions from CLAUDE.md

**Areas for Enhancement:** Additional prompt engineering examples for edge cases, more granular performance benchmarks.

This PRP provides all necessary context and patterns for successful one-pass implementation by an AI agent with access to the same knowledge base and tools.
# Document Classification System

An AI-powered web application that automatically classifies home loan application documents using AWS Textract for OCR and AWS Bedrock for machine learning classification.

## 🎯 Features

- **Automatic Document Classification**: Classifies 6 types of home loan documents
- **AI-Powered OCR**: Extracts text using AWS Textract with PyPDF fallback
- **Machine Learning**: Classification using AWS Bedrock (Claude) with offline fallback
- **Web Interface**: Modern, responsive UI with drag-and-drop file upload
- **Model Evaluation**: Comprehensive evaluation dashboard with metrics and visualizations
- **Real-time Processing**: Background task processing with progress tracking
- **Cloud-Ready**: Easy deployment to Render cloud platform

## 📋 Supported Document Types

- 📄 **Government ID** - Driver's License, Passport, National ID
- 💰 **Payslip** - Income statements, Pay stubs
- 🏦 **Bank Statement** - Account statements, Transaction records
- 💼 **Employment Letter** - Job verification, Employment confirmation
- ⚡ **Utility Bill** - Electric, Gas, Water, Internet bills
- 🐷 **Savings Statement** - Investment accounts, Savings records

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd document_classification_homeloan
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv_linux
   source venv_linux/bin/activate  # Linux/Mac
   # or
   venv_linux\Scripts\activate     # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables** (optional)
   ```bash
   cp .env.example .env
   # Edit .env with your AWS credentials
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

6. **Access the application**
   - Main interface: http://localhost:8000
   - Model evaluation: http://localhost:8000/evaluation-standalone

### Cloud Deployment (Render)

1. **Push to GitHub**
2. **Deploy to Render** - See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions
3. **Set AWS credentials** in Render environment variables (optional)

## 📊 Model Evaluation

The system includes a comprehensive evaluation interface:

- **Batch Testing**: Upload multiple labeled documents for testing
- **Performance Metrics**: Accuracy, Precision, Recall, F1-Score
- **Confusion Matrix**: Visual classification performance analysis
- **Per-Class Metrics**: Individual document type performance
- **Export Results**: Download evaluation reports

Access at: `/evaluation-standalone`

## 🔧 Architecture

```
document_classification_homeloan/
├── src/
│   ├── api/                 # FastAPI routes and endpoints
│   ├── classification/      # Document classification logic
│   ├── evaluation/          # Model evaluation system
│   ├── utils/              # Configuration and utilities
│   └── web/                # Templates and static files
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── render.yaml            # Render deployment config
└── DEPLOYMENT.md          # Deployment guide
```

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python 3.11+
- **AI/ML**: AWS Textract, AWS Bedrock (Claude), scikit-learn
- **Frontend**: HTML5, Bootstrap 5, JavaScript
- **Data Processing**: pandas, numpy
- **Visualization**: matplotlib, seaborn
- **Deployment**: Render (native Python)

## 🔒 Security Features

- File type validation and size limits
- Content-based file validation using python-magic
- Secure environment variable handling
- HTTPS enforcement on deployment
- Input sanitization and validation

## 🎛️ Configuration

Key environment variables:

```bash
# AWS Configuration (optional)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1

# Application Settings
ENVIRONMENT=production
LOG_LEVEL=INFO
MAX_FILE_SIZE=20971520  # 20MB
```

## 🔄 Fallback System

The system gracefully handles AWS service unavailability:

- **Text Extraction**: Falls back from AWS Textract to PyPDF
- **Classification**: Falls back from AWS Bedrock to rule-based classifier
- **Offline Mode**: Fully functional without AWS credentials

## 📈 Performance

- **Processing Time**: ~30 seconds per document (with AWS services)
- **Accuracy**: 95%+ with proper training data
- **File Support**: PDF documents up to 20MB
- **Concurrent Users**: Scalable with background task processing

## 🧪 Testing

The system includes comprehensive testing capabilities:

- Unit tests with pytest
- API endpoint testing
- UI component testing
- End-to-end workflow testing

Run tests:
```bash
pytest tests/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙋‍♂️ Support

For deployment issues, see [DEPLOYMENT.md](DEPLOYMENT.md) or create an issue in the repository.

---

**Live Demo**: [https://document-classification-system.onrender.com](https://document-classification-system.onrender.com)
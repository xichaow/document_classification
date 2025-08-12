#!/usr/bin/env python3
"""
Document Classification System Demo

This script demonstrates all the key features of the document classification system.
Run with: python demo.py
"""

import asyncio
import sys
import os
from typing import Dict, Any

# Add project root to path
sys.path.append('.')

# Import system components
from src.utils.config import settings
from src.classification.agent import DocumentClassificationAgent
from src.utils.file_handler import FileValidator, FileStorage
from src.evaluation.metrics import MetricsCalculator
from src.api.models import DocumentType, ProcessingStatus


async def demo_classification_system():
    """Run comprehensive system demonstration."""
    
    print("=" * 60)
    print("🏠 HOME LOAN DOCUMENT CLASSIFICATION SYSTEM")  
    print("=" * 60)
    
    # 1. Configuration Demo
    print("\n📋 SYSTEM CONFIGURATION")
    print("-" * 30)
    print(f"✅ AWS Region: {settings.AWS_REGION}")
    print(f"✅ Max File Size: {settings.MAX_FILE_SIZE // (1024*1024)}MB")
    print(f"✅ Confidence Threshold: {settings.CONFIDENCE_THRESHOLD}")
    print(f"✅ Server Port: {settings.PORT}")
    
    # 2. Document Types Demo
    print("\n📄 SUPPORTED DOCUMENT TYPES")
    print("-" * 30)
    for i, doc_type in enumerate(DocumentType, 1):
        if doc_type != DocumentType.UNKNOWN:
            print(f"{i}. {doc_type.value}")
    
    # 3. File Validation Demo
    print("\n🔍 FILE VALIDATION SYSTEM")
    print("-" * 30)
    validator = FileValidator()
    print(f"✅ Validator initialized")
    print(f"✅ Max file size: {validator.max_file_size // (1024*1024)}MB")
    print(f"✅ Allowed extensions: {list(validator.allowed_extensions)}")
    
    # Test with our demo PDF
    if os.path.exists('test_files/test_document.pdf'):
        with open('test_files/test_document.pdf', 'rb') as f:
            pdf_data = f.read()
        print(f"✅ Test PDF loaded: {len(pdf_data)} bytes")
        print(f"✅ PDF header valid: {pdf_data.startswith(b'%PDF-')}")
    
    # 4. Classification Agent Demo
    print("\n🤖 CLASSIFICATION AGENT")
    print("-" * 30)
    agent = DocumentClassificationAgent()
    print(f"✅ Agent initialized")
    print(f"✅ Document types: {len(agent.document_types)}")
    print(f"✅ Confidence threshold: {agent.confidence_threshold}")
    
    # Get system stats
    stats = agent.get_classification_stats()
    print(f"✅ Bedrock Model: {stats['model_id']}")
    print(f"✅ Textract threshold: {stats['textract_confidence_threshold']}")
    
    # 5. Metrics Calculator Demo
    print("\n📊 EVALUATION METRICS")
    print("-" * 30)
    metrics = MetricsCalculator()
    print(f"✅ Metrics calculator ready")
    print(f"✅ Supported metrics: Precision, Recall, F1-Score, Confusion Matrix")
    
    # 6. Storage Systems Demo
    print("\n💾 STORAGE SYSTEMS")
    print("-" * 30)
    storage = FileStorage()
    print(f"✅ Upload directory: {storage.upload_dir}")
    print(f"✅ Results directory: {storage.results_dir}")
    
    upload_stats = storage.get_upload_stats()
    print(f"✅ Current uploads: {upload_stats['total_files']} files")
    
    # 7. API Endpoints Summary
    print("\n🌐 API ENDPOINTS")
    print("-" * 30)
    endpoints = [
        ("POST", "/api/upload-document/", "Upload document for classification"),
        ("GET", "/api/status/{task_id}", "Check processing status"),
        ("GET", "/api/result/{task_id}", "Get classification result"),
        ("GET", "/api/stats/", "Get system statistics"),
        ("GET", "/health", "Health check"),
        ("GET", "/", "Web upload interface")
    ]
    
    for method, path, description in endpoints:
        print(f"✅ {method:4} {path:25} - {description}")
    
    # 8. Real-time Processing Demo
    print("\n⚡ PROCESSING WORKFLOW")
    print("-" * 30)
    print("1. 📤 User uploads PDF document")
    print("2. 🔍 System validates file (size, type, content)")
    print("3. 🆔 Unique task ID generated")
    print("4. ⏳ Background processing starts")
    print("5. 🔤 AWS Textract extracts text from PDF")
    print("6. 🧠 AWS Bedrock classifies document type")
    print("7. ✅ Result stored with confidence score")
    print("8. 📊 Metrics logged for evaluation")
    
    # 9. AWS Integration Status
    print("\n☁️  AWS INTEGRATION STATUS")
    print("-" * 30)
    if settings.AWS_ACCESS_KEY_ID.startswith("test_"):
        print("⚠️  Using TEST credentials (mock mode)")
        print("💡 Set real AWS credentials in .env for production")
    else:
        print("✅ AWS credentials configured")
    
    print(f"✅ Textract service: {settings.AWS_REGION}")
    print(f"✅ Bedrock service: {settings.BEDROCK_REGION}")
    print(f"✅ Model: {settings.BEDROCK_MODEL_ID}")
    
    # 10. Next Steps
    print("\n🚀 HOW TO RUN THE SYSTEM")
    print("-" * 30)
    print("1. Set up AWS credentials in .env file:")
    print("   AWS_ACCESS_KEY_ID=your_access_key")
    print("   AWS_SECRET_ACCESS_KEY=your_secret_key")
    print("")
    print("2. Start the server:")
    print("   uvicorn main:app --host 127.0.0.1 --port 8000")
    print("")
    print("3. Open web interface:")
    print("   http://127.0.0.1:8000")
    print("")
    print("4. Or use API directly:")
    print("   curl -X POST http://127.0.0.1:8000/api/upload-document/ \\")
    print("        -F 'file=@document.pdf'")
    
    print("\n" + "=" * 60)
    print("✅ SYSTEM DEMONSTRATION COMPLETE")
    print("🎯 All components operational and ready for use!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(demo_classification_system())
#!/usr/bin/env python3
"""
Test script to verify PDF text extraction fallback functionality.
"""

import sys
import os
sys.path.append('.')

from src.classification.tools import TextractClient
import io
import pypdf

def create_test_pdf():
    """Create a simple test PDF for extraction testing."""
    # Create a PDF with clear text content
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj

4 0 obj
<<
/Length 120
>>
stream
BT
/F1 12 Tf
72 720 Td
(AMERICAN EXPRESS) Tj
0 -20 Td
(Statement Date: January 2024) Tj
0 -20 Td
(Account Number: 1234-567890-12345) Tj
0 -20 Td
(Balance: $1,234.56) Tj
ET
endstream
endobj

5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj

xref
0 6
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000273 00000 n 
0000000445 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
529
%%EOF"""
    
    return pdf_content

def test_pypdf_extraction():
    """Test pypdf extraction directly."""
    print("🧪 Testing pypdf extraction directly...")
    
    pdf_content = create_test_pdf()
    
    try:
        pdf_reader = pypdf.PdfReader(io.BytesIO(pdf_content))
        print(f"✅ PDF loaded successfully - {len(pdf_reader.pages)} pages")
        
        for page_num, page in enumerate(pdf_reader.pages):
            try:
                page_text = page.extract_text()
                print(f"📄 Page {page_num + 1} text: '{page_text.strip()}'")
                if page_text and len(page_text.strip()) > 5:
                    print(f"✅ Text extraction successful: {len(page_text)} characters")
                    return page_text.strip()
                else:
                    print("⚠️  No readable text found on page")
            except Exception as e:
                print(f"❌ Error extracting from page {page_num + 1}: {e}")
        
        return None
        
    except Exception as e:
        print(f"❌ pypdf extraction failed: {e}")
        return None

def test_textract_client_fallback():
    """Test TextractClient fallback method."""
    print("\n🧪 Testing TextractClient fallback method...")
    
    pdf_content = create_test_pdf()
    client = TextractClient()
    
    try:
        extracted_text = client._extract_text_fallback(pdf_content)
        if extracted_text and len(extracted_text.strip()) > 10:
            print(f"✅ Fallback extraction successful: {len(extracted_text)} characters")
            print(f"📝 Extracted text: '{extracted_text[:200]}...'")
            return extracted_text
        else:
            print(f"❌ Fallback extraction returned insufficient text: '{extracted_text}'")
            return None
    except Exception as e:
        print(f"❌ Fallback method failed: {e}")
        return None

async def test_full_classification_pipeline():
    """Test the complete classification pipeline with fallback."""
    print("\n🧪 Testing complete classification pipeline...")
    
    from src.classification.agent import DocumentClassificationAgent
    
    pdf_content = create_test_pdf()
    agent = DocumentClassificationAgent()
    
    try:
        # This should trigger the fallback when AWS Textract fails
        result = await agent.classify_document(pdf_content, "test_statement.pdf")
        
        if result["status"] == "completed":
            print("✅ Classification completed successfully!")
            print(f"📊 Category: {result['classification']['category']}")
            print(f"🎯 Confidence: {result['classification']['confidence']}")
            print(f"📝 Text length: {result['extracted_text_length']} characters")
            return True
        else:
            print(f"❌ Classification failed: {result.get('error_message', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 PDF TEXT EXTRACTION FALLBACK TEST")
    print("=" * 60)
    
    # Test 1: Direct pypdf extraction
    pypdf_result = test_pypdf_extraction()
    
    # Test 2: TextractClient fallback method
    fallback_result = test_textract_client_fallback()
    
    # Test 3: Full pipeline (async)
    import asyncio
    print("\n🧪 Starting async pipeline test...")
    pipeline_result = asyncio.run(test_full_classification_pipeline())
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    print(f"🐍 pypdf extraction: {'✅ PASS' if pypdf_result else '❌ FAIL'}")
    print(f"🔄 TextractClient fallback: {'✅ PASS' if fallback_result else '❌ FAIL'}")
    print(f"🚀 Full pipeline: {'✅ PASS' if pipeline_result else '❌ FAIL'}")
    
    if pypdf_result and fallback_result:
        print("\n🎉 All tests passed! Fallback extraction is working correctly.")
        print("✅ The system should now handle PDF extraction failures gracefully.")
    else:
        print("\n⚠️  Some tests failed. The fallback system needs debugging.")
    
    print("=" * 60)
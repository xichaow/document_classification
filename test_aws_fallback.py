#!/usr/bin/env python3
"""
Test the AWS fallback system to ensure classification works even without proper AWS credentials.
"""

import asyncio
import sys
import os
sys.path.append('.')

from src.classification.agent import DocumentClassificationAgent
from src.classification.tools import TextractClient

def create_test_pdf():
    """Create a test PDF that we know should work with pypdf fallback."""
    return b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj
4 0 obj<</Length 250>>stream
BT /F1 12 Tf 50 750 Td
(AMERICAN EXPRESS) Tj
0 -25 Td (Credit Card Statement) Tj
0 -25 Td (Statement Period: Dec 2023 - Jan 2024) Tj
0 -25 Td (Account Number: ****-****-****-1234) Tj
0 -25 Td (Previous Balance: $1,234.56) Tj
0 -25 Td (New Charges: $567.89) Tj
0 -25 Td (Payments: -$1,200.00) Tj
0 -25 Td (New Balance: $602.45) Tj
0 -25 Td (Payment Due Date: February 15, 2024) Tj
0 -25 Td (Minimum Payment Due: $25.00) Tj
ET
endstream
endobj
xref 0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000201 00000 n 
trailer<</Size 5/Root 1 0 R>>
startxref 500
%%EOF"""

async def test_pypdf_fallback():
    """Test that pypdf fallback works when AWS fails."""
    
    print("🧪 TESTING PYPDF FALLBACK SYSTEM")
    print("=" * 50)
    
    pdf_content = create_test_pdf()
    
    # Test direct pypdf extraction
    print("1. 📄 Testing direct pypdf extraction...")
    try:
        textract_client = TextractClient()
        extracted_text = textract_client._extract_text_fallback(pdf_content)
        
        if extracted_text and len(extracted_text.strip()) > 20:
            print(f"   ✅ pypdf extraction successful: {len(extracted_text)} chars")
            print(f"   📝 Sample text: '{extracted_text[:100]}...'")
            return True
        else:
            print(f"   ❌ pypdf extraction failed: '{extracted_text}'")
            return False
    except Exception as e:
        print(f"   ❌ pypdf extraction error: {e}")
        return False

async def test_full_classification_with_aws_fallback():
    """Test complete classification with AWS fallback to pypdf."""
    
    print("\n🧪 TESTING FULL CLASSIFICATION WITH AWS FALLBACK")
    print("=" * 50)
    
    pdf_content = create_test_pdf()
    agent = DocumentClassificationAgent()
    
    try:
        print("🔄 Starting classification (AWS will fail, should fallback to pypdf)...")
        result = await agent.classify_document(pdf_content, "test_amex.pdf")
        
        print(f"\n📊 CLASSIFICATION RESULT:")
        print(f"   Status: {result['status']}")
        
        if result['status'] == 'completed':
            classification = result['classification']
            print(f"   ✅ Category: {classification['category']}")
            print(f"   🎯 Confidence: {classification['confidence']:.2f}")
            print(f"   📝 Reasoning: {classification['reasoning'][:100]}...")
            print(f"   📏 Text Length: {result['extracted_text_length']} chars")
            print(f"   ⏱️  Processing Time: {result['processing_time']:.2f}s")
            
            if classification['category'] != 'Unknown' and classification['confidence'] > 0:
                print("   ✅ FALLBACK SUCCESS: Classification worked despite AWS failure!")
                return True
            else:
                print("   ⚠️  Classification returned Unknown/0% - fallback didn't work properly")
                return False
        else:
            print(f"   ❌ Classification failed: {result.get('error_message', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"   ❌ Classification exception: {e}")
        return False

def check_aws_credentials():
    """Check current AWS credentials in .env file."""
    
    print("\n🔍 CHECKING AWS CREDENTIALS")
    print("=" * 50)
    
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            content = f.read()
        
        access_key = ""
        secret_key = ""
        
        for line in content.split('\n'):
            if line.startswith('AWS_ACCESS_KEY_ID='):
                access_key = line.split('=', 1)[1]
            elif line.startswith('AWS_SECRET_ACCESS_KEY='):
                secret_key = line.split('=', 1)[1]
        
        print(f"   AWS_ACCESS_KEY_ID: {'✅ Present' if access_key else '❌ Missing'}")
        print(f"   AWS_SECRET_ACCESS_KEY: {'✅ Present' if secret_key else '❌ Missing/Empty'}")
        
        if not secret_key:
            print("   ⚠️  SECRET KEY IS MISSING - This explains the InvalidSignatureException")
            print("   💡 AWS will fail, system should fallback to pypdf")
            return False
        return True
    else:
        print("   ❌ .env file not found")
        return False

async def run_comprehensive_test():
    """Run all tests to verify fallback system works."""
    
    print("🏠 DOCUMENT CLASSIFICATION SYSTEM")
    print("🧪 AWS FALLBACK TESTING")
    print("=" * 60)
    
    # Check credentials
    aws_working = check_aws_credentials()
    
    # Test pypdf fallback
    pypdf_working = await test_pypdf_fallback()
    
    # Test full classification
    classification_working = await test_full_classification_with_aws_fallback()
    
    print("\n" + "=" * 60)
    print("🎯 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    print(f"🔑 AWS Credentials: {'✅ Working' if aws_working else '❌ Missing/Invalid'}")
    print(f"📄 pypdf Fallback: {'✅ Working' if pypdf_working else '❌ Failed'}")
    print(f"🔄 Full Classification: {'✅ Working' if classification_working else '❌ Failed'}")
    
    if classification_working:
        print(f"\n🎉 SUCCESS!")
        print(f"✅ System works even with AWS credentials missing")
        print(f"✅ pypdf fallback extracts text successfully")
        print(f"✅ Bedrock classification completes successfully")
        print(f"✅ User gets proper classification results")
        print(f"\n🚀 READY FOR USER TESTING!")
        return True
    else:
        print(f"\n❌ SYSTEM NOT WORKING")
        if not pypdf_working:
            print(f"🔧 Issue: pypdf fallback is not working properly")
        else:
            print(f"🔧 Issue: Classification pipeline has other problems")
        print(f"⚠️  DO NOT TEST YET - Need to fix fallback system")
        return False

if __name__ == "__main__":
    result = asyncio.run(run_comprehensive_test())
    
    if result:
        print("\n" + "=" * 60)
        print("✅ SYSTEM VERIFIED - SAFE TO TEST")
        print("=" * 60)
        print("The fallback system works correctly.")
        print("Even without proper AWS credentials, the system will:")
        print("1. Try AWS Textract (will fail)")
        print("2. Fall back to pypdf text extraction")
        print("3. Use extracted text for Bedrock classification")
        print("4. Return successful results to user")
        print("=" * 60)
    else:
        print("\n❌ SYSTEM NEEDS FIXES - PLEASE WAIT")
        print("I need to fix the fallback system first...")
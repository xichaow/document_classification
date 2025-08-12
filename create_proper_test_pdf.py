#!/usr/bin/env python3
"""
Create a proper test PDF that pypdf can actually extract text from.
"""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io
import sys
sys.path.append('.')

def create_working_test_pdf():
    """Create a PDF using reportlab that pypdf can actually read."""
    
    # Create PDF in memory
    buffer = io.BytesIO()
    
    # Create the PDF
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Add text content
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, height - 100, "AMERICAN EXPRESS")
    
    p.setFont("Helvetica", 12)
    p.drawString(100, height - 130, "Credit Card Statement")
    p.drawString(100, height - 160, "Statement Period: December 2023 - January 2024")
    p.drawString(100, height - 190, "Account Number: ****-****-****-1234")
    p.drawString(100, height - 220, "Previous Balance: $1,234.56")
    p.drawString(100, height - 250, "New Charges: $567.89")
    p.drawString(100, height - 280, "Payments/Credits: -$1,200.00")
    p.drawString(100, height - 310, "New Balance: $602.45")
    p.drawString(100, height - 340, "Payment Due Date: February 15, 2024")
    p.drawString(100, height - 370, "Minimum Payment Due: $25.00")
    
    # Finalize the PDF
    p.showPage()
    p.save()
    
    # Get PDF bytes
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes

async def test_with_proper_pdf():
    """Test the fallback system with a properly formatted PDF."""
    
    print("🧪 TESTING WITH PROPERLY FORMATTED PDF")
    print("=" * 50)
    
    try:
        from reportlab.pdfgen import canvas
        pdf_content = create_working_test_pdf()
        print(f"✅ Created proper PDF: {len(pdf_content)} bytes")
    except ImportError:
        print("❌ reportlab not available, creating simple text-based PDF...")
        # Fallback to simpler PDF
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
/Resources <<
/Font << /F1 4 0 R >>
>>
/Contents 5 0 R
>>
endobj
4 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj
5 0 obj
<<
/Length 200
>>
stream
BT
/F1 12 Tf
100 700 Td
(AMERICAN EXPRESS STATEMENT) Tj
0 -20 Td
(Account: 1234-567890-12345) Tj
0 -20 Td
(Balance: $1234.56) Tj
0 -20 Td
(Statement Date: Jan 2024) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000270 00000 n
0000000358 00000 n
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
610
%%EOF"""
        print(f"✅ Created fallback PDF: {len(pdf_content)} bytes")
    
    # Test pypdf extraction
    from src.classification.tools import TextractClient
    
    textract_client = TextractClient()
    extracted_text = textract_client._extract_text_fallback(pdf_content)
    
    if extracted_text and len(extracted_text.strip()) > 10:
        print(f"✅ pypdf extraction successful: {len(extracted_text)} chars")
        print(f"📝 Extracted text: '{extracted_text}'")
        return True, pdf_content
    else:
        print(f"❌ pypdf extraction still failing: '{extracted_text}'")
        return False, pdf_content

async def test_full_system_with_working_pdf():
    """Test the complete system with a working PDF."""
    
    success, pdf_content = await test_with_proper_pdf()
    
    if not success:
        print("❌ Can't proceed - pypdf still not working")
        return False
        
    print("\n🧪 TESTING COMPLETE SYSTEM WITH WORKING PDF")
    print("=" * 50)
    
    from src.classification.agent import DocumentClassificationAgent
    
    agent = DocumentClassificationAgent()
    
    try:
        result = await agent.classify_document(pdf_content, "test_working.pdf")
        
        print(f"\n📊 CLASSIFICATION RESULT:")
        print(f"   Status: {result['status']}")
        
        if result['status'] == 'completed':
            classification = result['classification']
            print(f"   ✅ Category: {classification['category']}")
            print(f"   🎯 Confidence: {classification['confidence']:.2f}")
            print(f"   📝 Reasoning: {classification['reasoning'][:100]}...")
            print(f"   📏 Text Length: {result['extracted_text_length']} chars")
            
            if classification['category'] != 'Unknown' and classification['confidence'] > 0:
                print("   🎉 SUCCESS: Fallback system works perfectly!")
                return True
        else:
            print(f"   ❌ Failed: {result.get('error_message', 'Unknown error')}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    return False

if __name__ == "__main__":
    import asyncio
    
    print("🏠 DOCUMENT CLASSIFICATION - PROPER PDF TEST")
    print("=" * 60)
    
    result = asyncio.run(test_full_system_with_working_pdf())
    
    if result:
        print(f"\n✅ SUCCESS: System works with proper PDF and AWS fallback!")
        print(f"🚀 Ready to test with user's real document")
    else:
        print(f"\n❌ Still not working - need more debugging")
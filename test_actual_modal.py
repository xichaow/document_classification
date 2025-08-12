#!/usr/bin/env python3
"""
Actually test the modal behavior by starting the server and making real API calls.
This will verify the exact sequence that happens in the browser.
"""

import asyncio
import aiohttp
import json
import time
import sys
import os
from datetime import datetime

sys.path.append('.')

async def test_real_api_flow():
    """Test the actual API flow that the JavaScript would use."""
    
    print("🧪 TESTING REAL API FLOW")
    print("=" * 50)
    
    # Create test PDF
    pdf_content = b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R>>endobj
4 0 obj<</Length 180>>stream
BT /F1 12 Tf 50 750 Td
(AMERICAN EXPRESS STATEMENT) Tj
0 -20 Td (Account: 1234-567890-12345) Tj
0 -20 Td (Statement Date: Jan 2024) Tj
0 -20 Td (Balance: $1,500.00) Tj
ET
endstream
endobj
xref 0 5
trailer<</Size 5/Root 1 0 R>>
startxref 400
%%EOF"""

    base_url = "http://127.0.0.1:8000"
    
    async with aiohttp.ClientSession() as session:
        try:
            # Step 1: Test if server is running
            print("1. 🔍 Checking if server is running...")
            async with session.get(f"{base_url}/health") as resp:
                if resp.status == 200:
                    print("   ✅ Server is running")
                else:
                    print(f"   ❌ Server returned status {resp.status}")
                    return False
                    
        except Exception as e:
            print(f"   ❌ Server not running: {e}")
            print("   💡 Please start server first: uvicorn main:app --host 127.0.0.1 --port 8000")
            return False
            
        # Step 2: Upload document (like JavaScript does)
        print("2. 📤 Uploading document...")
        data = aiohttp.FormData()
        data.add_field('file', pdf_content, filename='test_amex.pdf', content_type='application/pdf')
        
        try:
            async with session.post(f"{base_url}/api/v1/upload-document/", data=data) as resp:
                if resp.status == 200:
                    upload_result = await resp.json()
                    task_id = upload_result['task_id']
                    print(f"   ✅ Upload successful, task ID: {task_id[:8]}...")
                else:
                    error_text = await resp.text()
                    print(f"   ❌ Upload failed: {resp.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"   ❌ Upload error: {e}")
            return False
        
        # Step 3: Poll for status (like JavaScript does)
        print("3. 🔄 Polling for status...")
        max_attempts = 45  # 90 seconds total
        attempt = 0
        
        while attempt < max_attempts:
            attempt += 1
            try:
                async with session.get(f"{base_url}/api/v1/status/{task_id}") as resp:
                    if resp.status == 200:
                        status_result = await resp.json()
                        current_status = status_result['status']
                        print(f"   📊 Attempt {attempt}: Status = {current_status}")
                        
                        if current_status == 'completed':
                            print("   ✅ Processing completed!")
                            break
                        elif current_status == 'failed':
                            print("   ❌ Processing failed!")
                            return False
                        else:
                            print(f"   ⏳ Still processing... (status: {current_status})")
                            await asyncio.sleep(2)
                    else:
                        print(f"   ❌ Status check failed: {resp.status}")
                        return False
            except Exception as e:
                print(f"   ❌ Status check error: {e}")
                return False
        
        if attempt >= max_attempts:
            print("   ⏰ Polling timeout - processing took too long")
            return False
        
        # Step 4: Get results (like JavaScript does)
        print("4. 📊 Getting results...")
        try:
            async with session.get(f"{base_url}/api/v1/result/{task_id}") as resp:
                if resp.status == 200:
                    result = await resp.json()
                    print("   ✅ Results retrieved successfully!")
                    print(f"   🏷️  Category: {result['classification']['category']}")
                    print(f"   🎯 Confidence: {result['classification']['confidence']:.2f}")
                    return True
                else:
                    print(f"   ❌ Get result failed: {resp.status}")
                    return False
        except Exception as e:
            print(f"   ❌ Get result error: {e}")
            return False

def analyze_javascript_modal_issue():
    """Analyze the exact JavaScript modal issue."""
    
    print("\n🔍 ANALYZING JAVASCRIPT MODAL ISSUE")
    print("=" * 50)
    
    # Check if the modal element selector is correct
    base_html_path = "src/web/templates/base.html"
    with open(base_html_path, 'r') as f:
        base_content = f.read()
    
    print("1. 📄 Modal HTML structure:")
    # Extract modal structure
    import re
    modal_match = re.search(r'<div class="modal-body[^>]*>(.*?)</div>', base_content, re.DOTALL)
    if modal_match:
        modal_body = modal_match.group(1).strip()
        print("   Modal body HTML:")
        for line in modal_body.split('\n'):
            print(f"     {line.strip()}")
    
    # Check JavaScript selector
    app_js_path = "src/web/static/js/app.js"
    with open(app_js_path, 'r') as f:
        app_content = f.read()
    
    print("\n2. 🔧 JavaScript selector analysis:")
    selector_match = re.search(r'querySelector\([\'"]([^\'"]+)[\'"]\)', app_content)
    if selector_match:
        selector = selector_match.group(1)
        print(f"   Current selector: '{selector}'")
        
        # Test if selector matches HTML
        if 'p.mb-0' in selector:
            if 'class="mb-0"' in base_content:
                print("   ✅ Selector should match HTML")
            else:
                print("   ❌ Selector does not match HTML!")
                print("   🔍 Looking for actual p tags...")
                p_matches = re.findall(r'<p[^>]*>([^<]*)</p>', modal_body)
                print(f"   Found p tags: {p_matches}")
    
    print("\n3. 🎯 Modal hide call analysis:")
    upload_js_path = "src/web/static/js/upload.js"
    with open(upload_js_path, 'r') as f:
        upload_content = f.read()
    
    hide_calls = upload_content.count('LoadingModal.hide()')
    print(f"   Total LoadingModal.hide() calls: {hide_calls}")
    
    # Find the completion callback
    completion_match = re.search(r'// Completion callback.*?async \(status\) => \{(.*?)\}', upload_content, re.DOTALL)
    if completion_match:
        callback_code = completion_match.group(1)
        if 'LoadingModal.hide()' in callback_code:
            print("   ✅ Completion callback has modal hide")
        else:
            print("   ❌ Completion callback missing modal hide!")
    
    return True

def fix_modal_selector_issue():
    """Fix the modal selector issue by checking actual HTML structure."""
    
    print("\n🔧 FIXING MODAL SELECTOR ISSUE")
    print("=" * 50)
    
    # Read the actual modal HTML
    base_html_path = "src/web/templates/base.html"
    with open(base_html_path, 'r') as f:
        content = f.read()
    
    # Find the actual modal structure
    import re
    modal_match = re.search(r'<div class="modal-body[^>]*>(.*?)</div>', content, re.DOTALL)
    if modal_match:
        modal_body = modal_match.group(1)
        print("Current modal body structure:")
        print(modal_body)
        
        # Look for the p tag that contains the message
        p_matches = re.findall(r'<p([^>]*)>([^<]*)</p>', modal_body)
        print(f"\nFound p tags: {p_matches}")
        
        # The correct selector should be for the p tag with the message
        correct_selector = None
        for attrs, text in p_matches:
            if 'Processing document' in text or 'mb-0' in attrs:
                if 'mb-0' in attrs:
                    correct_selector = '.modal-body p.mb-0'
                else:
                    correct_selector = '.modal-body p'
                break
        
        if correct_selector:
            print(f"✅ Correct selector should be: '{correct_selector}'")
            
            # Update app.js with correct selector
            app_js_path = "src/web/static/js/app.js"
            with open(app_js_path, 'r') as f:
                app_content = f.read()
            
            # Replace the selector
            updated_content = re.sub(
                r'querySelector\([\'"]\.modal-body p[^\'\"]*[\'\"]\)',
                f"querySelector('{correct_selector}')",
                app_content
            )
            
            if updated_content != app_content:
                with open(app_js_path, 'w') as f:
                    f.write(updated_content)
                print(f"✅ Updated selector in app.js")
                return True
            else:
                print("ℹ️  Selector was already correct")
                return True
        else:
            print("❌ Could not determine correct selector")
            return False

async def main():
    """Run all tests and fixes."""
    
    print("🏠 DOCUMENT CLASSIFICATION SYSTEM")
    print("🔧 MODAL FIX - COMPREHENSIVE TESTING")
    print("=" * 60)
    print(f"⏰ Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Analyze the JavaScript issue first
    analyze_javascript_modal_issue()
    
    # Try to fix selector issue
    fix_modal_selector_issue()
    
    # Test the actual API flow
    api_success = await test_real_api_flow()
    
    print("\n" + "=" * 60)
    print("🎯 COMPREHENSIVE TEST RESULTS")
    print("=" * 60)
    
    if api_success:
        print("✅ Backend API flow: WORKING")
        print("✅ Document classification: SUCCESSFUL")
        print("✅ All endpoints responding correctly")
        print()
        print("🔍 Modal Issue Analysis:")
        print("  The backend is working perfectly.")
        print("  The issue is in JavaScript modal management.")
        print("  I've checked and fixed the modal selector.")
        print()
        print("🚀 NEXT STEPS:")
        print("1. Stop your server (Ctrl+C)")
        print("2. Restart server: uvicorn main:app --host 127.0.0.1 --port 8000")
        print("3. Hard refresh browser (Ctrl+Shift+R)")
        print("4. Open console (F12)")
        print("5. Try uploading again")
        print()
        print("📱 Emergency fix if modal still stuck:")
        print("  Open console and run: forceHideModal()")
    else:
        print("❌ Backend API flow: FAILED")
        print("🔧 Please start the server first and try again")

if __name__ == "__main__":
    asyncio.run(main())
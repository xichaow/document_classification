#!/usr/bin/env python3
"""
Create test files for demonstrating the evaluation system.
"""

import io
import json
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_test_pdf(content_text, output_path):
    """Create a simple PDF with the given text content."""
    
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Add content
    p.setFont("Helvetica", 12)
    lines = content_text.split('\n')
    y_position = height - 100
    
    for line in lines:
        p.drawString(100, y_position, line)
        y_position -= 20
        if y_position < 100:  # Start new page if needed
            p.showPage()
            y_position = height - 100
    
    p.save()
    
    # Write to file
    with open(output_path, 'wb') as f:
        f.write(buffer.getvalue())
    
    buffer.close()
    print(f"✅ Created test PDF: {output_path}")

def main():
    """Create test documents for evaluation."""
    
    print("🧪 CREATING TEST DOCUMENTS FOR EVALUATION")
    print("=" * 50)
    
    # Test documents with different types
    test_docs = [
        {
            "filename": "test_bank_statement.pdf",
            "true_label": "Bank Statement", 
            "content": """AMERICAN EXPRESS
Bank Statement
Account Number: ****-****-****-1234
Statement Period: December 2023 - January 2024
Previous Balance: $1,234.56
New Charges: $567.89
Payments/Credits: -$1,200.00
New Balance: $602.45
Payment Due Date: February 15, 2024
Minimum Payment Due: $25.00"""
        },
        {
            "filename": "test_payslip.pdf",
            "true_label": "Payslip",
            "content": """COMPANY PAYSLIP
Employee: John Smith
Pay Period: January 1-15, 2024
Gross Pay: $2,500.00
Deductions:
  Federal Tax: $450.00
  State Tax: $125.00
  Social Security: $155.00
  Medicare: $36.25
Net Pay: $1,733.75
Hours Worked: 80"""
        },
        {
            "filename": "test_government_id.pdf", 
            "true_label": "Government ID",
            "content": """STATE OF CALIFORNIA
DRIVER'S LICENSE
Name: Jane Doe
License Number: D1234567
Date of Birth: 01/01/1990
Issue Date: 06/15/2023
Expiration Date: 01/01/2028
Class: C
Restrictions: NONE"""
        },
        {
            "filename": "test_utility_bill.pdf",
            "true_label": "Utility Bill", 
            "content": """PACIFIC GAS & ELECTRIC
Utility Bill
Account Number: 1234567890
Service Address: 123 Main St, San Francisco, CA
Billing Period: Dec 1 - Dec 31, 2023
Electric Usage: 450 kWh
Gas Usage: 25 therms
Amount Due: $156.78
Due Date: January 15, 2024"""
        },
        {
            "filename": "test_employment_letter.pdf",
            "true_label": "Employment Letter",
            "content": """ABC CORPORATION
Employment Verification Letter

To Whom It May Concern:

This letter confirms that John Smith has been employed
with ABC Corporation since March 15, 2020.

Current Position: Software Engineer
Employment Status: Full-time
Annual Salary: $95,000

Please contact HR if you need additional information.

Sincerely,
HR Department"""
        }
    ]
    
    # Create test directory
    import os
    test_dir = "test_evaluation_docs"
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
    
    # Create PDFs
    ground_truth = {}
    
    for doc in test_docs:
        file_path = os.path.join(test_dir, doc["filename"])
        create_test_pdf(doc["content"], file_path)
        ground_truth[doc["filename"]] = doc["true_label"]
    
    # Save ground truth labels
    labels_file = os.path.join(test_dir, "ground_truth_labels.json")
    with open(labels_file, 'w') as f:
        json.dump(ground_truth, f, indent=2)
    
    print(f"✅ Created ground truth labels: {labels_file}")
    
    print("\n" + "=" * 50)
    print("🎯 TEST DATASET READY!")
    print("=" * 50)
    print(f"📁 Directory: {test_dir}")
    print(f"📄 Test documents: {len(test_docs)}")
    print(f"🏷️  Ground truth labels: {labels_file}")
    
    print("\n📋 GROUND TRUTH LABELS:")
    for filename, label in ground_truth.items():
        print(f"   {filename} → {label}")
    
    print(f"\n🚀 HOW TO USE:")
    print(f"1. Go to http://localhost:8000/evaluation")
    print(f"2. Upload all PDF files from {test_dir}/")
    print(f"3. Copy the JSON from {labels_file} into the ground truth field")
    print(f"4. Click 'Start Evaluation' to run batch test")
    print(f"5. View comprehensive metrics and results!")
    
    # Print the JSON for easy copying
    print(f"\n📋 COPY THIS JSON FOR GROUND TRUTH LABELS:")
    print(json.dumps(ground_truth, indent=2))

if __name__ == "__main__":
    try:
        main()
    except ImportError as e:
        print("❌ Missing dependency. Install reportlab:")
        print("pip install reportlab")
        print(f"Error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
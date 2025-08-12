"""
Classification prompts and templates for document classification.

This module contains carefully crafted prompts with few-shot examples
for accurate document type classification using AWS Bedrock.
"""

# Document types for classification
DOCUMENT_TYPES = [
    "Government ID",
    "Payslip",
    "Bank Statement",
    "Employment Letter",
    "Utility Bill",
    "Savings Statement",
]

# Main classification prompt template with few-shot examples
CLASSIFICATION_PROMPT_TEMPLATE = """
You are an expert document classifier for home loan applications. Your task is to analyze document text and classify it into one of these categories:

- Government ID (Driver's License, Passport, National ID)
- Payslip (Income statements, pay stubs, salary slips)
- Bank Statement (Account statements, transaction records)
- Employment Letter (Job verification, employment confirmation)
- Utility Bill (Electric, gas, water, internet, phone bills)
- Savings Statement (Investment accounts, savings records, retirement accounts)

<text>
{extracted_text}
</text>

Classification Examples:

Example 1:
Text: "DRIVER LICENSE Class C License Number: D123456789 Date of Birth: 01/15/1985 Expires: 12/31/2027 Address: 123 Main St"
Analysis: Contains license number, date of birth, expiration date, and official government format
Category: Government ID

Example 2:
Text: "Pay Period: 01/01/2024 - 01/31/2024 Employee ID: E12345 Gross Pay: $5,000.00 Federal Tax: $750.00 Net Pay: $3,800.00"
Analysis: Shows pay period, employee information, salary details, and tax deductions
Category: Payslip

Example 3:
Text: "BANK STATEMENT Account Number: ****1234 Statement Period: Jan 1 - Jan 31, 2024 Beginning Balance: $2,500.00 Ending Balance: $2,750.00"
Analysis: Contains account information, statement period, and balance details from financial institution
Category: Bank Statement

Example 4:
Text: "Employment Verification Letter John Smith has been employed with ABC Corporation since March 2020 as Senior Software Engineer Annual Salary: $75,000"
Analysis: Official employment confirmation with job title, start date, and salary information
Category: Employment Letter

Example 5:
Text: "Electric Company Monthly Bill Account: 123456789 Service Period: Jan 1-31, 2024 Amount Due: $145.67 Due Date: Feb 15, 2024"
Analysis: Utility service bill with account details, service period, and payment information
Category: Utility Bill

Example 6:
Text: "Savings Account Statement Account Type: High-Yield Savings Interest Rate: 2.5% APY Current Balance: $15,000.00 Interest Earned: $312.50"
Analysis: Savings account details with interest information and balance from financial institution
Category: Savings Statement

Instructions:
1. Carefully analyze the document text for key identifying features
2. Match patterns and terminology to the appropriate document type
3. Consider document structure, formatting, and specific terminology
4. If the document contains mixed content, classify based on the primary purpose
5. Provide a confidence score between 0.0 and 1.0
6. Include brief reasoning for your classification

Respond in JSON format:
{{
    "category": "document_type",
    "confidence": 0.95,
    "reasoning": "Brief explanation of classification decision"
}}

Classification:"""

# Prompt for handling unclear or ambiguous documents
AMBIGUOUS_DOCUMENT_PROMPT = """
The document text provided does not clearly match any of the standard home loan document categories. 

Please analyze if this could be:
1. A partial or damaged document from one of the standard types
2. A supporting document related to home loan applications
3. An irrelevant document that should be rejected

Standard categories:
- Government ID, Payslip, Bank Statement, Employment Letter, Utility Bill, Savings Statement

If unsure, classify as "Unknown" with low confidence and explain why the document is ambiguous.
"""

# Prompt templates for specific document types (for fine-tuning)
GOVERNMENT_ID_INDICATORS = [
    "license number",
    "driver license",
    "passport",
    "national id",
    "date of birth",
    "expires",
    "issued",
    "state id",
    "identification",
]

PAYSLIP_INDICATORS = [
    "pay period",
    "gross pay",
    "net pay",
    "employee id",
    "salary",
    "wages",
    "deductions",
    "tax",
    "payroll",
    "pay stub",
    "earnings",
]

BANK_STATEMENT_INDICATORS = [
    "account number",
    "statement period",
    "balance",
    "transaction",
    "deposit",
    "withdrawal",
    "checking",
    "savings account statement",
]

EMPLOYMENT_LETTER_INDICATORS = [
    "employment verification",
    "employed with",
    "job title",
    "position",
    "annual salary",
    "start date",
    "employment status",
    "hr department",
]

UTILITY_BILL_INDICATORS = [
    "electric",
    "gas",
    "water",
    "internet",
    "phone",
    "cable",
    "utility",
    "service period",
    "amount due",
    "kwh",
    "usage",
]

SAVINGS_STATEMENT_INDICATORS = [
    "savings account",
    "investment",
    "retirement",
    "401k",
    "ira",
    "interest rate",
    "apy",
    "dividend",
    "portfolio",
    "mutual fund",
]


def build_confidence_explanation(category: str, confidence: float) -> str:
    """
    Build explanation for confidence score.

    Args:
        category: Classified document category.
        confidence: Confidence score.

    Returns:
        str: Explanation of confidence level.
    """
    if confidence >= 0.9:
        return f"High confidence - clear {category} indicators present"
    elif confidence >= 0.7:
        return f"Good confidence - most {category} characteristics identified"
    elif confidence >= 0.5:
        return f"Moderate confidence - some {category} features detected"
    else:
        return f"Low confidence - ambiguous or unclear {category} classification"


def get_document_indicators(category: str) -> list:
    """
    Get keyword indicators for a specific document category.

    Args:
        category: Document category name.

    Returns:
        list: List of indicator keywords.
    """
    indicators_map = {
        "Government ID": GOVERNMENT_ID_INDICATORS,
        "Payslip": PAYSLIP_INDICATORS,
        "Bank Statement": BANK_STATEMENT_INDICATORS,
        "Employment Letter": EMPLOYMENT_LETTER_INDICATORS,
        "Utility Bill": UTILITY_BILL_INDICATORS,
        "Savings Statement": SAVINGS_STATEMENT_INDICATORS,
    }

    return indicators_map.get(category, [])

"""
Offline document classifier that works without AWS credentials.

This provides a fallback classification system using rule-based matching
when AWS services are not available.
"""

import re
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class OfflineClassifier:
    """
    Rule-based document classifier for when AWS services are unavailable.
    
    Uses text pattern matching to identify document types based on common
    keywords and phrases found in different document categories.
    """
    
    def __init__(self):
        """Initialize the offline classifier with rule patterns."""
        self.classification_rules = {
            'Government ID': {
                'keywords': [
                    'driver', 'license', 'passport', 'national id', 'identity card',
                    'drivers license', "driver's license", 'state id', 'identification',
                    'license number', 'dl number', 'passport number', 'id number'
                ],
                'patterns': [
                    r'\b(drivers?\s+licen[cs]e|dl)\b',
                    r'\bpassport\s+number\b',
                    r'\bid\s*number\b',
                    r'\bstate\s+id\b'
                ]
            },
            'Payslip': {
                'keywords': [
                    'payslip', 'pay slip', 'pay stub', 'paystub', 'salary', 'wages',
                    'earnings', 'gross pay', 'net pay', 'deductions', 'tax withheld',
                    'employer', 'employee', 'pay period', 'hours worked', 'overtime'
                ],
                'patterns': [
                    r'\b(gross|net)\s+pay\b',
                    r'\bpay\s+(period|stub|slip)\b',
                    r'\bearnings\b',
                    r'\bdeductions\b',
                    r'\btax\s+with[he]eld\b'
                ]
            },
            'Bank Statement': {
                'keywords': [
                    'bank statement', 'account statement', 'checking account', 'savings account',
                    'balance', 'transaction', 'deposit', 'withdrawal', 'transfer',
                    'beginning balance', 'ending balance', 'account number', 'routing number',
                    'statement period', 'credit card', 'american express', 'visa', 'mastercard'
                ],
                'patterns': [
                    r'\b(bank|account)\s+statement\b',
                    r'\b(checking|savings)\s+account\b',
                    r'\b(beginning|ending)\s+balance\b',
                    r'\baccount\s+number\b',
                    r'\bstatement\s+period\b',
                    r'\b(american\s+express|amex|visa|mastercard)\b'
                ]
            },
            'Employment Letter': {
                'keywords': [
                    'employment letter', 'employment verification', 'job offer', 'offer letter',
                    'employment confirmation', 'work verification', 'position', 'title',
                    'start date', 'hire date', 'employment status', 'full time', 'part time',
                    'salary', 'compensation', 'benefits', 'hr department', 'human resources'
                ],
                'patterns': [
                    r'\bemployment\s+(letter|verification|confirmation)\b',
                    r'\b(job|offer)\s+letter\b',
                    r'\bstart\s+date\b',
                    r'\bemployment\s+status\b',
                    r'\b(full|part)\s+time\b'
                ]
            },
            'Utility Bill': {
                'keywords': [
                    'utility bill', 'electric bill', 'gas bill', 'water bill', 'electricity',
                    'natural gas', 'water service', 'sewage', 'internet bill', 'phone bill',
                    'cable bill', 'utility company', 'service period', 'meter reading',
                    'kilowatt', 'kwh', 'usage', 'due date', 'amount due'
                ],
                'patterns': [
                    r'\b(utility|electric|gas|water)\s+bill\b',
                    r'\b(electricity|natural\s+gas)\b',
                    r'\bmeter\s+reading\b',
                    r'\bkilowatt|kwh\b',
                    r'\bservice\s+period\b'
                ]
            },
            'Savings Statement': {
                'keywords': [
                    'savings statement', 'investment statement', 'portfolio statement',
                    'savings account', 'investment account', 'mutual fund', 'stocks',
                    'bonds', 'securities', 'dividend', 'interest earned', 'capital gains',
                    'portfolio value', 'investment summary', 'asset allocation'
                ],
                'patterns': [
                    r'\b(savings|investment|portfolio)\s+statement\b',
                    r'\binvestment\s+account\b',
                    r'\bmutual\s+fund\b',
                    r'\b(dividend|interest)\s+earned\b',
                    r'\bportfolio\s+value\b'
                ]
            }
        }
    
    def classify_text(self, text: str) -> Dict[str, Any]:
        """
        Classify text using rule-based matching.
        
        Args:
            text: Extracted text from document.
            
        Returns:
            Dict containing classification result.
        """
        if not text or len(text.strip()) < 10:
            return {
                'category': 'Unknown',
                'confidence': 0.0,
                'reasoning': 'Insufficient text content for classification'
            }
        
        # Normalize text for matching
        normalized_text = text.lower().strip()
        
        # Score each category
        category_scores = {}
        
        for category, rules in self.classification_rules.items():
            score = 0
            matched_items = []
            
            # Check keywords
            for keyword in rules['keywords']:
                if keyword.lower() in normalized_text:
                    score += 1
                    matched_items.append(keyword)
            
            # Check regex patterns
            for pattern in rules['patterns']:
                if re.search(pattern, normalized_text, re.IGNORECASE):
                    score += 2  # Patterns get higher weight
                    matched_items.append(f"pattern: {pattern}")
            
            if score > 0:
                category_scores[category] = {
                    'score': score,
                    'matches': matched_items
                }
        
        if not category_scores:
            return {
                'category': 'Unknown',
                'confidence': 0.0,
                'reasoning': 'No matching patterns found in document text'
            }
        
        # Find best match
        best_category = max(category_scores.keys(), key=lambda k: category_scores[k]['score'])
        best_score = category_scores[best_category]['score']
        best_matches = category_scores[best_category]['matches']
        
        # Calculate confidence based on score and text length
        max_possible_score = len(self.classification_rules[best_category]['keywords']) + \
                           (len(self.classification_rules[best_category]['patterns']) * 2)
        
        confidence = min(0.95, (best_score / max_possible_score) * 0.8 + 0.3)  # 0.3-0.95 range
        
        # Create reasoning
        reasoning = f"Classified as {best_category} based on {len(best_matches)} matching indicators: {', '.join(best_matches[:3])}"
        if len(best_matches) > 3:
            reasoning += f" and {len(best_matches) - 3} others"
        reasoning += ". This is an offline classification using rule-based matching."
        
        return {
            'category': best_category,
            'confidence': confidence,
            'reasoning': reasoning
        }
    
    def extract_key_info(self, text: str, category: str) -> Dict[str, str]:
        """
        Extract key information based on document category.
        
        Args:
            text: Document text.
            category: Classified document category.
            
        Returns:
            Dict of extracted key information.
        """
        info = {}
        normalized_text = text.lower()
        
        # Common patterns
        date_pattern = r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b'
        money_pattern = r'\$[\d,]+\.?\d*'
        
        # Extract dates
        dates = re.findall(date_pattern, text)
        if dates:
            info['dates'] = dates[:3]  # First 3 dates found
        
        # Extract amounts
        amounts = re.findall(money_pattern, text)
        if amounts:
            info['amounts'] = amounts[:5]  # First 5 amounts found
        
        # Category-specific extraction
        if category == 'Bank Statement':
            # Look for account numbers
            account_patterns = [
                r'account\s+number[:\s]+([*\d-]+)',
                r'account[:\s]+([*\d-]+)'
            ]
            for pattern in account_patterns:
                match = re.search(pattern, normalized_text)
                if match:
                    info['account_number'] = match.group(1)
                    break
        
        return info


def create_offline_classification_result(text: str, filename: str, processing_time: float) -> Dict[str, Any]:
    """
    Create a complete classification result using offline classifier.
    
    Args:
        text: Extracted text.
        filename: Original filename.
        processing_time: Time taken to process.
        
    Returns:
        Complete classification result.
    """
    classifier = OfflineClassifier()
    classification = classifier.classify_text(text)
    
    return {
        'status': 'completed',
        'filename': filename,
        'classification': {
            'category': classification['category'],
            'confidence': classification['confidence'],
            'reasoning': classification['reasoning'],
            'needs_manual_review': classification['confidence'] < 0.6  # Lower threshold for offline
        },
        'extracted_text_length': len(text) if text else 0,
        'processing_time': processing_time,
        'metadata': {
            'textract_success': False,
            'bedrock_success': False,
            'offline_classification': True,
            'extraction_method': 'pypdf',
            'classification_method': 'rule_based'
        }
    }
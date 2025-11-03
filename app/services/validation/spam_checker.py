"""
Spam Score Checker
Analyzes email content for spam indicators
"""
import re
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class SpamChecker:
    """Check email content for spam indicators"""
    
    # Spam trigger words (weighted by severity)
    SPAM_WORDS = {
        'high': [
            'viagra', 'cialis', 'nigerian prince', 'lottery winner',
            'act now', 'click here', 'limited time', 'urgent',
            'congratulations', 'you\'ve won', 'free money', 'get paid',
            'work from home', 'make money fast', 'guaranteed income',
            'buy now', 'order now', 'special promotion', 'once in lifetime'
        ],
        'medium': [
            'free', 'discount', 'offer', 'deal', 'save', 'cash',
            'credit', 'insurance', 'investment', 'loan', 'mortgage',
            'refinance', 'weight loss', 'MLM', 'network marketing'
        ],
        'low': [
            'subscribe', 'unsubscribe', 'click', 'here', 'now',
            'today', 'limited', 'offer expires', 'don\'t miss'
        ]
    }
    
    def __init__(self):
        pass
    
    def check(self, subject: str, html_body: str, text_body: str = '') -> Dict:
        """
        Comprehensive spam check
        Returns: {
            'score': int (0-100, lower is better),
            'verdict': 'safe'|'warning'|'spam',
            'issues': list,
            'recommendations': list
        }
        """
        score = 0
        issues = []
        recommendations = []
        
        # Combine all text
        all_text = f"{subject} {html_body} {text_body}".lower()
        
        # 1. Check spam words
        spam_word_score, spam_issues = self._check_spam_words(all_text)
        score += spam_word_score
        issues.extend(spam_issues)
        
        # 2. Check excessive punctuation
        if re.search(r'[!?]{3,}', subject):
            score += 10
            issues.append('Excessive punctuation in subject')
        
        # 3. Check all caps
        if subject.isupper() and len(subject) > 10:
            score += 15
            issues.append('Subject line in all caps')
            recommendations.append('Use normal capitalization')
        
        # 4. Check for ALL CAPS in body
        caps_ratio = sum(1 for c in all_text if c.isupper()) / max(len(all_text), 1)
        if caps_ratio > 0.3:
            score += 10
            issues.append('Too much capitalization in content')
        
        # 5. Check link count
        link_count = len(re.findall(r'https?://', html_body))
        if link_count > 10:
            score += link_count - 10
            issues.append(f'Too many links ({link_count})')
            recommendations.append('Reduce number of links')
        
        # 6. Check for URL shorteners
        if re.search(r'bit\.ly|tinyurl|goo\.gl', all_text):
            score += 15
            issues.append('URL shorteners detected')
            recommendations.append('Use full URLs instead of shorteners')
        
        # 7. Check image to text ratio
        img_count = len(re.findall(r'<img', html_body))
        text_length = len(re.sub(r'<[^>]+>', '', html_body))
        
        if img_count > 0 and text_length < 100:
            score += 20
            issues.append('Image-heavy email with little text')
            recommendations.append('Add more text content')
        
        # 8. Check for proper unsubscribe
        if not re.search(r'unsubscribe', all_text):
            score += 10
            issues.append('No unsubscribe link found')
            recommendations.append('Add unsubscribe link')
        
        # 9. Check for from name
        # (Would be passed separately in real implementation)
        
        # 10. Check HTML quality
        if html_body and not re.search(r'<!DOCTYPE|<html', html_body):
            score += 5
            issues.append('Missing proper HTML structure')
        
        # Determine verdict
        if score <= 30:
            verdict = 'safe'
        elif score <= 60:
            verdict = 'warning'
        else:
            verdict = 'spam'
        
        return {
            'score': min(score, 100),
            'verdict': verdict,
            'issues': issues,
            'recommendations': recommendations,
            'details': {
                'spam_words_found': spam_word_score > 0,
                'excessive_caps': caps_ratio > 0.3,
                'too_many_links': link_count > 10,
                'missing_unsubscribe': 'unsubscribe' not in all_text
            }
        }
    
    def _check_spam_words(self, text: str) -> tuple:
        """Check for spam trigger words"""
        score = 0
        issues = []
        found_words = []
        
        for severity, words in self.SPAM_WORDS.items():
            for word in words:
                if word in text:
                    found_words.append(word)
                    if severity == 'high':
                        score += 20
                    elif severity == 'medium':
                        score += 10
                    else:
                        score += 5
        
        if found_words:
            issues.append(f'Spam trigger words found: {", ".join(found_words[:5])}')
        
        return score, issues

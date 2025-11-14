"""
Advanced AI Features for Reply Intelligence
"""
import re
from datetime import datetime, timedelta
from collections import Counter

class AdvancedReplyAI:
    """Advanced AI capabilities for replies"""
    
    def extract_contact_info(self, text):
        """Extract phone numbers, emails, etc from reply"""
        info = {
            'phone_numbers': [],
            'emails': [],
            'urls': []
        }
        
        # Extract phone numbers
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        info['phone_numbers'] = re.findall(phone_pattern, text)
        
        # Extract emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        info['emails'] = re.findall(email_pattern, text)
        
        # Extract URLs
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        info['urls'] = re.findall(url_pattern, text)
        
        return info
    
    def detect_pain_points(self, text):
        """Detect customer pain points"""
        pain_indicators = {
            'cost': ['expensive', 'too much', 'costly', 'price', 'budget'],
            'complexity': ['difficult', 'complicated', 'confusing', 'hard to use'],
            'time': ['slow', 'takes forever', 'waste of time', 'inefficient'],
            'support': ['no help', 'no response', 'poor support', 'unanswered'],
            'features': ['missing', 'lack of', 'doesn\'t have', 'need more'],
            'reliability': ['broken', 'doesn\'t work', 'bug', 'error', 'crash']
        }
        
        detected_pains = []
        text_lower = text.lower()
        
        for pain_type, keywords in pain_indicators.items():
            if any(keyword in text_lower for keyword in keywords):
                detected_pains.append(pain_type)
        
        return detected_pains
    
    def detect_buying_signals(self, text):
        """Detect if customer is ready to buy"""
        strong_signals = [
            'ready to buy', 'want to purchase', 'sign up now',
            'get started', 'credit card', 'payment', 'invoice'
        ]
        
        medium_signals = [
            'interested', 'tell me more', 'learn more',
            'demo', 'trial', 'pricing'
        ]
        
        weak_signals = [
            'curious', 'looking at', 'considering',
            'might be', 'thinking about'
        ]
        
        text_lower = text.lower()
        
        if any(signal in text_lower for signal in strong_signals):
            return 'hot'  # Ready to buy
        elif any(signal in text_lower for signal in medium_signals):
            return 'warm'  # Interested
        elif any(signal in text_lower for signal in weak_signals):
            return 'cold'  # Just browsing
        
        return 'unknown'
    
    def extract_company_info(self, text):
        """Extract company name, size, industry"""
        info = {
            'company_name': None,
            'company_size': None,
            'industry': None
        }
        
        # Look for company mentions
        company_pattern = r'(?:at|from|with)\s+([A-Z][a-zA-Z0-9\s&]+?)(?:\.|,|\s+(?:and|in|with))'
        matches = re.findall(company_pattern, text)
        if matches:
            info['company_name'] = matches[0].strip()
        
        # Detect company size mentions
        size_patterns = {
            'startup': ['startup', 'small team', 'few people'],
            'small': ['small business', 'small company', '10 people', 'dozen'],
            'medium': ['medium-sized', '100 people', 'hundred'],
            'large': ['enterprise', 'large company', 'fortune', '1000 people', 'thousand']
        }
        
        text_lower = text.lower()
        for size, patterns in size_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                info['company_size'] = size
                break
        
        return info
    
    def suggest_next_action(self, reply_data):
        """AI suggests what to do next"""
        intent = reply_data.get('intent')
        category = reply_data.get('category')
        sentiment = reply_data.get('sentiment')
        urgency = reply_data.get('urgency')
        
        suggestions = []
        
        # High urgency + negative sentiment = immediate action
        if urgency == 'high' and sentiment == 'negative':
            suggestions.append({
                'action': 'escalate',
                'priority': 'critical',
                'message': 'Escalate to senior support immediately',
                'reason': 'Urgent negative feedback requires immediate attention'
            })
        
        # Interested + pricing = send proposal
        if intent == 'interested' and category == 'pricing':
            suggestions.append({
                'action': 'send_proposal',
                'priority': 'high',
                'message': 'Send detailed pricing proposal with ROI calculator',
                'reason': 'Customer is interested and asking about pricing'
            })
        
        # Demo request = schedule
        if category == 'demo_request':
            suggestions.append({
                'action': 'schedule_demo',
                'priority': 'high',
                'message': 'Send calendar link to book demo',
                'reason': 'Customer explicitly requested demo'
            })
        
        # Question + neutral = provide info
        if intent == 'question' and sentiment == 'neutral':
            suggestions.append({
                'action': 'provide_info',
                'priority': 'medium',
                'message': 'Answer their questions thoroughly',
                'reason': 'Customer seeking information'
            })
        
        # Positive sentiment = nurture
        if sentiment == 'positive':
            suggestions.append({
                'action': 'nurture',
                'priority': 'medium',
                'message': 'Send case studies and success stories',
                'reason': 'Customer has positive sentiment, keep momentum'
            })
        
        # Not interested = add to suppression
        if intent == 'not_interested':
            suggestions.append({
                'action': 'suppress',
                'priority': 'low',
                'message': 'Add to suppression list and unsubscribe',
                'reason': 'Customer explicitly not interested'
            })
        
        return suggestions
    
    def predict_conversion_probability(self, reply_data):
        """Predict likelihood of conversion"""
        score = 50  # Base score
        
        # Sentiment impact
        if reply_data.get('sentiment') == 'positive':
            score += 20
        elif reply_data.get('sentiment') == 'negative':
            score -= 30
        
        # Intent impact
        if reply_data.get('intent') == 'interested':
            score += 25
        elif reply_data.get('intent') == 'not_interested':
            score -= 40
        
        # Category impact
        if reply_data.get('category') in ['pricing', 'demo_request']:
            score += 15
        
        # Urgency impact
        if reply_data.get('urgency') == 'high':
            score += 10
        
        # Cap between 0-100
        score = max(0, min(100, score))
        
        return {
            'probability': score,
            'rating': 'high' if score >= 70 else 'medium' if score >= 40 else 'low'
        }
    
    def analyze_reply_patterns(self, organization_id):
        """Analyze patterns across all replies"""
        from app import db
        from app.models.reply import EmailReply
        
        # Get all replies for org
        replies = EmailReply.query.filter_by(
            organization_id=organization_id
        ).all()
        
        if not replies:
            return None
        
        # Calculate metrics
        total = len(replies)
        
        # Sentiment distribution
        sentiments = Counter(r.sentiment for r in replies)
        
        # Category distribution
        categories = Counter(r.category for r in replies)
        
        # Response rate
        responded = len([r for r in replies if r.responded])
        response_rate = (responded / total * 100) if total > 0 else 0
        
        # Average response time
        response_times = []
        for r in replies:
            if r.responded and r.responded_at:
                delta = (r.responded_at - r.created_at).total_seconds() / 3600
                response_times.append(delta)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Common questions (extract from replies with '?')
        questions = []
        for r in replies:
            if r.text_body and '?' in r.text_body:
                sentences = r.text_body.split('?')
                questions.extend([s.strip()[-50:] for s in sentences if s.strip()])
        
        common_questions = Counter(questions).most_common(5)
        
        return {
            'total_replies': total,
            'sentiment_breakdown': dict(sentiments),
            'category_breakdown': dict(categories),
            'response_rate': round(response_rate, 2),
            'avg_response_time_hours': round(avg_response_time, 2),
            'common_questions': [q for q, _ in common_questions]
        }
    
    def generate_reply_insights(self, organization_id):
        """Generate actionable insights"""
        patterns = self.analyze_reply_patterns(organization_id)
        
        if not patterns:
            return []
        
        insights = []
        
        # Low response rate
        if patterns['response_rate'] < 50:
            insights.append({
                'type': 'warning',
                'title': 'Low Response Rate',
                'message': f"Only {patterns['response_rate']}% of replies are being answered. Consider enabling more auto-responses.",
                'action': 'Create more auto-response templates'
            })
        
        # High negative sentiment
        sentiment = patterns['sentiment_breakdown']
        if sentiment.get('negative', 0) > sentiment.get('positive', 0):
            insights.append({
                'type': 'critical',
                'title': 'High Negative Sentiment',
                'message': 'More negative replies than positive. Review customer complaints.',
                'action': 'Analyze negative feedback and address concerns'
            })
        
        # Slow response time
        if patterns['avg_response_time_hours'] > 24:
            insights.append({
                'type': 'warning',
                'title': 'Slow Response Time',
                'message': f"Average response time is {patterns['avg_response_time_hours']:.1f} hours. Customers expect faster replies.",
                'action': 'Set up response time SLA alerts'
            })
        
        # Common questions
        if patterns['common_questions']:
            insights.append({
                'type': 'opportunity',
                'title': 'Frequent Questions Detected',
                'message': f"These questions appear often: {', '.join(patterns['common_questions'][:3])}",
                'action': 'Create FAQ or knowledge base article'
            })
        
        return insights

# Initialize
advanced_ai = AdvancedReplyAI()

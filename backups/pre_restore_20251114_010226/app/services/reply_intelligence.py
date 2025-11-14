import re
from datetime import datetime
from app import db
from app.models.reply import EmailReply
from app.models.contact import Contact

class ReplyIntelligence:
    """AI-powered reply analysis"""
    
    def analyze_reply(self, reply_text, subject=""):
        """
        Analyze reply and return intelligence
        """
        text_lower = (reply_text or "").lower()
        subject_lower = (subject or "").lower()
        combined = f"{subject_lower} {text_lower}"
        
        # Analyze sentiment
        sentiment, sentiment_score = self.analyze_sentiment(combined)
        
        # Detect intent
        intent = self.detect_intent(combined)
        
        # Categorize
        category = self.categorize_reply(combined, intent)
        
        # Detect urgency
        urgency = self.detect_urgency(combined)
        
        # Extract key information
        questions = self.extract_questions(reply_text)
        
        return {
            'sentiment': sentiment,
            'sentiment_score': sentiment_score,
            'intent': intent,
            'category': category,
            'urgency': urgency,
            'questions': questions,
            'summary': self.generate_summary(reply_text, intent, category)
        }
    
    def analyze_sentiment(self, text):
        """Analyze sentiment of reply"""
        # Positive indicators
        positive_words = [
            'great', 'awesome', 'love', 'excellent', 'perfect', 'amazing',
            'interested', 'yes', 'please', 'thank', 'thanks', 'appreciate',
            'helpful', 'good', 'wonderful', 'fantastic', 'impressed'
        ]
        
        # Negative indicators
        negative_words = [
            'no', 'not interested', 'remove', 'unsubscribe', 'spam', 'stop',
            'never', 'terrible', 'bad', 'worst', 'hate', 'angry', 'frustrated',
            'disappointed', 'poor', 'awful', 'horrible'
        ]
        
        # Count occurrences
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        # Calculate score
        total = positive_count + negative_count
        if total == 0:
            return 'neutral', 0.5
        
        score = positive_count / total
        
        if score > 0.6:
            return 'positive', score
        elif score < 0.4:
            return 'negative', score
        else:
            return 'neutral', score
    
    def detect_intent(self, text):
        """Detect what the person wants"""
        # Question intent
        if '?' in text or any(q in text for q in ['how', 'what', 'when', 'where', 'why', 'who', 'which']):
            return 'question'
        
        # Strong interest
        if any(w in text for w in [
            'interested', 'tell me more', 'demo', 'trial', 'sign up', 
            'get started', 'want to', 'would like', 'buy', 'purchase'
        ]):
            return 'interested'
        
        # Not interested
        if any(w in text for w in [
            'not interested', 'no thank', 'remove me', 'unsubscribe',
            'stop sending', 'leave me alone'
        ]):
            return 'not_interested'
        
        # Support needed
        if any(w in text for w in [
            'help', 'support', 'problem', 'issue', 'bug', 'error',
            'not working', 'broken', 'fix'
        ]):
            return 'support'
        
        # Complaint
        if any(w in text for w in [
            'complain', 'angry', 'frustrated', 'disappointed', 'terrible'
        ]):
            return 'complaint'
        
        # Feedback
        if any(w in text for w in [
            'feedback', 'suggest', 'recommendation', 'feature request'
        ]):
            return 'feedback'
        
        return 'general'
    
    def categorize_reply(self, text, intent):
        """Categorize for routing"""
        # Pricing questions
        if any(w in text for w in ['price', 'cost', 'pricing', 'how much', '$', 'fee', 'payment']):
            return 'pricing'
        
        # Demo/trial requests
        if any(w in text for w in ['demo', 'trial', 'test', 'try', 'see it', 'show me']):
            return 'demo_request'
        
        # Feature questions
        if any(w in text for w in ['feature', 'can it', 'does it', 'support', 'integrate', 'work with']):
            return 'features'
        
        # Technical support
        if intent == 'support':
            return 'support'
        
        # Opt-out
        if intent == 'not_interested':
            return 'opt_out'
        
        # Meeting request
        if any(w in text for w in ['call', 'meeting', 'schedule', 'talk', 'discuss', 'speak']):
            return 'meeting_request'
        
        return 'general'
    
    def detect_urgency(self, text):
        """Detect how urgent the reply is"""
        # High urgency
        high_urgency_words = [
            'urgent', 'asap', 'immediately', 'emergency', 'critical',
            'right now', 'today', 'help', 'problem', 'broken'
        ]
        
        if any(word in text for word in high_urgency_words):
            return 'high'
        
        # Low urgency
        low_urgency_words = [
            'whenever', 'no rush', 'not urgent', 'future', 'eventually'
        ]
        
        if any(word in text for word in low_urgency_words):
            return 'low'
        
        return 'medium'
    
    def extract_questions(self, text):
        """Extract questions from reply"""
        if not text:
            return []
        
        # Split by sentence
        sentences = re.split(r'[.!?]+', text)
        
        # Find questions
        questions = [s.strip() for s in sentences if '?' in s]
        
        return questions[:5]  # Return up to 5 questions
    
    def generate_summary(self, text, intent, category):
        """Generate a one-line summary"""
        summaries = {
            ('question', 'pricing'): 'Customer asking about pricing',
            ('question', 'features'): 'Customer asking about features',
            ('interested', 'demo_request'): 'Customer wants a demo',
            ('interested', 'general'): 'Customer expressed interest',
            ('not_interested', 'opt_out'): 'Customer wants to unsubscribe',
            ('support', 'support'): 'Customer needs technical support',
            ('complaint', 'general'): 'Customer has a complaint',
            ('feedback', 'general'): 'Customer provided feedback'
        }
        
        key = (intent, category)
        if key in summaries:
            return summaries[key]
        
        # Default summary
        if not text:
            return 'Empty reply'
        
        # Return first sentence
        first_sentence = text.split('.')[0][:100]
        return first_sentence if first_sentence else 'Reply received'
    
    def should_auto_respond(self, category, intent, organization_id):
        """Check if we should auto-respond"""
        from app.models.reply import ReplyRule
        
        # Get active rules for this organization
        rules = ReplyRule.query.filter_by(
            organization_id=organization_id,
            is_active=True
        ).order_by(ReplyRule.priority.desc()).all()
        
        for rule in rules:
            # Check if rule matches
            if rule.trigger_category and rule.trigger_category == category:
                if rule.action == 'auto_reply' and rule.template_id:
                    return True, rule.template_id
            
            if rule.trigger_sentiment and rule.trigger_sentiment == intent:
                if rule.action == 'auto_reply' and rule.template_id:
                    return True, rule.template_id
        
        # Default auto-respond categories
        auto_respond_categories = ['pricing', 'demo_request', 'features']
        if category in auto_respond_categories:
            return True, None  # Use default template
        
        return False, None

# Initialize service
reply_intelligence = ReplyIntelligence()

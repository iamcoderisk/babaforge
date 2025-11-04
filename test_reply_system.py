#!/usr/bin/env python3
"""
Test Script for Reply Intelligence System
"""
import sys
sys.path.insert(0, '/opt/sendbaba-smtp')

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app import create_app, db
from app.models.reply import EmailReply
from app.services.reply_intelligence import reply_intelligence
import time

app = create_app()

def test_ai_analysis():
    """Test AI sentiment and intent detection"""
    print("\n🧠 Testing AI Analysis...")
    print("=" * 60)
    
    test_cases = [
        {
            'text': "I'm very interested in your product! Can you tell me more about pricing?",
            'expected_sentiment': 'positive',
            'expected_intent': 'question',
            'expected_category': 'pricing'
        },
        {
            'text': "This is terrible. I want to unsubscribe immediately.",
            'expected_sentiment': 'negative',
            'expected_intent': 'not_interested',
            'expected_category': 'opt_out'
        },
        {
            'text': "Can I schedule a demo for next week?",
            'expected_sentiment': 'neutral',
            'expected_intent': 'interested',
            'expected_category': 'demo_request'
        },
        {
            'text': "Help! The system is not working and I need support urgently!",
            'expected_sentiment': 'negative',
            'expected_intent': 'support',
            'expected_category': 'support'
        },
        {
            'text': "Does your platform support integration with Shopify?",
            'expected_sentiment': 'neutral',
            'expected_intent': 'question',
            'expected_category': 'features'
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test['text'][:50]}...")
        
        result = reply_intelligence.analyze_reply(test['text'])
        
        # Check sentiment
        if result['sentiment'] == test['expected_sentiment']:
            print(f"  ✅ Sentiment: {result['sentiment']} (score: {result['sentiment_score']:.2f})")
            passed += 1
        else:
            print(f"  ❌ Sentiment: Expected {test['expected_sentiment']}, got {result['sentiment']}")
            failed += 1
        
        # Check intent
        if result['intent'] == test['expected_intent']:
            print(f"  ✅ Intent: {result['intent']}")
            passed += 1
        else:
            print(f"  ❌ Intent: Expected {test['expected_intent']}, got {result['intent']}")
            failed += 1
        
        # Check category
        if result['category'] == test['expected_category']:
            print(f"  ✅ Category: {result['category']}")
            passed += 1
        else:
            print(f"  ❌ Category: Expected {test['expected_category']}, got {result['category']}")
            failed += 1
        
        print(f"  📊 Urgency: {result['urgency']}")
        print(f"  📝 Summary: {result['summary']}")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0

def test_reply_catcher():
    """Test SMTP reply catcher"""
    print("\n📧 Testing Reply Catcher...")
    print("=" * 60)
    
    try:
        # Create test email
        msg = MIMEMultipart()
        msg['From'] = 'test@example.com'
        msg['To'] = 'reply-org1@mail.sendbaba.com'
        msg['Subject'] = 'Test Reply - Pricing Question'
        
        body = """Hi there,

I'm very interested in SendBaba! Can you tell me more about your pricing plans?

Also, do you offer a free trial?

Thanks,
John Doe"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send to reply catcher
        print("Sending test email to reply catcher...")
        
        server = smtplib.SMTP('localhost', 2525)
        server.send_message(msg)
        server.quit()
        
        print("✅ Email sent successfully!")
        
        # Wait a moment for processing
        print("Waiting for processing...")
        time.sleep(2)
        
        # Check database
        with app.app_context():
            recent_reply = EmailReply.query.order_by(
                EmailReply.created_at.desc()
            ).first()
            
            if recent_reply:
                print("\n✅ Reply captured in database!")
                print(f"  From: {recent_reply.from_email}")
                print(f"  Subject: {recent_reply.subject}")
                print(f"  Sentiment: {recent_reply.sentiment}")
                print(f"  Intent: {recent_reply.intent}")
                print(f"  Category: {recent_reply.category}")
                print(f"  Auto-responded: {recent_reply.auto_responded}")
                return True
            else:
                print("❌ No reply found in database")
                return False
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database():
    """Test database tables"""
    print("\n🗄️  Testing Database...")
    print("=" * 60)
    
    with app.app_context():
        from sqlalchemy import inspect
        
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        required_tables = ['email_replies', 'reply_templates', 'reply_rules']
        
        print("Checking required tables...")
        all_exist = True
        
        for table in required_tables:
            if table in tables:
                # Get row count
                result = db.engine.execute(f"SELECT COUNT(*) FROM {table}")
                count = result.fetchone()[0]
                print(f"  ✅ {table}: {count} rows")
            else:
                print(f"  ❌ {table}: NOT FOUND")
                all_exist = False
        
        return all_exist

def test_templates():
    """Test reply templates"""
    print("\n📝 Testing Reply Templates...")
    print("=" * 60)
    
    with app.app_context():
        from app.models.reply import ReplyTemplate
        
        templates = ReplyTemplate.query.all()
        
        if templates:
            print(f"Found {len(templates)} templates:")
            for template in templates:
                print(f"  ✅ {template.name} ({template.category})")
                if template.auto_send:
                    print(f"     Auto-send: ENABLED")
            return True
        else:
            print("❌ No templates found")
            return False

def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🚀 REPLY INTELLIGENCE SYSTEM TEST SUITE")
    print("=" * 60)
    
    results = []
    
    # Test 1: Database
    results.append(("Database Tables", test_database()))
    
    # Test 2: AI Analysis
    results.append(("AI Analysis", test_ai_analysis()))
    
    # Test 3: Templates
    results.append(("Reply Templates", test_templates()))
    
    # Test 4: Reply Catcher (optional - requires SMTP)
    try:
        results.append(("Reply Catcher", test_reply_catcher()))
    except Exception as e:
        print(f"\n⚠️  Reply Catcher test skipped: {e}")
        results.append(("Reply Catcher", None))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    for test_name, result in results:
        if result is True:
            print(f"✅ {test_name}: PASSED")
        elif result is False:
            print(f"❌ {test_name}: FAILED")
        else:
            print(f"⏭️  {test_name}: SKIPPED")
    
    passed = sum(1 for _, r in results if r is True)
    total = len([r for _, r in results if r is not None])
    
    print("=" * 60)
    print(f"Final Score: {passed}/{total} tests passed")
    print("=" * 60)
    
    return passed == total

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)

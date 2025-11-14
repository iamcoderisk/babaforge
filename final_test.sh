#!/bin/bash
echo "🧪 FINAL EMAIL DELIVERABILITY TEST"
echo "===================================="
echo ""

echo "1. Sending to Gmail (your inbox)..."
python3 << 'EOF'
import sys
sys.path.insert(0, '/opt/sendbaba-smtp')
import redis, json, uuid

r = redis.Redis(host='localhost', port=6379, db=0)

email = {
    'id': str(uuid.uuid4()),
    'from': 'hello@myakama.com',
    'to': 'ekeminyd@gmail.com',
    'subject': 'Final Test - Should Be In Inbox ✅',
    'html_body': '''
        <html>
        <body style="font-family: Arial; padding: 20px;">
            <h1 style="color: #4CAF50;">✅ This Should Be In Your Inbox!</h1>
            <p>If you see this in your inbox (not spam), our fixes are working!</p>
            <ul>
                <li>✅ SPF Configured</li>
                <li>✅ DKIM Signed</li>
                <li>✅ DMARC Policy Set</li>
                <li>✅ PTR Record Active</li>
                <li>✅ IP Warmup Started</li>
            </ul>
            <p><strong>Action:</strong> Click "Not Spam" if in spam folder</p>
        </body>
        </html>
    ''',
    'priority': 10
}

r.lpush('outgoing_10', json.dumps(email))
print("✅ Sent to ekeminyd@gmail.com")
EOF

sleep 3

echo ""
echo "2. Check worker processed it..."
pm2 logs sendbaba-worker --lines 5 --nostream | grep -E "(Sent|DKIM)"

echo ""
echo "===================================="
echo "📧 CHECK YOUR EMAIL NOW:"
echo "   1. Check ekeminyd@gmail.com inbox"
echo "   2. If in spam, click 'Not Spam'"
echo "   3. View email source > check for:"
echo "      - dkim=pass"
echo "      - spf=pass"
echo "      - dmarc=pass"
echo ""
echo "📊 To verify authentication:"
echo "   Gmail: Three dots > Show original"
echo "   Look at top for authentication results"
echo ""

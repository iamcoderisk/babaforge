#!/bin/bash
echo "🔍 Testing SMTP Server Directly"
echo "================================"
echo ""

# Test connection
echo "1. Testing SMTP connection to localhost:25..."
timeout 5 bash -c 'cat < /dev/null > /dev/tcp/localhost/25' 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   ✅ Port 25 is open and accepting connections"
else
    echo "   ❌ Port 25 is not accessible"
fi

echo ""
echo "2. Testing SMTP handshake..."
(
    sleep 1
    echo "EHLO myakama.com"
    sleep 1
    echo "MAIL FROM:<test@myakama.com>"
    sleep 1
    echo "RCPT TO:<ekeminyd@gmail.com>"
    sleep 1
    echo "DATA"
    sleep 1
    echo "From: test@myakama.com"
    echo "To: ekeminyd@gmail.com"
    echo "Subject: Direct SMTP Test"
    echo ""
    echo "This is a test message"
    echo "."
    sleep 1
    echo "QUIT"
) | telnet localhost 25 2>&1 | head -20

echo ""
echo "================================"

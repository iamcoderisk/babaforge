#!/bin/bash
echo "🔍 Checking Reverse DNS (PTR)"
echo "============================="
echo ""

ptr=$(dig -x 156.67.29.186 +short 2>/dev/null)

if [ -z "$ptr" ]; then
    echo "❌ NO REVERSE DNS CONFIGURED"
    echo ""
    echo "This is CRITICAL for email deliverability!"
    echo "Without PTR:"
    echo "  - Emails delayed 30-60 minutes"
    echo "  - Marked as spam automatically"
    echo "  - Rejected by many servers"
    echo ""
    echo "📧 EMAIL THIS TO CONTABO SUPPORT:"
    echo "=================================="
    cat << 'EMAIL'
Subject: Urgent - PTR Record Setup for 156.67.29.186

Dear Contabo Support,

I urgently need a PTR (reverse DNS) record for my VPS:

IP Address: 156.67.29.186
PTR Record: mail.myakama.com
Hostname:   mail.myakama.com

Without this, my email server is experiencing severe delivery 
issues (30-60 minute delays, spam classification).

Please configure this as soon as possible.

Thank you.
EMAIL
    echo "=================================="
    echo ""
    echo "Send to: support@contabo.com"
else
    echo "✅ Reverse DNS found: $ptr"
    
    # Check if it matches domain
    if [[ $ptr == *"myakama.com"* ]] || [[ $ptr == *"sendbaba.com"* ]]; then
        echo "✅ PTR matches sending domain"
    else
        echo "⚠️  PTR doesn't match sending domain"
        echo "   Current: $ptr"
        echo "   Should be: mail.myakama.com or mail.sendbaba.com"
    fi
fi

echo ""
echo "============================="

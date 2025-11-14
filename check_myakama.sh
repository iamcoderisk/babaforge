#!/bin/bash
echo "🔍 Checking myakama.com Email Authentication"
echo "============================================="
echo ""

domain="myakama.com"

echo "1. SPF Record:"
spf=$(dig TXT $domain +short 2>/dev/null | grep "v=spf1")
if [ -z "$spf" ]; then
    echo "   ❌ NOT FOUND"
else
    echo "   ✅ $spf"
    # Check if includes server IP
    if echo "$spf" | grep -q "156.67.29.186"; then
        echo "   ✅ Server IP included"
    else
        echo "   ⚠️  Server IP 156.67.29.186 NOT in SPF"
    fi
fi

echo ""
echo "2. DKIM Record:"
dkim=$(dig TXT default._domainkey.$domain +short 2>/dev/null)
if [ -z "$dkim" ]; then
    echo "   ❌ NOT FOUND"
else
    echo "   ✅ Found (${#dkim} characters)"
    if echo "$dkim" | grep -q "v=DKIM1"; then
        echo "   ✅ Valid DKIM format"
    fi
fi

echo ""
echo "3. DMARC Record:"
dmarc=$(dig TXT _dmarc.$domain +short 2>/dev/null)
if [ -z "$dmarc" ]; then
    echo "   ❌ NOT FOUND"
else
    echo "   ✅ $dmarc"
fi

echo ""
echo "4. Reverse DNS (PTR):"
ptr=$(dig -x 156.67.29.186 +short 2>/dev/null)
if [ -z "$ptr" ]; then
    echo "   ❌ NOT FOUND - Critical for deliverability!"
else
    echo "   ✅ $ptr"
fi

echo ""
echo "5. MX Record:"
mx=$(dig MX $domain +short 2>/dev/null)
if [ -z "$mx" ]; then
    echo "   ⚠️  No MX record (optional for sending)"
else
    echo "   ✅ $mx"
fi

echo ""
echo "============================================="

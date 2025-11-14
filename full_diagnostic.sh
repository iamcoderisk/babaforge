#!/bin/bash
echo "🔍 COMPLETE EMAIL DELIVERABILITY DIAGNOSTIC"
echo "============================================="
echo ""

echo "1️⃣  DNS AUTHENTICATION (myakama.com)"
echo "-------------------------------------"
./check_myakama.sh
echo ""

echo "2️⃣  DKIM SIGNING TEST"
echo "-------------------------------------"
python3 << 'EOF'
import sys
sys.path.insert(0, '/opt/sendbaba-smtp')
exec(open('test_dkim.py').read()) if __import__('os').path.exists('test_dkim.py') else print("Run Step 2 first")
EOF
echo ""

echo "3️⃣  WORKER INTEGRATION"
echo "-------------------------------------"
python3 fix_worker_dkim.py
echo ""

echo "4️⃣  REVERSE DNS (PTR)"
echo "-------------------------------------"
./check_ptr.sh
echo ""

echo "5️⃣  SMTP SERVER STATUS"
echo "-------------------------------------"
pm2 status | grep sendbaba
echo ""

echo "============================================="
echo "📊 SUMMARY & RECOMMENDATIONS"
echo "============================================="
echo ""

# Analyze results
echo "Based on diagnostics above:"
echo ""
echo "If SPF/DKIM/DMARC show ✅:"
echo "  → DNS is configured correctly"
echo ""
echo "If DKIM test shows ❌:"
echo "  → Worker not signing emails (fix worker.py)"
echo ""
echo "If PTR shows ❌:"
echo "  → Email Contabo immediately (30-60 min delays)"
echo ""
echo "If all show ✅ but still spam:"
echo "  → IP reputation issue (need warmup)"
echo ""


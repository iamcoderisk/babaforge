#!/bin/bash
echo "🔍 Deliverability Check"
echo "======================="
echo ""

echo "1. DNS Records (sendbaba.com):"
python3 << 'EOF'
import sys
sys.path.insert(0, '/opt/sendbaba-smtp')
from app.services.deliverability.dns_verifier import DNSVerifier

verifier = DNSVerifier()
result = verifier.verify_domain('sendbaba.com')

print(f"   Score: {result['score']}/100")
print(f"   SPF: {'✅' if result['spf']['valid'] else '❌'}")
print(f"   DKIM: {'✅' if result['dkim']['valid'] else '❌'}")
print(f"   DMARC: {'✅' if result['dmarc']['valid'] else '❌'}")
print(f"   Verified: {'✅ YES' if result['verified'] else '⏳ Pending'}")
EOF

echo ""
echo "2. Domains in System:"
python3 << 'EOF'
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cursor = conn.cursor()

cursor.execute("""
    SELECT domain_name, dns_verified, dkim_verified
    FROM domains
    ORDER BY created_at DESC
    LIMIT 5
""")

for domain, dns_verified, dkim_verified in cursor.fetchall():
    dns_icon = "✅" if dns_verified else "⏳"
    dkim_icon = "🔐" if dkim_verified else "⏳"
    print(f"   {domain:20} DNS:{dns_icon} DKIM:{dkim_icon}")

cursor.close()
conn.close()
EOF

echo ""
echo "3. Recent Email Speed:"
pm2 logs sendbaba-worker --lines 50 --nostream 2>&1 | grep "Sent.*ms" | tail -5

echo ""
echo "======================="

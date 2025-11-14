#!/bin/bash
echo "========================================="
echo "📊 SENDBABA EMAIL SYSTEM STATUS"
echo "========================================="
echo ""

# Worker Status
echo "1️⃣ Worker Status:"
pm2 list | grep sendbaba-worker
echo ""

# Queue Status
echo "2️⃣ Queue Status:"
echo "   Priority 10: $(redis-cli LLEN outgoing_10) emails"
echo "   Priority 5: $(redis-cli LLEN outgoing_5) emails"
echo "   Priority 1: $(redis-cli LLEN outgoing_1) emails"
echo ""

# Recent Activity
echo "3️⃣ Recent Worker Activity:"
pm2 logs sendbaba-worker --lines 15 --nostream 2>&1 | grep -E "(Sending|sent|failed|Stats)" | tail -10
echo ""

# Database Stats
echo "4️⃣ Email Stats (Last 24h):"
python3 -c "
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
cursor = conn.cursor()

cursor.execute(\"\"\"
    SELECT status, COUNT(*) 
    FROM emails 
    WHERE created_at > NOW() - INTERVAL '24 hours' 
    GROUP BY status
\"\"\")

for status, count in cursor.fetchall():
    print(f'   {status}: {count}')

cursor.close()
conn.close()
" 2>/dev/null || echo "   Database query failed"

echo ""
echo "========================================="

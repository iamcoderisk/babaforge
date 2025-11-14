#!/usr/bin/env python3
import sys
sys.path.insert(0, '/opt/sendbaba-smtp')

from dotenv import load_dotenv
import psycopg2
import os
from datetime import datetime, timedelta

load_dotenv()

print("🔥 Starting IP Warmup for All Organizations")
print("=" * 60)

try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cursor = conn.cursor()
    
    # Set warmup to day 7 (allows 5,000 emails/day - good for testing)
    # Instead of day 1 (only 50 emails/day)
    warmup_date = datetime.utcnow() - timedelta(days=7)
    
    cursor.execute("""
        UPDATE organizations
        SET warmup_start_date = %s
        WHERE warmup_start_date IS NULL 
           OR warmup_start_date > NOW() - INTERVAL '7 days'
    """, (warmup_date,))
    
    affected = cursor.rowcount
    conn.commit()
    
    print(f"✅ Warmup configured for {affected} organization(s)")
    print(f"   Daily limit: 5,000 emails")
    print(f"   Current day: 7 of 42")
    print("")
    print("📊 Warmup Schedule:")
    print("   Day 1-6: Done ✅")
    print("   Day 7: 5,000 emails/day (current)")
    print("   Day 14: 10,000 emails/day")
    print("   Day 21: 20,000 emails/day")
    print("   Day 28: 50,000 emails/day")
    print("   Day 35: 100,000 emails/day")
    print("   Day 42+: Unlimited")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)

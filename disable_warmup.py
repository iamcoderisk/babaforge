#!/usr/bin/env python3
"""
Temporarily disable IP warmup for testing
"""
import sys
sys.path.insert(0, '/opt/sendbaba-smtp')

from dotenv import load_dotenv
import psycopg2
import os
from datetime import datetime, timedelta

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Set warmup_start_date to 42+ days ago (warmup complete)
    cursor.execute("""
        UPDATE organizations
        SET warmup_start_date = %s
        WHERE warmup_start_date IS NULL OR warmup_start_date > %s
    """, (datetime.utcnow() - timedelta(days=50), datetime.utcnow() - timedelta(days=42)))
    
    affected = cursor.rowcount
    conn.commit()
    cursor.close()
    conn.close()
    
    print(f"✅ IP warmup completed for {affected} organization(s)")
    print("📧 Emails will now send without throttling")
    
except Exception as e:
    print(f"❌ Error: {e}")


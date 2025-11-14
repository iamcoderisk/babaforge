#!/usr/bin/env python3
"""
Automated domain verification
Runs periodically to check DNS records
"""
import sys
sys.path.insert(0, '/opt/sendbaba-smtp')

from app.services.deliverability.dns_verifier import DNSVerifier
from dotenv import load_dotenv
import psycopg2
import os

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

try:
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Get unverified domains
    cursor.execute("""
        SELECT id, domain_name, dkim_selector
        FROM domains
        WHERE dns_verified = FALSE
        ORDER BY created_at DESC
        LIMIT 20
    """)
    
    verifier = DNSVerifier()
    
    for domain_id, domain_name, dkim_selector in cursor.fetchall():
        print(f"🔍 Checking {domain_name}...")
        
        result = verifier.verify_domain(domain_name)
        
        if result['verified'] and result['score'] >= 70:
            # Update database
            cursor.execute("""
                UPDATE domains
                SET dns_verified = TRUE,
                    dkim_verified = %s
                WHERE id = %s
            """, (result['dkim']['valid'], domain_id))
            
            print(f"✅ {domain_name} verified (score: {result['score']})")
        else:
            print(f"⏳ {domain_name} not ready (score: {result['score']})")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    print("\n✅ Verification complete")
    
except Exception as e:
    print(f"❌ Error: {e}")


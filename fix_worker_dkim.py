#!/usr/bin/env python3
"""
Verify worker DKIM integration
"""
import sys
sys.path.insert(0, '/opt/sendbaba-smtp')

print("🔍 Checking Worker DKIM Integration")
print("=" * 60)

# Check if worker.py has DKIM code
with open('worker.py', 'r') as f:
    worker_code = f.read()

checks = [
    ('Import DKIMService', 'from app.services.dkim.dkim_service import DKIMService' in worker_code),
    ('Get DKIM key from DB', 'dkim_private_key' in worker_code),
    ('Call sign_email', 'sign_email' in worker_code),
    ('DKIM-Signature check', 'DKIM' in worker_code)
]

print("\n✅ Worker DKIM Integration Checks:")
print("-" * 60)

all_pass = True
for check_name, result in checks:
    status = "✅" if result else "❌"
    print(f"{status} {check_name}")
    if not result:
        all_pass = False

if all_pass:
    print("\n✅ Worker has DKIM integration")
else:
    print("\n⚠️  Worker is missing DKIM integration!")
    print("\nThe worker needs to:")
    print("1. Import DKIMService from app.services.dkim.dkim_service")
    print("2. Get DKIM private key from domains table")
    print("3. Call dkim_service.sign_email(message_bytes, private_key)")
    print("4. Send the signed message")

print("\n" + "=" * 60)

# Check what's in database
from dotenv import load_dotenv
import psycopg2
import os

load_dotenv()

try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT domain_name, 
               CASE WHEN dkim_private_key IS NOT NULL THEN 'Yes' ELSE 'No' END as has_key,
               dkim_selector
        FROM domains
        WHERE domain_name = 'myakama.com'
    """)
    
    result = cursor.fetchone()
    
    print("\n📊 Database Check (myakama.com):")
    print("-" * 60)
    if result:
        domain, has_key, selector = result
        print(f"Domain: {domain}")
        print(f"Has DKIM Key: {has_key}")
        print(f"Selector: {selector or 'default'}")
        
        if has_key == 'No':
            print("\n❌ DKIM key missing from database!")
            print("   Generate with: python3 generate_dkim_for_domains.py")
    else:
        print("❌ myakama.com not found in domains table")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\n❌ Database error: {e}")

print("\n" + "=" * 60)


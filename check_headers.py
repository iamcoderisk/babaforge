#!/usr/bin/env python3
import sys
sys.path.insert(0, '/opt/sendbaba-smtp')

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, formatdate, make_msgid

print("📋 Checking Required Email Headers")
print("=" * 60)

# Simulate what worker creates
msg = MIMEText("Test body", 'html', 'utf-8')

msg['From'] = formataddr(("Sender Name", "test@myakama.com"))
msg['To'] = 'recipient@example.com'
msg['Subject'] = 'Test Subject'
msg['Date'] = formatdate(localtime=True)
msg['Message-ID'] = make_msgid(domain='myakama.com')
msg['Return-Path'] = 'test@myakama.com'
msg['Reply-To'] = 'test@myakama.com'
msg['X-Mailer'] = 'SendBaba'
msg['X-Priority'] = '3'
msg['Precedence'] = 'bulk'
msg['MIME-Version'] = '1.0'
msg['List-Unsubscribe'] = '<https://sendbaba.com/unsubscribe/123>'
msg['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'

print("\n✅ Headers being added by worker:")
print("-" * 60)
for header, value in msg.items():
    print(f"{header}: {value}")

print("\n" + "=" * 60)
print("\n⚠️  CRITICAL MISSING HEADERS (add if not present):")
print("   - Authentication-Results (added by receiver)")
print("   - Received (added by SMTP servers)")
print("   - DKIM-Signature (should be added by worker)")

message_bytes = msg.as_bytes()

if b'DKIM-Signature:' in message_bytes:
    print("\n✅ DKIM-Signature present")
else:
    print("\n❌ DKIM-Signature MISSING - This causes spam!")


#!/usr/bin/env python3
import sys

with open('worker.py', 'r') as f:
    worker_code = f.read()

# Check if tracking already exists
if 'tracking-pixel' in worker_code or 'open-tracking' in worker_code:
    print("✅ Tracking already configured")
    sys.exit(0)

print("Adding engagement tracking to improve IP reputation...")

# Find html_body processing section
search_str = "msg['List-Unsubscribe-Post'] = 'List-Unsubscribe=One-Click'"

if search_str not in worker_code:
    print("⚠️  Could not add tracking (non-critical)")
    sys.exit(0)

# Add tracking pixel to HTML emails
tracking_code = """
            
            # Add tracking pixel for engagement metrics (improves reputation)
            if html_body and email_id:
                tracking_pixel = f'<img src="https://sendbaba.com/t/o/{email_id}.gif" width="1" height="1" alt="" />'
                if '</body>' in html_body:
                    html_body = html_body.replace('</body>', f'{tracking_pixel}</body>')
                else:
                    html_body += tracking_pixel
"""

worker_code = worker_code.replace(
    "html_body = email_data.get('html_body', '')",
    "html_body = email_data.get('html_body', '')" + tracking_code
)

with open('worker.py', 'w') as f:
    f.write(worker_code)

print("✅ Engagement tracking added")


#!/bin/bash
echo "⚡ Testing Email Speed..."
echo ""

# Queue 5 test emails
python3 << 'EOF'
import redis
import json
import uuid
import time

r = redis.Redis(host='localhost', port=6379, db=0)

start = time.time()

for i in range(5):
    email = {
        'id': str(uuid.uuid4()),
        'from': 'hello@sendbaba.com',
        'to': 'ekeminyd@gmail.com',
        'subject': f'Speed Test {i+1}/5',
        'html_body': f'<h1>Speed Test Email {i+1}</h1><p>Testing delivery speed...</p>',
        'priority': 10
    }
    
    r.lpush('outgoing_10', json.dumps(email))
    print(f"✅ Queued email {i+1}/5")

print(f"\n📊 5 emails queued in {(time.time() - start)*1000:.0f}ms")
print(f"📬 Queue size: {r.llen('outgoing_10')}")
EOF

echo ""
echo "⏱️  Measuring send time..."
start_time=$(date +%s)

# Wait for queue to empty
while [ $(redis-cli LLEN outgoing_10) -gt 0 ]; do
    sleep 0.5
done

end_time=$(date +%s)
duration=$((end_time - start_time))

echo ""
echo "✅ All 5 emails sent in ${duration} seconds"
echo "⚡ Average: $((duration*1000/5))ms per email"

echo ""
echo "📝 Worker logs:"
pm2 logs sendbaba-worker --lines 10 --nostream | grep -E "(Sent|ms)"


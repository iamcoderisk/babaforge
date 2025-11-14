#!/bin/bash
echo "📊 SendBaba Monitor"
echo "===================="
echo ""
echo "Services:"
pm2 list | grep sendbaba
echo ""
echo "Queue:"
redis-cli llen outgoing_10 | xargs echo "  Queued:"
echo ""
echo "Worker Logs:"
pm2 logs sendbaba-worker --lines 5 --nostream | tail -5
echo ""
echo "Last 3 Emails:"
python3 << 'PY'
import sys
sys.path.insert(0, '/opt/sendbaba-smtp')
from app import create_app, db
from sqlalchemy import text
app = create_app()
with app.app_context():
    result = db.session.execute(text("SELECT sender, recipient, status FROM emails ORDER BY created_at DESC LIMIT 3"))
    for row in result:
        emoji = "✅" if row[2] == "sent" else "⏳" if row[2] == "queued" else "❌"
        print(f"  {emoji} {row[0]} → {row[1]} [{row[2]}]")
PY
echo "===================="

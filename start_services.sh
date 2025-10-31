#!/bin/bash

# Kill old processes
sudo pkill -9 -f "run.py"
sudo pkill -9 -f "email_worker"

# Start API in screen
screen -dmS sendbaba-api bash -c "cd /opt/sendbaba-smtp && source venv/bin/activate && export DATABASE_URL=postgresql://emailer:SecurePassword123@localhost:5432/emailer && export REDIS_HOST=localhost && python run.py"

# Wait for API to start
sleep 3

# Start 4 workers in screen
for i in {1..4}; do
    screen -dmS sendbaba-worker-${i} bash -c "cd /opt/sendbaba-smtp && source venv/bin/activate && export DATABASE_URL=postgresql://emailer:SecurePassword123@localhost:5432/emailer && export REDIS_HOST=localhost && export ENVIRONMENT=production && export PYTHONPATH=/opt/sendbaba-smtp && export WORKER_ID=${i} && python -m app.workers.email_worker"
    echo "Started worker ${i}"
    sleep 1
done

echo ""
echo "✅ Services started in screen sessions"
echo ""
echo "View sessions:"
echo "  screen -ls"
echo ""
echo "Attach to API:"
echo "  screen -r sendbaba-api"
echo ""
echo "Attach to worker:"
echo "  screen -r sendbaba-worker-1"
echo ""
echo "Detach: Ctrl+A then D"

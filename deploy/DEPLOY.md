# Deployment Guide

## 1. Upload to VPS
```bash
cd /Users/ekeminifx/Desktop/sendbaba-smtp
rsync -avz --exclude 'venv' --exclude '__pycache__' --exclude '*.log' \
  . root@156.67.29.186:/opt/sendbaba-smtp/
```

## 2. SSH and Setup
```bash
ssh root@156.67.29.186
cd /opt/sendbaba-smtp/deploy
sudo bash vps_setup.sh
```

## 3. Install Python Packages
```bash
cd /opt/sendbaba-smtp
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 4. Start Services
```bash
# API
nohup python run.py > logs/api.log 2>&1 &

# Workers
for i in {1..10}; do
  nohup python -m app.workers.email_worker $i > logs/worker-$i.log 2>&1 &
done

# Bounce receiver
sudo nohup python -m app.smtp.bounce_receiver > logs/bounces.log 2>&1 &
```

## 5. Test
```bash
curl -X POST http://156.67.29.186/api/v1/send \
  -H "Content-Type: application/json" \
  -d '{
    "to": "test@gmail.com",
    "from": "hello@sendbaba.com",
    "subject": "Test",
    "text_body": "Testing!"
  }'
```

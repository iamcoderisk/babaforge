#!/bin/bash
cd /opt/sendbaba-smtp
source venv/bin/activate
python -m app.workers.email_worker 1

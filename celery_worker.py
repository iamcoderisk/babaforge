#!/usr/bin/env python3
from app.tasks import celery
from app import create_app

app = create_app()
app.app_context().push()

if __name__ == '__main__':
    celery.start()

#!/usr/bin/env python
import sys
sys.path.insert(0, '/opt/sendbaba-smtp')

from app.workers.email_worker import main

if __name__ == '__main__':
    main()

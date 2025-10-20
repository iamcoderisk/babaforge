#!/usr/bin/env python3
"""
Enterprise Email System
Main application entry point
"""
import os
from app import create_app
from app.config.settings import Config

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║  Enterprise Email System - sendbaba.com                  ║
    ║  Capacity: 2B+ emails/day                                ║
    ║  Running on: http://localhost:{port}                    ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug,
        threaded=True
    )

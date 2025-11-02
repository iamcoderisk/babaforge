module.exports = {
  apps: [
    {
      name: 'sendbaba-flask',
      script: 'gunicorn',
      interpreter: '/opt/sendbaba-smtp/venv/bin/python',
      args: '--config gunicorn_config.py --bind 0.0.0.0:5000 run:app',
      cwd: '/opt/sendbaba-smtp',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        FLASK_ENV: 'production'
      }
    },
    {
      name: 'sendbaba-worker',
      script: 'app/workers/email_worker.py',
      interpreter: '/opt/sendbaba-smtp/venv/bin/python',
      args: '1',
      cwd: '/opt/sendbaba-smtp',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      restart_delay: 3000,
      exp_backoff_restart_delay: 100,
      env: {
        PYTHONPATH: '/opt/sendbaba-smtp'
      }
    }
  ]
};

module.exports = {
  apps: [
    {
      name: 'sendbaba-flask',
      script: './venv/bin/python',
      args: 'run.py',
      cwd: '/opt/sendbaba-smtp',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        FLASK_APP: 'run.py',
        FLASK_ENV: 'production',
        PYTHONUNBUFFERED: '1'
      },
      error_file: '/opt/sendbaba-smtp/logs/flask-error.log',
      out_file: '/opt/sendbaba-smtp/logs/flask-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss'
    },
    {
      name: 'sendbaba-worker',
      script: './venv/bin/python',
      args: 'worker.py',
      cwd: '/opt/sendbaba-smtp',
      instances: 2,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PYTHONUNBUFFERED: '1'
      }
    },
    {
      name: 'sendbaba-reply-catcher',
      script: './venv/bin/python',
      args: 'reply_catcher_worker.py',
      cwd: '/opt/sendbaba-smtp',
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PYTHONUNBUFFERED: '1'
      }
    }
  ]
};

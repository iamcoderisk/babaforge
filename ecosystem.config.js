module.exports = {
  apps: [
    {
      name: 'sendbaba-flask',
      script: 'venv/bin/python',
      args: 'run.py',
      cwd: '/opt/sendbaba-smtp',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      env: {
        FLASK_ENV: 'production',
        PORT: 5000
      }
    },
    {
      name: 'sendbaba-worker',
      script: 'venv/bin/python',
      args: '-m app.workers.email_worker 1',
      cwd: '/opt/sendbaba-smtp',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G'
    },
    {
      name: 'sendbaba-worker-2',
      script: 'venv/bin/python',
      args: '-m app.workers.email_worker 2',
      cwd: '/opt/sendbaba-smtp',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G'
    }
  ]
};

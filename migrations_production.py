"""
Production Database Migrations
Run this to add all new tables
"""
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("🔄 Running database migrations...")
    
    # Add warmup_start_date to organizations
    try:
        db.session.execute(text("""
            ALTER TABLE organizations 
            ADD COLUMN IF NOT EXISTS warmup_start_date TIMESTAMP
        """))
        print("✅ Added warmup_start_date to organizations")
    except Exception as e:
        print(f"⚠️  warmup_start_date: {e}")
    
    # Create suppression_list table
    try:
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS suppression_list (
                id VARCHAR(36) PRIMARY KEY,
                email VARCHAR(255) NOT NULL UNIQUE,
                type VARCHAR(20) NOT NULL,
                reason TEXT,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                bounce_count INTEGER DEFAULT 1,
                last_bounce_at TIMESTAMP
            )
        """))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_suppression_email ON suppression_list(email)"))
        print("✅ Created suppression_list table")
    except Exception as e:
        print(f"⚠️  suppression_list: {e}")
    
    # Create workflows table
    try:
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS workflows (
                id VARCHAR(36) PRIMARY KEY,
                organization_id VARCHAR(36) NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                trigger_type VARCHAR(50) NOT NULL,
                trigger_config TEXT,
                steps TEXT NOT NULL,
                status VARCHAR(20) DEFAULT 'draft',
                total_executions INTEGER DEFAULT 0,
                active_executions INTEGER DEFAULT 0,
                completed_executions INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (organization_id) REFERENCES organizations(id)
            )
        """))
        print("✅ Created workflows table")
    except Exception as e:
        print(f"⚠️  workflows: {e}")
    
    # Create workflow_executions table
    try:
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS workflow_executions (
                id VARCHAR(36) PRIMARY KEY,
                workflow_id VARCHAR(36) NOT NULL,
                contact_id VARCHAR(36) NOT NULL,
                status VARCHAR(20) DEFAULT 'running',
                current_step INTEGER DEFAULT 0,
                next_step_at TIMESTAMP,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                error_message TEXT,
                FOREIGN KEY (workflow_id) REFERENCES workflows(id),
                FOREIGN KEY (contact_id) REFERENCES contacts(id)
            )
        """))
        print("✅ Created workflow_executions table")
    except Exception as e:
        print(f"⚠️  workflow_executions: {e}")
    
    # Create email_opens table
    try:
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS email_opens (
                id VARCHAR(36) PRIMARY KEY,
                email_id VARCHAR(36) NOT NULL,
                user_agent VARCHAR(500),
                ip_address VARCHAR(45),
                location TEXT,
                opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (email_id) REFERENCES emails(id)
            )
        """))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_email_opens_email ON email_opens(email_id)"))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_email_opens_time ON email_opens(opened_at)"))
        print("✅ Created email_opens table")
    except Exception as e:
        print(f"⚠️  email_opens: {e}")
    
    # Create email_clicks table
    try:
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS email_clicks (
                id VARCHAR(36) PRIMARY KEY,
                email_id VARCHAR(36) NOT NULL,
                link_url TEXT NOT NULL,
                link_text VARCHAR(500),
                click_x INTEGER,
                click_y INTEGER,
                user_agent VARCHAR(500),
                ip_address VARCHAR(45),
                clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (email_id) REFERENCES emails(id)
            )
        """))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_email_clicks_email ON email_clicks(email_id)"))
        db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_email_clicks_time ON email_clicks(clicked_at)"))
        print("✅ Created email_clicks table")
    except Exception as e:
        print(f"⚠️  email_clicks: {e}")
    
    # Create campaign_analytics table
    try:
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS campaign_analytics (
                id VARCHAR(36) PRIMARY KEY,
                campaign_id VARCHAR(36) NOT NULL UNIQUE,
                total_sent INTEGER DEFAULT 0,
                total_delivered INTEGER DEFAULT 0,
                total_bounced INTEGER DEFAULT 0,
                total_opened INTEGER DEFAULT 0,
                total_clicked INTEGER DEFAULT 0,
                total_unsubscribed INTEGER DEFAULT 0,
                total_complained INTEGER DEFAULT 0,
                delivery_rate FLOAT DEFAULT 0.0,
                open_rate FLOAT DEFAULT 0.0,
                click_rate FLOAT DEFAULT 0.0,
                bounce_rate FLOAT DEFAULT 0.0,
                device_stats TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
            )
        """))
        print("✅ Created campaign_analytics table")
    except Exception as e:
        print(f"⚠️  campaign_analytics: {e}")
    
    # Add workflow_execution_id to emails
    try:
        db.session.execute(text("""
            ALTER TABLE emails 
            ADD COLUMN IF NOT EXISTS workflow_execution_id VARCHAR(36)
        """))
        print("✅ Added workflow_execution_id to emails")
    except Exception as e:
        print(f"⚠️  workflow_execution_id: {e}")
    
    # Add opened_at to emails
    try:
        db.session.execute(text("""
            ALTER TABLE emails 
            ADD COLUMN IF NOT EXISTS opened_at TIMESTAMP
        """))
        print("✅ Added opened_at to emails")
    except Exception as e:
        print(f"⚠️  opened_at: {e}")
    
    db.session.commit()
    print("\n✅ All migrations completed!")

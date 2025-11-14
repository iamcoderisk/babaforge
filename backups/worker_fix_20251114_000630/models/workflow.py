from app import db
from datetime import datetime

class Workflow(db.Model):
    __tablename__ = 'workflows'
    
    id = db.Column(db.Integer, primary_key=True)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'))
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    trigger_type = db.Column(db.String(50))  # signup, tag, date, webhook, etc.
    trigger_config = db.Column(db.JSON)
    workflow_data = db.Column(db.JSON)  # nodes and edges
    status = db.Column(db.String(20), default='draft')  # draft, active, paused
    subscribers_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    organization = db.relationship('Organization', backref='workflows')

class WorkflowSubscriber(db.Model):
    __tablename__ = 'workflow_subscribers'
    
    id = db.Column(db.Integer, primary_key=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey('workflows.id'))
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'))
    current_step = db.Column(db.String(100))
    step_data = db.Column(db.JSON)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')  # active, completed, exited
    
    workflow = db.relationship('Workflow', backref='subscribers')
    contact = db.relationship('Contact')

class WorkflowLog(db.Model):
    __tablename__ = 'workflow_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    workflow_subscriber_id = db.Column(db.Integer, db.ForeignKey('workflow_subscribers.id'))
    step_id = db.Column(db.String(100))
    action = db.Column(db.String(100))
    status = db.Column(db.String(20))
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    subscriber = db.relationship('WorkflowSubscriber', backref='logs')

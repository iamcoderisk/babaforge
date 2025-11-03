"""
Workflow and Automation Models
"""
from app import db
from datetime import datetime
import uuid


class Workflow(db.Model):
    __tablename__ = 'workflows'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = db.Column(db.String(36), db.ForeignKey('organizations.id'), nullable=False)
    
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    
    trigger_type = db.Column(db.String(50), nullable=False)
    trigger_config = db.Column(db.Text)  # JSON
    
    steps = db.Column(db.Text, nullable=False)  # JSON array
    
    status = db.Column(db.String(20), default='draft')  # draft, active, paused, archived
    
    # Stats
    total_executions = db.Column(db.Integer, default=0)
    active_executions = db.Column(db.Integer, default=0)
    completed_executions = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    executions = db.relationship('WorkflowExecution', backref='workflow', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'trigger_type': self.trigger_type,
            'status': self.status,
            'total_executions': self.total_executions,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class WorkflowExecution(db.Model):
    __tablename__ = 'workflow_executions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = db.Column(db.String(36), db.ForeignKey('workflows.id'), nullable=False)
    contact_id = db.Column(db.String(36), db.ForeignKey('contacts.id'), nullable=False)
    
    status = db.Column(db.String(20), default='running')  # running, completed, failed, cancelled
    current_step = db.Column(db.Integer, default=0)
    next_step_at = db.Column(db.DateTime)
    
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    error_message = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'workflow_id': self.workflow_id,
            'contact_id': self.contact_id,
            'status': self.status,
            'current_step': self.current_step,
            'started_at': self.started_at.isoformat() if self.started_at else None
        }

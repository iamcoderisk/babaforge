"""
Email Automation Workflow Engine
Handles triggers, conditions, and automated email sequences
"""
from datetime import datetime, timedelta
from typing import Dict, List
import json
import logging

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """Execute email automation workflows"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def create_workflow(self, organization_id: str, workflow_data: Dict) -> Dict:
        """
        Create new workflow
        workflow_data: {
            'name': str,
            'trigger': {'type': 'contact_added'|'tag_added'|'email_opened'|'link_clicked'|'date_based', ...},
            'steps': [
                {'type': 'wait', 'duration': 3600},  # seconds
                {'type': 'email', 'template_id': '...', 'subject': '...'},
                {'type': 'condition', 'field': 'opened', 'operator': 'equals', 'value': True},
                {'type': 'tag', 'action': 'add', 'tag': 'engaged'}
            ]
        }
        """
        from app.models.workflow import Workflow
        
        workflow = Workflow(
            organization_id=organization_id,
            name=workflow_data['name'],
            trigger_type=workflow_data['trigger']['type'],
            trigger_config=json.dumps(workflow_data['trigger']),
            steps=json.dumps(workflow_data['steps']),
            status='active'
        )
        
        self.db.add(workflow)
        self.db.commit()
        
        logger.info(f"Created workflow: {workflow.name}")
        
        return workflow.to_dict()
    
    def trigger_workflow(self, workflow_id: str, contact_id: str, trigger_data: Dict = None):
        """Start workflow for a contact"""
        from app.models.workflow import Workflow, WorkflowExecution
        
        workflow = Workflow.query.get(workflow_id)
        if not workflow or workflow.status != 'active':
            return
        
        # Create execution
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            contact_id=contact_id,
            status='running',
            current_step=0,
            started_at=datetime.utcnow()
        )
        
        self.db.add(execution)
        self.db.commit()
        
        logger.info(f"Triggered workflow {workflow.name} for contact {contact_id}")
        
        # Process first step
        self.process_next_step(execution.id)
    
    def process_next_step(self, execution_id: str):
        """Process next step in workflow"""
        from app.models.workflow import WorkflowExecution
        
        execution = WorkflowExecution.query.get(execution_id)
        if not execution or execution.status != 'running':
            return
        
        workflow = execution.workflow
        steps = json.loads(workflow.steps)
        
        if execution.current_step >= len(steps):
            # Workflow complete
            execution.status = 'completed'
            execution.completed_at = datetime.utcnow()
            self.db.commit()
            return
        
        step = steps[execution.current_step]
        
        # Execute step based on type
        if step['type'] == 'email':
            self._execute_email_step(execution, step)
        elif step['type'] == 'wait':
            self._execute_wait_step(execution, step)
        elif step['type'] == 'condition':
            self._execute_condition_step(execution, step)
        elif step['type'] == 'tag':
            self._execute_tag_step(execution, step)
        
        # Move to next step
        execution.current_step += 1
        self.db.commit()
    
    def _execute_email_step(self, execution, step):
        """Send email as part of workflow"""
        from app.models.email import Email
        from app.models.contact import Contact
        
        contact = Contact.query.get(execution.contact_id)
        if not contact:
            return
        
        # Create email
        email = Email(
            organization_id=execution.workflow.organization_id,
            sender=step.get('from', 'noreply@sendbaba.com'),
            recipient=contact.email,
            subject=step['subject'],
            html_body=step.get('html_body', ''),
            status='queued',
            workflow_execution_id=execution.id
        )
        
        self.db.add(email)
        self.db.commit()
        
        logger.info(f"Queued workflow email to {contact.email}")
    
    def _execute_wait_step(self, execution, step):
        """Wait before next step"""
        duration = step.get('duration', 3600)  # seconds
        
        # Schedule next step
        execution.next_step_at = datetime.utcnow() + timedelta(seconds=duration)
        self.db.commit()
        
        logger.info(f"Workflow waiting {duration} seconds")
    
    def _execute_condition_step(self, execution, step):
        """Evaluate condition and branch"""
        # Check condition
        # This would check contact data, email status, etc.
        # For now, just continue
        pass
    
    def _execute_tag_step(self, execution, step):
        """Add/remove tag from contact"""
        from app.models.contact import Contact
        
        contact = Contact.query.get(execution.contact_id)
        if not contact:
            return
        
        if step['action'] == 'add':
            # Add tag logic
            pass
        elif step['action'] == 'remove':
            # Remove tag logic
            pass


class TriggerManager:
    """Manage workflow triggers"""
    
    TRIGGER_TYPES = {
        'contact_added': 'When a new contact is added',
        'tag_added': 'When a tag is added to contact',
        'email_opened': 'When contact opens an email',
        'link_clicked': 'When contact clicks a link',
        'form_submitted': 'When contact submits a form',
        'date_based': 'On a specific date/time',
        'abandoned_cart': 'When cart is abandoned',
        'purchase': 'When purchase is made'
    }
    
    def __init__(self, db_session):
        self.db = db_session
        self.workflow_engine = WorkflowEngine(db_session)
    
    def fire_trigger(self, trigger_type: str, contact_id: str, trigger_data: Dict = None):
        """Fire trigger and start matching workflows"""
        from app.models.workflow import Workflow
        
        # Find workflows with this trigger
        workflows = Workflow.query.filter_by(
            trigger_type=trigger_type,
            status='active'
        ).all()
        
        for workflow in workflows:
            self.workflow_engine.trigger_workflow(
                workflow.id,
                contact_id,
                trigger_data
            )

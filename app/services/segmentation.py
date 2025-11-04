"""
Advanced Segmentation Service
Create dynamic segments based on behavior and attributes
"""
from app import db
from app.models.contact import Contact
from app.models.segment import Segment
from datetime import datetime, timedelta

class SegmentationService:
    """Advanced contact segmentation"""
    
    def create_segment(self, organization_id, name, conditions, is_dynamic=True):
        """Create new segment"""
        segment = Segment(
            organization_id=organization_id,
            name=name,
            conditions=conditions,
            is_dynamic=is_dynamic
        )
        
        # Calculate initial count
        contacts = self.get_segment_contacts(segment)
        segment.contacts_count = len(contacts)
        
        db.session.add(segment)
        db.session.commit()
        
        return segment
    
    def get_segment_contacts(self, segment):
        """Get contacts matching segment conditions"""
        query = Contact.query.filter_by(
            organization_id=segment.organization_id,
            status='active'
        )
        
        # Apply conditions
        for condition in segment.conditions:
            field = condition.get('field')
            operator = condition.get('operator')
            value = condition.get('value')
            
            if field == 'email':
                if operator == 'contains':
                    query = query.filter(Contact.email.contains(value))
                elif operator == 'equals':
                    query = query.filter(Contact.email == value)
            
            elif field == 'tags':
                if operator == 'has':
                    query = query.filter(Contact.tags.contains([value]))
            
            elif field == 'created_date':
                if operator == 'after':
                    date = datetime.strptime(value, '%Y-%m-%d')
                    query = query.filter(Contact.created_at >= date)
                elif operator == 'before':
                    date = datetime.strptime(value, '%Y-%m-%d')
                    query = query.filter(Contact.created_at <= date)
            
            elif field == 'engagement':
                # Engagement-based segmentation
                if operator == 'high':
                    # Get contacts with high open rates
                    pass
                elif operator == 'low':
                    # Get contacts with low engagement
                    pass
        
        return query.all()
    
    def update_dynamic_segments(self, organization_id):
        """Update contact counts for dynamic segments"""
        segments = Segment.query.filter_by(
            organization_id=organization_id,
            is_dynamic=True
        ).all()
        
        for segment in segments:
            contacts = self.get_segment_contacts(segment)
            segment.contacts_count = len(contacts)
        
        db.session.commit()
    
    def get_segment_by_behavior(self, organization_id, behavior_type):
        """Create behavioral segments"""
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        if behavior_type == 'highly_engaged':
            # Contacts who opened 80%+ of emails
            return self.create_segment(
                organization_id,
                'Highly Engaged',
                [{
                    'field': 'engagement',
                    'operator': 'high',
                    'value': 80
                }]
            )
        
        elif behavior_type == 'inactive':
            # No activity in 30 days
            return self.create_segment(
                organization_id,
                'Inactive',
                [{
                    'field': 'last_activity',
                    'operator': 'before',
                    'value': thirty_days_ago.strftime('%Y-%m-%d')
                }]
            )
        
        elif behavior_type == 'new_subscribers':
            # Subscribed in last 7 days
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            return self.create_segment(
                organization_id,
                'New Subscribers',
                [{
                    'field': 'created_date',
                    'operator': 'after',
                    'value': seven_days_ago.strftime('%Y-%m-%d')
                }]
            )

# Initialize service
segmentation_service = SegmentationService()

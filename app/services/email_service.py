
def generate_reply_address(campaign_id, contact_id, organization_id):
    """Generate unique reply-to address for tracking"""
    if campaign_id and contact_id:
        return f"reply-campaign{campaign_id}-contact{contact_id}@mail.sendbaba.com"
    elif organization_id:
        return f"reply-org{organization_id}@mail.sendbaba.com"
    else:
        return "noreply@sendbaba.com"

def send_email(to_email, subject, body, from_email=None, from_name=None, organization_id=None):
    """
    Send email via SMTP
    Simple wrapper function for reply controller
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = from_email or 'noreply@sendbaba.com'
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        
        # Send via localhost SMTP
        with smtplib.SMTP('localhost', 2525) as server:
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

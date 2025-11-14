"""
Email Helper Utilities
Add tracking pixels and convert links to tracking links
"""
import re
import hashlib
from urllib.parse import quote


def add_tracking_pixel(html_body: str, email_id: str, base_url: str = 'https://sendbaba.com') -> str:
    """Add tracking pixel to email"""
    pixel = f'<img src="{base_url}/t/open/{email_id}.gif" width="1" height="1" border="0" style="display:none;" />'
    
    # Add before closing body tag
    if '</body>' in html_body:
        html_body = html_body.replace('</body>', f'{pixel}</body>')
    else:
        html_body += pixel
    
    return html_body


def add_click_tracking(html_body: str, email_id: str, base_url: str = 'https://sendbaba.com') -> str:
    """Convert all links to tracking links"""
    
    def replace_link(match):
        original_url = match.group(1)
        
        # Skip if already a tracking link
        if '/t/click/' in original_url:
            return match.group(0)
        
        # Generate link ID
        link_id = hashlib.md5(original_url.encode()).hexdigest()[:8]
        
        # Create tracking URL
        tracking_url = f"{base_url}/t/click/{email_id}/{link_id}?url={quote(original_url)}"
        
        return f'href="{tracking_url}"'
    
    # Replace all href attributes
    html_body = re.sub(r'href=["\']([^"\']+)["\']', replace_link, html_body)
    
    return html_body


def add_unsubscribe_link(html_body: str, email_id: str, base_url: str = 'https://sendbaba.com') -> str:
    """Add unsubscribe link to email"""
    unsubscribe_html = f'''
    <div style="text-align: center; padding: 20px; font-size: 12px; color: #666; border-top: 1px solid #ddd; margin-top: 30px;">
        <p>
            If you no longer wish to receive these emails, you can 
            <a href="{base_url}/t/unsubscribe/{email_id}" style="color: #666; text-decoration: underline;">unsubscribe here</a>.
        </p>
    </div>
    '''
    
    # Add before closing body tag
    if '</body>' in html_body:
        html_body = html_body.replace('</body>', f'{unsubscribe_html}</body>')
    else:
        html_body += unsubscribe_html
    
    return html_body


def prepare_email_for_sending(html_body: str, email_id: str, 
                              add_tracking: bool = True,
                              add_unsubscribe: bool = True) -> str:
    """Prepare email with all tracking and compliance features"""
    
    if add_tracking:
        html_body = add_tracking_pixel(html_body, email_id)
        html_body = add_click_tracking(html_body, email_id)
    
    if add_unsubscribe:
        html_body = add_unsubscribe_link(html_body, email_id)
    
    return html_body

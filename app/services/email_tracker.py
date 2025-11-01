import re
from urllib.parse import quote

def add_tracking_to_email(html_body, tracking_id, base_url='https://sendbaba.com'):
    """Add tracking pixel and link tracking to email HTML"""
    
    if not html_body or not tracking_id:
        return html_body
    
    # Add tracking pixel at the end of body
    tracking_pixel = f'<img src="{base_url}/t/open/{tracking_id}" width="1" height="1" style="display:none;" alt="" />'
    
    # Add before closing body tag or at the end
    if '</body>' in html_body:
        html_body = html_body.replace('</body>', f'{tracking_pixel}</body>')
    else:
        html_body += tracking_pixel
    
    # Track all links
    def replace_link(match):
        full_match = match.group(0)
        url = match.group(1)
        
        # Skip mailto, tel, and tracking links
        if url.startswith(('mailto:', 'tel:', '#', '/t/')):
            return full_match
        
        # Create tracking URL
        tracked_url = f"{base_url}/t/click/{tracking_id}?url={quote(url)}"
        
        return full_match.replace(f'href="{url}"', f'href="{tracked_url}"')
    
    # Replace all href links
    html_body = re.sub(r'href="([^"]+)"', replace_link, html_body)
    
    # Add unsubscribe link if not present
    unsubscribe_link = f'{base_url}/t/unsubscribe/{tracking_id}'
    if 'unsubscribe' not in html_body.lower():
        unsubscribe_html = f'''
        <div style="text-align: center; margin-top: 20px; padding: 20px; font-size: 12px; color: #666;">
            <p>Don't want to receive these emails? <a href="{unsubscribe_link}" style="color: #666; text-decoration: underline;">Unsubscribe</a></p>
        </div>
        '''
        
        if '</body>' in html_body:
            html_body = html_body.replace('</body>', f'{unsubscribe_html}</body>')
        else:
            html_body += unsubscribe_html
    
    return html_body

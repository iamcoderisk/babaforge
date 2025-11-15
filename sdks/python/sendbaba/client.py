"""SendBaba API Client"""
import requests
from typing import Dict, List, Optional
from .exceptions import (
    SendBabaError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    NotFoundError
)


class SendBaba:
    """SendBaba API Client"""
    
    def __init__(self, api_key: str, base_url: str = "https://sendbaba.com/api/v1"):
        """
        Initialize SendBaba client
        
        Args:
            api_key: Your SendBaba API key
            base_url: API base URL (default: https://sendbaba.com/api/v1)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'User-Agent': 'SendBaba-Python/1.0.0'
        })
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make HTTP request"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            if response.status_code == 401:
                raise AuthenticationError("Invalid API key")
            elif response.status_code == 429:
                raise RateLimitError("Rate limit exceeded")
            elif response.status_code == 404:
                raise NotFoundError("Resource not found")
            elif response.status_code == 400:
                error_data = response.json()
                raise ValidationError(error_data.get('message', 'Validation error'))
            elif response.status_code >= 400:
                raise SendBabaError(f"API error: {response.status_code}")
            
            return response.json()
            
        except requests.RequestException as e:
            raise SendBabaError(f"Request failed: {str(e)}")
    
    # ============================================
    # EMAILS
    # ============================================
    
    def send_email(
        self,
        to: str,
        subject: str,
        html: Optional[str] = None,
        text: Optional[str] = None,
        from_email: Optional[str] = None,
        reply_to: Optional[str] = None,
        priority: int = 5,
        tags: Optional[List[str]] = None
    ) -> Dict:
        """
        Send an email
        
        Args:
            to: Recipient email address
            subject: Email subject
            html: HTML body (optional if text provided)
            text: Plain text body (optional if html provided)
            from_email: Sender email (optional)
            reply_to: Reply-to email (optional)
            priority: Priority 1-10 (default: 5)
            tags: List of tags (optional)
        
        Returns:
            Dict with email details
        
        Example:
            >>> client.send_email(
            ...     to="user@example.com",
            ...     subject="Welcome!",
            ...     html="<h1>Hello!</h1>"
            ... )
        """
        data = {
            'to': to,
            'subject': subject,
            'priority': priority
        }
        
        if html:
            data['html'] = html
        if text:
            data['text'] = text
        if from_email:
            data['from'] = from_email
        if reply_to:
            data['reply_to'] = reply_to
        if tags:
            data['tags'] = tags
        
        return self._request('POST', '/emails/send', json=data)
    
    def get_email(self, email_id: str) -> Dict:
        """Get email by ID"""
        return self._request('GET', f'/emails/{email_id}')
    
    def list_emails(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict:
        """
        List emails
        
        Args:
            status: Filter by status (queued, sent, failed, bounced)
            limit: Results per page (max 100)
            offset: Pagination offset
        """
        params = {'limit': limit, 'offset': offset}
        if status:
            params['status'] = status
        
        return self._request('GET', '/emails', params=params)
    
    # ============================================
    # CONTACTS
    # ============================================
    
    def create_contact(
        self,
        email: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone: Optional[str] = None,
        company: Optional[str] = None,
        tags: Optional[List[str]] = None,
        custom_fields: Optional[Dict] = None
    ) -> Dict:
        """
        Create a new contact
        
        Args:
            email: Contact email (required)
            first_name: First name
            last_name: Last name
            phone: Phone number
            company: Company name
            tags: List of tags
            custom_fields: Custom fields dictionary
        
        Returns:
            Dict with contact details
        """
        data = {'email': email}
        
        if first_name:
            data['first_name'] = first_name
        if last_name:
            data['last_name'] = last_name
        if phone:
            data['phone'] = phone
        if company:
            data['company'] = company
        if tags:
            data['tags'] = tags
        if custom_fields:
            data['custom_fields'] = custom_fields
        
        return self._request('POST', '/contacts', json=data)
    
    def get_contact(self, contact_id: str) -> Dict:
        """Get contact by ID"""
        return self._request('GET', f'/contacts/{contact_id}')
    
    def update_contact(self, contact_id: str, **kwargs) -> Dict:
        """Update contact"""
        return self._request('PUT', f'/contacts/{contact_id}', json=kwargs)
    
    def delete_contact(self, contact_id: str) -> Dict:
        """Delete contact"""
        return self._request('DELETE', f'/contacts/{contact_id}')
    
    def list_contacts(
        self,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict:
        """List contacts"""
        params = {'limit': limit, 'offset': offset}
        if status:
            params['status'] = status
        
        return self._request('GET', '/contacts', params=params)
    
    # ============================================
    # CAMPAIGNS
    # ============================================
    
    def create_campaign(
        self,
        name: str,
        subject: Optional[str] = None,
        from_email: Optional[str] = None
    ) -> Dict:
        """Create a new campaign"""
        data = {'name': name}
        if subject:
            data['subject'] = subject
        if from_email:
            data['from_email'] = from_email
        
        return self._request('POST', '/campaigns', json=data)
    
    def get_campaign(self, campaign_id: str) -> Dict:
        """Get campaign by ID"""
        return self._request('GET', f'/campaigns/{campaign_id}')
    
    def list_campaigns(self, limit: int = 50, offset: int = 0) -> Dict:
        """List campaigns"""
        return self._request('GET', '/campaigns', params={'limit': limit, 'offset': offset})
    
    # ============================================
    # UTILITY
    # ============================================
    
    def ping(self) -> Dict:
        """Health check"""
        return self._request('GET', '/ping')
    
    def get_api_info(self) -> Dict:
        """Get current API key information"""
        return self._request('GET', '/me')

#!/usr/bin/env python3
"""
Manually create an API key for testing
"""
import sys
sys.path.insert(0, '/opt/sendbaba-staging')

from app import create_app, db
from app.models.api_key import APIKey
from app.models.user import User

app = create_app()

with app.app_context():
    # Get first user's organization
    user = User.query.first()
    
    if not user:
        print("❌ No users found. Please create a user first.")
        sys.exit(1)
    
    if not user.organization_id:
        print("❌ User has no organization. Please set up organization.")
        sys.exit(1)
    
    print(f"Creating API key for organization: {user.organization_id}")
    
    # Create API key
    api_key = APIKey(
        organization_id=user.organization_id,
        name="Test API Key",
        scopes=['emails.send', 'emails.read', 'contacts.write', 'contacts.read', 'campaigns.write', 'campaigns.read']
    )
    
    db.session.add(api_key)
    db.session.commit()
    
    print("\n" + "="*60)
    print("✅ API KEY CREATED SUCCESSFULLY!")
    print("="*60)
    print(f"\nAPI Key: {api_key._plain_key}")
    print(f"Key Prefix: {api_key.key_prefix}")
    print(f"Organization ID: {api_key.organization_id}")
    print(f"Scopes: {', '.join(api_key.scopes)}")
    print("\n⚠️  SAVE THIS KEY NOW! You won't be able to see it again.")
    print("\nTest with:")
    print(f'curl -X POST https://playmaster.sendbaba.com/api/v1/emails/send \\')
    print(f'  -H "Authorization: Bearer {api_key._plain_key}" \\')
    print(f'  -H "Content-Type: application/json" \\')
    print(f'  -d \'{{"to":"ekeminyd@gmail.com","subject":"Test","html":"<h1>Hello!</h1>"}}\'')
    print("\n" + "="*60)


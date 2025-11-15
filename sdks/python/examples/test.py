"""
SendBaba Python SDK - Test Examples
"""
from sendbaba import SendBaba

# Initialize client
client = SendBaba(
    api_key='sb_live_YOUR_API_KEY',
    base_url='https://playmaster.sendbaba.com/api/v1'
)

print("🧪 Testing SendBaba Python SDK\n")

# 1. Test ping
print("1. Testing ping...")
try:
    result = client.ping()
    print(f"   ✅ Ping successful: {result['message']}\n")
except Exception as e:
    print(f"   ❌ Ping failed: {e}\n")

# 2. Get API info
print("2. Getting API info...")
try:
    info = client.get_api_info()
    print(f"   ✅ Organization ID: {info['data']['organization_id']}")
    print(f"   ✅ Scopes: {', '.join(info['data']['scopes'])}\n")
except Exception as e:
    print(f"   ❌ Failed: {e}\n")

# 3. Send email
print("3. Sending test email...")
try:
    result = client.send_email(
        to='test@example.com',
        subject='Test Email from Python SDK',
        html='<h1>Hello from SendBaba!</h1><p>This is a test email.</p>'
    )
    print(f"   ✅ Email queued: {result['data']['id']}\n")
except Exception as e:
    print(f"   ❌ Failed: {e}\n")

# 4. Create contact
print("4. Creating test contact...")
try:
    result = client.create_contact(
        email='john.doe@example.com',
        first_name='John',
        last_name='Doe',
        company='Test Company',
        tags=['test', 'sdk']
    )
    contact_id = result['data']['id']
    print(f"   ✅ Contact created: {contact_id}\n")
    
    # List contacts
    print("5. Listing contacts...")
    contacts = client.list_contacts(limit=5)
    print(f"   ✅ Found {len(contacts['data'])} contacts\n")
    
except Exception as e:
    print(f"   ❌ Failed: {e}\n")

print("✅ All tests completed!")

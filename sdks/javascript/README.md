# SendBaba JavaScript SDK

Official JavaScript/Node.js client for the SendBaba API.

## Installation
```bash
npm install sendbaba
```

Or with Yarn:
```bash
yarn add sendbaba
```

## Quick Start
```javascript
const SendBaba = require('sendbaba');

// Initialize client
const client = new SendBaba('sb_live_your_api_key');

// Send an email
const response = await client.sendEmail({
    to: 'user@example.com',
    subject: 'Welcome to SendBaba!',
    html: '<h1>Hello!</h1><p>Welcome to our platform.</p>'
});

console.log(`Email queued: ${response.data.id}`);
```

## Usage Examples

### Send Email
```javascript
// Simple email
await client.sendEmail({
    to: 'user@example.com',
    subject: 'Hello',
    html: '<h1>Hello World!</h1>'
});

// With all options
await client.sendEmail({
    to: 'user@example.com',
    from: 'noreply@yourdomain.com',
    subject: 'Order Confirmation',
    html: '<h1>Your order is confirmed!</h1>',
    text: 'Your order is confirmed!',
    reply_to: 'support@yourdomain.com',
    priority: 8,
    tags: ['order', 'confirmation']
});
```

### Express.js Integration
```javascript
const express = require('express');
const SendBaba = require('sendbaba');

const app = express();
const client = new SendBaba(process.env.SENDBABA_API_KEY);

app.post('/send-welcome', async (req, res) => {
    try {
        const result = await client.sendEmail({
            to: req.body.email,
            subject: 'Welcome!',
            html: '<h1>Welcome to our platform!</h1>'
        });
        
        res.json({ success: true, emailId: result.data.id });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});
```

### Manage Contacts
```javascript
// Create contact
const contact = await client.createContact({
    email: 'john@example.com',
    first_name: 'John',
    last_name: 'Doe',
    company: 'Acme Inc',
    tags: ['customer', 'premium'],
    custom_fields: { plan: 'premium' }
});

// Get contact
const contact = await client.getContact(contactId);

// Update contact
await client.updateContact(contactId, {
    first_name: 'Jane',
    tags: ['vip']
});

// List contacts
const contacts = await client.listContacts({
    status: 'active',
    limit: 100
});
```

### Error Handling
```javascript
try {
    await client.sendEmail({
        to: 'user@example.com',
        subject: 'Test'
    });
} catch (error) {
    console.error('Error:', error.message);
}
```

## TypeScript Support
```typescript
import SendBaba from 'sendbaba';

const client = new SendBaba('your_api_key');

interface EmailParams {
    to: string;
    subject: string;
    html?: string;
    text?: string;
}

const params: EmailParams = {
    to: 'user@example.com',
    subject: 'Hello',
    html: '<h1>Hello!</h1>'
};

await client.sendEmail(params);
```

## Documentation

Full API documentation: https://sendbaba.com/api/docs

## Support

- Email: support@sendbaba.com
- Docs: https://sendbaba.com/docs
- GitHub: https://github.com/sendbaba/sendbaba-js

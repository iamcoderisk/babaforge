# SendBaba PHP SDK

Official PHP client for the SendBaba API.

## Installation
```bash
composer require sendbaba/sendbaba-php
```

Or download manually and include:
```php
require_once 'src/SendBaba.php';
```

## Quick Start
```php
<?php

require 'vendor/autoload.php';

use SendBaba\SendBaba;

// Initialize client
$client = new SendBaba('sb_live_your_api_key');

// Send an email
$response = $client->sendEmail([
    'to' => 'user@example.com',
    'subject' => 'Welcome to SendBaba!',
    'html' => '<h1>Hello!</h1><p>Welcome to our platform.</p>'
]);

echo "Email queued: " . $response['data']['id'];
```

## Usage Examples

### Send Email
```php
// Simple email
$client->sendEmail([
    'to' => 'user@example.com',
    'subject' => 'Hello',
    'html' => '<h1>Hello World!</h1>'
]);

// With all options
$client->sendEmail([
    'to' => 'user@example.com',
    'from' => 'noreply@yourdomain.com',
    'subject' => 'Order Confirmation',
    'html' => '<h1>Your order is confirmed!</h1>',
    'text' => 'Your order is confirmed!',
    'reply_to' => 'support@yourdomain.com',
    'priority' => 8,
    'tags' => ['order', 'confirmation']
]);
```

### Laravel Integration
```php
// In your Laravel controller
use SendBaba\SendBaba;

class EmailController extends Controller
{
    public function sendWelcome()
    {
        $client = new SendBaba(env('SENDBABA_API_KEY'));
        
        $client->sendEmail([
            'to' => auth()->user()->email,
            'subject' => 'Welcome!',
            'html' => view('emails.welcome')->render()
        ]);
        
        return response()->json(['success' => true]);
    }
}
```

### Manage Contacts
```php
// Create contact
$contact = $client->createContact([
    'email' => 'john@example.com',
    'first_name' => 'John',
    'last_name' => 'Doe',
    'company' => 'Acme Inc',
    'tags' => ['customer', 'premium'],
    'custom_fields' => ['plan' => 'premium']
]);

// Get contact
$contact = $client->getContact($contactId);

// Update contact
$client->updateContact($contactId, [
    'first_name' => 'Jane',
    'tags' => ['vip']
]);

// List contacts
$contacts = $client->listContacts([
    'status' => 'active',
    'limit' => 100
]);
```

### Error Handling
```php
try {
    $client->sendEmail([
        'to' => 'user@example.com',
        'subject' => 'Test'
    ]);
} catch (Exception $e) {
    echo "Error: " . $e->getMessage();
}
```

## Documentation

Full API documentation: https://sendbaba.com/api/docs

## Support

- Email: support@sendbaba.com
- Docs: https://sendbaba.com/docs

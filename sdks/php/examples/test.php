<?php
/**
 * SendBaba PHP SDK - Test Examples
 */

require_once __DIR__ . '/../src/SendBaba.php';

use SendBaba\SendBaba;

// Initialize client
$client = new SendBaba(
    'sb_live_YOUR_API_KEY',
    'https://playmaster.sendbaba.com/api/v1'
);

echo "🧪 Testing SendBaba PHP SDK\n\n";

// 1. Test ping
echo "1. Testing ping...\n";
try {
    $result = $client->ping();
    echo "   ✅ Ping successful: {$result['message']}\n\n";
} catch (Exception $e) {
    echo "   ❌ Ping failed: {$e->getMessage()}\n\n";
}

// 2. Get API info
echo "2. Getting API info...\n";
try {
    $info = $client->getApiInfo();
    echo "   ✅ Organization ID: {$info['data']['organization_id']}\n";
    echo "   ✅ Scopes: " . implode(', ', $info['data']['scopes']) . "\n\n";
} catch (Exception $e) {
    echo "   ❌ Failed: {$e->getMessage()}\n\n";
}

// 3. Send email
echo "3. Sending test email...\n";
try {
    $result = $client->sendEmail([
        'to' => 'test@example.com',
        'subject' => 'Test Email from PHP SDK',
        'html' => '<h1>Hello from SendBaba!</h1><p>This is a test email.</p>'
    ]);
    echo "   ✅ Email queued: {$result['data']['id']}\n\n";
} catch (Exception $e) {
    echo "   ❌ Failed: {$e->getMessage()}\n\n";
}

// 4. Create contact
echo "4. Creating test contact...\n";
try {
    $result = $client->createContact([
        'email' => 'jane.doe@example.com',
        'first_name' => 'Jane',
        'last_name' => 'Doe',
        'company' => 'Test Company',
        'tags' => ['test', 'sdk']
    ]);
    $contactId = $result['data']['id'];
    echo "   ✅ Contact created: {$contactId}\n\n";
    
    // List contacts
    echo "5. Listing contacts...\n";
    $contacts = $client->listContacts(['limit' => 5]);
    $count = count($contacts['data']);
    echo "   ✅ Found {$count} contacts\n\n";
    
} catch (Exception $e) {
    echo "   ❌ Failed: {$e->getMessage()}\n\n";
}

echo "✅ All tests completed!\n";

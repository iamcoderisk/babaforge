/**
 * SendBaba JavaScript SDK - Test Examples
 */

const SendBaba = require('../src/index');

// Initialize client
const client = new SendBaba(
    'sb_live_YOUR_API_KEY',
    'https://playmaster.sendbaba.com/api/v1'
);

async function runTests() {
    console.log('🧪 Testing SendBaba JavaScript SDK\n');

    // 1. Test ping
    console.log('1. Testing ping...');
    try {
        const result = await client.ping();
        console.log(`   ✅ Ping successful: ${result.message}\n`);
    } catch (error) {
        console.log(`   ❌ Ping failed: ${error.message}\n`);
    }

    // 2. Get API info
    console.log('2. Getting API info...');
    try {
        const info = await client.getApiInfo();
        console.log(`   ✅ Organization ID: ${info.data.organization_id}`);
        console.log(`   ✅ Scopes: ${info.data.scopes.join(', ')}\n`);
    } catch (error) {
        console.log(`   ❌ Failed: ${error.message}\n`);
    }

    // 3. Send email
    console.log('3. Sending test email...');
    try {
        const result = await client.sendEmail({
            to: 'test@example.com',
            subject: 'Test Email from JavaScript SDK',
            html: '<h1>Hello from SendBaba!</h1><p>This is a test email.</p>'
        });
        console.log(`   ✅ Email queued: ${result.data.id}\n`);
    } catch (error) {
        console.log(`   ❌ Failed: ${error.message}\n`);
    }

    // 4. Create contact
    console.log('4. Creating test contact...');
    try {
        const result = await client.createContact({
            email: 'bob.smith@example.com',
            first_name: 'Bob',
            last_name: 'Smith',
            company: 'Test Company',
            tags: ['test', 'sdk']
        });
        const contactId = result.data.id;
        console.log(`   ✅ Contact created: ${contactId}\n`);
        
        // List contacts
        console.log('5. Listing contacts...');
        const contacts = await client.listContacts({ limit: 5 });
        console.log(`   ✅ Found ${contacts.data.length} contacts\n`);
        
    } catch (error) {
        console.log(`   ❌ Failed: ${error.message}\n`);
    }

    console.log('✅ All tests completed!');
}

runTests().catch(console.error);

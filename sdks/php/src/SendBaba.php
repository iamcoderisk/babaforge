<?php

namespace SendBaba;

use Exception;

/**
 * SendBaba PHP SDK
 * Official PHP client for the SendBaba API
 */
class SendBaba
{
    private $apiKey;
    private $baseUrl;
    
    /**
     * Initialize SendBaba client
     *
     * @param string $apiKey Your SendBaba API key
     * @param string $baseUrl API base URL
     */
    public function __construct($apiKey, $baseUrl = 'https://sendbaba.com/api/v1')
    {
        $this->apiKey = $apiKey;
        $this->baseUrl = rtrim($baseUrl, '/');
    }
    
    /**
     * Make HTTP request
     */
    private function request($method, $endpoint, $data = null)
    {
        $url = $this->baseUrl . '/' . ltrim($endpoint, '/');
        
        $headers = [
            'Authorization: Bearer ' . $this->apiKey,
            'Content-Type: application/json',
            'User-Agent: SendBaba-PHP/1.0.0'
        ];
        
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
        curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
        
        if ($data !== null) {
            curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        }
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error = curl_error($ch);
        curl_close($ch);
        
        if ($error) {
            throw new Exception("Request failed: $error");
        }
        
        $responseData = json_decode($response, true);
        
        if ($httpCode === 401) {
            throw new Exception("Authentication failed: Invalid API key");
        } elseif ($httpCode === 429) {
            throw new Exception("Rate limit exceeded");
        } elseif ($httpCode === 404) {
            throw new Exception("Resource not found");
        } elseif ($httpCode === 400) {
            $message = $responseData['message'] ?? 'Validation error';
            throw new Exception($message);
        } elseif ($httpCode >= 400) {
            throw new Exception("API error: HTTP $httpCode");
        }
        
        return $responseData;
    }
    
    // ============================================
    // EMAILS
    // ============================================
    
    /**
     * Send an email
     *
     * @param array $params Email parameters
     * @return array Response data
     *
     * Example:
     * $client->sendEmail([
     *     'to' => 'user@example.com',
     *     'subject' => 'Welcome!',
     *     'html' => '<h1>Hello!</h1>'
     * ]);
     */
    public function sendEmail($params)
    {
        $required = ['to', 'subject'];
        foreach ($required as $field) {
            if (empty($params[$field])) {
                throw new Exception("Field '$field' is required");
            }
        }
        
        if (empty($params['html']) && empty($params['text'])) {
            throw new Exception("Either 'html' or 'text' body is required");
        }
        
        return $this->request('POST', '/emails/send', $params);
    }
    
    /**
     * Get email by ID
     */
    public function getEmail($emailId)
    {
        return $this->request('GET', "/emails/$emailId");
    }
    
    /**
     * List emails
     */
    public function listEmails($params = [])
    {
        $query = http_build_query($params);
        return $this->request('GET', "/emails?$query");
    }
    
    // ============================================
    // CONTACTS
    // ============================================
    
    /**
     * Create a new contact
     *
     * @param array $params Contact parameters
     * @return array Response data
     *
     * Example:
     * $client->createContact([
     *     'email' => 'john@example.com',
     *     'first_name' => 'John',
     *     'last_name' => 'Doe',
     *     'company' => 'Acme Inc',
     *     'tags' => ['customer', 'premium']
     * ]);
     */
    public function createContact($params)
    {
        if (empty($params['email'])) {
            throw new Exception("Email is required");
        }
        
        return $this->request('POST', '/contacts', $params);
    }
    
    /**
     * Get contact by ID
     */
    public function getContact($contactId)
    {
        return $this->request('GET', "/contacts/$contactId");
    }
    
    /**
     * Update contact
     */
    public function updateContact($contactId, $params)
    {
        return $this->request('PUT', "/contacts/$contactId", $params);
    }
    
    /**
     * Delete contact
     */
    public function deleteContact($contactId)
    {
        return $this->request('DELETE', "/contacts/$contactId");
    }
    
    /**
     * List contacts
     */
    public function listContacts($params = [])
    {
        $query = http_build_query($params);
        return $this->request('GET', "/contacts?$query");
    }
    
    // ============================================
    // CAMPAIGNS
    // ============================================
    
    /**
     * Create a campaign
     */
    public function createCampaign($params)
    {
        if (empty($params['name'])) {
            throw new Exception("Campaign name is required");
        }
        
        return $this->request('POST', '/campaigns', $params);
    }
    
    /**
     * Get campaign by ID
     */
    public function getCampaign($campaignId)
    {
        return $this->request('GET', "/campaigns/$campaignId");
    }
    
    /**
     * List campaigns
     */
    public function listCampaigns($params = [])
    {
        $query = http_build_query($params);
        return $this->request('GET', "/campaigns?$query");
    }
    
    // ============================================
    // UTILITY
    // ============================================
    
    /**
     * Health check
     */
    public function ping()
    {
        return $this->request('GET', '/ping');
    }
    
    /**
     * Get API key information
     */
    public function getApiInfo()
    {
        return $this->request('GET', '/me');
    }
}

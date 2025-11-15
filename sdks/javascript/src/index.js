/**
 * SendBaba JavaScript SDK
 * Official JavaScript/Node.js client for the SendBaba API
 */

const axios = require('axios');

class SendBaba {
    /**
     * Initialize SendBaba client
     * @param {string} apiKey - Your SendBaba API key
     * @param {string} baseUrl - API base URL
     */
    constructor(apiKey, baseUrl = 'https://sendbaba.com/api/v1') {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl.replace(/\/$/, '');
        
        this.client = axios.create({
            baseURL: this.baseUrl,
            headers: {
                'Authorization': `Bearer ${apiKey}`,
                'Content-Type': 'application/json',
                'User-Agent': 'SendBaba-JS/1.0.0'
            }
        });
        
        // Add response interceptor for error handling
        this.client.interceptors.response.use(
            response => response,
            error => {
                if (error.response) {
                    const status = error.response.status;
                    const data = error.response.data;
                    
                    if (status === 401) {
                        throw new Error('Authentication failed: Invalid API key');
                    } else if (status === 429) {
                        throw new Error('Rate limit exceeded');
                    } else if (status === 404) {
                        throw new Error('Resource not found');
                    } else if (status === 400) {
                        throw new Error(data.message || 'Validation error');
                    } else {
                        throw new Error(`API error: ${status}`);
                    }
                }
                throw error;
            }
        );
    }
    
    // ============================================
    // EMAILS
    // ============================================
    
    /**
     * Send an email
     * @param {Object} params - Email parameters
     * @returns {Promise<Object>} Response data
     * 
     * @example
     * await client.sendEmail({
     *     to: 'user@example.com',
     *     subject: 'Welcome!',
     *     html: '<h1>Hello!</h1>'
     * });
     */
    async sendEmail(params) {
        const required = ['to', 'subject'];
        for (const field of required) {
            if (!params[field]) {
                throw new Error(`Field '${field}' is required`);
            }
        }
        
        if (!params.html && !params.text) {
            throw new Error("Either 'html' or 'text' body is required");
        }
        
        const response = await this.client.post('/emails/send', params);
        return response.data;
    }
    
    /**
     * Get email by ID
     * @param {string} emailId - Email ID
     */
    async getEmail(emailId) {
        const response = await this.client.get(`/emails/${emailId}`);
        return response.data;
    }
    
    /**
     * List emails
     * @param {Object} params - Query parameters
     */
    async listEmails(params = {}) {
        const response = await this.client.get('/emails', { params });
        return response.data;
    }
    
    // ============================================
    // CONTACTS
    // ============================================
    
    /**
     * Create a new contact
     * @param {Object} params - Contact parameters
     * 
     * @example
     * await client.createContact({
     *     email: 'john@example.com',
     *     first_name: 'John',
     *     last_name: 'Doe',
     *     company: 'Acme Inc',
     *     tags: ['customer', 'premium']
     * });
     */
    async createContact(params) {
        if (!params.email) {
            throw new Error("Email is required");
        }
        
        const response = await this.client.post('/contacts', params);
        return response.data;
    }
    
    /**
     * Get contact by ID
     */
    async getContact(contactId) {
        const response = await this.client.get(`/contacts/${contactId}`);
        return response.data;
    }
    
    /**
     * Update contact
     */
    async updateContact(contactId, params) {
        const response = await this.client.put(`/contacts/${contactId}`, params);
        return response.data;
    }
    
    /**
     * Delete contact
     */
    async deleteContact(contactId) {
        const response = await this.client.delete(`/contacts/${contactId}`);
        return response.data;
    }
    
    /**
     * List contacts
     */
    async listContacts(params = {}) {
        const response = await this.client.get('/contacts', { params });
        return response.data;
    }
    
    // ============================================
    // CAMPAIGNS
    // ============================================
    
    /**
     * Create a campaign
     */
    async createCampaign(params) {
        if (!params.name) {
            throw new Error("Campaign name is required");
        }
        
        const response = await this.client.post('/campaigns', params);
        return response.data;
    }
    
    /**
     * Get campaign by ID
     */
    async getCampaign(campaignId) {
        const response = await this.client.get(`/campaigns/${campaignId}`);
        return response.data;
    }
    
    /**
     * List campaigns
     */
    async listCampaigns(params = {}) {
        const response = await this.client.get('/campaigns', { params });
        return response.data;
    }
    
    // ============================================
    // UTILITY
    // ============================================
    
    /**
     * Health check
     */
    async ping() {
        const response = await this.client.get('/ping');
        return response.data;
    }
    
    /**
     * Get API key information
     */
    async getApiInfo() {
        const response = await this.client.get('/me');
        return response.data;
    }
}

module.exports = SendBaba;

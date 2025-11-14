/**
 * SENDBABA EMAIL BUILDER
 * Professional Email Template System
 */

class EmailBuilder {
    constructor() {
        this.templates = [];
        this.selectedTemplate = null;
        this.currentHTML = '';
        this.variables = {};
        
        this.init();
    }
    
    async init() {
        await this.loadTemplates();
        this.setupEventListeners();
        this.renderTemplateGallery();
    }
    
    async loadTemplates() {
        try {
            const response = await fetch('/static/email-templates/templates.json');
            const data = await response.json();
            this.templates = data.templates;
        } catch (error) {
            console.error('Error loading templates:', error);
            this.showAlert('Failed to load templates', 'error');
        }
    }
    
    setupEventListeners() {
        // Template selection
        document.addEventListener('click', (e) => {
            if (e.target.closest('.template-card')) {
                const card = e.target.closest('.template-card');
                const templateId = card.dataset.templateId;
                this.selectTemplate(templateId);
            }
        });
        
        // Tab switching
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.addEventListener('click', () => this.switchTab(btn.dataset.tab));
        });
        
        // Variable tag insertion
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('variable-tag')) {
                this.insertVariable(e.target.dataset.variable);
            }
        });
        
        // Preview update on content change
        const subjectInput = document.getElementById('email-subject');
        const htmlEditor = document.getElementById('html-editor');
        
        if (subjectInput) {
            subjectInput.addEventListener('input', () => this.updatePreview());
        }
        
        if (htmlEditor) {
            htmlEditor.addEventListener('input', () => this.updatePreview());
        }
        
        // Send email button
        const sendBtn = document.getElementById('send-email-btn');
        if (sendBtn) {
            sendBtn.addEventListener('click', () => this.sendEmail());
        }
    }
    
    renderTemplateGallery() {
        const gallery = document.getElementById('template-gallery');
        if (!gallery) return;
        
        gallery.innerHTML = this.templates.map(template => `
            <div class="template-card" data-template-id="${template.id}">
                <div class="template-thumbnail">
                    ${this.getTemplateIcon(template.category)}
                </div>
                <div class="template-info">
                    <div class="template-name">${template.name}</div>
                    <div class="template-category">${template.category}</div>
                </div>
            </div>
        `).join('');
    }
    
    getTemplateIcon(category) {
        const icons = {
            'Marketing': '📧',
            'Transactional': '💳',
            'Basic': '📄'
        };
        return icons[category] || '✉️';
    }
    
    selectTemplate(templateId) {
        // Remove previous selection
        document.querySelectorAll('.template-card').forEach(card => {
            card.classList.remove('selected');
        });
        
        // Find and select template
        const template = this.templates.find(t => t.id === templateId);
        if (!template) return;
        
        this.selectedTemplate = template;
        this.currentHTML = template.html;
        
        // Update UI
        const card = document.querySelector(`[data-template-id="${templateId}"]`);
        if (card) card.classList.add('selected');
        
        // Update editor
        const htmlEditor = document.getElementById('html-editor');
        if (htmlEditor) {
            htmlEditor.value = this.formatHTML(template.html);
        }
        
        // Update preview
        this.updatePreview();
        
        // Close modal if open
        this.closeModal('template-modal');
        
        this.showAlert(`Template "${template.name}" loaded!`, 'success');
    }
    
    formatHTML(html) {
        // Basic HTML formatting for readability
        return html
            .replace(/></g, '>\n<')
            .replace(/\n\s*\n/g, '\n');
    }
    
    switchTab(tab) {
        // Update tab buttons
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tab}"]`).classList.add('active');
        
        // Show corresponding content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.add('hidden');
        });
        document.getElementById(`${tab}-tab`).classList.remove('hidden');
    }
    
    insertVariable(variable) {
        const htmlEditor = document.getElementById('html-editor');
        if (!htmlEditor) return;
        
        const cursorPos = htmlEditor.selectionStart;
        const textBefore = htmlEditor.value.substring(0, cursorPos);
        const textAfter = htmlEditor.value.substring(cursorPos);
        
        htmlEditor.value = textBefore + `{{${variable}}}` + textAfter;
        htmlEditor.focus();
        
        // Update preview
        this.updatePreview();
    }
    
    updatePreview() {
        const htmlEditor = document.getElementById('html-editor');
        const previewFrame = document.getElementById('preview-iframe');
        
        if (!htmlEditor || !previewFrame) return;
        
        let html = htmlEditor.value;
        
        // Replace variables with sample data for preview
        const sampleData = {
            name: 'John Doe',
            email: 'john@example.com',
            action_url: '#',
            unsubscribe_url: '#',
            transaction_id: 'TXN-123456',
            date: new Date().toLocaleDateString(),
            amount: '99.99',
            customer_name: 'John Doe',
            article_title: 'Sample Article Title',
            article_excerpt: 'This is a sample excerpt...',
            article_url: '#',
            preferences_url: '#',
            alert_title: 'Important Update',
            alert_message: 'This is a sample alert message',
            description: 'Additional details here...',
            event_name: 'Annual Conference 2025',
            event_date: 'March 15, 2025',
            event_time: '10:00 AM - 5:00 PM',
            event_location: 'Convention Center',
            rsvp_url: '#'
        };
        
        // Replace variables
        Object.keys(sampleData).forEach(key => {
            const regex = new RegExp(`{{${key}}}`, 'g');
            html = html.replace(regex, sampleData[key]);
        });
        
        // Update iframe
        const iframeDoc = previewFrame.contentDocument || previewFrame.contentWindow.document;
        iframeDoc.open();
        iframeDoc.write(html);
        iframeDoc.close();
    }
    
    async sendEmail() {
        const form = document.getElementById('send-email-form');
        if (!form) return;
        
        const formData = new FormData(form);
        const htmlEditor = document.getElementById('html-editor');
        
        // Add HTML content
        formData.set('html_body', htmlEditor.value);
        
        // Show loading
        const sendBtn = document.getElementById('send-email-btn');
        const originalText = sendBtn.innerHTML;
        sendBtn.innerHTML = '<span class="loading"></span> Sending...';
        sendBtn.disabled = true;
        
        try {
            const response = await fetch(form.action, {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showAlert('Email sent successfully!', 'success');
                form.reset();
            } else {
                this.showAlert(result.message || 'Failed to send email', 'error');
            }
        } catch (error) {
            console.error('Send error:', error);
            this.showAlert('Error sending email', 'error');
        } finally {
            sendBtn.innerHTML = originalText;
            sendBtn.disabled = false;
        }
    }
    
    showAlert(message, type = 'info') {
        const alertContainer = document.getElementById('alert-container');
        if (!alertContainer) {
            console.log(`${type.toUpperCase()}: ${message}`);
            return;
        }
        
        const alert = document.createElement('div');
        alert.className = `alert alert-${type}`;
        alert.textContent = message;
        
        alertContainer.appendChild(alert);
        
        setTimeout(() => {
            alert.remove();
        }, 5000);
    }
    
    openModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
        }
    }
    
    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.emailBuilder = new EmailBuilder();
});

// Global functions for template modal
function openTemplateModal() {
    window.emailBuilder.openModal('template-modal');
}

function closeTemplateModal() {
    window.emailBuilder.closeModal('template-modal');
}

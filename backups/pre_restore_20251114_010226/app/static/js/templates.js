// SendBaba Template System JavaScript
// High-quality, production-ready code

class TemplateManager {
    constructor() {
        this.selectedTemplate = null;
        this.previewModal = null;
        this.init();
    }
    
    init() {
        console.log('🎨 Template Manager initialized');
        this.setupEventListeners();
        this.previewModal = document.getElementById('previewModal');
    }
    
    setupEventListeners() {
        // Close modal on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.previewModal && !this.previewModal.classList.contains('hidden')) {
                this.closePreview();
            }
        });
        
        // Close modal on backdrop click
        if (this.previewModal) {
            this.previewModal.addEventListener('click', (e) => {
                if (e.target === this.previewModal) {
                    this.closePreview();
                }
            });
        }
    }
    
    filterTemplates(category) {
        const cards = document.querySelectorAll('.template-card');
        const buttons = document.querySelectorAll('.filter-btn');
        
        // Update button states
        buttons.forEach(btn => {
            btn.classList.remove('active', 'bg-purple-100', 'text-purple-700');
            btn.classList.add('bg-gray-100', 'text-gray-700');
        });
        
        event.target.classList.remove('bg-gray-100', 'text-gray-700');
        event.target.classList.add('active', 'bg-purple-100', 'text-purple-700');
        
        // Filter cards with animation
        cards.forEach((card, index) => {
            const cardCategory = card.dataset.category;
            const shouldShow = category === 'all' || cardCategory === category;
            
            if (shouldShow) {
                card.style.display = 'block';
                setTimeout(() => {
                    card.style.opacity = '1';
                    card.style.transform = 'scale(1)';
                }, index * 50);
            } else {
                card.style.opacity = '0';
                card.style.transform = 'scale(0.8)';
                setTimeout(() => {
                    card.style.display = 'none';
                }, 300);
            }
        });
        
        console.log(`🔍 Filtered templates: ${category}`);
    }
    
    async previewTemplate(templateName) {
        console.log(`👁️ Previewing template: ${templateName}`);
        
        if (!this.previewModal) {
            console.error('Preview modal not found');
            return;
        }
        
        this.selectedTemplate = templateName;
        
        // Show modal with animation
        this.previewModal.classList.remove('hidden');
        this.previewModal.classList.add('modal-enter');
        
        // Update title
        const title = document.getElementById('previewTitle');
        if (title) {
            title.textContent = this.formatTemplateName(templateName);
        }
        
        // Show loading state
        const content = document.getElementById('previewContent');
        if (content) {
            content.innerHTML = `
                <div class="flex items-center justify-center py-12">
                    <div class="loading-spinner"></div>
                    <span class="ml-3 text-gray-600">Loading preview...</span>
                </div>
            `;
        }
        
        try {
            // Fetch template HTML
            const response = await fetch(`/api/templates/preview/${templateName}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const html = await response.text();
            
            // Display in iframe
            if (content) {
                content.innerHTML = `
                    <iframe 
                        class="preview-frame" 
                        srcdoc="${this.escapeHtml(html)}"
                        sandbox="allow-same-origin"
                    ></iframe>
                `;
            }
            
            console.log('✅ Preview loaded successfully');
            
        } catch (error) {
            console.error('❌ Preview error:', error);
            
            if (content) {
                content.innerHTML = `
                    <div class="alert alert-error">
                        <strong>Error loading preview:</strong> ${error.message}
                    </div>
                `;
            }
        }
    }
    
    closePreview() {
        if (this.previewModal) {
            this.previewModal.classList.add('hidden');
            this.previewModal.classList.remove('modal-enter');
        }
        console.log('👋 Preview closed');
    }
    
    async useTemplate(templateName) {
        console.log(`✅ Using template: ${templateName}`);
        
        const confirmed = confirm(`Use "${this.formatTemplateName(templateName)}" template?\n\nThis will open the send email page with this template.`);
        
        if (!confirmed) {
            return;
        }
        
        try {
            // Fetch template HTML
            const response = await fetch(`/api/templates/preview/${templateName}`);
            
            if (!response.ok) {
                throw new Error('Failed to load template');
            }
            
            const html = await response.text();
            
            // Store in sessionStorage
            sessionStorage.setItem('selectedTemplate', html);
            sessionStorage.setItem('selectedTemplateName', templateName);
            
            // Redirect to send email page
            window.location.href = '/dashboard/send-email';
            
        } catch (error) {
            console.error('❌ Error using template:', error);
            alert('Error loading template. Please try again.');
        }
    }
    
    formatTemplateName(name) {
        return name
            .split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }
    
    escapeHtml(html) {
        return html
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
}

// Initialize template manager
let templateManager;

document.addEventListener('DOMContentLoaded', () => {
    templateManager = new TemplateManager();
    
    // Load template if coming from template gallery
    const savedTemplate = sessionStorage.getItem('selectedTemplate');
    const savedTemplateName = sessionStorage.getItem('selectedTemplateName');
    
    if (savedTemplate && window.location.pathname.includes('send-email')) {
        const htmlBody = document.getElementById('htmlBody');
        if (htmlBody) {
            htmlBody.value = savedTemplate;
            
            // Show success message
            showAlert('success', `Template "${templateManager.formatTemplateName(savedTemplateName)}" loaded successfully!`);
            
            // Clear from session storage
            sessionStorage.removeItem('selectedTemplate');
            sessionStorage.removeItem('selectedTemplateName');
        }
    }
});

// Global functions for inline event handlers
function filterTemplates(category) {
    if (templateManager) {
        templateManager.filterTemplates(category);
    }
}

function previewTemplate(templateName) {
    if (templateManager) {
        templateManager.previewTemplate(templateName);
    }
}

function closePreview() {
    if (templateManager) {
        templateManager.closePreview();
    }
}

function useTemplate(templateName) {
    if (templateManager) {
        templateManager.useTemplate(templateName);
    }
}

// Utility function to show alerts
function showAlert(type, message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    
    const container = document.querySelector('.max-w-4xl, .max-w-7xl');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            alertDiv.style.opacity = '0';
            setTimeout(() => alertDiv.remove(), 300);
        }, 5000);
    }
}

console.log('✨ SendBaba Template System loaded');

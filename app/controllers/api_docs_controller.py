from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user

api_docs_bp = Blueprint('api_docs', __name__, url_prefix='/docs')

@api_docs_bp.route('/')
def index():
    """API Documentation landing page"""
    return render_template('docs/api_index.html')

@api_docs_bp.route('/openapi.json')
def openapi_spec():
    """OpenAPI 3.0 specification"""
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "SendBaba API",
            "version": "1.0.0",
            "description": "Powerful Email Marketing API for developers",
            "contact": {
                "name": "SendBaba Support",
                "email": "support@sendbaba.com",
                "url": "https://sendbaba.com"
            }
        },
        "servers": [
            {
                "url": "https://sendbaba.com/api/v1",
                "description": "Production server"
            },
            {
                "url": "https://playmaster.sendbaba.com/api/v1",
                "description": "Staging server"
            }
        ],
        "security": [
            {
                "BearerAuth": []
            }
        ],
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "API Key",
                    "description": "Enter your API key in format: sb_live_xxxxxxxxxxxxx"
                }
            },
            "schemas": {
                "Email": {
                    "type": "object",
                    "required": ["to", "subject"],
                    "properties": {
                        "from": {
                            "type": "string",
                            "format": "email",
                            "example": "sender@yourdomain.com"
                        },
                        "to": {
                            "type": "string",
                            "format": "email",
                            "example": "recipient@example.com"
                        },
                        "subject": {
                            "type": "string",
                            "example": "Welcome to our service!"
                        },
                        "html": {
                            "type": "string",
                            "example": "<h1>Welcome!</h1><p>Thanks for signing up.</p>"
                        },
                        "text": {
                            "type": "string",
                            "example": "Welcome! Thanks for signing up."
                        },
                        "reply_to": {
                            "type": "string",
                            "format": "email"
                        },
                        "tags": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "priority": {
                            "type": "integer",
                            "minimum": 1,
                            "maximum": 10,
                            "default": 5
                        }
                    }
                },
                "Contact": {
                    "type": "object",
                    "required": ["email"],
                    "properties": {
                        "email": {
                            "type": "string",
                            "format": "email",
                            "example": "john@example.com"
                        },
                        "first_name": {
                            "type": "string",
                            "example": "John"
                        },
                        "last_name": {
                            "type": "string",
                            "example": "Doe"
                        },
                        "company": {
                            "type": "string",
                            "example": "Acme Inc"
                        },
                        "phone": {
                            "type": "string",
                            "example": "+234801234567"
                        },
                        "tags": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        },
                        "custom_fields": {
                            "type": "object"
                        }
                    }
                },
                "Error": {
                    "type": "object",
                    "properties": {
                        "error": {
                            "type": "string"
                        },
                        "message": {
                            "type": "string"
                        }
                    }
                }
            }
        },
        "paths": {
            "/ping": {
                "get": {
                    "summary": "Health check",
                    "description": "Check if API is running",
                    "security": [],
                    "responses": {
                        "200": {
                            "description": "API is healthy"
                        }
                    }
                }
            },
            "/emails/send": {
                "post": {
                    "summary": "Send email",
                    "description": "Send a single transactional email",
                    "tags": ["Emails"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/Email"
                                }
                            }
                        }
                    },
                    "responses": {
                        "202": {
                            "description": "Email queued successfully"
                        },
                        "400": {
                            "description": "Validation error"
                        },
                        "401": {
                            "description": "Unauthorized"
                        },
                        "429": {
                            "description": "Rate limit exceeded"
                        }
                    }
                }
            },
            "/emails/{email_id}": {
                "get": {
                    "summary": "Get email",
                    "description": "Retrieve email details by ID",
                    "tags": ["Emails"],
                    "parameters": [
                        {
                            "name": "email_id",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "string"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Email found"
                        },
                        "404": {
                            "description": "Email not found"
                        }
                    }
                }
            },
            "/emails": {
                "get": {
                    "summary": "List emails",
                    "description": "List all emails with pagination",
                    "tags": ["Emails"],
                    "parameters": [
                        {
                            "name": "status",
                            "in": "query",
                            "schema": {
                                "type": "string",
                                "enum": ["queued", "sent", "failed", "bounced"]
                            }
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "schema": {
                                "type": "integer",
                                "default": 50,
                                "maximum": 100
                            }
                        },
                        {
                            "name": "offset",
                            "in": "query",
                            "schema": {
                                "type": "integer",
                                "default": 0
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of emails"
                        }
                    }
                }
            },
            "/contacts": {
                "post": {
                    "summary": "Create contact",
                    "description": "Add a new contact to your list",
                    "tags": ["Contacts"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/Contact"
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Contact created"
                        },
                        "409": {
                            "description": "Contact already exists"
                        }
                    }
                },
                "get": {
                    "summary": "List contacts",
                    "description": "List all contacts with pagination",
                    "tags": ["Contacts"],
                    "parameters": [
                        {
                            "name": "status",
                            "in": "query",
                            "schema": {
                                "type": "string",
                                "enum": ["active", "unsubscribed", "bounced"]
                            }
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "schema": {
                                "type": "integer",
                                "default": 50
                            }
                        },
                        {
                            "name": "offset",
                            "in": "query",
                            "schema": {
                                "type": "integer",
                                "default": 0
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "List of contacts"
                        }
                    }
                }
            },
            "/contacts/{contact_id}": {
                "get": {
                    "summary": "Get contact",
                    "tags": ["Contacts"],
                    "parameters": [
                        {
                            "name": "contact_id",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "string"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Contact found"
                        },
                        "404": {
                            "description": "Contact not found"
                        }
                    }
                },
                "put": {
                    "summary": "Update contact",
                    "tags": ["Contacts"],
                    "parameters": [
                        {
                            "name": "contact_id",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "string"
                            }
                        }
                    ],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": "#/components/schemas/Contact"
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Contact updated"
                        }
                    }
                },
                "delete": {
                    "summary": "Delete contact",
                    "tags": ["Contacts"],
                    "parameters": [
                        {
                            "name": "contact_id",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "string"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Contact deleted"
                        }
                    }
                }
            }
        }
    }
    
    return jsonify(spec)

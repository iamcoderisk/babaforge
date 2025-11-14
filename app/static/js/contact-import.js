let uploadedData = null;
let headers = [];

// Drag and drop
const dropZone = document.getElementById('dropZone');

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('border-purple-500', 'bg-purple-50');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('border-purple-500', 'bg-purple-50');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('border-purple-500', 'bg-purple-50');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        document.getElementById('fileInput').files = files;
        handleFileSelect({ target: { files } });
    }
});

// Show notification
function showNotification(type, message) {
    const area = document.getElementById('notificationArea');
    const colors = {
        success: 'bg-green-50 border-green-500 text-green-800',
        error: 'bg-red-50 border-red-500 text-red-800',
        info: 'bg-blue-50 border-blue-500 text-blue-800',
        warning: 'bg-yellow-50 border-yellow-500 text-yellow-800'
    };
    
    const notification = document.createElement('div');
    notification.className = `${colors[type]} border-l-4 p-4 mb-4 rounded-lg animate-slide-down`;
    notification.innerHTML = `
        <div class="flex items-center justify-between">
            <p class="font-medium">${message}</p>
            <button onclick="this.parentElement.parentElement.remove()" class="text-xl">&times;</button>
        </div>
    `;
    
    area.appendChild(notification);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transition = 'opacity 0.3s';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Handle file selection
async function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    // Show file info
    document.getElementById('fileInfo').classList.remove('hidden');
    document.getElementById('fileName').textContent = file.name;
    document.getElementById('fileSize').textContent = `${(file.size / 1024).toFixed(2)} KB`;
    
    // Parse file
    showNotification('info', 'Processing file...');
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/contacts/parse', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            uploadedData = data.rows;
            headers = data.headers;
            
            showPreview(data.headers, data.rows.slice(0, 5));
            populateColumnSelects(data.headers);
            autoMapColumns(data.headers);
            
            document.getElementById('mappingSection').classList.remove('hidden');
            document.getElementById('importSection').classList.remove('hidden');
            document.getElementById('totalRows').textContent = data.rows.length;
            document.getElementById('importCount').textContent = data.rows.length;
            
            showNotification('success', `✅ Parsed ${data.rows.length} rows successfully`);
        } else {
            showNotification('error', 'Error: ' + (data.error || 'Failed to parse file'));
        }
    } catch (error) {
        showNotification('error', 'Network error: ' + error.message);
    }
}

// Show preview table
function showPreview(headers, rows) {
    const headerRow = document.getElementById('headerRow');
    const previewBody = document.getElementById('previewBody');
    
    // Headers
    headerRow.innerHTML = headers.map(h => 
        `<th class="px-4 py-2 border bg-gray-100 font-medium">${h}</th>`
    ).join('');
    
    // Preview rows
    previewBody.innerHTML = rows.map(row => 
        `<tr>${headers.map(h => 
            `<td class="px-4 py-2 border text-sm">${row[h] || ''}</td>`
        ).join('')}</tr>`
    ).join('');
}

// Populate column selects
function populateColumnSelects(headers) {
    const selects = ['emailColumn', 'firstNameColumn', 'lastNameColumn', 'companyColumn'];
    
    selects.forEach(id => {
        const select = document.getElementById(id);
        select.innerHTML = '<option value="">-- Select Column --</option>' +
            headers.map(h => `<option value="${h}">${h}</option>`).join('');
    });
}

// Auto-map columns
function autoMapColumns(headers) {
    const mappings = {
        email: ['email', 'e-mail', 'email address', 'mail'],
        first_name: ['first name', 'firstname', 'first', 'fname', 'given name'],
        last_name: ['last name', 'lastname', 'last', 'lname', 'surname', 'family name'],
        company: ['company', 'organization', 'org', 'business']
    };
    
    Object.entries(mappings).forEach(([field, keywords]) => {
        const match = headers.find(h => 
            keywords.some(k => h.toLowerCase().includes(k))
        );
        
        if (match) {
            const selectId = field === 'first_name' ? 'firstNameColumn' :
                           field === 'last_name' ? 'lastNameColumn' :
                           field + 'Column';
            document.getElementById(selectId).value = match;
        }
    });
}

// Form submission
document.getElementById('importForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const emailColumn = document.getElementById('emailColumn').value;
    if (!emailColumn) {
        showNotification('error', 'Please select an email column');
        return;
    }
    
    const mapping = {
        email: emailColumn,
        first_name: document.getElementById('firstNameColumn').value,
        last_name: document.getElementById('lastNameColumn').value,
        company: document.getElementById('companyColumn').value
    };
    
    const options = {
        skip_duplicates: document.querySelector('input[name="skip_duplicates"]').checked,
        validate_emails: document.querySelector('input[name="validate_emails"]').checked
    };
    
    const btn = document.getElementById('importBtn');
    btn.disabled = true;
    btn.textContent = 'Importing...';
    
    try {
        const response = await fetch('/api/contacts/import', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                data: uploadedData,
                mapping: mapping,
                options: options
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('success', `✅ Successfully imported ${result.imported} contacts!`);
            setTimeout(() => window.location.href = '/dashboard/contacts', 2000);
        } else {
            showNotification('error', 'Error: ' + (result.error || 'Import failed'));
            btn.disabled = false;
            btn.innerHTML = 'Import <span id="importCount">' + uploadedData.length + '</span> Contacts';
        }
    } catch (error) {
        showNotification('error', 'Network error: ' + error.message);
        btn.disabled = false;
        btn.innerHTML = 'Import <span id="importCount">' + uploadedData.length + '</span> Contacts';
    }
});

function resetForm() {
    window.location.reload();
}

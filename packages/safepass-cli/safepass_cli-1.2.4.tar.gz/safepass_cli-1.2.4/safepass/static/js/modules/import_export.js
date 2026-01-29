// Import/Export functionality
// showNotification is available globally via window.showNotification

// DOM Elements
const fileUploadArea = document.getElementById('file-upload-area');
const csvFileInput = document.getElementById('csv-file-input');
const selectFileBtn = document.getElementById('select-file-btn');
const fileInfo = document.getElementById('file-info');
const fileName = document.getElementById('file-name');
const fileSize = document.getElementById('file-size');
const removeFileBtn = document.getElementById('remove-file-btn');
const importBtn = document.getElementById('import-btn');
const importProgress = document.getElementById('import-progress');
const progressFill = document.getElementById('progress-fill');
const progressText = document.getElementById('progress-text');
const importResult = document.getElementById('import-result');
const exportBtn = document.getElementById('export-btn');
const includeMetadata = document.getElementById('include-metadata');
const importJsonBtn = document.getElementById('import-json-btn');
const jsonFileInput = document.getElementById('json-file-input');
const jsonImportResult = document.getElementById('json-import-result');

let selectedFile = null;

// Initialize
async function init() {
    setupEventListeners();
}

// Setup event listeners
function setupEventListeners() {
    // File selection
    selectFileBtn.addEventListener('click', () => csvFileInput.click());
    csvFileInput.addEventListener('change', handleFileSelect);
    removeFileBtn.addEventListener('click', clearFile);

    // Drag and drop
    fileUploadArea.addEventListener('dragover', handleDragOver);
    fileUploadArea.addEventListener('dragleave', handleDragLeave);
    fileUploadArea.addEventListener('drop', handleDrop);
    fileUploadArea.addEventListener('click', () => csvFileInput.click());

    // Import
    importBtn.addEventListener('click', handleImport);

    // Export
    exportBtn.addEventListener('click', handleExport);

    // JSON Import
    importJsonBtn.addEventListener('click', () => jsonFileInput.click());
    jsonFileInput.addEventListener('change', handleJsonImport);
}

// Drag and drop handlers
function handleDragOver(e) {
    e.preventDefault();
    fileUploadArea.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    fileUploadArea.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    fileUploadArea.classList.remove('drag-over');

    const files = e.dataTransfer.files;
    if (files.length > 0) {
        const file = files[0];
        if (file.name.endsWith('.csv')) {
            selectedFile = file;
            displayFileInfo(file);
        } else {
            showNotification('Lütfen .csv uzantılı bir dosya seçin', 'error');
        }
    }
}

// Handle file selection
function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        selectedFile = file;
        displayFileInfo(file);
    }
}

// Display file information
function displayFileInfo(file) {
    fileName.textContent = file.name;
    fileSize.textContent = formatFileSize(file.size);
    fileUploadArea.style.display = 'none';
    fileInfo.style.display = 'flex';
    importBtn.disabled = false;
    importResult.style.display = 'none';
}

// Clear selected file
function clearFile() {
    selectedFile = null;
    csvFileInput.value = '';
    fileUploadArea.style.display = 'block';
    fileInfo.style.display = 'none';
    importBtn.disabled = true;
    importResult.style.display = 'none';
}

// Format file size
function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// Parse CSV file
async function parseCSV(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();

        reader.onload = (e) => {
            try {
                const text = e.target.result;
                const lines = text.split('\n').filter(line => line.trim());

                if (lines.length < 2) {
                    reject(new Error('CSV dosyası boş veya geçersiz'));
                    return;
                }

                // Parse header
                const header = parseCSVLine(lines[0]);
                
                // Check for KeePass format (Group, Subcategory, Title, Username, Password, URL)
                const keepassFields = ['Group', 'Subcategory', 'Title', 'Username', 'Password', 'URL'];
                const isKeePassFormat = keepassFields.every(field =>
                    header.some(h => h.toLowerCase() === field.toLowerCase())
                );
                
                // Check for SafePass format (title, username, password, category)
                const safepassFields = ['title', 'username', 'password'];
                const isSafePassFormat = safepassFields.every(field =>
                    header.some(h => h.toLowerCase() === field.toLowerCase())
                );

                if (!isKeePassFormat && !isSafePassFormat) {
                    reject(new Error('CSV dosyası gerekli sütunları içermiyor. KeePass veya SafePass formatı kullanın.'));
                    return;
                }

                // Parse data rows
                const passwords = [];
                
                if (isKeePassFormat) {
                    // KeePass format: Group,Subcategory,Title,Username,Password,URL
                    for (let i = 1; i < lines.length; i++) {
                        const values = parseCSVLine(lines[i]);
                        if (values.length >= 6) {
                            passwords.push({
                                category: values[0].toLowerCase().trim(),
                                subcategory: values[1].toLowerCase().trim(),
                                title: values[2],
                                username: values[3],
                                password: values[4],
                                website: values[5],
                                notes: values[6] || ''
                            });
                        }
                    }
                } else {
                    // SafePass format: title,app_name,username,password,website,url,category,subcategory
                    const headerMap = {};
                    header.forEach((col, idx) => {
                        headerMap[col.toLowerCase().trim()] = idx;
                    });
                    
                    for (let i = 1; i < lines.length; i++) {
                        const values = parseCSVLine(lines[i]);
                        if (values.length >= 3) {
                            passwords.push({
                                title: values[headerMap['title']] || values[headerMap['app_name']] || '',
                                username: values[headerMap['username']] || '',
                                password: values[headerMap['password']] || '',
                                website: values[headerMap['website']] || values[headerMap['url']] || '',
                                category: values[headerMap['category']] || 'genel',
                                subcategory: values[headerMap['subcategory']] || '',
                                notes: values[headerMap['notes']] || ''
                            });
                        }
                    }
                }

                resolve(passwords);
            } catch (error) {
                reject(error);
            }
        };

        reader.onerror = () => reject(new Error('Dosya okunamadı'));
        reader.readAsText(file);
    });
}

// Parse CSV line (handles quoted values)
function parseCSVLine(line) {
    const values = [];
    let current = '';
    let inQuotes = false;

    for (let i = 0; i < line.length; i++) {
        const char = line[i];

        if (char === '"') {
            inQuotes = !inQuotes;
        } else if (char === ',' && !inQuotes) {
            values.push(current.trim());
            current = '';
        } else {
            current += char;
        }
    }

    values.push(current.trim());
    return values.map(v => v.replace(/^"|"$/g, ''));
}

// Handle import
async function handleImport() {
    if (!selectedFile) return;

    try {
        importBtn.disabled = true;
        importProgress.style.display = 'block';
        importResult.style.display = 'none';
        progressFill.style.width = '0%';
        progressText.textContent = 'CSV dosyası okunuyor...';

        // Parse CSV
        const passwords = await parseCSV(selectedFile);

        if (passwords.length === 0) {
            throw new Error('CSV dosyasında geçerli şifre bulunamadı');
        }

        progressText.textContent = `${passwords.length} şifre bulundu, içe aktarılıyor...`;
        progressFill.style.width = '30%';

        // Import passwords
        const response = await fetch('/api/import-passwords', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                passwords: passwords
            })
        });

        const result = await response.json();
        progressFill.style.width = '100%';

        if (response.ok) {
            progressText.textContent = 'Tamamlandı!';
            setTimeout(() => {
                importProgress.style.display = 'none';
                
                const imported = result.imported || 0;
                const updated = result.updated || 0;
                const skipped = result.skipped || 0;
                
                let message = 'Başarıyla tamamlandı! ';
                const parts = [];
                
                if (imported > 0) parts.push(`${imported} yeni şifre eklendi`);
                if (updated > 0) parts.push(`${updated} şifre güncellendi`);
                if (skipped > 0) parts.push(`${skipped} atlandı`);
                
                message += parts.join(', ') + '.';
                
                showResult(message, 'success');
                clearFile();
            }, 500);
        } else {
            throw new Error(result.error || 'İçe aktarma başarısız');
        }

    } catch (error) {
        console.error('Import error:', error);
        importProgress.style.display = 'none';
        showResult(error.message, 'error');
    } finally {
        importBtn.disabled = false;
    }
}

// Handle export
async function handleExport() {
    try {
        exportBtn.disabled = true;
        exportBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <polyline points="12 6 12 12 16 14"></polyline>
            </svg>
            İndiriliyor...
        `;

        const response = await fetch('/api/export-passwords', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                include_metadata: includeMetadata.checked
            })
        });

        if (!response.ok) {
            throw new Error('Dışa aktarma başarısız');
        }

        const data = await response.json();

        // Create download
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `safepass-export-${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        showNotification('Şifreler başarıyla dışa aktarıldı', 'success');

    } catch (error) {
        console.error('Export error:', error);
        showNotification(error.message, 'error');
    } finally {
        exportBtn.disabled = false;
        exportBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                <polyline points="7 10 12 15 17 10"></polyline>
                <line x1="12" y1="15" x2="12" y2="3"></line>
            </svg>
            JSON Olarak İndir
        `;
    }
}

// Show result message
function showResult(message, type) {
    importResult.textContent = message;
    importResult.className = `import-result ${type}`;
    importResult.style.display = 'block';
}

// Handle JSON import
async function handleJsonImport(e) {
    const file = e.target.files[0];
    if (!file) return;

    try {
        importJsonBtn.disabled = true;
        jsonImportResult.style.display = 'none';

        const text = await file.text();
        const data = JSON.parse(text);

        if (!data.passwords || !Array.isArray(data.passwords)) {
            throw new Error('Geçersiz JSON formatı');
        }

        // Send passwords array to backend
        const response = await fetch('/api/import', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                passwords: data.passwords,
                skip_duplicates: true
            })
        });

        const result = await response.json();

        // Debug logging
        console.log('[DEBUG] Response:', result);
        if (result.debug) {
            console.log('[DEBUG] Backend debug info:', result.debug);
        }

        if (response.ok) {
            const imported = result.imported || 0;
            const updated = result.updated || 0;
            const skipped = result.skipped || 0;
            
            let message = '';
            if (imported > 0 && updated > 0) {
                message = `${imported} yeni şifre eklendi, ${updated} şifre güncellendi`;
            } else if (imported > 0) {
                message = `${imported} yeni şifre eklendi`;
            } else if (updated > 0) {
                message = `${updated} şifre güncellendi`;
            } else {
                message = 'Hiçbir değişiklik yapılmadı';
            }
            
            if (skipped > 0) {
                message += `, ${skipped} atlandı`;
            }
            
            jsonImportResult.textContent = `Başarılı! ${message}`;
            jsonImportResult.className = 'import-result success';
            jsonImportResult.style.display = 'block';
            window.showNotification('Şifreler başarıyla içe aktarıldı', 'success');
        } else {
            throw new Error(result.error || 'İçe aktarma başarısız');
        }

    } catch (error) {
        console.error('JSON import error:', error);
        jsonImportResult.textContent = error.message;
        jsonImportResult.className = 'import-result error';
        jsonImportResult.style.display = 'block';
        window.showNotification(error.message, 'error');
    } finally {
        importJsonBtn.disabled = false;
        jsonFileInput.value = '';
    }
}

// Initialize on page load
init();

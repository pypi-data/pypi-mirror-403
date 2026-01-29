/* SafePass - Cards Module */

let currentCategory = '';

document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('search-input');
    
    // Custom dropdown
    const customSelect = document.getElementById('custom-category-select');
    const trigger = customSelect?.querySelector('.custom-select-trigger');
    const options = customSelect?.querySelectorAll('.custom-option');
    
    if (trigger) {
        trigger.addEventListener('click', function(e) {
            e.stopPropagation();
            customSelect.classList.toggle('open');
        });
    }
    
    if (options) {
        options.forEach(option => {
            option.addEventListener('click', function(e) {
                e.stopPropagation();
                const value = this.dataset.value;
                const text = this.textContent;
                
                // Update selected text
                document.getElementById('selected-category').textContent = text;
                
                // Update selected class
                options.forEach(opt => opt.classList.remove('selected'));
                this.classList.add('selected');
                
                // Close dropdown
                customSelect.classList.remove('open');
                
                // Update current category and filter
                currentCategory = value;
                handleFilter();
            });
        });
    }
    
    // Close dropdown when clicking outside
    document.addEventListener('click', function() {
        if (customSelect) {
            customSelect.classList.remove('open');
        }
    });
    
    if (searchInput) {
        searchInput.addEventListener('input', handleFilter);
    }
    
    // Event delegation for card actions
    document.addEventListener('click', function(e) {
        // Find the actual button element (handle SVG clicks)
        const button = e.target.closest('button');
        
        if (button && button.classList.contains('btn-history')) {
            const cardId = button.dataset.cardId;
            showPasswordHistory(cardId);
        }
        
        if (button && button.classList.contains('btn-edit')) {
            const cardId = button.dataset.cardId;
            editCard(cardId);
        }
        
        if (button && button.classList.contains('btn-delete')) {
            const cardId = button.dataset.cardId;
            deleteCard(cardId);
        }
        
        if (button && button.classList.contains('btn-toggle-password')) {
            togglePassword(button);
        }
        
        if (button && button.classList.contains('btn-copy-password')) {
            const password = button.dataset.password;
            copyPassword(password);
        }
    });
});

function handleFilter() {
    const searchTerm = document.getElementById('search-input')?.value.toLowerCase() || '';
    const selectedCategory = currentCategory.toLowerCase();
    const cards = document.querySelectorAll('.password-card');
    
    // Main categories that group subcategories
    const mainCategoryMap = {
        'genel': ['genel', 'e-posta', 'sosyal-medya', 'alisveris', 'forumlar-uyelikler'],
        'finans': ['finans', 'bankacilik', 'kredi-kartlari', 'kripto-paralar', 'faturalar'],
        'is-gelistirici': ['is-gelistirici', 'sirket-hesaplari', 'sunucular-ssh', 'veritabanlari', 'git-repolar', 'api-lisanslar'],
        'sistem-ag': ['sistem-ag', 'wifi-sifreleri', 'cihaz-pinleri', 'modem-arayuzleri', 'yazilim-lisanslari'],
        'kisisel': ['kisisel', 'e-devlet-resmi-kurum', 'saglik', 'notlar-guvenli-dosyalar']
    };
    
    cards.forEach(card => {
        const appName = card.querySelector('.card-title')?.textContent.toLowerCase() || '';
        const username = card.querySelector('.card-username')?.textContent.toLowerCase() || '';
        const cardCategory = (card.dataset.category || 'genel').toLowerCase();
        const cardSubcategory = (card.dataset.subcategory || '').toLowerCase();
        
        // Search filter
        const matchesSearch = !searchTerm || 
            appName.includes(searchTerm) || 
            username.includes(searchTerm);
        
        // Category filter - check if it's a main category or subcategory
        let matchesCategory = !selectedCategory;
        
        if (selectedCategory) {
            // Check if selected is a main category
            if (mainCategoryMap[selectedCategory]) {
                // Match if card's category OR subcategory is in the group
                matchesCategory = mainCategoryMap[selectedCategory].includes(cardCategory) || 
                                  mainCategoryMap[selectedCategory].includes(cardSubcategory);
            } else {
                // It's a subcategory, match directly
                matchesCategory = cardCategory === selectedCategory || cardSubcategory === selectedCategory;
            }
        }
        
        // Show card only if both filters match
        if (matchesSearch && matchesCategory) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });
}

function handleSearch(e) {
    handleFilter();
}

function togglePassword(button) {
    const passwordField = button.closest('.password-field');
    const hidden = passwordField.querySelector('.password-hidden');
    const visible = passwordField.querySelector('.password-visible');
    
    if (hidden && visible) {
        if (hidden.style.display === 'none') {
            hidden.style.display = '';
            visible.style.display = 'none';
        } else {
            hidden.style.display = 'none';
            visible.style.display = '';
        }
    }
}

async function copyPassword(password) {
    try {
        await navigator.clipboard.writeText(password);
        showToast('Şifre kopyalandı!', 'success');
    } catch (error) {
        showToast('Kopyalama başarısız', 'error');
    }
}

async function deleteCard(cardId) {
    if (!confirm('Bu şifreyi silmek istediğinize emin misiniz?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/passwords/${cardId}/delete`, {
            method: 'DELETE',
        });
        
        if (response.ok) {
            document.querySelector(`[data-id="${cardId}"]`).remove();
            showToast('Şifre silindi', 'success');
        } else {
            showToast('Silme başarısız', 'error');
        }
    } catch (error) {
        showToast('Bir hata oluştu', 'error');
    }
}

function editCard(cardId) {
    window.location.href = `/passwords/${cardId}/edit`;
}

async function showPasswordHistory(cardId) {
    const modal = document.getElementById('history-modal');
    const historyList = document.getElementById('history-list');
    const historyEmpty = document.getElementById('history-empty');
    
    // Show modal
    modal.style.display = 'flex';
    
    // Clear previous content
    historyList.innerHTML = '<div class="loading">Yükleniyor...</div>';
    historyEmpty.style.display = 'none';
    
    try {
        const response = await fetch(`/api/passwords/${cardId}/history`);
        const data = await response.json();
        
        if (data.success && data.history.length > 0) {
            historyList.innerHTML = '';
            data.history.forEach((item, index) => {
                const historyItem = document.createElement('div');
                historyItem.className = 'history-item';
                historyItem.innerHTML = `
                    <div class="history-info">
                        <span class="history-number">#${index + 1}</span>
                        <span class="history-date">${item.changed_at}</span>
                    </div>
                    <div class="history-password">
                        <span class="password-text">${item.password}</span>
                        <button class="btn-icon btn-copy-history" data-password="${item.password}" title="Kopyala">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                            </svg>
                        </button>
                    </div>
                `;
                historyList.appendChild(historyItem);
            });
            
            // Add copy event listeners
            document.querySelectorAll('.btn-copy-history').forEach(btn => {
                btn.addEventListener('click', async function() {
                    const password = this.dataset.password;
                    await copyPassword(password);
                });
            });
        } else {
            historyList.innerHTML = '';
            historyEmpty.style.display = 'block';
        }
    } catch (error) {
        historyList.innerHTML = '';
        historyEmpty.innerHTML = '<p>Geçmiş yüklenirken hata oluştu</p>';
        historyEmpty.style.display = 'block';
    }
}

// Modal close functionality
document.addEventListener('click', function(e) {
    const modal = document.getElementById('history-modal');
    if (e.target === modal || e.target.classList.contains('modal-close')) {
        modal.style.display = 'none';
    }
});

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type}`;
    toast.textContent = message;
    toast.style.position = 'fixed';
    toast.style.top = '2rem';
    toast.style.right = '2rem';
    toast.style.zIndex = '1000';
    
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

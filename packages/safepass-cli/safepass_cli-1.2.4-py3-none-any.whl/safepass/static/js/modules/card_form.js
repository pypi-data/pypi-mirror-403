/**
 * Card Form Module
 * Handles add/edit card functionality
 */

// Subcategory options based on main category
const subcategoryOptions = {
    'genel': [
        { value: 'e-posta', label: 'E-Posta' },
        { value: 'sosyal-medya', label: 'Sosyal Medya' },
        { value: 'alisveris', label: 'Alışveriş (E-Ticaret)' },
        { value: 'forumlar-uyelikler', label: 'Forumlar & Üyelikler' }
    ],
    'finans': [
        { value: 'bankacilik', label: 'Bankacılık' },
        { value: 'kredi-kartlari', label: 'Kredi Kartları' },
        { value: 'kripto-paralar', label: 'Kripto Paralar' },
        { value: 'faturalar', label: 'Faturalar' }
    ],
    'is-gelistirici': [
        { value: 'sirket-hesaplari', label: 'Şirket Hesapları' },
        { value: 'sunucular-ssh', label: 'Sunucular & SSH' },
        { value: 'veritabanlari', label: 'Veritabanları' },
        { value: 'git-repolar', label: 'Git & Repolar' },
        { value: 'api-lisanslar', label: 'API & Lisanslar' }
    ],
    'sistem-ag': [
        { value: 'wifi-sifreleri', label: 'Wi-Fi Şifreleri' },
        { value: 'cihaz-pinleri', label: 'Cihaz Pinleri' },
        { value: 'modem-arayuzleri', label: 'Modem Arayüzleri' },
        { value: 'yazilim-lisanslari', label: 'Yazılım Lisansları' }
    ],
    'kisisel': [
        { value: 'e-devlet-resmi-kurum', label: 'E-Devlet & Resmi Kurum' },
        { value: 'saglik', label: 'Sağlık' },
        { value: 'notlar-guvenli-dosyalar', label: 'Notlar & Güvenli Dosyalar' }
    ]
};

function updateSubcategoryOptions(categoryValue, selectedSubcategory = '') {
    console.log('updateSubcategoryOptions called with:', categoryValue);
    const subcategorySelect = document.getElementById('subcategory');
    if (!subcategorySelect) {
        console.log('Subcategory select NOT found!');
        return;
    }
    
    // Clear current options
    subcategorySelect.innerHTML = '<option value="">Seçiniz...</option>';
    
    // Get subcategories for selected category
    const subcategories = subcategoryOptions[categoryValue] || [];
    console.log('Found subcategories:', subcategories);
    
    // Add new options
    subcategories.forEach(sub => {
        const option = document.createElement('option');
        option.value = sub.value;
        option.textContent = sub.label;
        if (sub.value === selectedSubcategory) {
            option.selected = true;
        }
        subcategorySelect.appendChild(option);
    });
    console.log('Subcategory options updated, total:', subcategories.length);
}

// Service button handlers
document.addEventListener('DOMContentLoaded', function() {
    const showAlert = window.showAlert;
    const getCookie = window.getCookie;
    
    // Get form elements
    const addCardForm = document.getElementById('addCardForm');
    const passwordInput = document.getElementById('password');
    const passwordStrengthBar = document.getElementById('passwordStrengthBar');
    const passwordStrengthText = document.getElementById('passwordStrengthText');
    const categorySelect = document.getElementById('category');
    
    // Category change handler - update subcategories
    if (categorySelect) {
        console.log('Category select found:', categorySelect.value);
        categorySelect.addEventListener('change', function() {
            console.log('Category changed to:', this.value);
            updateSubcategoryOptions(this.value);
        });
        // Initialize subcategories for default category
        console.log('Initializing subcategories for:', categorySelect.value);
        updateSubcategoryOptions(categorySelect.value);
    } else {
        console.log('Category select NOT found!');
    }

    // Service button click handlers
    const serviceButtons = document.querySelectorAll('.service-btn');
    
    if (serviceButtons.length > 0) {
        serviceButtons.forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                // Remove selected class from all buttons
                serviceButtons.forEach(function(b) {
                    b.classList.remove('selected');
                });
                
                // Add selected class to clicked button
                btn.classList.add('selected');
                
                // Get data from button attributes
                const serviceName = btn.getAttribute('data-service');
                const serviceUrl = btn.getAttribute('data-url');
                
                // Fill form fields
                const titleInput = document.getElementById('title');
                const urlInput = document.getElementById('url');
                const usernameInput = document.getElementById('username');
                
                if (titleInput && serviceName) {
                    titleInput.value = serviceName;
                }
                
                if (urlInput && serviceUrl) {
                    urlInput.value = serviceUrl;
                }
                
                // Focus username field
                if (usernameInput) {
                    setTimeout(function() {
                        usernameInput.focus();
                    }, 100);
                }
            });
        });
    }

    // Password toggle handler
    const toggleButtons = document.querySelectorAll('.btn-toggle-password');
    toggleButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = btn.dataset.target;
            const input = document.getElementById(targetId);
            const eyeOpen = btn.querySelector('.icon-eye-open');
            const eyeClosed = btn.querySelector('.icon-eye-closed');
            
            if (input) {
                if (input.type === 'password') {
                    input.type = 'text';
                    if (eyeOpen) eyeOpen.style.display = 'none';
                    if (eyeClosed) eyeClosed.style.display = 'block';
                } else {
                    input.type = 'password';
                    if (eyeOpen) eyeOpen.style.display = 'block';
                    if (eyeClosed) eyeClosed.style.display = 'none';
                }
            }
        });
    });

    // Password strength check on input
    if (passwordInput) {
        passwordInput.addEventListener('input', () => {
            const password = passwordInput.value;

            if (!password) {
                passwordStrengthBar.style.width = '0%';
                passwordStrengthText.textContent = 'Şifre girin';
                passwordStrengthText.style.color = '#94a3b8';
                return;
            }

            // Simple client-side strength check
            let score = 0;
            
            // Length
            if (password.length >= 8) score += 20;
            if (password.length >= 12) score += 20;
            if (password.length >= 16) score += 10;
            
            // Character types
            if (/[a-z]/.test(password)) score += 15;
            if (/[A-Z]/.test(password)) score += 15;
            if (/[0-9]/.test(password)) score += 15;
            if (/[^a-zA-Z0-9]/.test(password)) score += 15;

            const percentage = Math.min(score, 100);
            passwordStrengthBar.style.width = percentage + '%';

            let label = 'Zayıf';
            let color = '#ef4444';

            if (percentage >= 80) {
                label = 'Çok Güçlü';
                color = '#10b981';
            } else if (percentage >= 60) {
                label = 'Güçlü';
                color = '#3b82f6';
            } else if (percentage >= 40) {
                label = 'Orta';
                color = '#f59e0b';
            }

            passwordStrengthText.textContent = label;
            passwordStrengthText.style.color = color;
            passwordStrengthBar.style.backgroundColor = color;
        });
    }

    // Form submit handler
    if (addCardForm) {
        addCardForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = {
                app_name: document.getElementById('title').value.trim(),
                username: document.getElementById('username').value.trim(),
                password: document.getElementById('password').value,
                url: document.getElementById('url')?.value.trim() || '',
                notes: document.getElementById('notes')?.value.trim() || '',
                category: document.getElementById('category')?.value || 'genel',
                subcategory: document.getElementById('subcategory')?.value || ''
            };

            // Validation
            if (!formData.app_name) {
                showAlert('Başlık gereklidir', 'error');
                return;
            }

            if (!formData.password || formData.password.length < 8) {
                showAlert('Şifre en az 8 karakter olmalıdır', 'error');
                return;
            }

            try {
                const response = await fetch('/api/passwords', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                    body: JSON.stringify(formData)
                });

                const data = await response.json();

                if (data.success) {
                    showAlert('Şifre başarıyla eklendi!', 'success');
                    setTimeout(() => {
                        window.location.href = '/passwords';
                    }, 1000);
                } else {
                    showAlert(data.error || 'Şifre eklenemedi', 'error');
                }
            } catch (error) {
                console.error('Add card error:', error);
                showAlert('Bir hata oluştu', 'error');
            }
        });
    }
});

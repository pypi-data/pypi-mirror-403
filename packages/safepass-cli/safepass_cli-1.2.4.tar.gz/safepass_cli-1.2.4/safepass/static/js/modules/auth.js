/* SafePass - Auth Module */

// Helper function for password strength requirements
function updateRequirement(id, isMet, isOptional = false) {
    const element = document.getElementById(id);
    if (!element) return;
    
    const icon = element.querySelector('.req-icon');
    if (isMet) {
        element.classList.add('met');
        element.classList.remove('optional');
        icon.textContent = '✅';
    } else if (isOptional) {
        element.classList.remove('met');
        element.classList.add('optional');
        icon.textContent = '✨';
    } else {
        element.classList.remove('met', 'optional');
        icon.textContent = '❌';
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');

    // Password toggle functionality
    const passwordToggles = document.querySelectorAll('.password-toggle');
    console.log('Password toggle buttons found:', passwordToggles.length);
    
    passwordToggles.forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('data-target');
            const input = document.getElementById(targetId);
            
            console.log('Toggle clicked for:', targetId, 'Input found:', !!input);
            
            if (input) {
                if (input.type === 'password') {
                    input.type = 'text';
                    this.classList.add('visible');
                    console.log('Password shown');
                } else {
                    input.type = 'password';
                    this.classList.remove('visible');
                    console.log('Password hidden');
                }
            }
        });
    });

    if (loginForm) {
        loginForm.addEventListener('submit', handleLogin);
        
        // Login password validation
        const loginPasswordInput = document.getElementById('master-password');
        const loginPasswordError = document.getElementById('login-password-error');
        
        if (loginPasswordInput && loginPasswordError) {
            // Real-time validation
            loginPasswordInput.addEventListener('input', function() {
                const password = loginPasswordInput.value;
                
                if (password.length > 0 && password.length < 8) {
                    loginPasswordError.textContent = 'Şifre en az 8 karakter olmalıdır.';
                    loginPasswordError.style.display = 'block';
                    loginPasswordInput.classList.add('error');
                } else {
                    loginPasswordError.style.display = 'none';
                    loginPasswordInput.classList.remove('error');
                }
            });
            
            // Clear error on focus
            loginPasswordInput.addEventListener('focus', function() {
                if (loginPasswordInput.value.length >= 8) {
                    loginPasswordError.style.display = 'none';
                    loginPasswordInput.classList.remove('error');
                }
            });
        }
    }

    if (registerForm) {
        registerForm.addEventListener('submit', handleRegister);
        
        // Real-time password strength validation
        const passwordInput = document.getElementById('master-password');
        const strengthIndicator = document.getElementById('password-strength');
        const strengthFill = document.getElementById('strength-fill');
        
        console.log('Password strength elements:', { passwordInput, strengthIndicator, strengthFill });
        
        if (passwordInput && strengthIndicator) {
            console.log('Setting up password strength listener');
            passwordInput.addEventListener('input', function() {
                const password = passwordInput.value;
                console.log('Password changed:', password.length, 'chars');
                
                if (password.length === 0) {
                    strengthIndicator.style.display = 'none';
                    return;
                }
                
                strengthIndicator.style.display = 'block';
                
                // Check requirements
                const hasLength = password.length >= 8;
                const hasUpper = /[A-Z]/.test(password);
                const hasLower = /[a-z]/.test(password);
                const hasDigit = /[0-9]/.test(password);
                const hasSpecial = /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password);
                
                // Update requirement indicators
                updateRequirement('req-length', hasLength);
                updateRequirement('req-upper', hasUpper);
                updateRequirement('req-lower', hasLower);
                updateRequirement('req-digit', hasDigit);
                updateRequirement('req-special', hasSpecial, true); // optional
                
                // Calculate strength
                let strength = 0;
                if (hasLength) strength += 25;
                if (hasUpper) strength += 25;
                if (hasLower) strength += 25;
                if (hasDigit) strength += 25;
                if (hasSpecial) strength += 20;
                
                // Update strength bar
                strengthFill.style.width = Math.min(strength, 100) + '%';
                
                // Update color
                if (strength < 50) {
                    strengthFill.style.background = '#ef4444';
                } else if (strength < 75) {
                    strengthFill.style.background = '#f59e0b';
                } else if (strength < 100) {
                    strengthFill.style.background = '#10b981';
                } else {
                    strengthFill.style.background = 'linear-gradient(90deg, #10b981, #059669)';
                }
            });
        }
        
        // Info modal functionality
        const infoBtn = document.getElementById('info-btn');
        const infoModal = document.getElementById('info-modal');
        const closeModal = document.getElementById('close-modal');
        
        if (infoBtn && infoModal && closeModal) {
            infoBtn.addEventListener('click', function() {
                infoModal.classList.add('show');
            });
            
            closeModal.addEventListener('click', function() {
                infoModal.classList.remove('show');
            });
            
            // Close on outside click
            infoModal.addEventListener('click', function(e) {
                if (e.target === infoModal) {
                    infoModal.classList.remove('show');
                }
            });
            
            // Close on ESC key
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape' && infoModal.classList.contains('show')) {
                    infoModal.classList.remove('show');
                }
            });
        }
        
        // Real-time password match validation
        const confirmInput = document.getElementById('master-password-confirm');
        const matchHint = document.getElementById('password-match-hint');
        
        if (passwordInput && confirmInput && matchHint) {
            confirmInput.addEventListener('input', function() {
                const password = passwordInput.value;
                const confirm = confirmInput.value;
                
                if (confirm.length === 0) {
                    matchHint.textContent = '';
                    matchHint.className = 'form-hint password-match-hint';
                    confirmInput.style.borderColor = '';
                } else if (password === confirm) {
                    matchHint.textContent = '✓ Şifreler eşleşiyor';
                    matchHint.className = 'form-hint password-match-hint match-success';
                    confirmInput.style.borderColor = 'var(--success)';
                } else {
                    matchHint.textContent = '✗ Şifreler eşleşmiyor';
                    matchHint.className = 'form-hint password-match-hint match-error';
                    confirmInput.style.borderColor = 'var(--danger)';
                }
            });
            
            // Also check when password changes
            passwordInput.addEventListener('input', function() {
                if (confirmInput.value.length > 0) {
                    confirmInput.dispatchEvent(new Event('input'));
                }
            });
        }
    }
});

async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const masterPassword = document.getElementById('master-password').value;
    
    // Frontend validation
    if (!username) {
        showToast('Kullanıcı adı boş bırakılamaz', 'error');
        return;
    }
    
    if (!masterPassword) {
        showToast('Şifre boş bırakılamaz', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: username,
                master_password: masterPassword
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast('Giriş başarılı! Yönlendiriliyorsunuz...', 'success');
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1000);
        } else {
            showToast(data.error || 'Giriş başarısız', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showToast('Sunucuya bağlanılamadı. Lütfen tekrar deneyin', 'error');
    }
}

async function handleRegister(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const masterPassword = document.getElementById('master-password').value;
    const masterPasswordConfirm = document.getElementById('master-password-confirm').value;
    const checkbox = document.querySelector('input[type="checkbox"]');
    
    // Frontend validation
    if (!username) {
        showToast('Kullanıcı adı boş bırakılamaz', 'error');
        return;
    }
    
    if (username.length < 3) {
        showToast('Kullanıcı adı en az 3 karakter olmalı', 'error');
        return;
    }
    
    if (!masterPassword) {
        showToast('Ana şifre boş bırakılamaz', 'error');
        return;
    }
    
    if (masterPassword.length < 8) {
        showToast('Ana şifre en az 8 karakter olmalı', 'error');
        return;
    }
    
    if (!checkbox.checked) {
        showToast('Devam etmek için şartları kabul etmelisiniz', 'warning');
        return;
    }
    
    if (masterPassword !== masterPasswordConfirm) {
        showToast('Şifreler eşleşmiyor! Lütfen aynı şifreyi girin', 'error');
        return;
    }
    
    // Check password strength
    const hasUpper = /[A-Z]/.test(masterPassword);
    const hasLower = /[a-z]/.test(masterPassword);
    const hasDigit = /[0-9]/.test(masterPassword);
    
    if (!hasUpper || !hasLower || !hasDigit) {
        showToast('Zayıf şifre! Büyük harf, küçük harf ve rakam içermelidir', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: username,
                master_password: masterPassword
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast('Kayıt başarılı! Giriş yapılıyor...', 'success');
            setTimeout(() => {
                window.location.href = '/dashboard';
            }, 1500);
        } else {
            showToast(data.error || 'Kayıt başarısız', 'error');
        }
    } catch (error) {
        console.error('Register error:', error);
        showToast('Sunucuya bağlanılamadı. Lütfen tekrar deneyin', 'error');
    }
}

function showAlert(message, type = 'info') {
    // Deprecated - use showToast instead
    showToast(message, type);
}

function showToast(message, type = 'info') {
    // Remove existing toasts
    const existingToasts = document.querySelectorAll('.toast-notification');
    existingToasts.forEach(toast => toast.remove());
    
    // Create toast container if it doesn't exist
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    
    // Icon based on type
    let icon = '📝';
    if (type === 'error') icon = '❌';
    if (type === 'success') icon = '✅';
    if (type === 'warning') icon = '⚠️';
    
    toast.innerHTML = `
        <div class="toast-icon">${icon}</div>
        <div class="toast-message">${message}</div>
        <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
    `;
    
    toastContainer.appendChild(toast);
    
    // Animate in
    setTimeout(() => toast.classList.add('show'), 10);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

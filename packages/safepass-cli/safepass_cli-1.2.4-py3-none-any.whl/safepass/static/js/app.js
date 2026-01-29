/* SafePass - Main Application */

// Global utilities - Define before exports to ensure it's available
function showAlert(message, type = 'info') {
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.textContent = message;
    alert.style.position = 'fixed';
    alert.style.top = '2rem';
    alert.style.right = '2rem';
    alert.style.zIndex = '1000';
    alert.style.maxWidth = '400px';

    document.body.appendChild(alert);

    setTimeout(() => {
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 300);
    }, 3000);
}

// Make globally available
window.showAlert = showAlert;

// CSRF Token handling
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Make globally available
window.getCookie = getCookie;

// Global fetch wrapper - Session timeout ve error handling
const originalFetch = window.fetch;
window.fetch = function (...args) {
    // CSRF token ekleme
    if (args[1] && ['POST', 'PUT', 'DELETE', 'PATCH'].includes(args[1].method)) {
        args[1].headers = args[1].headers || {};
        args[1].headers['X-CSRFToken'] = getCookie('csrftoken');
    }

    // Fetch isteğini yap ve hataları yakala
    return originalFetch.apply(this, args)
        .then(response => {
            // 401 Unauthorized - Session dolmuş veya yetkisiz erişim
            if (response.status === 401) {
                // Sadece API çağrılarında uyarı göster (login/register sayfalarında gösterme)
                const currentPath = window.location.pathname;
                if (!currentPath.includes('/auth/login') && !currentPath.includes('/auth/register')) {
                    alert('⏰ Oturumunuz sona erdi.\n\nGüvenliğiniz için lütfen tekrar giriş yapın.');
                    window.location.href = '/auth/login';
                }
                // Response'u yine de döndür (catch bloğunda handle edilebilir)
                return response;
            }

            // 403 Forbidden
            if (response.status === 403) {
                showAlert('Bu işlem için yetkiniz yok', 'error');
                return response;
            }

            // 500 Internal Server Error
            if (response.status === 500) {
                showAlert('Sunucu hatası oluştu. Lütfen tekrar deneyin.', 'error');
                return response;
            }

            return response;
        })
        .catch(error => {
            // Network hatası veya timeout
            console.error('Fetch error:', error);

            // Timeout hatası
            if (error.name === 'AbortError' || error.message.includes('timeout')) {
                showAlert('İstek zaman aşımına uğradı. Lütfen tekrar deneyin.', 'error');
            }
            // Network hatası
            else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
                showAlert('Bağlantı hatası. İnternet bağlantınızı kontrol edin.', 'error');
            }

            throw error;
        });
};

// Active navigation highlighting
document.addEventListener('DOMContentLoaded', function () {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar-menu a');

    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // ========================================================================
    // FRONTEND SESSION TIMEOUT KONTROLÜ
    // ========================================================================
    // Session timeout: 1 saat (3600000 ms) - backend ile senkron
    const SESSION_TIMEOUT = 3600000; // 1 saat
    const WARNING_TIME = 300000; // 5 dakika kala uyar

    let lastActivity = Date.now();
    let warningShown = false;
    let sessionCheckInterval = null;

    // Kullanıcı aktivitesini takip et
    function resetSessionTimer() {
        lastActivity = Date.now();
        warningShown = false;
    }

    // Sadece login gerektiren sayfalarda session kontrolü yap
    const isAuthPage = currentPath.includes('/auth/login') || currentPath.includes('/auth/register');

    if (!isAuthPage) {
        // Kullanıcı aktivitelerini dinle
        document.addEventListener('mousemove', resetSessionTimer);
        document.addEventListener('keypress', resetSessionTimer);
        document.addEventListener('click', resetSessionTimer);
        document.addEventListener('scroll', resetSessionTimer);

        // Her 30 saniyede bir session kontrolü yap
        sessionCheckInterval = setInterval(() => {
            const elapsed = Date.now() - lastActivity;
            const remaining = SESSION_TIMEOUT - elapsed;

            // 5 dakika kaldıysa ve henüz uyarı gösterilmediyse
            if (remaining < WARNING_TIME && remaining > 0 && !warningShown) {
                warningShown = true;
                const minutes = Math.ceil(remaining / 60000);

                if (confirm(`⏰ Oturumunuz ${minutes} dakika içinde sona erecek.\n\nDevam etmek ister misiniz?`)) {
                    // Kullanıcı devam etmek istiyorsa session'ı yenile
                    fetch('/api/auth/check')
                        .then(response => {
                            if (response.ok) {
                                resetSessionTimer();
                                showAlert('Oturumunuz yenilendi', 'success');
                            } else {
                                throw new Error('Session refresh failed');
                            }
                        })
                        .catch(() => {
                            alert('⚠️ Oturum yenilenemedi.\n\nLütfen tekrar giriş yapın.');
                            window.location.href = '/auth/login';
                        });
                } else {
                    // Kullanıcı çıkmak istiyorsa logout yap
                    window.location.href = '/api/logout';
                }
            }

            // Session tamamen dolmuşsa
            if (remaining <= 0) {
                clearInterval(sessionCheckInterval);
                alert('⏰ Oturumunuz sona erdi.\n\nGüvenliğiniz için lütfen tekrar giriş yapın.');
                window.location.href = '/auth/login';
            }
        }, 30000); // 30 saniyede bir kontrol
    }

    // ========================================================================
    // DEVELOPER INFO MODAL
    // ========================================================================
    const devBtn = document.getElementById('devInfoBtn');
    const devModal = document.getElementById('devModal');
    const closeBtn = document.getElementById('closeModal');

    console.log('Dev Info Elements:', { devBtn, devModal, closeBtn });

    if (devBtn && devModal) {
        devBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            console.log('Dev button clicked!');
            devModal.classList.add('show');
            devModal.style.display = 'flex';
        });

        if (closeBtn) {
            closeBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('Close button clicked!');
                devModal.classList.remove('show');
                setTimeout(() => {
                    devModal.style.display = 'none';
                }, 300);
            });
        }

        devModal.addEventListener('click', (e) => {
            if (e.target === devModal) {
                console.log('Modal background clicked!');
                devModal.classList.remove('show');
                setTimeout(() => {
                    devModal.style.display = 'none';
                }, 300);
            }
        });
    } else {
        console.error('Dev Info elements not found!', { devBtn, devModal, closeBtn });
    }
});

// Make showAlert available globally as showNotification for compatibility
window.showNotification = showAlert;


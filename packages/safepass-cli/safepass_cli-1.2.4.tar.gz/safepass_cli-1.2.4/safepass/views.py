"""Views for SafePass"""

import json
import time
from datetime import datetime
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .models import User, PasswordCard
from .encryption import (
    generate_salt, hash_master_password, verify_master_password,
    derive_key_from_master_password, encrypt_data, decrypt_data
)
from .generator import generate_password, calculate_password_strength
from .analytics import get_dashboard_stats


def get_json_body(request):
    """Parse JSON body from request"""
    try:
        return json.loads(request.body.decode('utf-8'))
    except:
        return {}


def check_session_timeout(request):
    """Check if session has timed out"""
    last_activity = request.session.get('last_activity')
    if last_activity:
        elapsed = time.time() - last_activity
        timeout = getattr(settings, 'SESSION_TIMEOUT', 3600)
        if elapsed > timeout:
            request.session.flush()
            return True
    
    request.session['last_activity'] = time.time()
    return False


def get_session_user(request):
    """Get user from session"""
    if check_session_timeout(request):
        return None
    
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    try:
        user = User.objects.get(id=user_id)
        user.session_master_password = request.session.get('master_password', '')
        
        # SESSION_SAVE_EVERY_REQUEST = False olduğu için
        # Django'ya session'ın değiştiğini manuel söylememiz gerekiyor
        # Bu sayede last_activity güncellemesi kaydedilir
        request.session.modified = True
        
        return user
    except User.DoesNotExist:
        return None


def require_auth(view_func):
    """Decorator to require authentication"""
    def wrapper(request, *args, **kwargs):
        user = get_session_user(request)
        if not user:
            return redirect('/auth/login')
        return view_func(request, *args, **kwargs)
    return wrapper


def login_page(request):
    """Render login page"""
    user = get_session_user(request)
    if user:
        return redirect('/dashboard')
    request.session.flush()
    return render(request, 'auth/login.html')


def register_page(request):
    """Render register page"""
    if get_session_user(request):
        return redirect('/dashboard')
    return render(request, 'auth/register.html')


@require_auth
def dashboard_page(request):
    """Render dashboard page"""
    user = get_session_user(request)
    cards = PasswordCard.objects.filter(user=user)
    stats = get_dashboard_stats(user, cards)
    recent_cards = cards.order_by('-created_at')[:5]
    
    encryption_key = bytes(user.encryption_key_encrypted)
    for card in recent_cards:
        try:
            card.password = decrypt_data(bytes(card.password_encrypted), encryption_key)
        except:
            card.password = ''
    
    context = {
        'user': user,
        'stats': stats,
        'recent_cards': recent_cards
    }
    return render(request, 'dashboard.html', context)


@require_auth
def passwords_page(request):
    """Render passwords list page"""
    user = get_session_user(request)
    cards = PasswordCard.objects.filter(user=user).order_by('-updated_at')
    
    encryption_key = bytes(user.encryption_key_encrypted)
    for card in cards:
        try:
            card.password = decrypt_data(bytes(card.password_encrypted), encryption_key)
        except:
            card.password = ''
    
    context = {
        'user': user,
        'cards': cards
    }
    return render(request, 'cards.html', context)


@require_auth
def generator_page(request):
    """Render password generator page"""
    user = get_session_user(request)
    context = {'user': user}
    return render(request, 'generator.html', context)


@require_auth
def password_add_page(request):
    """Render add password page"""
    user = get_session_user(request)
    context = {'user': user}
    return render(request, 'card_add.html', context)


@require_auth
def password_edit_page(request, password_id):
    """Render edit password page"""
    user = get_session_user(request)
    try:
        card = PasswordCard.objects.get(id=password_id, user=user)
        encryption_key = bytes(user.encryption_key_encrypted)
        
        try:
            decrypted_password = decrypt_data(bytes(card.password_encrypted), encryption_key)
        except:
            decrypted_password = ''
        
        context = {
            'user': user,
            'card': card,
            'decrypted_password': decrypted_password
        }
        return render(request, 'password_edit.html', context)
    except PasswordCard.DoesNotExist:
        return redirect('/passwords')


@require_auth
def profile_page(request):
    """Render profile page"""
    user = get_session_user(request)
    context = {'user': user}
    return render(request, 'profile.html', context)


@require_auth
def help_page(request):
    """Render help page"""
    user = get_session_user(request)
    context = {'user': user}
    return render(request, 'help.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def api_register(request):
    """Register a new user"""
    data = get_json_body(request)
    username = data.get('username', '').strip()
    master_password = data.get('master_password', '')
    
    # Validation with specific error messages
    if not username:
        return JsonResponse({'error': 'Kullanıcı adı boş bırakılamaz', 'field': 'username'}, status=400)
    
    if not master_password:
        return JsonResponse({'error': 'Ana şifre boş bırakılamaz', 'field': 'master_password'}, status=400)
    
    if len(username) < 3:
        return JsonResponse({'error': 'Kullanıcı adı en az 3 karakter olmalı', 'field': 'username'}, status=400)
    
    if len(username) > 30:
        return JsonResponse({'error': 'Kullanıcı adı en fazla 30 karakter olabilir', 'field': 'username'}, status=400)
    
    if len(master_password) < 8:
        return JsonResponse({'error': 'Ana şifre en az 8 karakter olmalı', 'field': 'master_password'}, status=400)
    
    if len(master_password) > 128:
        return JsonResponse({'error': 'Ana şifre en fazla 128 karakter olabilir', 'field': 'master_password'}, status=400)
    
    # Check password strength
    has_upper = any(c.isupper() for c in master_password)
    has_lower = any(c.islower() for c in master_password)
    has_digit = any(c.isdigit() for c in master_password)
    
    if not (has_upper and has_lower and has_digit):
        return JsonResponse({
            'error': 'Zayıf şifre! Büyük harf, küçük harf ve rakam içermelidir',
            'field': 'master_password'
        }, status=400)
    
    if User.objects.filter(username=username).exists():
        return JsonResponse({'error': 'Bu kullanıcı adı zaten kullanılıyor! Bu bilgisayarda daha önce aynı kullanıcı adıyla hesap oluşturmuş olabilirsiniz. Farklı bir kullanıcı adı deneyin veya mevcut hesabınızla giriş yapın', 'field': 'username'}, status=400)
    
    salt = generate_salt()
    master_hash = hash_master_password(master_password, salt)
    encryption_key = derive_key_from_master_password(master_password, salt)
    
    user = User.objects.create(
        username=username,
        master_password_hash=master_hash,
        encryption_key_encrypted=encryption_key,
        salt=salt
    )
    
    request.session['user_id'] = user.id
    request.session['master_password'] = master_password
    request.session['last_activity'] = time.time()
    
    return JsonResponse({
        'success': True,
        'message': 'Kayıt başarılı',
        'user': {'id': user.id, 'username': user.username}
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_login(request):
    """Login user"""
    data = get_json_body(request)
    username = data.get('username', '').strip()
    master_password = data.get('master_password', '')
    
    # Validation
    if not username:
        return JsonResponse({'error': 'Kullanıcı adı boş bırakılamaz', 'field': 'username'}, status=400)
    
    if not master_password:
        return JsonResponse({'error': 'Şifre boş bırakılamaz', 'field': 'master_password'}, status=400)
    
    if len(master_password) < 8:
        return JsonResponse({'error': 'Şifre en az 8 karakter olmalıdır', 'field': 'master_password'}, status=400)
    
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return JsonResponse({
            'error': 'Bu kullanıcı adıyla bir hesap bulunamadı. Bu bilgisayarda henüz hesap oluşturmadıysanız, kayıt olmanız gerekiyor',
            'field': 'username'
        }, status=404)
    
    if not verify_master_password(master_password, bytes(user.salt), user.master_password_hash):
        return JsonResponse({
            'error': 'Yanlış şifre! Ana şifrenizi doğru girdiğinizden emin olun. Unuttusanız verilerinize erişemezsiniz',
            'field': 'master_password'
        }, status=401)
    
    request.session['user_id'] = user.id
    request.session['master_password'] = master_password
    request.session['last_activity'] = time.time()
    
    return JsonResponse({
        'success': True,
        'message': 'Giriş başarılı',
        'user': {'id': user.id, 'username': user.username}
    })


@csrf_exempt
@require_http_methods(["POST", "GET"])
def api_logout(request):
    """Logout user"""
    request.session.flush()
    if request.method == 'GET':
        return redirect('/auth/login')
    return JsonResponse({'success': True, 'message': 'Çıkış yapıldı'})


@csrf_exempt
@require_http_methods(["GET"])
def api_check_auth(request):
    """Check if user is authenticated"""
    user = get_session_user(request)
    if user:
        return JsonResponse({
            'authenticated': True,
            'user': {'id': user.id, 'username': user.username}
        })
    return JsonResponse({'authenticated': False})


@csrf_exempt
@require_http_methods(["GET", "POST"])
def api_passwords(request):
    """List all passwords or create new password"""
    user = get_session_user(request)
    if not user:
        return JsonResponse({'error': 'Oturum açmanız gerekiyor'}, status=401)
    
    if request.method == 'GET':
        cards = PasswordCard.objects.filter(user=user).order_by('-created_at')
        encryption_key = bytes(user.encryption_key_encrypted)
        
        cards_data = []
        for card in cards:
            try:
                password = decrypt_data(bytes(card.password_encrypted), encryption_key)
            except:
                password = ''
            
            cards_data.append({
                'id': card.id,
                'app_name': card.app_name,
                'username': card.username,
                'password': password,
                'url': card.url,
                'notes': card.notes,
                'category': card.category,
                'subcategory': card.subcategory or '',
                'created_at': card.created_at.isoformat(),
                'updated_at': card.updated_at.isoformat()
            })
        
        return JsonResponse({'cards': cards_data})
    
    elif request.method == 'POST':
        data = get_json_body(request)
        app_name = data.get('app_name', '').strip()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        url = data.get('url', '').strip()
        notes = data.get('notes', '')
        category = data.get('category', '')
        subcategory = data.get('subcategory', '')
        
        if not app_name or not password:
            return JsonResponse({'error': 'Uygulama adı ve şifre gerekli'}, status=400)
        
        encryption_key = bytes(user.encryption_key_encrypted)
        password_encrypted = encrypt_data(password, encryption_key)
        
        card = PasswordCard.objects.create(
            user=user,
            app_name=app_name,
            username=username,
            password_encrypted=password_encrypted,
            url=url,
            notes=notes,
            category=category,
            subcategory=subcategory
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Şifre oluşturuldu',
            'card': {
                'id': card.id,
                'app_name': card.app_name,
                'username': card.username
            }
        })


@csrf_exempt
@require_http_methods(["GET", "PUT"])
def api_password_detail(request, password_id):
    """Get or update a specific password"""
    user = get_session_user(request)
    if not user:
        return JsonResponse({'error': 'Oturum açmanız gerekiyor'}, status=401)
    
    try:
        card = PasswordCard.objects.get(id=password_id, user=user)
    except PasswordCard.DoesNotExist:
        return JsonResponse({'error': 'Şifre bulunamadı'}, status=404)
    
    if request.method == 'GET':
        encryption_key = bytes(user.encryption_key_encrypted)
        try:
            password = decrypt_data(bytes(card.password_encrypted), encryption_key)
        except:
            password = ''
        
        return JsonResponse({
            'card': {
                'id': card.id,
                'app_name': card.app_name,
                'username': card.username,
                'password': password,
                'notes': card.notes,
                'category': card.category,
                'subcategory': card.subcategory or '',
                'url': getattr(card, 'url', '')
            }
        })
    
    elif request.method == 'PUT':
        data = get_json_body(request)
        app_name = data.get('app_name', '').strip()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        url = data.get('url', '').strip()
        notes = data.get('notes', '')
        category = data.get('category', '')
        subcategory = data.get('subcategory', '')
        
        if not app_name or not password:
            return JsonResponse({'error': 'Uygulama adı ve şifre gerekli'}, status=400)
        
        # Save old password to history before updating
        from .models import PasswordHistory
        if card.password_encrypted:
            PasswordHistory.objects.create(
                card=card,
                password_encrypted=card.password_encrypted
            )
        
        card.app_name = app_name
        card.username = username
        card.url = url
        card.notes = notes
        card.category = category
        card.subcategory = subcategory
        
        encryption_key = bytes(user.encryption_key_encrypted)
        card.password_encrypted = encrypt_data(password, encryption_key)
        
        card.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Şifre güncellendi',
            'card': {
                'id': card.id,
                'app_name': card.app_name,
                'username': card.username
            }
        })


@csrf_exempt
@require_http_methods(["DELETE"])
def api_password_delete(request, password_id):
    """Delete a password"""
    user = get_session_user(request)
    if not user:
        return JsonResponse({'error': 'Oturum açmanız gerekiyor'}, status=401)
    
    try:
        card = PasswordCard.objects.get(id=password_id, user=user)
        card.delete()
        return JsonResponse({'success': True, 'message': 'Şifre silindi'})
    except PasswordCard.DoesNotExist:
        return JsonResponse({'error': 'Şifre bulunamadı'}, status=404)


@csrf_exempt
@require_http_methods(["POST"])
def api_generate_password(request):
    """Generate a random password"""
    data = get_json_body(request)
    length = data.get('length', 16)
    use_uppercase = data.get('uppercase', True)
    use_lowercase = data.get('lowercase', True)
    use_digits = data.get('numbers', True)
    use_symbols = data.get('symbols', True)
    exclude_similar = data.get('exclude_similar', False)
    
    password = generate_password(
        length=length,
        use_uppercase=use_uppercase,
        use_lowercase=use_lowercase,
        use_digits=use_digits,
        use_symbols=use_symbols,
        exclude_similar=exclude_similar
    )
    
    strength = calculate_password_strength(password)
    
    return JsonResponse({
        'success': True,
        'password': password,
        'strength': strength
    })


@csrf_exempt
@require_http_methods(["GET"])
def api_dashboard_stats(request):
    """Get dashboard statistics"""
    user = get_session_user(request)
    if not user:
        return JsonResponse({'error': 'Oturum açmanız gerekiyor'}, status=401)
    
    cards = PasswordCard.objects.filter(user=user)
    stats = get_dashboard_stats(user, cards)
    return JsonResponse(stats)


@csrf_exempt
@require_http_methods(["GET"])
def api_export_data(request):
    """Export all user data as JSON"""
    user = get_session_user(request)
    if not user:
        return JsonResponse({'error': 'Oturum açmanız gerekiyor'}, status=401)
    
    # Get master password from session
    master_password = request.session.get('master_password', '')
    if not master_password:
        return JsonResponse({'error': 'Oturum süresi dolmuş'}, status=401)
    
    # Derive encryption key from master password
    salt = bytes(user.salt)
    encryption_key = derive_key_from_master_password(master_password, salt)
    
    # Get all password cards
    cards = PasswordCard.objects.filter(user=user)
    
    # Build export data
    export_data = {
        'version': '1.0',
        'exported_at': datetime.now().isoformat(),
        'username': user.username,
        'passwords': []
    }
    
    for card in cards:
        try:
            # Decrypt password for export
            decrypted_password = decrypt_data(bytes(card.password_encrypted), encryption_key)
            
            export_data['passwords'].append({
                'app_name': card.app_name,
                'title': card.app_name,
                'username': card.username,
                'password': decrypted_password,
                'url': card.url,
                'website': card.url,
                'notes': card.notes,
                'category': card.category or '',
                'subcategory': card.subcategory or '',
                'created_at': card.created_at.isoformat(),
                'updated_at': card.updated_at.isoformat()
            })
        except Exception:
            # Skip cards that fail to decrypt
            continue
    
    # Create response with JSON file
    response = HttpResponse(
        json.dumps(export_data, indent=2, ensure_ascii=False),
        content_type='application/json'
    )
    filename = f'safepass_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response


@csrf_exempt
@require_http_methods(["POST"])
def api_import_data(request):
    """Import data from JSON file or JSON body"""
    user = get_session_user(request)
    if not user:
        return JsonResponse({'error': 'Oturum açmanız gerekiyor'}, status=401)
    
    # Get master password from session
    master_password = request.session.get('master_password', '')
    if not master_password:
        return JsonResponse({'error': 'Oturum süresi dolmuş'}, status=401)
    
    # File size limit: 10MB
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
    if 'file' in request.FILES:
        uploaded_file = request.FILES['file']
        if uploaded_file.size > MAX_FILE_SIZE:
            return JsonResponse({
                'error': f'Dosya boyutu çok büyük! Maksimum {MAX_FILE_SIZE // (1024 * 1024)}MB yüklenebilir'
            }, status=400)
    
    # Derive encryption key from master password
    salt = bytes(user.salt)
    encryption_key = derive_key_from_master_password(master_password, salt)
    
    try:
        # Check if data is coming from file upload or JSON body
        if 'file' in request.FILES:
            # File upload
            uploaded_file = request.FILES['file']
            file_content = uploaded_file.read().decode('utf-8')
            import_data = json.loads(file_content)
        else:
            # JSON body
            data = get_json_body(request)
            
            # Check if passwords are provided directly
            if 'passwords' in data:
                import_data = data
            else:
                return JsonResponse({'error': 'Dosya yüklenmedi'}, status=400)
        
        # Validate format
        if 'passwords' not in import_data or not isinstance(import_data['passwords'], list):
            return JsonResponse({'error': 'Geçersiz dosya formatı'}, status=400)
        
        # Import passwords
        imported_count = 0
        updated_count = 0
        skipped_count = 0
        skip_duplicates = import_data.get('skip_duplicates', True)
        
        for pwd_data in import_data['passwords']:
            try:
                # Get app_name from either 'title' or 'app_name'
                app_name = pwd_data.get('app_name', pwd_data.get('title', 'Bilinmeyen'))
                username_val = pwd_data.get('username', '')
                password_val = pwd_data.get('password', '')
                url_val = pwd_data.get('url', pwd_data.get('website', ''))
                category_val = pwd_data.get('category', 'genel')
                subcategory_val = pwd_data.get('subcategory', '')
                
                if not password_val:
                    skipped_count += 1
                    continue
                
                # Check if card with same details exists
                existing = PasswordCard.objects.filter(
                    user=user,
                    app_name=app_name,
                    username=username_val,
                    url=url_val,
                    category=category_val
                ).first()
                
                if existing:
                    # Card exists - check if password is different
                    try:
                        current_password = decrypt_data(bytes(existing.password_encrypted), encryption_key)
                        
                        if current_password != password_val:
                            # Password is different - update and save old password to history
                            from .models import PasswordHistory
                            
                            # Save current password to history
                            PasswordHistory.objects.create(
                                card=existing,
                                password_encrypted=existing.password_encrypted
                            )
                            
                            # Update with new password
                            new_encrypted_password = encrypt_data(password_val, encryption_key)
                            existing.password_encrypted = new_encrypted_password
                            existing.save()
                            
                            updated_count += 1
                        else:
                            # Same password - skip
                            skipped_count += 1
                    except:
                        # Decryption failed or other error - skip
                        skipped_count += 1
                else:
                    # New card - create it
                    encrypted_password = encrypt_data(password_val, encryption_key)
                    
                    PasswordCard.objects.create(
                        user=user,
                        app_name=app_name,
                        username=username_val,
                        password_encrypted=encrypted_password,
                        url=url_val,
                        notes=pwd_data.get('notes', ''),
                        category=category_val,
                        subcategory=subcategory_val
                    )
                    imported_count += 1
                
            except Exception as e:
                skipped_count += 1
                continue
        
        return JsonResponse({
            'success': True,
            'imported': imported_count,
            'updated': updated_count,
            'skipped': skipped_count,
            'total': len(import_data['passwords']),
            'message': f'{imported_count} yeni şifre eklendi, {updated_count} şifre güncellendi, {skipped_count} atlandı'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Geçersiz JSON formatı'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'İçe aktarma hatası: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["DELETE", "POST"])
def api_delete_account(request):
    """Delete user account and all associated data"""
    user = get_session_user(request)
    if not user:
        return JsonResponse({'error': 'Oturum açmanız gerekiyor'}, status=401)
    
    try:
        data = get_json_body(request)
        master_password = data.get('master_password', '')
        
        if not master_password:
            return JsonResponse({'error': 'Ana şifre gerekli'}, status=400)
        
        if not verify_master_password(master_password, bytes(user.salt), user.master_password_hash):
            return JsonResponse({'error': 'Yanlış ana şifre'}, status=401)
        
        username = user.username
        user.delete()
        
        request.session.flush()
        
        return JsonResponse({            'success': True,
            'message': f'{username} hesabı ve tüm verileri silindi'
        })
        
    except Exception as e:
        return JsonResponse({'error': f'Hesap silinirken hata: {str(e)}'}, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def api_password_history(request, password_id):
    """Get password history for a specific card"""
    user = get_session_user(request)
    if not user:
        return JsonResponse({'error': 'Oturum açmanız gerekiyor'}, status=401)
    
    try:
        card = PasswordCard.objects.get(id=password_id, user=user)
        from .models import PasswordHistory
        history = PasswordHistory.objects.filter(card=card).order_by('-changed_at')[:10]  # Last 10 changes
        
        encryption_key = bytes(user.encryption_key_encrypted)
        history_list = []
        
        for item in history:
            try:
                decrypted_password = decrypt_data(bytes(item.password_encrypted), encryption_key)
                history_list.append({
                    'id': item.id,
                    'password': decrypted_password,
                    'changed_at': item.changed_at.strftime('%d.%m.%Y %H:%M')
                })
            except:
                continue
        
        return JsonResponse({
            'success': True,
            'history': history_list
        })
    except PasswordCard.DoesNotExist:
        return JsonResponse({'error': 'Kart bulunamadı'}, status=404)


@require_auth
def import_export_page(request):
    """Import/Export page"""
    user = get_session_user(request)
    context = {'user': user}
    return render(request, 'import_export.html', context)


@csrf_exempt
@require_http_methods(["POST"])
def api_import_passwords(request):
    """Import passwords from KeePass CSV"""
    # Custom session-based authentication (tutarlılık için)
    user = get_session_user(request)
    if not user:
        return JsonResponse({'error': 'Oturum açmanız gerekiyor'}, status=401)
    
    # Get master password from session for encryption
    master_password = request.session.get('master_password', '')
    if not master_password:
        return JsonResponse({'error': 'Oturum süresi dolmuş'}, status=401)
    
    # File size limit: 10MB
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
    if request.body and len(request.body) > MAX_FILE_SIZE:
        return JsonResponse({
            'error': f'Dosya boyutu çok büyük! Maksimum {MAX_FILE_SIZE // (1024 * 1024)}MB yüklenebilir'
        }, status=400)
    
    try:
        # Debug logging
        print(f"[DEBUG] Request body: {request.body[:200]}")  # İlk 200 karakter
        data = get_json_body(request)
        print(f"[DEBUG] Parsed data keys: {data.keys() if data else 'None'}")
        print(f"[DEBUG] Passwords count: {len(data.get('passwords', []))}")
        
        passwords = data.get('passwords', [])
        skip_duplicates = data.get('skip_duplicates', True)
        
        if not passwords:
            # Debug bilgisi ile hata döndür
            return JsonResponse({
                'error': 'Şifre verisi sağlanmadı',
                'debug': {
                    'received_keys': list(data.keys()) if data else [],
                    'passwords_type': str(type(data.get('passwords'))),
                    'passwords_value': str(data.get('passwords'))[:100]
                }
            }, status=400)
        
        # Derive encryption key
        salt = bytes(user.salt)
        encryption_key = derive_key_from_master_password(master_password, salt)
        
        imported = 0
        updated = 0
        skipped = 0
        
        for pwd_data in passwords:
            try:
                # Model alanlarını düzelt: title → app_name, website → url
                app_name = pwd_data.get('title', pwd_data.get('app_name', 'Bilinmeyen'))
                username_val = pwd_data.get('username', '')
                password_val = pwd_data.get('password', '')
                url_val = pwd_data.get('website', pwd_data.get('url', ''))
                category_val = pwd_data.get('category', 'genel')
                subcategory_val = pwd_data.get('subcategory', '')
                notes_val = pwd_data.get('notes', '')
                
                if not password_val:
                    skipped += 1
                    continue
                
                # Check if card with same details exists
                existing = PasswordCard.objects.filter(
                    user=user,
                    app_name=app_name,
                    username=username_val,
                    url=url_val,
                    category=category_val
                ).first()
                
                if existing:
                    # Card exists - check if password is different
                    try:
                        current_password = decrypt_data(bytes(existing.password_encrypted), encryption_key)
                        
                        if current_password != password_val:
                            # Password is different - update and save old password to history
                            from .models import PasswordHistory
                            
                            # Save current password to history
                            PasswordHistory.objects.create(
                                card=existing,
                                password_encrypted=existing.password_encrypted
                            )
                            
                            # Update with new password
                            new_encrypted_password = encrypt_data(password_val, encryption_key)
                            existing.password_encrypted = new_encrypted_password
                            existing.save()
                            
                            updated += 1
                        else:
                            # Same password - skip
                            skipped += 1
                    except:
                        # Decryption failed or other error - skip
                        skipped += 1
                else:
                    # New card - create it
                    encrypted_password = encrypt_data(password_val, encryption_key)
                    
                    PasswordCard.objects.create(
                        user=user,
                        app_name=app_name,
                        username=username_val,
                        password_encrypted=encrypted_password,
                        url=url_val,
                        category=category_val,
                        subcategory=subcategory_val,
                        notes=notes_val
                    )
                    imported += 1
                
            except Exception as e:
                # Skip individual password errors
                skipped += 1
                continue
        
        return JsonResponse({
            'success': True,
            'imported': imported,
            'updated': updated,
            'skipped': skipped,
            'total': len(passwords),
            'message': f'{imported} yeni şifre eklendi, {updated} şifre güncellendi, {skipped} atlandı'
        })
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Geçersiz JSON formatı'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'İçe aktarma hatası: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_export_passwords(request):
    """Export passwords to JSON"""
    # Custom session-based authentication (tutarlılık için)
    user = get_session_user(request)
    if not user:
        return JsonResponse({'error': 'Oturum açmanız gerekiyor'}, status=401)
    
    # Get master password from session for decryption
    master_password = request.session.get('master_password', '')
    if not master_password:
        return JsonResponse({'error': 'Oturum süresi dolmuş'}, status=401)
    
    try:
        data = get_json_body(request)
        include_metadata = data.get('include_metadata', True)
        
        # Derive encryption key
        salt = bytes(user.salt)
        encryption_key = derive_key_from_master_password(master_password, salt)
        
        # Get all password cards
        cards = PasswordCard.objects.filter(user=user).order_by('-created_at')
        
        export_data = {
            'version': '1.2.3',
            'export_date': datetime.now().isoformat(),
            'total_passwords': cards.count(),
            'passwords': []
        }
        
        for card in cards:
            try:
                # Decrypt password using correct function
                decrypted_password = decrypt_data(bytes(card.password_encrypted), encryption_key)
                
                # Model alanlarını düzelt: app_name ve url kullan
                password_data = {
                    'title': card.app_name,  # Export'ta 'title' olarak gönder (uyumluluk için)
                    'app_name': card.app_name,  # Her iki formatı da destekle
                    'username': card.username,
                    'password': decrypted_password,
                    'website': card.url,  # Export'ta 'website' olarak gönder (uyumluluk için)
                    'url': card.url,  # Her iki formatı da destekle
                    'category': card.category or 'genel',
                    'subcategory': card.subcategory or ''
                }
                
                if include_metadata:
                    password_data.update({
                        'notes': card.notes or '',
                        'created_at': card.created_at.isoformat(),
                        'updated_at': card.updated_at.isoformat()
                    })
                
                export_data['passwords'].append(password_data)
                
            except Exception as e:
                # Skip cards that fail to decrypt
                continue
        
        return JsonResponse(export_data)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Geçersiz JSON formatı'}, status=400)
    except Exception as e:
        return JsonResponse({'error': f'Dışa aktarma hatası: {str(e)}'}, status=500)

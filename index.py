from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import hashlib
import secrets
import requests
import asyncio
import re
import os
import time
from datetime import datetime, timedelta
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
from user_agents import parse

app = Flask(__name__)
CORS(app)

# ============== Configuration ==============
TELEGRAM_API_ID = 27241932
TELEGRAM_API_HASH = "218edeae0f4cf9053d7dcbf3b1485048"
WALLET_ADDRESS = "0x8E00A980274Cfb22798290586d97F7D185E3092D"
BSCSCAN_API_KEY = "8BHURRRGKXD35BPGQZ8E94CVEVAUNMD9UF"
USDT_CONTRACT_BSC = "0x55d398326f99059fF775485246999027B3197955"
MIN_DEPOSIT = 1.5
MIN_WITHDRAWAL = 2.0
REFERRAL_BONUS = 0.01  # $0.01 per referral
FRAUD_THRESHOLD = 0.65  # 65% similarity = fraud

# Firebase
FIREBASE_URL = "https://lolaminig-afea4-default-rtdb.firebaseio.com"

# Thread pool
executor = ThreadPoolExecutor(max_workers=4)

# Session storage
phone_sessions = {}

# ============== Default Settings ==============
DEFAULT_SETTINGS = {
    'minDeposit': 1.5,
    'minWithdrawal': 2.0,
    'referralBonus': 0.01,
    'fraudThreshold': 0.65,
    'maintenanceMode': False,
    'registrationEnabled': True,
    'buyEnabled': True,
    'sellEnabled': True,
    'depositEnabled': True,
    'withdrawalEnabled': True
}

# ============== Default Countries ==============
DEFAULT_COUNTRIES = {
    'US': {'sell': 0.75, 'buy': 0.95, 'name': 'الولايات المتحدة', 'flag': 'us', 'code': '+1', 'enabled': True},
    'UK': {'sell': 0.80, 'buy': 1.00, 'name': 'المملكة المتحدة', 'flag': 'gb', 'code': '+44', 'enabled': True},
    'CA': {'sell': 0.25, 'buy': 0.45, 'name': 'كندا', 'flag': 'ca', 'code': '+1', 'enabled': True},
    'DE': {'sell': 1.50, 'buy': 1.70, 'name': 'ألمانيا', 'flag': 'de', 'code': '+49', 'enabled': True},
    'FR': {'sell': 1.20, 'buy': 1.40, 'name': 'فرنسا', 'flag': 'fr', 'code': '+33', 'enabled': True},
    'NL': {'sell': 1.00, 'buy': 1.20, 'name': 'هولندا', 'flag': 'nl', 'code': '+31', 'enabled': True},
    'PL': {'sell': 0.90, 'buy': 1.10, 'name': 'بولندا', 'flag': 'pl', 'code': '+48', 'enabled': True},
    'AU': {'sell': 1.00, 'buy': 1.20, 'name': 'أستراليا', 'flag': 'au', 'code': '+61', 'enabled': True},
    'ES': {'sell': 0.90, 'buy': 1.10, 'name': 'إسبانيا', 'flag': 'es', 'code': '+34', 'enabled': True},
    'IT': {'sell': 0.85, 'buy': 1.05, 'name': 'إيطاليا', 'flag': 'it', 'code': '+39', 'enabled': True},
    'BR': {'sell': 0.50, 'buy': 0.70, 'name': 'البرازيل', 'flag': 'br', 'code': '+55', 'enabled': True},
    'IN': {'sell': 0.30, 'buy': 0.50, 'name': 'الهند', 'flag': 'in', 'code': '+91', 'enabled': True},
    'RU': {'sell': 0.60, 'buy': 0.80, 'name': 'روسيا', 'flag': 'ru', 'code': '+7', 'enabled': True},
    'JP': {'sell': 1.30, 'buy': 1.50, 'name': 'اليابان', 'flag': 'jp', 'code': '+81', 'enabled': True},
    'KR': {'sell': 1.20, 'buy': 1.40, 'name': 'كوريا الجنوبية', 'flag': 'kr', 'code': '+82', 'enabled': True},
    'SA': {'sell': 0.80, 'buy': 1.00, 'name': 'السعودية', 'flag': 'sa', 'code': '+966', 'enabled': True},
    'AE': {'sell': 0.90, 'buy': 1.10, 'name': 'الإمارات', 'flag': 'ae', 'code': '+971', 'enabled': True},
    'EG': {'sell': 0.40, 'buy': 0.60, 'name': 'مصر', 'flag': 'eg', 'code': '+20', 'enabled': True},
    'TR': {'sell': 0.55, 'buy': 0.75, 'name': 'تركيا', 'flag': 'tr', 'code': '+90', 'enabled': True},
    'ID': {'sell': 0.35, 'buy': 0.55, 'name': 'إندونيسيا', 'flag': 'id', 'code': '+62', 'enabled': True},
    'MY': {'sell': 0.45, 'buy': 0.65, 'name': 'ماليزيا', 'flag': 'my', 'code': '+60', 'enabled': True},
    'PH': {'sell': 0.40, 'buy': 0.60, 'name': 'الفلبين', 'flag': 'ph', 'code': '+63', 'enabled': True},
    'TH': {'sell': 0.45, 'buy': 0.65, 'name': 'تايلاند', 'flag': 'th', 'code': '+66', 'enabled': True},
    'VN': {'sell': 0.35, 'buy': 0.55, 'name': 'فيتنام', 'flag': 'vn', 'code': '+84', 'enabled': True},
    'PK': {'sell': 0.30, 'buy': 0.50, 'name': 'باكستان', 'flag': 'pk', 'code': '+92', 'enabled': True},
    'NG': {'sell': 0.35, 'buy': 0.55, 'name': 'نيجيريا', 'flag': 'ng', 'code': '+234', 'enabled': True},
    'ZA': {'sell': 0.50, 'buy': 0.70, 'name': 'جنوب أفريقيا', 'flag': 'za', 'code': '+27', 'enabled': True},
    'MX': {'sell': 0.45, 'buy': 0.65, 'name': 'المكسيك', 'flag': 'mx', 'code': '+52', 'enabled': True},
    'AR': {'sell': 0.40, 'buy': 0.60, 'name': 'الأرجنتين', 'flag': 'ar', 'code': '+54', 'enabled': True},
    'CL': {'sell': 0.50, 'buy': 0.70, 'name': 'تشيلي', 'flag': 'cl', 'code': '+56', 'enabled': True},
    'CO': {'sell': 0.40, 'buy': 0.60, 'name': 'كولومبيا', 'flag': 'co', 'code': '+57', 'enabled': True},
    'SE': {'sell': 1.10, 'buy': 1.30, 'name': 'السويد', 'flag': 'se', 'code': '+46', 'enabled': True},
    'NO': {'sell': 1.15, 'buy': 1.35, 'name': 'النرويج', 'flag': 'no', 'code': '+47', 'enabled': True},
    'DK': {'sell': 1.05, 'buy': 1.25, 'name': 'الدنمارك', 'flag': 'dk', 'code': '+45', 'enabled': True},
    'FI': {'sell': 1.00, 'buy': 1.20, 'name': 'فنلندا', 'flag': 'fi', 'code': '+358', 'enabled': True},
    'CH': {'sell': 1.40, 'buy': 1.60, 'name': 'سويسرا', 'flag': 'ch', 'code': '+41', 'enabled': True},
    'AT': {'sell': 1.00, 'buy': 1.20, 'name': 'النمسا', 'flag': 'at', 'code': '+43', 'enabled': True},
    'BE': {'sell': 0.95, 'buy': 1.15, 'name': 'بلجيكا', 'flag': 'be', 'code': '+32', 'enabled': True},
    'PT': {'sell': 0.85, 'buy': 1.05, 'name': 'البرتغال', 'flag': 'pt', 'code': '+351', 'enabled': True},
    'GR': {'sell': 0.75, 'buy': 0.95, 'name': 'اليونان', 'flag': 'gr', 'code': '+30', 'enabled': True},
    'CZ': {'sell': 0.70, 'buy': 0.90, 'name': 'التشيك', 'flag': 'cz', 'code': '+420', 'enabled': True},
    'RO': {'sell': 0.55, 'buy': 0.75, 'name': 'رومانيا', 'flag': 'ro', 'code': '+40', 'enabled': True},
    'HU': {'sell': 0.60, 'buy': 0.80, 'name': 'المجر', 'flag': 'hu', 'code': '+36', 'enabled': True},
    'UA': {'sell': 0.45, 'buy': 0.65, 'name': 'أوكرانيا', 'flag': 'ua', 'code': '+380', 'enabled': True},
    'IL': {'sell': 1.00, 'buy': 1.20, 'name': 'إسرائيل', 'flag': 'il', 'code': '+972', 'enabled': True},
    'SG': {'sell': 1.10, 'buy': 1.30, 'name': 'سنغافورة', 'flag': 'sg', 'code': '+65', 'enabled': True},
    'HK': {'sell': 0.90, 'buy': 1.10, 'name': 'هونغ كونغ', 'flag': 'hk', 'code': '+852', 'enabled': True},
    'TW': {'sell': 0.85, 'buy': 1.05, 'name': 'تايوان', 'flag': 'tw', 'code': '+886', 'enabled': True},
    'NZ': {'sell': 0.95, 'buy': 1.15, 'name': 'نيوزيلندا', 'flag': 'nz', 'code': '+64', 'enabled': True},
    'IE': {'sell': 1.00, 'buy': 1.20, 'name': 'أيرلندا', 'flag': 'ie', 'code': '+353', 'enabled': True}
}

# ============== Firebase Helpers ==============
def fb_request(method, path, data=None):
    url = f"{FIREBASE_URL}/{path}.json"
    try:
        if method == 'GET':
            r = requests.get(url, timeout=10)
        elif method == 'POST':
            r = requests.post(url, json=data, timeout=10)
        elif method == 'PUT':
            r = requests.put(url, json=data, timeout=10)
        elif method == 'PATCH':
            r = requests.patch(url, json=data, timeout=10)
        elif method == 'DELETE':
            r = requests.delete(url, timeout=10)
        else:
            return None
        return r.json() if r.status_code == 200 else None
    except:
        return None

def fb_get(path): return fb_request('GET', path)
def fb_set(path, data): return fb_request('PUT', path, data)
def fb_push(path, data): 
    r = fb_request('POST', path, data)
    return r.get('name') if r else None
def fb_update(path, data): return fb_request('PATCH', path, data)
def fb_delete(path): return fb_request('DELETE', path)

# ============== Settings & Countries Helpers ==============
def get_settings():
    settings = fb_get('settings')
    if not settings:
        fb_set('settings', DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS
    return {**DEFAULT_SETTINGS, **settings}

def get_countries():
    countries = fb_get('countries')
    if not countries:
        fb_set('countries', DEFAULT_COUNTRIES)
        return DEFAULT_COUNTRIES
    return countries

def get_country_prices():
    return get_countries()

# ============== Fraud Detection ==============
def get_device_fingerprint(request):
    """Generate device fingerprint from multiple data points"""
    ua_string = request.headers.get('User-Agent', '')
    ua = parse(ua_string)
    
    fingerprint = {
        'ip': request.headers.get('X-Forwarded-For', request.headers.get('X-Real-IP', request.remote_addr)),
        'user_agent': ua_string,
        'browser': f"{ua.browser.family} {ua.browser.version_string}",
        'os': f"{ua.os.family} {ua.os.version_string}",
        'device': ua.device.family,
        'is_mobile': ua.is_mobile,
        'is_tablet': ua.is_tablet,
        'is_pc': ua.is_pc,
        'accept_language': request.headers.get('Accept-Language', ''),
        'accept_encoding': request.headers.get('Accept-Encoding', ''),
        'screen_data': request.headers.get('X-Screen-Data', ''),  # From client
        'timezone': request.headers.get('X-Timezone', ''),  # From client
        'canvas_hash': request.headers.get('X-Canvas-Hash', ''),  # From client
        'webgl_hash': request.headers.get('X-WebGL-Hash', ''),  # From client
        'audio_hash': request.headers.get('X-Audio-Hash', ''),  # From client
        'fonts_hash': request.headers.get('X-Fonts-Hash', ''),  # From client
        'plugins_hash': request.headers.get('X-Plugins-Hash', ''),  # From client
    }
    
    # Generate hash
    fp_string = json.dumps(fingerprint, sort_keys=True)
    fingerprint['hash'] = hashlib.sha256(fp_string.encode()).hexdigest()
    
    return fingerprint

def calculate_similarity(fp1, fp2):
    """Calculate similarity between two fingerprints"""
    if not fp1 or not fp2:
        return 0
    
    matches = 0
    total = 0
    
    # Weight different factors
    weights = {
        'ip': 3,  # High weight - same IP is suspicious
        'canvas_hash': 2,
        'webgl_hash': 2,
        'audio_hash': 2,
        'fonts_hash': 1.5,
        'plugins_hash': 1.5,
        'screen_data': 1.5,
        'timezone': 1,
        'browser': 1,
        'os': 1,
        'device': 1,
        'user_agent': 0.5,
    }
    
    for key, weight in weights.items():
        total += weight
        if fp1.get(key) and fp2.get(key):
            if fp1[key] == fp2[key]:
                matches += weight
    
    return matches / total if total > 0 else 0

def check_fraud(user_id, fingerprint):
    """Check if this is a fraudulent referral attempt"""
    settings = get_settings()
    threshold = settings.get('fraudThreshold', FRAUD_THRESHOLD)
    
    # Get all fingerprints
    fingerprints = fb_get('fingerprints') or {}
    
    for fp_id, fp_data in fingerprints.items():
        if fp_data and fp_data.get('userId') != user_id:
            similarity = calculate_similarity(fingerprint, fp_data.get('data', {}))
            if similarity >= threshold:
                return True, fp_data.get('userId'), similarity
    
    return False, None, 0

def save_fingerprint(user_id, fingerprint):
    """Save user fingerprint"""
    fb_push('fingerprints', {
        'userId': user_id,
        'data': fingerprint,
        'createdAt': datetime.now().isoformat()
    })

# ============== Helpers ==============
def generate_token():
    return secrets.token_hex(32)

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def generate_referral_code():
    return secrets.token_urlsafe(8)

def detect_country(phone):
    phone = phone.replace(' ', '').replace('-', '')
    countries = get_country_prices()
    
    # Sort by code length descending to match longer codes first
    sorted_countries = sorted(
        [(k, v['code']) for k, v in countries.items()],
        key=lambda x: len(x[1]),
        reverse=True
    )
    
    for country_code, phone_code in sorted_countries:
        if phone.startswith(phone_code):
            return country_code
    
    return None

def verify_token_decorator(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        token = auth.replace('Bearer ', '') if auth.startswith('Bearer ') else ''
        if not token:
            return jsonify({'success': False, 'error': 'يرجى تسجيل الدخول'}), 401
        users = fb_get('users') or {}
        for uid, udata in users.items():
            if udata and udata.get('token') == token:
                if udata.get('banned'):
                    return jsonify({'success': False, 'error': 'حسابك محظور'}), 403
                request.user_id = uid
                request.user = udata
                return f(*args, **kwargs)
        return jsonify({'success': False, 'error': 'جلسة غير صالحة'}), 401
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Simple admin check - in production use proper auth
        admin_key = request.headers.get('X-Admin-Key', '')
        if admin_key != 'admin_secret_key_2024':
            # Check query param for backward compatibility
            if request.args.get('admin') != 'true':
                return jsonify({'success': False, 'error': 'غير مصرح'}), 403
        return f(*args, **kwargs)
    return decorated

# ============== Telegram Functions ==============
def run_telegram_async(coro):
    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    future = executor.submit(run)
    return future.result(timeout=60)

async def tg_send_code(phone):
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    from telethon.errors import FloodWaitError
    
    client = TelegramClient(
        StringSession(),
        TELEGRAM_API_ID,
        TELEGRAM_API_HASH,
        device_model="Samsung Galaxy S21",
        system_version="Android 12",
        app_version="8.9.0"
    )
    
    try:
        await client.connect()
        result = await client.send_code_request(phone)
        session_str = client.session.save()
        
        phone_sessions[phone] = {
            'session': session_str,
            'phone_code_hash': result.phone_code_hash,
            'timestamp': datetime.now().isoformat()
        }
        
        return True, "تم إرسال الكود"
    except FloodWaitError as e:
        return False, f"انتظر {e.seconds} ثانية"
    except Exception as e:
        return False, str(e)
    finally:
        if client.is_connected():
            await client.disconnect()

async def tg_verify_code(phone, code):
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    from telethon.errors import PhoneCodeInvalidError, PhoneCodeExpiredError, SessionPasswordNeededError
    
    if phone not in phone_sessions:
        return False, "اطلب كود جديد", None
    
    session_data = phone_sessions[phone]
    
    client = TelegramClient(
        StringSession(session_data['session']),
        TELEGRAM_API_ID,
        TELEGRAM_API_HASH
    )
    
    try:
        await client.connect()
        await client.sign_in(
            phone=phone,
            code=code,
            phone_code_hash=session_data['phone_code_hash']
        )
        final_session = client.session.save()
        del phone_sessions[phone]
        return True, "تم التحقق", final_session
    except PhoneCodeInvalidError:
        return False, "الكود غير صحيح", None
    except PhoneCodeExpiredError:
        if phone in phone_sessions:
            del phone_sessions[phone]
        return False, "انتهت صلاحية الكود", None
    except SessionPasswordNeededError:
        return False, "الحساب محمي بـ 2FA", None
    except Exception as e:
        return False, str(e), None
    finally:
        if client.is_connected():
            await client.disconnect()

async def tg_get_messages(session_string):
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    
    client = TelegramClient(
        StringSession(session_string),
        TELEGRAM_API_ID,
        TELEGRAM_API_HASH
    )
    
    messages = []
    try:
        await client.connect()
        if not await client.is_user_authorized():
            return []
        
        async for msg in client.iter_messages(777000, limit=10):
            if msg.message:
                codes = re.findall(r'\b\d{5,6}\b', msg.message)
                if codes:
                    messages.append({
                        'code': codes[0],
                        'text': msg.message[:100],
                        'timestamp': msg.date.isoformat()
                    })
        return messages
    except:
        return []
    finally:
        if client.is_connected():
            await client.disconnect()

async def tg_logout(session_string):
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    
    client = TelegramClient(
        StringSession(session_string),
        TELEGRAM_API_ID,
        TELEGRAM_API_HASH
    )
    
    try:
        await client.connect()
        await client.log_out()
        return True
    except:
        return False
    finally:
        if client.is_connected():
            await client.disconnect()

def verify_bsc_tx(txid):
    try:
        url = "https://api.bscscan.com/api"
        params = {
            'module': 'proxy',
            'action': 'eth_getTransactionByHash',
            'txhash': txid,
            'apikey': BSCSCAN_API_KEY
        }
        r = requests.get(url, params=params, timeout=15)
        data = r.json()
        
        if not data.get('result'):
            return False, 0
        
        tx = data['result']
        to_addr = tx.get('to', '').lower()
        
        if to_addr == USDT_CONTRACT_BSC.lower():
            input_data = tx.get('input', '')
            if input_data.startswith('0xa9059cbb'):
                recipient = '0x' + input_data[34:74]
                if recipient.lower() == WALLET_ADDRESS.lower():
                    amount_hex = input_data[74:138]
                    amount = int(amount_hex, 16) / (10 ** 18)
                    settings = get_settings()
                    if amount >= settings.get('minDeposit', MIN_DEPOSIT):
                        return True, amount
        
        if to_addr == WALLET_ADDRESS.lower():
            value = int(tx.get('value', '0'), 16) / (10 ** 18)
            if value >= 0.004:
                return True, value * 350
        
        return False, 0
    except:
        return False, 0

# ============== Routes ==============

@app.route('/')
def serve_index():
    return send_file('index.html')

# ============== Stats ==============
@app.route('/api/stats')
def get_stats():
    numbers = fb_get('numbers') or {}
    users = fb_get('users') or {}
    purchases = fb_get('purchases') or {}
    countries = get_countries()
    
    available = sum(1 for n in numbers.values() if n and n.get('status') == 'available')
    sold = sum(1 for n in numbers.values() if n and n.get('status') == 'sold')
    total_purchases = len([p for p in purchases.values() if p])
    
    return jsonify({
        'availableNumbers': available,
        'soldNumbers': sold,
        'totalUsers': len([u for u in users.values() if u]),
        'totalPurchases': total_purchases,
        'totalCountries': len([c for c in countries.values() if c and c.get('enabled', True)])
    })

@app.route('/api/countries')
def get_countries_api():
    numbers = fb_get('numbers') or {}
    countries = get_countries()
    
    result = []
    for code, info in countries.items():
        if info and info.get('enabled', True):
            count = sum(1 for n in numbers.values() 
                       if n and n.get('status') == 'available' and n.get('country') == code)
            result.append({
                'code': code,
                'name': info['name'],
                'flag': info['flag'],
                'phoneCode': info['code'],
                'buyPrice': info['buy'],
                'sellPrice': info['sell'],
                'stock': count
            })
    
    # Sort by stock (available first)
    result.sort(key=lambda x: (-x['stock'], x['name']))
    
    return jsonify({'countries': result})

@app.route('/api/settings')
def get_public_settings():
    settings = get_settings()
    return jsonify({
        'maintenanceMode': settings.get('maintenanceMode', False),
        'registrationEnabled': settings.get('registrationEnabled', True),
        'buyEnabled': settings.get('buyEnabled', True),
        'sellEnabled': settings.get('sellEnabled', True),
        'referralBonus': settings.get('referralBonus', REFERRAL_BONUS)
    })

# ============== Auth ==============
@app.route('/api/auth/register', methods=['POST'])
def register():
    settings = get_settings()
    if not settings.get('registrationEnabled', True):
        return jsonify({'success': False, 'error': 'التسجيل مغلق حالياً'})
    
    data = request.json or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    referral_code = data.get('referralCode', '').strip()
    
    if not all([username, email, password]):
        return jsonify({'success': False, 'error': 'جميع الحقول مطلوبة'})
    if len(password) < 6:
        return jsonify({'success': False, 'error': 'كلمة المرور قصيرة'})
    if len(username) < 3:
        return jsonify({'success': False, 'error': 'اسم المستخدم قصير'})
    
    users = fb_get('users') or {}
    for u in users.values():
        if u and u.get('email') == email:
            return jsonify({'success': False, 'error': 'البريد مستخدم'})
        if u and u.get('username', '').lower() == username.lower():
            return jsonify({'success': False, 'error': 'اسم المستخدم مستخدم'})
    
    # Get device fingerprint
    fingerprint = get_device_fingerprint(request)
    
    token = generate_token()
    user_ref_code = generate_referral_code()
    
    new_user = {
        'username': username,
        'email': email,
        'password': hash_password(password),
        'balance': 0.0,
        'token': token,
        'referralCode': user_ref_code,
        'referredBy': None,
        'referralCount': 0,
        'referralEarnings': 0.0,
        'totalDeposits': 0.0,
        'totalPurchases': 0,
        'totalSales': 0,
        'banned': False,
        'banReason': None,
        'role': 'user',
        'createdAt': datetime.now().isoformat(),
        'lastLogin': datetime.now().isoformat(),
        'fingerprint': fingerprint['hash']
    }
    
    uid = fb_push('users', new_user)
    
    if uid:
        # Save fingerprint
        save_fingerprint(uid, fingerprint)
        
        # Process referral
        if referral_code:
            # Find referrer
            referrer_id = None
            referrer = None
            for ref_uid, ref_user in users.items():
                if ref_user and ref_user.get('referralCode') == referral_code:
                    referrer_id = ref_uid
                    referrer = ref_user
                    break
            
            if referrer:
                # Check for fraud
                is_fraud, fraud_user_id, similarity = check_fraud(uid, fingerprint)
                
                if is_fraud:
                    # Ban the new account
                    fb_update(f'users/{uid}', {
                        'banned': True,
                        'banReason': f'نشاط احتيالي مكتشف (تشابه {similarity*100:.0f}%)'
                    })
                    
                    # Log fraud attempt
                    fb_push('fraud_logs', {
                        'newUserId': uid,
                        'matchedUserId': fraud_user_id,
                        'referrerId': referrer_id,
                        'similarity': similarity,
                        'fingerprint': fingerprint,
                        'createdAt': datetime.now().isoformat()
                    })
                    
                    return jsonify({'success': False, 'error': 'تم اكتشاف نشاط مشبوه. تم حظر الحساب.'})
                
                # Valid referral - give bonus
                bonus = settings.get('referralBonus', REFERRAL_BONUS)
                fb_update(f'users/{referrer_id}', {
                    'balance': referrer.get('balance', 0) + bonus,
                    'referralCount': referrer.get('referralCount', 0) + 1,
                    'referralEarnings': referrer.get('referralEarnings', 0) + bonus
                })
                
                fb_update(f'users/{uid}', {'referredBy': referrer_id})
                
                # Log referral
                fb_push('referral_logs', {
                    'referrerId': referrer_id,
                    'referredId': uid,
                    'bonus': bonus,
                    'createdAt': datetime.now().isoformat()
                })
        
        return jsonify({
            'success': True,
            'user': {
                'id': uid,
                'username': username,
                'email': email,
                'balance': 0.0,
                'token': token,
                'referralCode': user_ref_code
            }
        })
    
    return jsonify({'success': False, 'error': 'حدث خطأ'})

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    users = fb_get('users') or {}
    for uid, u in users.items():
        if u and u.get('email') == email and u.get('password') == hash_password(password):
            if u.get('banned'):
                return jsonify({'success': False, 'error': f"حسابك محظور: {u.get('banReason', 'غير محدد')}"})
            
            token = generate_token()
            fb_update(f'users/{uid}', {
                'token': token,
                'lastLogin': datetime.now().isoformat()
            })
            
            return jsonify({
                'success': True,
                'user': {
                    'id': uid,
                    'username': u.get('username'),
                    'email': email,
                    'balance': u.get('balance', 0),
                    'token': token,
                    'referralCode': u.get('referralCode'),
                    'referralCount': u.get('referralCount', 0),
                    'referralEarnings': u.get('referralEarnings', 0)
                }
            })
    
    return jsonify({'success': False, 'error': 'بيانات غير صحيحة'})

@app.route('/api/auth/me')
@verify_token_decorator
def get_me():
    return jsonify({
        'success': True,
        'user': {
            'id': request.user_id,
            'username': request.user.get('username'),
            'email': request.user.get('email'),
            'balance': request.user.get('balance', 0),
            'referralCode': request.user.get('referralCode'),
            'referralCount': request.user.get('referralCount', 0),
            'referralEarnings': request.user.get('referralEarnings', 0),
            'totalPurchases': request.user.get('totalPurchases', 0),
            'totalSales': request.user.get('totalSales', 0)
        }
    })

# ============== Buy ==============
@app.route('/api/buy', methods=['POST'])
@verify_token_decorator
def buy_number():
    settings = get_settings()
    if not settings.get('buyEnabled', True):
        return jsonify({'success': False, 'error': 'الشراء مغلق حالياً'})
    
    data = request.json or {}
    country = data.get('country')
    
    countries = get_country_prices()
    if country not in countries:
        return jsonify({'success': False, 'error': 'دولة غير مدعومة'})
    
    country_info = countries[country]
    if not country_info.get('enabled', True):
        return jsonify({'success': False, 'error': 'هذه الدولة غير متاحة حالياً'})
    
    price = country_info['buy']
    balance = request.user.get('balance', 0)
    
    if balance < price:
        return jsonify({'success': False, 'error': 'رصيد غير كافٍ'})
    
    numbers = fb_get('numbers') or {}
    target = None
    target_id = None
    
    for nid, n in numbers.items():
        if n and n.get('status') == 'available' and n.get('country') == country:
            target = n
            target_id = nid
            break
    
    if not target:
        return jsonify({'success': False, 'error': 'لا توجد أرقام متاحة'})
    
    new_balance = balance - price
    fb_update(f'users/{request.user_id}', {
        'balance': new_balance,
        'totalPurchases': request.user.get('totalPurchases', 0) + 1
    })
    
    purchase_id = fb_push('purchases', {
        'userId': request.user_id,
        'numberId': target_id,
        'phone': target['phone'],
        'country': country,
        'price': price,
        'session': target.get('session'),
        'status': 'active',
        'createdAt': datetime.now().isoformat()
    })
    
    fb_update(f'numbers/{target_id}', {'status': 'sold', 'soldTo': request.user_id})
    
    return jsonify({
        'success': True,
        'purchaseId': purchase_id,
        'phone': target['phone'],
        'newBalance': new_balance
    })

@app.route('/api/messages/<purchase_id>')
@verify_token_decorator
def get_messages(purchase_id):
    purchase = fb_get(f'purchases/{purchase_id}')
    if not purchase or purchase.get('userId') != request.user_id:
        return jsonify({'success': False, 'error': 'غير موجود'})
    
    session = purchase.get('session')
    if not session:
        return jsonify({'success': True, 'messages': []})
    
    try:
        messages = run_telegram_async(tg_get_messages(session))
        return jsonify({'success': True, 'messages': messages})
    except:
        return jsonify({'success': True, 'messages': []})

@app.route('/api/complete', methods=['POST'])
@verify_token_decorator
def complete_purchase():
    data = request.json or {}
    purchase_id = data.get('purchaseId')
    
    purchase = fb_get(f'purchases/{purchase_id}')
    if not purchase or purchase.get('userId') != request.user_id:
        return jsonify({'success': False, 'error': 'غير موجود'})
    
    session = purchase.get('session')
    if session:
        try:
            run_telegram_async(tg_logout(session))
        except:
            pass
    
    fb_update(f'purchases/{purchase_id}', {'status': 'completed', 'completedAt': datetime.now().isoformat()})
    return jsonify({'success': True})

@app.route('/api/my-numbers')
@verify_token_decorator
def my_numbers():
    purchases = fb_get('purchases') or {}
    result = []
    for pid, p in purchases.items():
        if p and p.get('userId') == request.user_id:
            result.append({
                'id': pid, 'phone': p.get('phone'), 'country': p.get('country'),
                'status': p.get('status'), 'createdAt': p.get('createdAt')
            })
    result.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
    return jsonify({'success': True, 'numbers': result})

# ============== Sell ==============
@app.route('/api/sell/send-code', methods=['POST'])
@verify_token_decorator
def sell_send_code():
    settings = get_settings()
    if not settings.get('sellEnabled', True):
        return jsonify({'success': False, 'error': 'البيع مغلق حالياً'})
    
    data = request.json or {}
    phone = data.get('phone', '').strip()
    
    if not phone.startswith('+'):
        return jsonify({'success': False, 'error': 'الرقم يجب أن يبدأ بـ +'})
    
    country = detect_country(phone)
    if not country:
        return jsonify({'success': False, 'error': 'دولة غير مدعومة'})
    
    countries = get_country_prices()
    country_info = countries.get(country)
    if not country_info or not country_info.get('enabled', True):
        return jsonify({'success': False, 'error': 'هذه الدولة غير متاحة حالياً'})
    
    try:
        success, msg = run_telegram_async(tg_send_code(phone))
        if success:
            return jsonify({
                'success': True,
                'country': country,
                'countryName': country_info['name'],
                'price': country_info['sell']
            })
        return jsonify({'success': False, 'error': msg})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/sell/verify', methods=['POST'])
@verify_token_decorator
def sell_verify():
    data = request.json or {}
    phone = data.get('phone', '').strip()
    code = data.get('code', '').strip()
    
    if not phone or not code:
        return jsonify({'success': False, 'error': 'بيانات ناقصة'})
    
    country = detect_country(phone)
    if not country:
        return jsonify({'success': False, 'error': 'دولة غير مدعومة'})
    
    countries = get_country_prices()
    country_info = countries.get(country)
    
    try:
        success, msg, session = run_telegram_async(tg_verify_code(phone, code))
        if not success:
            return jsonify({'success': False, 'error': msg})
        
        price = country_info['sell']
        fb_push('sell_requests', {
            'userId': request.user_id,
            'username': request.user.get('username'),
            'phone': phone,
            'country': country,
            'price': price,
            'session': session,
            'status': 'pending',
            'createdAt': datetime.now().isoformat()
        })
        
        return jsonify({'success': True, 'message': 'تم إرسال الطلب'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ============== Deposit ==============
@app.route('/api/deposit', methods=['POST'])
@verify_token_decorator
def verify_deposit():
    settings = get_settings()
    if not settings.get('depositEnabled', True):
        return jsonify({'success': False, 'error': 'الإيداع مغلق حالياً'})
    
    data = request.json or {}
    txid = data.get('txid', '').strip()
    
    if not txid.startswith('0x') or len(txid) < 60:
        return jsonify({'success': False, 'error': 'TXID غير صحيح'})
    
    deposits = fb_get('deposits') or {}
    for d in deposits.values():
        if d and d.get('txid') == txid:
            return jsonify({'success': False, 'error': 'المعاملة مستخدمة'})
    
    valid, amount = verify_bsc_tx(txid)
    if not valid:
        return jsonify({'success': False, 'error': 'المعاملة غير صالحة'})
    
    fb_push('deposits', {
        'userId': request.user_id,
        'txid': txid,
        'amount': amount,
        'status': 'approved',
        'createdAt': datetime.now().isoformat()
    })
    
    new_balance = request.user.get('balance', 0) + amount
    fb_update(f'users/{request.user_id}', {
        'balance': new_balance,
        'totalDeposits': request.user.get('totalDeposits', 0) + amount
    })
    
    return jsonify({'success': True, 'amount': amount, 'newBalance': new_balance})

# ============== Withdrawal ==============
@app.route('/api/withdraw', methods=['POST'])
@verify_token_decorator
def request_withdrawal():
    settings = get_settings()
    if not settings.get('withdrawalEnabled', True):
        return jsonify({'success': False, 'error': 'السحب مغلق حالياً'})
    
    data = request.json or {}
    amount = float(data.get('amount', 0))
    address = data.get('address', '').strip()
    
    min_withdrawal = settings.get('minWithdrawal', MIN_WITHDRAWAL)
    
    if amount < min_withdrawal:
        return jsonify({'success': False, 'error': f'الحد الأدنى للسحب ${min_withdrawal}'})
    
    if not address.startswith('0x') or len(address) != 42:
        return jsonify({'success': False, 'error': 'عنوان غير صحيح'})
    
    balance = request.user.get('balance', 0)
    if balance < amount:
        return jsonify({'success': False, 'error': 'رصيد غير كافٍ'})
    
    # Deduct balance
    new_balance = balance - amount
    fb_update(f'users/{request.user_id}', {'balance': new_balance})
    
    # Create withdrawal request
    fb_push('withdrawals', {
        'userId': request.user_id,
        'username': request.user.get('username'),
        'amount': amount,
        'address': address,
        'status': 'pending',
        'createdAt': datetime.now().isoformat()
    })
    
    return jsonify({'success': True, 'newBalance': new_balance})

@app.route('/api/my-withdrawals')
@verify_token_decorator
def my_withdrawals():
    withdrawals = fb_get('withdrawals') or {}
    result = []
    for wid, w in withdrawals.items():
        if w and w.get('userId') == request.user_id:
            result.append({
                'id': wid,
                'amount': w.get('amount'),
                'address': w.get('address'),
                'status': w.get('status'),
                'createdAt': w.get('createdAt')
            })
    result.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
    return jsonify({'success': True, 'withdrawals': result})

# ============== Admin Routes ==============

@app.route('/api/admin/dashboard')
@admin_required
def admin_dashboard():
    users = fb_get('users') or {}
    numbers = fb_get('numbers') or {}
    purchases = fb_get('purchases') or {}
    deposits = fb_get('deposits') or {}
    withdrawals = fb_get('withdrawals') or {}
    sell_requests = fb_get('sell_requests') or {}
    
    total_balance = sum(u.get('balance', 0) for u in users.values() if u)
    total_deposits = sum(d.get('amount', 0) for d in deposits.values() if d and d.get('status') == 'approved')
    pending_withdrawals = sum(w.get('amount', 0) for w in withdrawals.values() if w and w.get('status') == 'pending')
    
    return jsonify({
        'success': True,
        'stats': {
            'totalUsers': len([u for u in users.values() if u]),
            'bannedUsers': len([u for u in users.values() if u and u.get('banned')]),
            'availableNumbers': len([n for n in numbers.values() if n and n.get('status') == 'available']),
            'soldNumbers': len([n for n in numbers.values() if n and n.get('status') == 'sold']),
            'totalPurchases': len([p for p in purchases.values() if p]),
            'pendingSells': len([s for s in sell_requests.values() if s and s.get('status') == 'pending']),
            'pendingWithdrawals': len([w for w in withdrawals.values() if w and w.get('status') == 'pending']),
            'totalBalance': total_balance,
            'totalDeposits': total_deposits,
            'pendingWithdrawalsAmount': pending_withdrawals
        }
    })

@app.route('/api/admin/users')
@admin_required
def admin_users():
    users = fb_get('users') or {}
    result = []
    for uid, u in users.items():
        if u:
            result.append({
                'id': uid,
                'username': u.get('username'),
                'email': u.get('email'),
                'balance': u.get('balance', 0),
                'referralCode': u.get('referralCode'),
                'referralCount': u.get('referralCount', 0),
                'referralEarnings': u.get('referralEarnings', 0),
                'totalDeposits': u.get('totalDeposits', 0),
                'totalPurchases': u.get('totalPurchases', 0),
                'banned': u.get('banned', False),
                'banReason': u.get('banReason'),
                'createdAt': u.get('createdAt'),
                'lastLogin': u.get('lastLogin')
            })
    result.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
    return jsonify({'success': True, 'users': result})

@app.route('/api/admin/user/<user_id>', methods=['GET', 'PATCH'])
@admin_required
def admin_user(user_id):
    if request.method == 'GET':
        user = fb_get(f'users/{user_id}')
        if not user:
            return jsonify({'success': False, 'error': 'غير موجود'})
        return jsonify({'success': True, 'user': user})
    
    elif request.method == 'PATCH':
        data = request.json or {}
        updates = {}
        
        if 'balance' in data:
            updates['balance'] = float(data['balance'])
        if 'banned' in data:
            updates['banned'] = bool(data['banned'])
        if 'banReason' in data:
            updates['banReason'] = data['banReason']
        if 'role' in data:
            updates['role'] = data['role']
        
        if updates:
            fb_update(f'users/{user_id}', updates)
            
            # Log admin action
            fb_push('admin_logs', {
                'action': 'update_user',
                'userId': user_id,
                'updates': updates,
                'createdAt': datetime.now().isoformat()
            })
        
        return jsonify({'success': True})

@app.route('/api/admin/user/<user_id>/ban', methods=['POST'])
@admin_required
def admin_ban_user(user_id):
    data = request.json or {}
    reason = data.get('reason', 'غير محدد')
    
    fb_update(f'users/{user_id}', {
        'banned': True,
        'banReason': reason,
        'bannedAt': datetime.now().isoformat()
    })
    
    fb_push('admin_logs', {
        'action': 'ban_user',
        'userId': user_id,
        'reason': reason,
        'createdAt': datetime.now().isoformat()
    })
    
    return jsonify({'success': True})

@app.route('/api/admin/user/<user_id>/unban', methods=['POST'])
@admin_required
def admin_unban_user(user_id):
    fb_update(f'users/{user_id}', {
        'banned': False,
        'banReason': None
    })
    
    fb_push('admin_logs', {
        'action': 'unban_user',
        'userId': user_id,
        'createdAt': datetime.now().isoformat()
    })
    
    return jsonify({'success': True})

@app.route('/api/admin/user/<user_id>/add-balance', methods=['POST'])
@admin_required
def admin_add_balance(user_id):
    data = request.json or {}
    amount = float(data.get('amount', 0))
    reason = data.get('reason', '')
    
    user = fb_get(f'users/{user_id}')
    if not user:
        return jsonify({'success': False, 'error': 'غير موجود'})
    
    new_balance = user.get('balance', 0) + amount
    fb_update(f'users/{user_id}', {'balance': new_balance})
    
    fb_push('admin_logs', {
        'action': 'add_balance',
        'userId': user_id,
        'amount': amount,
        'reason': reason,
        'createdAt': datetime.now().isoformat()
    })
    
    return jsonify({'success': True, 'newBalance': new_balance})

# ============== Admin Countries ==============
@app.route('/api/admin/countries')
@admin_required
def admin_countries():
    countries = get_countries()
    result = []
    for code, info in countries.items():
        if info:
            result.append({
                'code': code,
                'name': info.get('name'),
                'flag': info.get('flag'),
                'phoneCode': info.get('code'),
                'buyPrice': info.get('buy'),
                'sellPrice': info.get('sell'),
                'enabled': info.get('enabled', True)
            })
    return jsonify({'success': True, 'countries': result})

@app.route('/api/admin/country', methods=['POST'])
@admin_required
def admin_add_country():
    data = request.json or {}
    
    code = data.get('code', '').upper()
    name = data.get('name', '')
    flag = data.get('flag', code.lower())
    phone_code = data.get('phoneCode', '')
    buy_price = float(data.get('buyPrice', 1.0))
    sell_price = float(data.get('sellPrice', 0.8))
    
    if not all([code, name, phone_code]):
        return jsonify({'success': False, 'error': 'بيانات ناقصة'})
    
    countries = get_countries()
    countries[code] = {
        'name': name,
        'flag': flag,
        'code': phone_code,
        'buy': buy_price,
        'sell': sell_price,
        'enabled': True
    }
    
    fb_set('countries', countries)
    
    fb_push('admin_logs', {
        'action': 'add_country',
        'countryCode': code,
        'createdAt': datetime.now().isoformat()
    })
    
    return jsonify({'success': True})

@app.route('/api/admin/country/<code>', methods=['PATCH', 'DELETE'])
@admin_required
def admin_update_country(code):
    countries = get_countries()
    
    if code not in countries:
        return jsonify({'success': False, 'error': 'غير موجود'})
    
    if request.method == 'DELETE':
        del countries[code]
        fb_set('countries', countries)
        
        fb_push('admin_logs', {
            'action': 'delete_country',
            'countryCode': code,
            'createdAt': datetime.now().isoformat()
        })
        
        return jsonify({'success': True})
    
    elif request.method == 'PATCH':
        data = request.json or {}
        
        if 'name' in data:
            countries[code]['name'] = data['name']
        if 'flag' in data:
            countries[code]['flag'] = data['flag']
        if 'phoneCode' in data:
            countries[code]['code'] = data['phoneCode']
        if 'buyPrice' in data:
            countries[code]['buy'] = float(data['buyPrice'])
        if 'sellPrice' in data:
            countries[code]['sell'] = float(data['sellPrice'])
        if 'enabled' in data:
            countries[code]['enabled'] = bool(data['enabled'])
        
        fb_set('countries', countries)
        
        fb_push('admin_logs', {
            'action': 'update_country',
            'countryCode': code,
            'updates': data,
            'createdAt': datetime.now().isoformat()
        })
        
        return jsonify({'success': True})

# ============== Admin Settings ==============
@app.route('/api/admin/settings', methods=['GET', 'PATCH'])
@admin_required
def admin_settings():
    if request.method == 'GET':
        settings = get_settings()
        return jsonify({'success': True, 'settings': settings})
    
    elif request.method == 'PATCH':
        data = request.json or {}
        settings = get_settings()
        
        allowed_keys = [
            'minDeposit', 'minWithdrawal', 'referralBonus', 'fraudThreshold',
            'maintenanceMode', 'registrationEnabled', 'buyEnabled', 'sellEnabled',
            'depositEnabled', 'withdrawalEnabled'
        ]
        
        for key in allowed_keys:
            if key in data:
                settings[key] = data[key]
        
        fb_set('settings', settings)
        
        fb_push('admin_logs', {
            'action': 'update_settings',
            'updates': data,
            'createdAt': datetime.now().isoformat()
        })
        
        return jsonify({'success': True})

# ============== Admin Sells ==============
@app.route('/api/admin/sells')
@admin_required
def admin_sells():
    sells = fb_get('sell_requests') or {}
    status_filter = request.args.get('status', 'pending')
    
    result = []
    for sid, s in sells.items():
        if s and (status_filter == 'all' or s.get('status') == status_filter):
            result.append({'id': sid, **s})
    
    result.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
    return jsonify({'success': True, 'items': result})

@app.route('/api/admin/approve-sell', methods=['POST'])
@admin_required
def admin_approve_sell():
    data = request.json or {}
    sell_id = data.get('id')
    
    sell = fb_get(f'sell_requests/{sell_id}')
    if not sell:
        return jsonify({'success': False, 'error': 'غير موجود'})
    
    country = sell.get('country')
    countries = get_country_prices()
    country_info = countries.get(country, {})
    buy_price = country_info.get('buy', 1.0)
    
    fb_push('numbers', {
        'phone': sell['phone'],
        'country': country,
        'price': buy_price,
        'session': sell.get('session'),
        'status': 'available',
        'createdAt': datetime.now().isoformat()
    })
    
    fb_update(f'sell_requests/{sell_id}', {
        'status': 'approved',
        'approvedAt': datetime.now().isoformat()
    })
    
    user = fb_get(f"users/{sell['userId']}")
    if user:
        new_bal = user.get('balance', 0) + sell['price']
        fb_update(f"users/{sell['userId']}", {
            'balance': new_bal,
            'totalSales': user.get('totalSales', 0) + 1
        })
    
    fb_push('admin_logs', {
        'action': 'approve_sell',
        'sellId': sell_id,
        'createdAt': datetime.now().isoformat()
    })
    
    return jsonify({'success': True})

@app.route('/api/admin/reject-sell', methods=['POST'])
@admin_required
def admin_reject_sell():
    data = request.json or {}
    sell_id = data.get('id')
    reason = data.get('reason', '')
    
    fb_update(f"sell_requests/{sell_id}", {
        'status': 'rejected',
        'rejectReason': reason,
        'rejectedAt': datetime.now().isoformat()
    })
    
    fb_push('admin_logs', {
        'action': 'reject_sell',
        'sellId': sell_id,
        'reason': reason,
        'createdAt': datetime.now().isoformat()
    })
    
    return jsonify({'success': True})

# ============== Admin Numbers ==============
@app.route('/api/admin/numbers')
@admin_required
def admin_numbers():
    numbers = fb_get('numbers') or {}
    status_filter = request.args.get('status', 'all')
    
    result = []
    for nid, n in numbers.items():
        if n and (status_filter == 'all' or n.get('status') == status_filter):
            result.append({'id': nid, **n})
    
    result.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
    return jsonify({'success': True, 'items': result})

@app.route('/api/admin/delete-number', methods=['POST'])
@admin_required
def admin_delete():
    data = request.json or {}
    num_id = data.get('id')
    
    fb_delete(f"numbers/{num_id}")
    
    fb_push('admin_logs', {
        'action': 'delete_number',
        'numberId': num_id,
        'createdAt': datetime.now().isoformat()
    })
    
    return jsonify({'success': True})

@app.route('/api/admin/add-send-code', methods=['POST'])
@admin_required
def admin_send_code():
    data = request.json or {}
    phone = data.get('phone', '').strip()
    try:
        success, msg = run_telegram_async(tg_send_code(phone))
        return jsonify({'success': success, 'message': msg})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/add-verify', methods=['POST'])
@admin_required
def admin_verify():
    data = request.json or {}
    phone = data.get('phone', '').strip()
    code = data.get('code', '').strip()
    
    country = detect_country(phone)
    if not country:
        return jsonify({'success': False, 'error': 'دولة غير مدعومة'})
    
    countries = get_country_prices()
    country_info = countries.get(country, {})
    
    try:
        success, msg, session = run_telegram_async(tg_verify_code(phone, code))
        if not success:
            return jsonify({'success': False, 'error': msg})
        
        fb_push('numbers', {
            'phone': phone,
            'country': country,
            'price': country_info.get('buy', 1.0),
            'session': session,
            'status': 'available',
            'createdAt': datetime.now().isoformat()
        })
        
        fb_push('admin_logs', {
            'action': 'add_number',
            'phone': phone,
            'country': country,
            'createdAt': datetime.now().isoformat()
        })
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ============== Admin Withdrawals ==============
@app.route('/api/admin/withdrawals')
@admin_required
def admin_withdrawals():
    withdrawals = fb_get('withdrawals') or {}
    status_filter = request.args.get('status', 'pending')
    
    result = []
    for wid, w in withdrawals.items():
        if w and (status_filter == 'all' or w.get('status') == status_filter):
            result.append({'id': wid, **w})
    
    result.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
    return jsonify({'success': True, 'items': result})

@app.route('/api/admin/approve-withdrawal', methods=['POST'])
@admin_required
def admin_approve_withdrawal():
    data = request.json or {}
    wid = data.get('id')
    txid = data.get('txid', '')
    
    fb_update(f"withdrawals/{wid}", {
        'status': 'approved',
        'txid': txid,
        'approvedAt': datetime.now().isoformat()
    })
    
    fb_push('admin_logs', {
        'action': 'approve_withdrawal',
        'withdrawalId': wid,
        'txid': txid,
        'createdAt': datetime.now().isoformat()
    })
    
    return jsonify({'success': True})

@app.route('/api/admin/reject-withdrawal', methods=['POST'])
@admin_required
def admin_reject_withdrawal():
    data = request.json or {}
    wid = data.get('id')
    reason = data.get('reason', '')
    
    withdrawal = fb_get(f'withdrawals/{wid}')
    if withdrawal:
        # Refund balance
        user = fb_get(f"users/{withdrawal['userId']}")
        if user:
            new_balance = user.get('balance', 0) + withdrawal.get('amount', 0)
            fb_update(f"users/{withdrawal['userId']}", {'balance': new_balance})
    
    fb_update(f"withdrawals/{wid}", {
        'status': 'rejected',
        'rejectReason': reason,
        'rejectedAt': datetime.now().isoformat()
    })
    
    fb_push('admin_logs', {
        'action': 'reject_withdrawal',
        'withdrawalId': wid,
        'reason': reason,
        'createdAt': datetime.now().isoformat()
    })
    
    return jsonify({'success': True})

# ============== Admin Deposits ==============
@app.route('/api/admin/deposits')
@admin_required
def admin_deposits():
    deposits = fb_get('deposits') or {}
    result = []
    for did, d in deposits.items():
        if d:
            result.append({'id': did, **d})
    result.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
    return jsonify({'success': True, 'items': result})

# ============== Admin Fraud Logs ==============
@app.route('/api/admin/fraud-logs')
@admin_required
def admin_fraud_logs():
    logs = fb_get('fraud_logs') or {}
    result = []
    for lid, l in logs.items():
        if l:
            result.append({'id': lid, **l})
    result.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
    return jsonify({'success': True, 'logs': result})

# ============== Admin Logs ==============
@app.route('/api/admin/logs')
@admin_required
def admin_logs():
    logs = fb_get('admin_logs') or {}
    result = []
    for lid, l in logs.items():
        if l:
            result.append({'id': lid, **l})
    result.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
    return jsonify({'success': True, 'logs': result[:100]})  # Last 100 logs

# ============== Referral Stats ==============
@app.route('/api/admin/referral-stats')
@admin_required
def admin_referral_stats():
    users = fb_get('users') or {}
    referral_logs = fb_get('referral_logs') or {}
    
    top_referrers = sorted(
        [{'id': uid, **u} for uid, u in users.items() if u and u.get('referralCount', 0) > 0],
        key=lambda x: x.get('referralCount', 0),
        reverse=True
    )[:20]
    
    total_referrals = sum(u.get('referralCount', 0) for u in users.values() if u)
    total_earnings = sum(u.get('referralEarnings', 0) for u in users.values() if u)
    
    return jsonify({
        'success': True,
        'stats': {
            'totalReferrals': total_referrals,
            'totalEarnings': total_earnings,
            'topReferrers': [{
                'id': r['id'],
                'username': r.get('username'),
                'referralCount': r.get('referralCount', 0),
                'referralEarnings': r.get('referralEarnings', 0)
            } for r in top_referrers]
        }
    })

# ============== Track Visit (for referrals) ==============
@app.route('/api/track-visit', methods=['POST'])
def track_visit():
    data = request.json or {}
    fingerprint = get_device_fingerprint(request)
    
    # Store visit with fingerprint for anti-fraud
    fb_push('visits', {
        'fingerprint': fingerprint,
        'referralCode': data.get('referralCode'),
        'createdAt': datetime.now().isoformat()
    })
    
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import json
import hashlib
import secrets
import requests
import asyncio
import re
from datetime import datetime
from functools import wraps
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)
CORS(app)

# ============== Configuration ==============
TELEGRAM_API_ID = 27241932
TELEGRAM_API_HASH = "218edeae0f4cf9053d7dcbf3b1485048"
WALLET_ADDRESS = "0x8E00A980274Cfb22798290586d97F7D185E3092D"
BSCSCAN_API_KEY = "8BHURRRGKXD35BPGQZ8E94CVEVAUNMD9UF"
USDT_CONTRACT_BSC = "0x55d398326f99059fF775485246999027B3197955"

FIREBASE_URL = "https://lolaminig-afea4-default-rtdb.firebaseio.com"

executor = ThreadPoolExecutor(max_workers=4)
phone_sessions = {}

# ============== Default Data ==============
DEFAULT_COUNTRIES = {
    'US': {'sell': 0.75, 'buy': 0.95, 'name': 'الولايات المتحدة', 'flag': 'us', 'code': '+1', 'enabled': True},
    'UK': {'sell': 0.80, 'buy': 1.00, 'name': 'المملكة المتحدة', 'flag': 'gb', 'code': '+44', 'enabled': True},
    'CA': {'sell': 0.25, 'buy': 0.45, 'name': 'كندا', 'flag': 'ca', 'code': '+1', 'enabled': True},
    'DE': {'sell': 1.50, 'buy': 1.70, 'name': 'ألمانيا', 'flag': 'de', 'code': '+49', 'enabled': True},
    'FR': {'sell': 1.20, 'buy': 1.40, 'name': 'فرنسا', 'flag': 'fr', 'code': '+33', 'enabled': True},
    'NL': {'sell': 1.00, 'buy': 1.20, 'name': 'هولندا', 'flag': 'nl', 'code': '+31', 'enabled': True},
    'PL': {'sell': 0.90, 'buy': 1.10, 'name': 'بولندا', 'flag': 'pl', 'code': '+48', 'enabled': True},
    'AU': {'sell': 1.00, 'buy': 1.20, 'name': 'أستراليا', 'flag': 'au', 'code': '+61', 'enabled': True},
    'SA': {'sell': 0.80, 'buy': 1.00, 'name': 'السعودية', 'flag': 'sa', 'code': '+966', 'enabled': True},
    'AE': {'sell': 0.90, 'buy': 1.10, 'name': 'الإمارات', 'flag': 'ae', 'code': '+971', 'enabled': True},
    'EG': {'sell': 0.40, 'buy': 0.60, 'name': 'مصر', 'flag': 'eg', 'code': '+20', 'enabled': True},
    'TR': {'sell': 0.55, 'buy': 0.75, 'name': 'تركيا', 'flag': 'tr', 'code': '+90', 'enabled': True},
    'IN': {'sell': 0.30, 'buy': 0.50, 'name': 'الهند', 'flag': 'in', 'code': '+91', 'enabled': True},
    'BR': {'sell': 0.50, 'buy': 0.70, 'name': 'البرازيل', 'flag': 'br', 'code': '+55', 'enabled': True},
    'RU': {'sell': 0.60, 'buy': 0.80, 'name': 'روسيا', 'flag': 'ru', 'code': '+7', 'enabled': True},
    'ES': {'sell': 0.90, 'buy': 1.10, 'name': 'إسبانيا', 'flag': 'es', 'code': '+34', 'enabled': True},
    'IT': {'sell': 0.85, 'buy': 1.05, 'name': 'إيطاليا', 'flag': 'it', 'code': '+39', 'enabled': True},
    'JP': {'sell': 1.30, 'buy': 1.50, 'name': 'اليابان', 'flag': 'jp', 'code': '+81', 'enabled': True},
    'KR': {'sell': 1.20, 'buy': 1.40, 'name': 'كوريا', 'flag': 'kr', 'code': '+82', 'enabled': True},
    'ID': {'sell': 0.35, 'buy': 0.55, 'name': 'إندونيسيا', 'flag': 'id', 'code': '+62', 'enabled': True},
}

DEFAULT_SETTINGS = {
    'minDeposit': 1.5,
    'minWithdrawal': 2.0,
    'referralBonus': 0.01,
    'fraudThreshold': 0.65,
    'maintenanceMode': False,
    'registrationEnabled': True,
    'buyEnabled': True,
    'sellEnabled': True,
}

# ============== Firebase ==============
def fb_get(path):
    try:
        r = requests.get(f"{FIREBASE_URL}/{path}.json", timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None

def fb_set(path, data):
    try:
        r = requests.put(f"{FIREBASE_URL}/{path}.json", json=data, timeout=10)
        return r.status_code == 200
    except:
        return False

def fb_push(path, data):
    try:
        r = requests.post(f"{FIREBASE_URL}/{path}.json", json=data, timeout=10)
        return r.json().get('name') if r.status_code == 200 else None
    except:
        return None

def fb_update(path, data):
    try:
        r = requests.patch(f"{FIREBASE_URL}/{path}.json", json=data, timeout=10)
        return r.status_code == 200
    except:
        return False

def fb_delete(path):
    try:
        r = requests.delete(f"{FIREBASE_URL}/{path}.json", timeout=10)
        return r.status_code == 200
    except:
        return False

# ============== Helpers ==============
def get_countries():
    countries = fb_get('countries')
    if not countries:
        fb_set('countries', DEFAULT_COUNTRIES)
        return DEFAULT_COUNTRIES
    return countries

def get_settings():
    settings = fb_get('settings')
    if not settings:
        fb_set('settings', DEFAULT_SETTINGS)
        return DEFAULT_SETTINGS
    return {**DEFAULT_SETTINGS, **settings}

def generate_token():
    return secrets.token_hex(32)

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def generate_referral_code():
    return secrets.token_urlsafe(6).upper()

def detect_country(phone):
    phone = phone.replace(' ', '').replace('-', '')
    countries = get_countries()
    matched = None
    for code, info in countries.items():
        if phone.startswith(info['code']):
            if not matched or len(info['code']) > len(countries[matched]['code']):
                matched = code
    return matched

def get_fingerprint(req):
    return {
        'ip': req.headers.get('X-Forwarded-For', req.headers.get('X-Real-IP', req.remote_addr)),
        'ua': req.headers.get('User-Agent', ''),
        'lang': req.headers.get('Accept-Language', ''),
    }

def check_fraud(user_id, fingerprint):
    fps = fb_get('fingerprints') or {}
    settings = get_settings()
    threshold = settings.get('fraudThreshold', 0.65)
    
    for fp_id, fp_data in fps.items():
        if fp_data and fp_data.get('userId') != user_id:
            matches = 0
            total = 3
            if fp_data.get('ip') == fingerprint.get('ip'):
                matches += 1
            if fp_data.get('ua') == fingerprint.get('ua'):
                matches += 1
            if fp_data.get('lang') == fingerprint.get('lang'):
                matches += 1
            
            similarity = matches / total
            if similarity >= threshold:
                return True, fp_data.get('userId'), similarity
    
    return False, None, 0

def verify_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        token = auth.replace('Bearer ', '') if auth.startswith('Bearer ') else ''
        if not token:
            return jsonify({'success': False, 'error': 'يرجى تسجيل الدخول'}), 401
        
        users = fb_get('users') or {}
        for uid, u in users.items():
            if u and u.get('token') == token:
                if u.get('banned'):
                    return jsonify({'success': False, 'error': 'حسابك محظور'}), 403
                request.user_id = uid
                request.user = u
                return f(*args, **kwargs)
        
        return jsonify({'success': False, 'error': 'جلسة غير صالحة'}), 401
    return decorated

# ============== Telegram ==============
def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

async def tg_send_code(phone):
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    from telethon.errors import FloodWaitError
    
    client = TelegramClient(StringSession(), TELEGRAM_API_ID, TELEGRAM_API_HASH)
    try:
        await client.connect()
        result = await client.send_code_request(phone)
        session = client.session.save()
        phone_sessions[phone] = {
            'session': session,
            'hash': result.phone_code_hash
        }
        return True, "تم إرسال الكود"
    except FloodWaitError as e:
        return False, f"انتظر {e.seconds} ثانية"
    except Exception as e:
        return False, str(e)
    finally:
        await client.disconnect()

async def tg_verify(phone, code):
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    from telethon.errors import PhoneCodeInvalidError, SessionPasswordNeededError
    
    if phone not in phone_sessions:
        return False, "اطلب كود جديد", None
    
    data = phone_sessions[phone]
    client = TelegramClient(StringSession(data['session']), TELEGRAM_API_ID, TELEGRAM_API_HASH)
    
    try:
        await client.connect()
        await client.sign_in(phone=phone, code=code, phone_code_hash=data['hash'])
        session = client.session.save()
        del phone_sessions[phone]
        return True, "تم", session
    except PhoneCodeInvalidError:
        return False, "الكود غير صحيح", None
    except SessionPasswordNeededError:
        return False, "الحساب محمي بـ 2FA", None
    except Exception as e:
        return False, str(e), None
    finally:
        await client.disconnect()

async def tg_get_messages(session_str):
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    
    client = TelegramClient(StringSession(session_str), TELEGRAM_API_ID, TELEGRAM_API_HASH)
    messages = []
    
    try:
        await client.connect()
        if await client.is_user_authorized():
            async for msg in client.iter_messages(777000, limit=10):
                if msg.message:
                    codes = re.findall(r'\b\d{5,6}\b', msg.message)
                    if codes:
                        messages.append({
                            'code': codes[0],
                            'timestamp': msg.date.isoformat()
                        })
    except:
        pass
    finally:
        await client.disconnect()
    
    return messages

def verify_bsc_tx(txid):
    try:
        r = requests.get(f"https://api.bscscan.com/api", params={
            'module': 'proxy',
            'action': 'eth_getTransactionByHash',
            'txhash': txid,
            'apikey': BSCSCAN_API_KEY
        }, timeout=15)
        
        data = r.json()
        if not data.get('result'):
            return False, 0
        
        tx = data['result']
        to = tx.get('to', '').lower()
        
        if to == USDT_CONTRACT_BSC.lower():
            inp = tx.get('input', '')
            if inp.startswith('0xa9059cbb'):
                recipient = '0x' + inp[34:74]
                if recipient.lower() == WALLET_ADDRESS.lower():
                    amount = int(inp[74:138], 16) / 1e18
                    if amount >= 1.5:
                        return True, amount
        
        if to == WALLET_ADDRESS.lower():
            val = int(tx.get('value', '0'), 16) / 1e18
            if val >= 0.004:
                return True, val * 350
        
        return False, 0
    except:
        return False, 0

# ============== HTML ==============
HTML = '''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
    <meta name="theme-color" content="#0d1117">
    <title>TeleNum - أرقام تيليجرام</title>
    <link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        :root{--p:#0088cc;--p2:#006699;--s:#00c853;--d:#ff5252;--w:#ffab00;--bg:#0d1117;--bg2:#161b22;--bg3:#21262d;--br:#30363d;--tx:#f0f6fc;--tx2:#8b949e;--r:14px}
        *{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
        body{font-family:'Tajawal',sans-serif;background:var(--bg);color:var(--tx);min-height:100vh}
        .hd{position:fixed;top:0;left:0;right:0;z-index:100;background:rgba(13,17,23,.95);backdrop-filter:blur(20px);border-bottom:1px solid var(--br);padding:12px 16px;display:flex;align-items:center;justify-content:space-between}
        .logo{display:flex;align-items:center;gap:8px;font-size:1.3rem;font-weight:800;color:var(--p)}
        .logo i{font-size:1.6rem}
        .bal{display:flex;align-items:center;gap:6px;background:linear-gradient(135deg,var(--s),#00a844);padding:8px 14px;border-radius:20px;font-weight:700;font-size:.9rem}
        .abtn{background:var(--p);color:#fff;border:none;padding:10px 18px;border-radius:20px;font-family:inherit;font-weight:600;cursor:pointer}
        .nav{position:fixed;bottom:0;left:0;right:0;z-index:100;background:var(--bg2);border-top:1px solid var(--br);padding:8px 0;padding-bottom:max(8px,env(safe-area-inset-bottom))}
        .nav-in{display:flex;justify-content:space-around;max-width:500px;margin:0 auto}
        .nav-i{display:flex;flex-direction:column;align-items:center;gap:3px;padding:8px 10px;color:var(--tx2);background:none;border:none;font-family:inherit;font-size:.7rem;cursor:pointer;border-radius:10px}
        .nav-i i{font-size:1.2rem}
        .nav-i.active{color:var(--p);background:rgba(0,136,204,.1)}
        .main{padding:70px 14px 90px;max-width:600px;margin:0 auto}
        .stats{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:18px}
        .stat{background:var(--bg2);border:1px solid var(--br);border-radius:var(--r);padding:14px;text-align:center}
        .stat i{font-size:1.4rem;color:var(--p);margin-bottom:6px}
        .stat-v{font-size:1.3rem;font-weight:800}
        .stat-l{font-size:.75rem;color:var(--tx2)}
        .sec{display:none;animation:fadeIn .3s}
        .sec.active{display:block}
        @keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
        .sec-t{font-size:1.1rem;font-weight:700;margin-bottom:14px;display:flex;align-items:center;gap:8px}
        .sec-t i{color:var(--p)}
        .search{position:relative;margin-bottom:14px}
        .search input{width:100%;padding:12px 16px 12px 42px;background:var(--bg3);border:1px solid var(--br);border-radius:10px;color:var(--tx);font-family:inherit;font-size:.95rem}
        .search input:focus{outline:none;border-color:var(--p)}
        .search i{position:absolute;left:14px;top:50%;transform:translateY(-50%);color:var(--tx2)}
        .cards{display:grid;gap:10px}
        .card{background:var(--bg2);border:1px solid var(--br);border-radius:var(--r);padding:14px;display:flex;align-items:center;gap:12px;cursor:pointer;transition:all .2s}
        .card:hover{border-color:var(--p)}
        .card:active{transform:scale(.98)}
        .card.out{opacity:.5;cursor:not-allowed}
        .card-flag{width:42px;height:42px;border-radius:50%;object-fit:cover;border:2px solid var(--br)}
        .card-info{flex:1}
        .card-name{font-weight:700;font-size:.95rem}
        .card-code{color:var(--tx2);font-size:.8rem}
        .card-meta{text-align:left}
        .card-price{font-size:1.1rem;font-weight:800;color:var(--s)}
        .card-stock{font-size:.75rem;display:flex;align-items:center;gap:4px;margin-top:2px}
        .card-stock.in{color:var(--s)}
        .card-stock.low{color:var(--w)}
        .card-stock.out{color:var(--d)}
        .fcard{background:var(--bg2);border:1px solid var(--br);border-radius:var(--r);padding:18px}
        .fg{margin-bottom:16px}
        .fl{display:block;margin-bottom:6px;font-weight:600;font-size:.9rem}
        .fi{width:100%;padding:13px 15px;background:var(--bg3);border:2px solid var(--br);border-radius:10px;color:var(--tx);font-family:inherit;font-size:1rem}
        .fi:focus{outline:none;border-color:var(--p)}
        .fh{margin-top:5px;font-size:.8rem;color:var(--tx2)}
        .fh.ok{color:var(--s)}
        .fh.err{color:var(--d)}
        .btn{width:100%;padding:14px;border:none;border-radius:10px;font-family:inherit;font-size:1rem;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:8px}
        .btn:disabled{opacity:.5;cursor:not-allowed}
        .btn-p{background:linear-gradient(135deg,var(--p),var(--p2));color:#fff}
        .btn-s{background:linear-gradient(135deg,var(--s),#00a844);color:#fff}
        .btn-d{background:var(--d);color:#fff}
        .btn-o{background:transparent;border:2px solid var(--br);color:var(--tx)}
        .alert{display:flex;gap:10px;padding:12px;border-radius:10px;margin-bottom:14px;font-size:.9rem}
        .alert i{flex-shrink:0}
        .alert-i{background:rgba(0,136,204,.15);border:1px solid rgba(0,136,204,.3);color:#58a6ff}
        .alert-w{background:rgba(255,171,0,.15);border:1px solid rgba(255,171,0,.3);color:#f0b429}
        .alert-s{background:rgba(0,200,83,.15);border:1px solid rgba(0,200,83,.3);color:#3fb950}
        .alert-d{background:rgba(255,82,82,.15);border:1px solid rgba(255,82,82,.3);color:#ff8a80}
        .wallet{background:var(--bg3);border:2px dashed var(--br);border-radius:10px;padding:12px;display:flex;align-items:center;gap:10px;margin:14px 0}
        .wallet-a{flex:1;font-family:monospace;font-size:.7rem;color:var(--p);word-break:break-all}
        .copy{background:var(--p);color:#fff;border:none;padding:10px 12px;border-radius:8px;cursor:pointer}
        .qr{display:flex;justify-content:center;margin:16px 0}
        .qr img{background:#fff;padding:10px;border-radius:10px;width:160px;height:160px}
        .modal{position:fixed;inset:0;background:rgba(0,0,0,.85);backdrop-filter:blur(8px);z-index:200;display:none;align-items:center;justify-content:center;padding:14px}
        .modal.active{display:flex}
        .modal-c{background:var(--bg2);border:1px solid var(--br);border-radius:var(--r);width:100%;max-width:380px;max-height:85vh;overflow-y:auto}
        .modal-h{display:flex;align-items:center;justify-content:space-between;padding:14px 16px;border-bottom:1px solid var(--br)}
        .modal-t{font-size:1rem;font-weight:700;display:flex;align-items:center;gap:8px}
        .modal-t i{color:var(--p)}
        .modal-x{background:none;border:none;color:var(--tx2);font-size:1.4rem;cursor:pointer}
        .modal-b{padding:16px}
        .code-box{background:linear-gradient(135deg,var(--p),var(--p2));border-radius:10px;padding:18px;text-align:center;margin:14px 0}
        .code-l{font-size:.85rem;opacity:.9}
        .code-v{font-size:1.5rem;font-weight:800;font-family:monospace;letter-spacing:3px;margin-top:4px}
        .msg-box{background:var(--bg3);border-radius:10px;padding:10px;max-height:180px;overflow-y:auto}
        .msg-i{padding:10px;border-bottom:1px solid var(--br)}
        .msg-i:last-child{border:none}
        .msg-c{font-size:1.3rem;font-weight:800;color:var(--p);font-family:monospace}
        .msg-t{font-size:.7rem;color:var(--tx2);margin-top:3px}
        .wait{text-align:center;padding:20px}
        .wait i{font-size:2rem;color:var(--w);animation:pulse 1.5s infinite}
        @keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
        .wait p{color:var(--tx2);margin-top:10px;font-size:.9rem}
        .num-c{background:var(--bg2);border:1px solid var(--br);border-radius:var(--r);padding:14px;margin-bottom:10px}
        .num-h{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}
        .num-p{font-size:1rem;font-weight:700;font-family:monospace;direction:ltr}
        .badge{padding:4px 8px;border-radius:12px;font-size:.7rem;font-weight:600}
        .badge.active{background:rgba(0,200,83,.2);color:var(--s)}
        .badge.pending{background:rgba(255,171,0,.2);color:var(--w)}
        .badge.completed{background:rgba(0,136,204,.2);color:var(--p)}
        .price-box{background:var(--bg3);border-radius:10px;padding:14px;text-align:center;margin:14px 0}
        .price-l{font-size:.85rem;color:var(--tx2)}
        .price-v{font-size:1.8rem;font-weight:800;color:var(--s);margin-top:4px}
        .ref-box{background:linear-gradient(135deg,#9c27b0,#7b1fa2);border-radius:var(--r);padding:18px;margin-bottom:18px}
        .ref-t{font-weight:700;margin-bottom:10px;display:flex;align-items:center;gap:8px}
        .ref-code{background:rgba(255,255,255,.2);padding:10px;border-radius:8px;display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}
        .ref-code span{font-family:monospace;font-weight:700;letter-spacing:1px}
        .ref-stats{display:grid;grid-template-columns:1fr 1fr;gap:8px}
        .ref-stat{background:rgba(255,255,255,.1);padding:10px;border-radius:8px;text-align:center}
        .ref-stat-v{font-size:1.2rem;font-weight:800}
        .ref-stat-l{font-size:.7rem;opacity:.8}
        .auth-c{max-width:380px;margin:0 auto}
        .auth-t{text-align:center;font-size:1.3rem;font-weight:800;margin-bottom:6px;display:flex;align-items:center;justify-content:center;gap:8px}
        .auth-t i{color:var(--p)}
        .auth-s{text-align:center;color:var(--tx2);margin-bottom:20px;font-size:.9rem}
        .auth-f{text-align:center;margin-top:18px;color:var(--tx2);font-size:.9rem}
        .auth-f a{color:var(--p);cursor:pointer;font-weight:600}
        .tabs{display:flex;gap:4px;margin-bottom:14px;background:var(--bg3);padding:4px;border-radius:10px}
        .tab{flex:1;padding:10px;background:transparent;border:none;border-radius:8px;color:var(--tx2);font-family:inherit;font-size:.9rem;font-weight:600;cursor:pointer}
        .tab.active{background:var(--p);color:#fff}
        .empty{text-align:center;padding:30px;color:var(--tx2)}
        .empty i{font-size:2.5rem;opacity:.3;margin-bottom:12px}
        .toast-c{position:fixed;top:70px;left:50%;transform:translateX(-50%);z-index:300;width:90%;max-width:340px}
        .toast{background:var(--bg2);border:1px solid var(--br);border-radius:10px;padding:12px 14px;margin-bottom:8px;display:flex;align-items:center;gap:10px;box-shadow:0 4px 20px rgba(0,0,0,.3);animation:toastIn .3s}
        @keyframes toastIn{from{opacity:0;transform:translateY(-8px)}to{opacity:1;transform:translateY(0)}}
        .toast.success{border-color:var(--s)}
        .toast.success i{color:var(--s)}
        .toast.error{border-color:var(--d)}
        .toast.error i{color:var(--d)}
        .spin{width:28px;height:28px;border:3px solid var(--br);border-top-color:var(--p);border-radius:50%;animation:spin .8s linear infinite;margin:18px auto}
        @keyframes spin{to{transform:rotate(360deg)}}
        .hidden{display:none!important}
        .admin-tabs{display:flex;gap:6px;margin-bottom:14px;overflow-x:auto;padding-bottom:6px}
        .admin-tab{padding:8px 14px;background:var(--bg3);border:1px solid var(--br);border-radius:8px;color:var(--tx);font-family:inherit;font-size:.8rem;white-space:nowrap;cursor:pointer;display:flex;align-items:center;gap:5px}
        .admin-tab.active{background:var(--p);border-color:var(--p)}
        .admin-item{background:var(--bg2);border:1px solid var(--br);border-radius:10px;padding:12px;margin-bottom:8px}
        .admin-h{display:flex;justify-content:space-between;align-items:flex-start;gap:10px}
        .admin-m{flex:1}
        .admin-t{font-weight:700;font-size:.9rem}
        .admin-meta{font-size:.8rem;color:var(--tx2);margin-top:4px}
        .admin-acts{display:flex;gap:6px;margin-top:10px}
        .admin-btn{flex:1;padding:8px;border:none;border-radius:6px;font-size:.8rem;font-weight:600;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:4px}
        .admin-btn.ok{background:var(--s);color:#fff}
        .admin-btn.no{background:var(--d);color:#fff}
        .admin-btn.edit{background:#2196f3;color:#fff}
    </style>
</head>
<body>
    <header class="hd">
        <div class="logo"><i class="fab fa-telegram"></i>TeleNum</div>
        <div id="uarea"></div>
    </header>
    
    <nav class="nav">
        <div class="nav-in">
            <button class="nav-i active" data-s="buy"><i class="fas fa-shopping-cart"></i>شراء</button>
            <button class="nav-i" data-s="sell"><i class="fas fa-dollar-sign"></i>بيع</button>
            <button class="nav-i" data-s="wallet"><i class="fas fa-wallet"></i>محفظة</button>
            <button class="nav-i" data-s="nums"><i class="fas fa-mobile-alt"></i>أرقامي</button>
            <button class="nav-i" data-s="profile"><i class="fas fa-user"></i>حسابي</button>
        </div>
    </nav>
    
    <main class="main">
        <div class="stats">
            <div class="stat"><i class="fas fa-globe"></i><div class="stat-v" id="stC">0</div><div class="stat-l">دولة</div></div>
            <div class="stat"><i class="fas fa-phone-alt"></i><div class="stat-v" id="stN">0</div><div class="stat-l">رقم متاح</div></div>
        </div>
        
        <section class="sec active" id="secBuy">
            <h2 class="sec-t"><i class="fas fa-shopping-cart"></i>شراء رقم</h2>
            <div class="search"><i class="fas fa-search"></i><input type="text" id="srcC" placeholder="ابحث عن دولة..." oninput="filterC()"></div>
            <div class="cards" id="clist"></div>
        </section>
        
        <section class="sec" id="secSell">
            <h2 class="sec-t"><i class="fas fa-dollar-sign"></i>بيع رقمك</h2>
            <div class="fcard">
                <div class="alert alert-i"><i class="fas fa-info-circle"></i><span>بع رقمك واحصل على رصيد فوري</span></div>
                <form id="sellF">
                    <div class="fg"><label class="fl">رقم الهاتف</label><input type="tel" class="fi" id="sellP" placeholder="+1234567890" dir="ltr" required><div class="fh" id="sellH"></div></div>
                    <div class="fg hidden" id="sellCG"><label class="fl">كود التحقق</label><input type="text" class="fi" id="sellC" placeholder="12345" dir="ltr" maxlength="6"></div>
                    <div class="alert alert-w"><i class="fas fa-exclamation-triangle"></i><div><b>شروط:</b><ul style="margin:6px 0 0 18px;font-size:.85rem"><li>بدون 2FA</li><li>بدون إيميل</li><li>سجل خروج بعد الإرسال</li></ul></div></div>
                    <div class="price-box hidden" id="sellPB"><div class="price-l">السعر</div><div class="price-v" id="sellPV">$0</div></div>
                    <button type="submit" class="btn btn-p" id="sellB"><i class="fas fa-paper-plane"></i>إرسال</button>
                </form>
            </div>
        </section>
        
        <section class="sec" id="secWallet">
            <h2 class="sec-t"><i class="fas fa-wallet"></i>المحفظة</h2>
            <div class="tabs"><button class="tab active" onclick="showWT('dep')">إيداع</button><button class="tab" onclick="showWT('wth')">سحب</button></div>
            <div id="wtDep" class="fcard">
                <div class="alert alert-i"><i class="fas fa-info-circle"></i><span>أرسل USDT (BEP-20) - الحد الأدنى $1.50</span></div>
                <div class="wallet"><span class="wallet-a">0x8E00A980274Cfb22798290586d97F7D185E3092D</span><button type="button" class="copy" onclick="copyW()"><i class="fas fa-copy"></i></button></div>
                <div class="qr"><img src="https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=0x8E00A980274Cfb22798290586d97F7D185E3092D" alt="QR"></div>
                <form id="depF"><div class="fg"><label class="fl">TXID</label><input type="text" class="fi" id="depT" placeholder="0x..." dir="ltr" required></div><button type="submit" class="btn btn-p" id="depB"><i class="fas fa-check-circle"></i>تحقق</button></form>
            </div>
            <div id="wtWth" class="fcard hidden">
                <div class="fg"><label class="fl">المبلغ ($)</label><input type="number" class="fi" id="wthA" placeholder="0.00" step="0.01" min="2"></div>
                <div class="fg"><label class="fl">عنوان المحفظة (BEP-20)</label><input type="text" class="fi" id="wthW" placeholder="0x..." dir="ltr"></div>
                <button type="button" class="btn btn-p" onclick="doWth()"><i class="fas fa-paper-plane"></i>طلب سحب</button>
            </div>
        </section>
        
        <section class="sec" id="secNums"><h2 class="sec-t"><i class="fas fa-mobile-alt"></i>أرقامي</h2><div id="numL"></div></section>
        <section class="sec" id="secProfile"><h2 class="sec-t"><i class="fas fa-user"></i>حسابي</h2><div id="profC"></div></section>
        <section class="sec" id="secAdmin"><h2 class="sec-t"><i class="fas fa-shield-alt"></i>الإدارة</h2><div class="admin-tabs" id="admT"></div><div id="admC"></div></section>
        
        <section class="sec" id="secAuth">
            <div class="auth-c">
                <div class="fcard" id="loginC">
                    <h2 class="auth-t"><i class="fas fa-sign-in-alt"></i>تسجيل الدخول</h2>
                    <p class="auth-s">مرحباً بعودتك!</p>
                    <form id="loginF"><div class="fg"><label class="fl">البريد</label><input type="email" class="fi" id="logE" required></div><div class="fg"><label class="fl">كلمة المرور</label><input type="password" class="fi" id="logP" required></div><button type="submit" class="btn btn-p"><i class="fas fa-sign-in-alt"></i>دخول</button></form>
                    <div class="auth-f">ليس لديك حساب؟ <a onclick="showReg()">إنشاء حساب</a></div>
                </div>
                <div class="fcard hidden" id="regC">
                    <h2 class="auth-t"><i class="fas fa-user-plus"></i>حساب جديد</h2>
                    <p class="auth-s">انضم إلينا!</p>
                    <form id="regF"><div class="fg"><label class="fl">الاسم</label><input type="text" class="fi" id="regN" required minlength="3"></div><div class="fg"><label class="fl">البريد</label><input type="email" class="fi" id="regE" required></div><div class="fg"><label class="fl">كلمة المرور</label><input type="password" class="fi" id="regP" required minlength="6"></div><div class="fg"><label class="fl">كود الإحالة (اختياري)</label><input type="text" class="fi" id="regR"></div><button type="submit" class="btn btn-p"><i class="fas fa-user-plus"></i>إنشاء</button></form>
                    <div class="auth-f">لديك حساب؟ <a onclick="showLog()">تسجيل الدخول</a></div>
                </div>
            </div>
        </section>
    </main>
    
    <div class="modal" id="modal"><div class="modal-c"><div class="modal-h"><h3 class="modal-t" id="modT"><i class="fas fa-shopping-cart"></i><span>شراء</span></h3><button class="modal-x" onclick="closeMod()">&times;</button></div><div class="modal-b" id="modB"></div></div></div>
    <div class="toast-c" id="toasts"></div>

<script>
const API='/api',WALL='0x8E00A980274Cfb22798290586d97F7D185E3092D';
let user=null,isAdm=false,countries=[],polls={};

document.addEventListener('DOMContentLoaded',init);

function init(){
    chkAdm();
    loadU();
    loadC();
    loadS();
    setupE();
    chkRef();
}

function chkAdm(){
    if(new URLSearchParams(location.search).get('admin')==='true'){
        isAdm=true;
        document.querySelector('.nav-in').innerHTML+=`<button class="nav-i" data-s="admin"><i class="fas fa-shield-alt"></i>إدارة</button>`;
    }
}

function chkRef(){
    const ref=new URLSearchParams(location.search).get('ref');
    if(ref){localStorage.setItem('ref',ref);document.getElementById('regR').value=ref;}
}

function loadU(){
    const s=localStorage.getItem('tgu');
    if(s){try{user=JSON.parse(s);refreshU();}catch(e){localStorage.removeItem('tgu');}}
    updUA();
}

async function refreshU(){
    if(!user?.token)return;
    try{
        const r=await fetch(`${API}/auth/me`,{headers:{'Authorization':`Bearer ${user.token}`}});
        const d=await r.json();
        if(d.success){user={...user,...d.user};localStorage.setItem('tgu',JSON.stringify(user));updUA();}
    }catch(e){}
}

function updUA(){
    const a=document.getElementById('uarea');
    if(user){
        a.innerHTML=`<div class="bal" onclick="showS('wallet')"><i class="fas fa-coins"></i>$${(user.balance||0).toFixed(2)}</div>`;
    }else{
        a.innerHTML=`<button class="abtn" onclick="showS('auth')"><i class="fas fa-user"></i>دخول</button>`;
    }
}

function logout(){user=null;localStorage.removeItem('tgu');updUA();showS('buy');toast('تم الخروج','success');}

function setupE(){
    document.querySelectorAll('[data-s]').forEach(b=>b.onclick=()=>{showS(b.dataset.s);document.querySelectorAll('.nav-i').forEach(n=>n.classList.remove('active'));if(b.classList.contains('nav-i'))b.classList.add('active');});
    document.getElementById('loginF').onsubmit=doLog;
    document.getElementById('regF').onsubmit=doReg;
    document.getElementById('sellF').onsubmit=doSell;
    document.getElementById('depF').onsubmit=doDep;
    document.getElementById('sellP').oninput=detC;
}

function showS(s){
    document.querySelectorAll('.sec').forEach(x=>x.classList.remove('active'));
    const map={buy:'secBuy',sell:'secSell',wallet:'secWallet',nums:'secNums',profile:'secProfile',admin:'secAdmin',auth:'secAuth'};
    const sec=document.getElementById(map[s]);
    if(sec){
        sec.classList.add('active');
        if(s==='admin'&&isAdm)loadAdm();
        if(s==='nums'&&user)loadNums();
        if(s==='profile'&&user)loadProf();
    }
}

async function loadC(){
    try{
        const r=await fetch(`${API}/countries`);
        const d=await r.json();
        if(d.success){countries=d.countries||[];renderC();}
    }catch(e){console.error(e);}
}

function renderC(f=''){
    const list=document.getElementById('clist');
    const fc=countries.filter(c=>!f||c.name.includes(f)||c.code.toLowerCase().includes(f.toLowerCase()));
    if(!fc.length){list.innerHTML='<div class="empty"><i class="fas fa-search"></i><p>لا نتائج</p></div>';return;}
    list.innerHTML=fc.map(c=>{
        const sc=c.stock>5?'in':c.stock>0?'low':'out';
        return`<div class="card ${c.stock===0?'out':''}" onclick="${c.stock?`openBuy('${c.code}')`:''}">
            <img src="https://flagcdn.com/w80/${c.flag}.png" class="card-flag" onerror="this.src='https://via.placeholder.com/42'">
            <div class="card-info"><div class="card-name">${c.name}</div><div class="card-code">${c.phoneCode}</div></div>
            <div class="card-meta"><div class="card-price">$${c.buyPrice.toFixed(2)}</div><div class="card-stock ${sc}"><i class="fas fa-${c.stock?'box':'times-circle'}"></i>${c.stock||'نفذ'}</div></div>
        </div>`;
    }).join('');
}

function filterC(){renderC(document.getElementById('srcC').value.trim());}

async function loadS(){
    try{
        const r=await fetch(`${API}/stats`);
        const d=await r.json();
        document.getElementById('stC').textContent=d.totalCountries||countries.length||0;
        document.getElementById('stN').textContent=d.availableNumbers||0;
    }catch(e){}
}

function openBuy(code){
    if(!user){toast('سجل دخول أولاً','error');showS('auth');return;}
    const c=countries.find(x=>x.code===code);
    if(!c||!c.stock)return;
    document.getElementById('modT').innerHTML='<i class="fas fa-shopping-cart"></i><span>شراء رقم</span>';
    document.getElementById('modB').innerHTML=`
        <div style="text-align:center;margin-bottom:16px"><img src="https://flagcdn.com/w80/${c.flag}.png" style="width:56px;border-radius:50%"><h3 style="margin-top:10px">${c.name}</h3><p style="color:var(--tx2)">${c.phoneCode}</p></div>
        <div class="price-box"><div class="price-l">السعر</div><div class="price-v">$${c.buyPrice.toFixed(2)}</div></div>
        <button class="btn btn-s" onclick="confBuy('${code}')"><i class="fas fa-check"></i>تأكيد الشراء</button>`;
    openMod();
}

async function confBuy(code){
    const c=countries.find(x=>x.code===code);
    if((user.balance||0)<c.buyPrice){toast('رصيد غير كافٍ','error');closeMod();showS('wallet');return;}
    document.getElementById('modB').innerHTML='<div class="wait"><i class="fas fa-spinner fa-spin"></i><p>جاري الشراء...</p></div>';
    try{
        const r=await fetch(`${API}/buy`,{method:'POST',headers:{'Content-Type':'application/json','Authorization':`Bearer ${user.token}`},body:JSON.stringify({country:code})});
        const d=await r.json();
        if(d.success){
            user.balance=d.newBalance;localStorage.setItem('tgu',JSON.stringify(user));updUA();loadC();loadS();
            document.getElementById('modB').innerHTML=`
                <div style="text-align:center"><i class="fas fa-check-circle" style="font-size:2.5rem;color:var(--s)"></i><h3 style="margin:10px 0">تم الشراء!</h3></div>
                <div class="code-box"><div class="code-l">الرقم</div><div class="code-v">${d.phone}</div></div>
                <div class="msg-box" id="msgB"><div class="wait"><i class="fas fa-spinner fa-spin"></i><p>انتظار الكود...</p></div></div>
                <div style="display:flex;gap:8px;margin-top:12px"><button class="btn btn-s" onclick="compBuy('${d.purchaseId}')"><i class="fas fa-check"></i>تم</button><button class="btn btn-o" onclick="closeMod()">إغلاق</button></div>`;
            startPoll(d.purchaseId);
        }else throw new Error(d.error);
    }catch(e){document.getElementById('modB').innerHTML=`<div style="text-align:center"><i class="fas fa-times-circle" style="font-size:2.5rem;color:var(--d)"></i><h3 style="margin:10px 0">فشل</h3><p style="color:var(--tx2)">${e.message}</p></div><button class="btn btn-o" onclick="closeMod()">إغلاق</button>`;}
}

function startPoll(id){
    const poll=async()=>{
        try{
            const r=await fetch(`${API}/messages/${id}`,{headers:{'Authorization':`Bearer ${user.token}`}});
            const d=await r.json();
            const b=document.getElementById('msgB');
            if(b&&d.messages?.length){b.innerHTML=d.messages.map(m=>`<div class="msg-i"><div class="msg-c">${m.code}</div><div class="msg-t">${new Date(m.timestamp).toLocaleString('ar')}</div></div>`).join('');}
        }catch(e){}
    };
    poll();polls[id]=setInterval(poll,3000);
}

async function compBuy(id){
    if(polls[id]){clearInterval(polls[id]);delete polls[id];}
    try{await fetch(`${API}/complete`,{method:'POST',headers:{'Content-Type':'application/json','Authorization':`Bearer ${user.token}`},body:JSON.stringify({purchaseId:id})});toast('تم!','success');closeMod();loadNums();}catch(e){toast('خطأ','error');}
}

function openMod(){document.getElementById('modal').classList.add('active');document.body.style.overflow='hidden';}
function closeMod(){document.getElementById('modal').classList.remove('active');document.body.style.overflow='';Object.keys(polls).forEach(k=>{clearInterval(polls[k]);delete polls[k];});}

async function doLog(e){
    e.preventDefault();const btn=e.target.querySelector('button');const ot=btn.innerHTML;btn.disabled=true;btn.innerHTML='<i class="fas fa-spinner fa-spin"></i>';
    try{
        const r=await fetch(`${API}/auth/login`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:document.getElementById('logE').value,password:document.getElementById('logP').value})});
        const d=await r.json();
        if(d.success){user=d.user;localStorage.setItem('tgu',JSON.stringify(user));updUA();showS('buy');toast('مرحباً!','success');e.target.reset();}else toast(d.error||'خطأ','error');
    }catch(err){toast('فشل الاتصال','error');}
    btn.disabled=false;btn.innerHTML=ot;
}

async function doReg(e){
    e.preventDefault();const btn=e.target.querySelector('button');const ot=btn.innerHTML;btn.disabled=true;btn.innerHTML='<i class="fas fa-spinner fa-spin"></i>';
    const ref=document.getElementById('regR').value||localStorage.getItem('ref')||'';
    try{
        const r=await fetch(`${API}/auth/register`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:document.getElementById('regN').value,email:document.getElementById('regE').value,password:document.getElementById('regP').value,referralCode:ref})});
        const d=await r.json();
        if(d.success){user=d.user;localStorage.setItem('tgu',JSON.stringify(user));localStorage.removeItem('ref');updUA();showS('buy');toast('تم إنشاء الحساب!','success');e.target.reset();}else toast(d.error||'خطأ','error');
    }catch(err){toast('فشل الاتصال','error');}
    btn.disabled=false;btn.innerHTML=ot;
}

function showLog(){document.getElementById('loginC').classList.remove('hidden');document.getElementById('regC').classList.add('hidden');}
function showReg(){document.getElementById('loginC').classList.add('hidden');document.getElementById('regC').classList.remove('hidden');}

function detC(){
    const p=document.getElementById('sellP').value.trim();
    const h=document.getElementById('sellH');
    const pb=document.getElementById('sellPB');
    const pv=document.getElementById('sellPV');
    if(!p.startsWith('+')){h.innerHTML='';pb.classList.add('hidden');return;}
    let m=null;for(const c of countries){if(p.startsWith(c.phoneCode)&&(!m||c.phoneCode.length>m.phoneCode.length))m=c;}
    if(m){h.innerHTML=`<i class="fas fa-flag"></i> ${m.name}`;h.className='fh ok';pb.classList.remove('hidden');pv.textContent=`$${m.sellPrice.toFixed(2)}`;}
    else{h.innerHTML='<i class="fas fa-exclamation-circle"></i> دولة غير مدعومة';h.className='fh err';pb.classList.add('hidden');}
}

async function doSell(e){
    e.preventDefault();if(!user){toast('سجل دخول','error');showS('auth');return;}
    const p=document.getElementById('sellP').value.trim();
    const cg=document.getElementById('sellCG');
    const c=document.getElementById('sellC').value.trim();
    const btn=document.getElementById('sellB');const ot=btn.innerHTML;
    if(cg.classList.contains('hidden')){
        btn.disabled=true;btn.innerHTML='<i class="fas fa-spinner fa-spin"></i>';
        try{
            const r=await fetch(`${API}/sell/send-code`,{method:'POST',headers:{'Content-Type':'application/json','Authorization':`Bearer ${user.token}`},body:JSON.stringify({phone:p})});
            const d=await r.json();
            if(d.success){cg.classList.remove('hidden');btn.innerHTML='<i class="fas fa-check"></i>تأكيد';toast('تم إرسال الكود','success');}else throw new Error(d.error);
        }catch(err){toast(err.message||'خطأ','error');btn.innerHTML=ot;}
        btn.disabled=false;
    }else{
        if(c.length<5){toast('أدخل الكود','error');return;}
        btn.disabled=true;btn.innerHTML='<i class="fas fa-spinner fa-spin"></i>';
        try{
            const r=await fetch(`${API}/sell/verify`,{method:'POST',headers:{'Content-Type':'application/json','Authorization':`Bearer ${user.token}`},body:JSON.stringify({phone:p,code:c})});
            const d=await r.json();
            if(d.success){toast('تم إرسال الطلب!','success');e.target.reset();cg.classList.add('hidden');document.getElementById('sellH').innerHTML='';document.getElementById('sellPB').classList.add('hidden');}else throw new Error(d.error);
        }catch(err){toast(err.message||'خطأ','error');}
        btn.disabled=false;btn.innerHTML='<i class="fas fa-paper-plane"></i>إرسال';
    }
}

function showWT(t){
    document.querySelectorAll('#secWallet .tab').forEach(b=>b.classList.remove('active'));event.target.classList.add('active');
    document.getElementById('wtDep').classList.add('hidden');document.getElementById('wtWth').classList.add('hidden');
    document.getElementById(t==='dep'?'wtDep':'wtWth').classList.remove('hidden');
}

async function doDep(e){
    e.preventDefault();if(!user){toast('سجل دخول','error');showS('auth');return;}
    const tx=document.getElementById('depT').value.trim();
    const btn=document.getElementById('depB');const ot=btn.innerHTML;
    if(!tx.startsWith('0x')||tx.length<60){toast('TXID غير صحيح','error');return;}
    btn.disabled=true;btn.innerHTML='<i class="fas fa-spinner fa-spin"></i>';
    try{
        const r=await fetch(`${API}/deposit`,{method:'POST',headers:{'Content-Type':'application/json','Authorization':`Bearer ${user.token}`},body:JSON.stringify({txid:tx})});
        const d=await r.json();
        if(d.success){user.balance=d.newBalance;localStorage.setItem('tgu',JSON.stringify(user));updUA();toast(`تم إيداع $${d.amount.toFixed(2)}!`,'success');document.getElementById('depT').value='';}else throw new Error(d.error);
    }catch(err){toast(err.message||'خطأ','error');}
    btn.disabled=false;btn.innerHTML=ot;
}

async function doWth(){
    if(!user){toast('سجل دخول','error');showS('auth');return;}
    const a=parseFloat(document.getElementById('wthA').value)||0;
    const w=document.getElementById('wthW').value.trim();
    if(a<2){toast('الحد الأدنى $2','error');return;}
    if(a>(user.balance||0)){toast('رصيد غير كافٍ','error');return;}
    if(!w.startsWith('0x')||w.length!==42){toast('عنوان غير صحيح','error');return;}
    try{
        const r=await fetch(`${API}/withdraw`,{method:'POST',headers:{'Content-Type':'application/json','Authorization':`Bearer ${user.token}`},body:JSON.stringify({amount:a,address:w})});
        const d=await r.json();
        if(d.success){user.balance=d.newBalance;localStorage.setItem('tgu',JSON.stringify(user));updUA();toast('تم إرسال الطلب','success');document.getElementById('wthA').value='';document.getElementById('wthW').value='';}else throw new Error(d.error);
    }catch(err){toast(err.message||'خطأ','error');}
}

function copyW(){navigator.clipboard.writeText(WALL);toast('تم النسخ','success');}

async function loadNums(){
    const l=document.getElementById('numL');l.innerHTML='<div class="spin"></div>';
    if(!user){l.innerHTML='<div class="empty"><i class="fas fa-sign-in-alt"></i><p>سجل دخول</p></div>';return;}
    try{
        const r=await fetch(`${API}/my-numbers`,{headers:{'Authorization':`Bearer ${user.token}`}});
        const d=await r.json();
        if(d.numbers?.length){
            l.innerHTML=d.numbers.map(n=>{
                const c=countries.find(x=>x.code===n.country);
                return`<div class="num-c"><div class="num-h"><div><div class="num-p">${n.phone}</div><div style="color:var(--tx2);font-size:.8rem">${c?.name||n.country}</div></div><span class="badge ${n.status}">${n.status==='active'?'نشط':n.status==='completed'?'مكتمل':'معلق'}</span></div>${n.status==='active'?`<div class="msg-box" id="nm${n.id}"><div class="wait"><i class="fas fa-spinner fa-spin"></i></div></div><button class="btn btn-s" style="margin-top:10px" onclick="compBuy('${n.id}')"><i class="fas fa-check"></i>تم الدخول</button>`:''}</div>`;
            }).join('');
            d.numbers.filter(n=>n.status==='active').forEach(n=>pollN(n.id));
        }else l.innerHTML='<div class="empty"><i class="fas fa-mobile-alt"></i><p>لا أرقام</p></div>';
    }catch(e){l.innerHTML='<div class="empty"><i class="fas fa-exclamation-circle"></i><p>خطأ</p></div>';}
}

function pollN(id){
    const poll=async()=>{const b=document.getElementById('nm'+id);if(!b)return;try{const r=await fetch(`${API}/messages/${id}`,{headers:{'Authorization':`Bearer ${user.token}`}});const d=await r.json();if(d.messages?.length)b.innerHTML=d.messages.map(m=>`<div class="msg-i"><div class="msg-c">${m.code}</div><div class="msg-t">${new Date(m.timestamp).toLocaleString('ar')}</div></div>`).join('');else b.innerHTML='<p style="text-align:center;color:var(--tx2);padding:12px">انتظار...</p>';}catch(e){}};
    poll();polls['n'+id]=setInterval(poll,3000);
}

async function loadProf(){
    const c=document.getElementById('profC');
    if(!user){c.innerHTML='<div class="empty"><i class="fas fa-sign-in-alt"></i><p>سجل دخول</p></div>';return;}
    await refreshU();
    c.innerHTML=`
        <div class="ref-box"><div class="ref-t"><i class="fas fa-gift"></i>برنامج الإحالة</div><div class="ref-code"><span>${user.referralCode||'N/A'}</span><button class="copy" onclick="copyRef()"><i class="fas fa-copy"></i></button></div><div class="ref-stats"><div class="ref-stat"><div class="ref-stat-v">${user.referralCount||0}</div><div class="ref-stat-l">إحالة</div></div><div class="ref-stat"><div class="ref-stat-v">$${(user.referralEarnings||0).toFixed(2)}</div><div class="ref-stat-l">أرباح</div></div></div></div>
        <div class="fcard"><h3 style="margin-bottom:14px"><i class="fas fa-user"></i> معلومات الحساب</h3><div class="fg"><label class="fl">الاسم</label><input type="text" class="fi" value="${user.username}" disabled></div><div class="fg"><label class="fl">البريد</label><input type="email" class="fi" value="${user.email}" disabled></div><div class="fg"><label class="fl">الرصيد</label><input type="text" class="fi" value="$${(user.balance||0).toFixed(2)}" disabled></div><button class="btn btn-d" onclick="logout()"><i class="fas fa-sign-out-alt"></i>خروج</button></div>`;
}

function copyRef(){if(!user?.referralCode)return;navigator.clipboard.writeText(`${location.origin}?ref=${user.referralCode}`);toast('تم نسخ الرابط','success');}

async function loadAdm(){
    if(!isAdm)return;
    document.getElementById('admT').innerHTML=`<button class="admin-tab active" data-t="sells"><i class="fas fa-clock"></i>طلبات البيع</button><button class="admin-tab" data-t="wths"><i class="fas fa-money-bill"></i>السحوبات</button><button class="admin-tab" data-t="users"><i class="fas fa-users"></i>المستخدمين</button><button class="admin-tab" data-t="nums"><i class="fas fa-phone"></i>الأرقام</button><button class="admin-tab" data-t="add"><i class="fas fa-plus"></i>إضافة رقم</button>`;
    document.getElementById('admT').onclick=e=>{const t=e.target.closest('.admin-tab');if(t){document.querySelectorAll('.admin-tab').forEach(x=>x.classList.remove('active'));t.classList.add('active');loadAT(t.dataset.t);}};
    loadAT('sells');
}

async function loadAT(t){
    const c=document.getElementById('admC');c.innerHTML='<div class="spin"></div>';
    try{
        if(t==='sells'){
            const r=await fetch(`${API}/admin/sells?admin=true`);const d=await r.json();
            if(d.items?.length)c.innerHTML=d.items.map(s=>`<div class="admin-item"><div class="admin-h"><div class="admin-m"><div class="admin-t" style="font-family:monospace;direction:ltr">${s.phone}</div><div class="admin-meta">${countries.find(x=>x.code===s.country)?.name||s.country} • $${s.price} • ${s.username}</div></div><span class="badge pending">معلق</span></div><div class="admin-acts"><button class="admin-btn ok" onclick="admAppS('${s.id}')"><i class="fas fa-check"></i>موافقة</button><button class="admin-btn no" onclick="admRejS('${s.id}')"><i class="fas fa-times"></i>رفض</button></div></div>`).join('');
            else c.innerHTML='<div class="empty"><i class="fas fa-inbox"></i><p>لا طلبات</p></div>';
        }else if(t==='wths'){
            const r=await fetch(`${API}/admin/withdrawals?admin=true`);const d=await r.json();
            if(d.items?.length)c.innerHTML=d.items.map(w=>`<div class="admin-item"><div class="admin-h"><div class="admin-m"><div class="admin-t">$${w.amount.toFixed(2)}</div><div class="admin-meta">${w.username} • ${w.address?.slice(0,15)}...</div></div><span class="badge ${w.status}">${w.status}</span></div>${w.status==='pending'?`<div class="admin-acts"><button class="admin-btn ok" onclick="admAppW('${w.id}')"><i class="fas fa-check"></i>موافقة</button><button class="admin-btn no" onclick="admRejW('${w.id}')"><i class="fas fa-times"></i>رفض</button></div>`:''}</div>`).join('');
            else c.innerHTML='<div class="empty"><i class="fas fa-inbox"></i><p>لا طلبات</p></div>';
        }else if(t==='users'){
            const r=await fetch(`${API}/admin/users?admin=true`);const d=await r.json();
            if(d.users?.length)c.innerHTML=d.users.map(u=>`<div class="admin-item"><div class="admin-h"><div class="admin-m"><div class="admin-t">${u.username} ${u.banned?'<span class="badge" style="background:rgba(255,82,82,.2);color:var(--d)">محظور</span>':''}</div><div class="admin-meta">${u.email} • $${(u.balance||0).toFixed(2)} • ${u.referralCount||0} إحالة</div></div></div><div class="admin-acts"><button class="admin-btn edit" onclick="editU('${u.id}',${u.balance||0})"><i class="fas fa-edit"></i>تعديل الرصيد</button>${u.banned?`<button class="admin-btn ok" onclick="unbanU('${u.id}')"><i class="fas fa-unlock"></i>رفع الحظر</button>`:`<button class="admin-btn no" onclick="banU('${u.id}')"><i class="fas fa-ban"></i>حظر</button>`}</div></div>`).join('');
            else c.innerHTML='<div class="empty"><i class="fas fa-users"></i><p>لا مستخدمين</p></div>';
        }else if(t==='nums'){
            const r=await fetch(`${API}/admin/numbers?admin=true`);const d=await r.json();
            if(d.items?.length)c.innerHTML=d.items.map(n=>`<div class="admin-item"><div class="admin-h"><div class="admin-m"><div class="admin-t" style="font-family:monospace;direction:ltr">${n.phone}</div><div class="admin-meta">${countries.find(x=>x.code===n.country)?.name||n.country} • $${n.price}</div></div><span class="badge ${n.status}">${n.status}</span></div><div class="admin-acts"><button class="admin-btn no" onclick="delN('${n.id}')"><i class="fas fa-trash"></i>حذف</button></div></div>`).join('');
            else c.innerHTML='<div class="empty"><i class="fas fa-phone"></i><p>لا أرقام</p></div>';
        }else if(t==='add'){
            c.innerHTML=`<div class="fcard"><div class="alert alert-i"><i class="fas fa-info-circle"></i><span>إضافة رقم جديد</span></div><form id="addF"><div class="fg"><label class="fl">الرقم</label><input type="tel" class="fi" id="addP" placeholder="+1234567890" dir="ltr" required></div><div class="fg hidden" id="addCG"><label class="fl">الكود</label><input type="text" class="fi" id="addC" placeholder="12345" dir="ltr" maxlength="6"></div><button type="submit" class="btn btn-p" id="addB"><i class="fas fa-paper-plane"></i>إرسال الكود</button></form></div>`;
            document.getElementById('addF').onsubmit=doAddN;
        }
    }catch(e){c.innerHTML='<div class="empty"><i class="fas fa-exclamation-circle"></i><p>خطأ</p></div>';}
}

async function doAddN(e){
    e.preventDefault();const p=document.getElementById('addP').value.trim();const cg=document.getElementById('addCG');const c=document.getElementById('addC').value.trim();const btn=document.getElementById('addB');const ot=btn.innerHTML;
    if(cg.classList.contains('hidden')){
        btn.disabled=true;btn.innerHTML='<i class="fas fa-spinner fa-spin"></i>';
        try{const r=await fetch(`${API}/admin/add-send-code?admin=true`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone:p})});const d=await r.json();if(d.success){cg.classList.remove('hidden');btn.innerHTML='<i class="fas fa-check"></i>تأكيد';toast('تم الإرسال','success');}else throw new Error(d.error||d.message);}catch(err){toast(err.message,'error');btn.innerHTML=ot;}
        btn.disabled=false;
    }else{
        if(c.length<5){toast('أدخل الكود','error');return;}
        btn.disabled=true;btn.innerHTML='<i class="fas fa-spinner fa-spin"></i>';
        try{const r=await fetch(`${API}/admin/add-verify?admin=true`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({phone:p,code:c})});const d=await r.json();if(d.success){toast('تمت الإضافة!','success');e.target.reset();cg.classList.add('hidden');loadC();loadAT('nums');}else throw new Error(d.error);}catch(err){toast(err.message,'error');}
        btn.disabled=false;btn.innerHTML='<i class="fas fa-paper-plane"></i>إرسال الكود';
    }
}

async function admAppS(id){try{const r=await fetch(`${API}/admin/approve-sell?admin=true`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});const d=await r.json();if(d.success){toast('تمت الموافقة','success');loadAT('sells');loadC();}else throw new Error(d.error);}catch(e){toast(e.message,'error');}}
async function admRejS(id){try{const r=await fetch(`${API}/admin/reject-sell?admin=true`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});const d=await r.json();if(d.success){toast('تم الرفض','success');loadAT('sells');}else throw new Error(d.error);}catch(e){toast(e.message,'error');}}
async function admAppW(id){const tx=prompt('TXID:');if(!tx)return;try{const r=await fetch(`${API}/admin/approve-withdrawal?admin=true`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,txid:tx})});const d=await r.json();if(d.success){toast('تمت الموافقة','success');loadAT('wths');}else throw new Error(d.error);}catch(e){toast(e.message,'error');}}
async function admRejW(id){const reason=prompt('سبب الرفض:');try{const r=await fetch(`${API}/admin/reject-withdrawal?admin=true`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,reason})});const d=await r.json();if(d.success){toast('تم الرفض','success');loadAT('wths');}else throw new Error(d.error);}catch(e){toast(e.message,'error');}}
async function delN(id){if(!confirm('حذف هذا الرقم؟'))return;try{const r=await fetch(`${API}/admin/delete-number?admin=true`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});const d=await r.json();if(d.success){toast('تم الحذف','success');loadAT('nums');loadC();}else throw new Error(d.error);}catch(e){toast(e.message,'error');}}
async function banU(id){const reason=prompt('سبب الحظر:');if(!reason)return;try{const r=await fetch(`${API}/admin/user/${id}/ban?admin=true`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({reason})});const d=await r.json();if(d.success){toast('تم الحظر','success');loadAT('users');}else throw new Error(d.error);}catch(e){toast(e.message,'error');}}
async function unbanU(id){try{const r=await fetch(`${API}/admin/user/${id}/unban?admin=true`,{method:'POST',headers:{'Content-Type':'application/json'}});const d=await r.json();if(d.success){toast('تم رفع الحظر','success');loadAT('users');}else throw new Error(d.error);}catch(e){toast(e.message,'error');}}
function editU(id,bal){const newBal=prompt('الرصيد الجديد:',bal);if(newBal===null)return;const amount=parseFloat(newBal)-bal;if(isNaN(amount))return;addBal(id,amount);}
async function addBal(id,amount){try{const r=await fetch(`${API}/admin/user/${id}/add-balance?admin=true`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({amount,reason:'تعديل يدوي'})});const d=await r.json();if(d.success){toast('تم التعديل','success');loadAT('users');}else throw new Error(d.error);}catch(e){toast(e.message,'error');}}

function toast(msg,type='success'){const c=document.getElementById('toasts');const t=document.createElement('div');t.className=`toast ${type}`;t.innerHTML=`<i class="fas fa-${type==='success'?'check-circle':'exclamation-circle'}"></i><span>${msg}</span>`;c.appendChild(t);setTimeout(()=>t.remove(),3000);}

window.addEventListener('beforeunload',()=>Object.values(polls).forEach(p=>clearInterval(p)));
document.addEventListener('keydown',e=>{if(e.key==='Escape')closeMod();});
document.getElementById('modal').addEventListener('click',e=>{if(e.target.id==='modal')closeMod();});
</script>
</body>
</html>'''

# ============== Routes ==============

@app.route('/')
def index():
    return Response(HTML, mimetype='text/html')

@app.route('/api/stats')
def stats():
    numbers = fb_get('numbers') or {}
    users = fb_get('users') or {}
    countries = get_countries()
    
    available = sum(1 for n in numbers.values() if n and n.get('status') == 'available')
    sold = sum(1 for n in numbers.values() if n and n.get('status') == 'sold')
    
    return jsonify({
        'availableNumbers': available,
        'soldNumbers': sold,
        'totalUsers': len([u for u in users.values() if u]),
        'totalCountries': len([c for c in countries.values() if c and c.get('enabled', True)])
    })

@app.route('/api/countries')
def countries_api():
    numbers = fb_get('numbers') or {}
    countries = get_countries()
    
    result = []
    for code, info in countries.items():
        if info and info.get('enabled', True):
            count = sum(1 for n in numbers.values() if n and n.get('status') == 'available' and n.get('country') == code)
            result.append({
                'code': code,
                'name': info['name'],
                'flag': info['flag'],
                'phoneCode': info['code'],
                'buyPrice': info['buy'],
                'sellPrice': info['sell'],
                'stock': count
            })
    
    result.sort(key=lambda x: (-x['stock'], x['name']))
    return jsonify({'success': True, 'countries': result})

@app.route('/api/settings')
def settings_api():
    s = get_settings()
    return jsonify({
        'maintenanceMode': s.get('maintenanceMode', False),
        'registrationEnabled': s.get('registrationEnabled', True),
        'buyEnabled': s.get('buyEnabled', True),
        'sellEnabled': s.get('sellEnabled', True),
        'referralBonus': s.get('referralBonus', 0.01)
    })

# Auth
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    ref_code = data.get('referralCode', '').strip()
    
    if not all([username, email, password]):
        return jsonify({'success': False, 'error': 'جميع الحقول مطلوبة'})
    if len(password) < 6:
        return jsonify({'success': False, 'error': 'كلمة المرور قصيرة'})
    if len(username) < 3:
        return jsonify({'success': False, 'error': 'الاسم قصير'})
    
    users = fb_get('users') or {}
    for u in users.values():
        if u and u.get('email') == email:
            return jsonify({'success': False, 'error': 'البريد مستخدم'})
    
    fp = get_fingerprint(request)
    token = generate_token()
    my_ref = generate_referral_code()
    
    new_user = {
        'username': username,
        'email': email,
        'password': hash_password(password),
        'balance': 0.0,
        'token': token,
        'referralCode': my_ref,
        'referredBy': None,
        'referralCount': 0,
        'referralEarnings': 0.0,
        'banned': False,
        'createdAt': datetime.now().isoformat()
    }
    
    uid = fb_push('users', new_user)
    
    if uid:
        fb_push('fingerprints', {'userId': uid, **fp, 'createdAt': datetime.now().isoformat()})
        
        # Process referral
        if ref_code:
            for ref_uid, ref_user in users.items():
                if ref_user and ref_user.get('referralCode') == ref_code:
                    is_fraud, fraud_uid, sim = check_fraud(uid, fp)
                    if is_fraud:
                        fb_update(f'users/{uid}', {'banned': True, 'banReason': f'احتيال ({sim*100:.0f}%)'})
                        fb_push('fraud_logs', {'newUser': uid, 'matched': fraud_uid, 'similarity': sim, 'createdAt': datetime.now().isoformat()})
                        return jsonify({'success': False, 'error': 'تم اكتشاف نشاط مشبوه'})
                    
                    settings = get_settings()
                    bonus = settings.get('referralBonus', 0.01)
                    fb_update(f'users/{ref_uid}', {
                        'balance': ref_user.get('balance', 0) + bonus,
                        'referralCount': ref_user.get('referralCount', 0) + 1,
                        'referralEarnings': ref_user.get('referralEarnings', 0) + bonus
                    })
                    fb_update(f'users/{uid}', {'referredBy': ref_uid})
                    break
        
        return jsonify({
            'success': True,
            'user': {'id': uid, 'username': username, 'email': email, 'balance': 0.0, 'token': token, 'referralCode': my_ref, 'referralCount': 0, 'referralEarnings': 0.0}
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
                return jsonify({'success': False, 'error': f"حسابك محظور: {u.get('banReason', '')}"})
            
            token = generate_token()
            fb_update(f'users/{uid}', {'token': token, 'lastLogin': datetime.now().isoformat()})
            
            return jsonify({
                'success': True,
                'user': {
                    'id': uid, 'username': u.get('username'), 'email': email,
                    'balance': u.get('balance', 0), 'token': token,
                    'referralCode': u.get('referralCode'),
                    'referralCount': u.get('referralCount', 0),
                    'referralEarnings': u.get('referralEarnings', 0)
                }
            })
    
    return jsonify({'success': False, 'error': 'بيانات غير صحيحة'})

@app.route('/api/auth/me')
@verify_token
def me():
    return jsonify({
        'success': True,
        'user': {
            'id': request.user_id,
            'username': request.user.get('username'),
            'email': request.user.get('email'),
            'balance': request.user.get('balance', 0),
            'referralCode': request.user.get('referralCode'),
            'referralCount': request.user.get('referralCount', 0),
            'referralEarnings': request.user.get('referralEarnings', 0)
        }
    })

# Buy
@app.route('/api/buy', methods=['POST'])
@verify_token
def buy():
    data = request.json or {}
    country = data.get('country')
    
    countries = get_countries()
    if country not in countries:
        return jsonify({'success': False, 'error': 'دولة غير مدعومة'})
    
    info = countries[country]
    price = info['buy']
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
        return jsonify({'success': False, 'error': 'لا توجد أرقام'})
    
    new_balance = balance - price
    fb_update(f'users/{request.user_id}', {'balance': new_balance})
    
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
    
    return jsonify({'success': True, 'purchaseId': purchase_id, 'phone': target['phone'], 'newBalance': new_balance})

@app.route('/api/messages/<purchase_id>')
@verify_token
def messages(purchase_id):
    purchase = fb_get(f'purchases/{purchase_id}')
    if not purchase or purchase.get('userId') != request.user_id:
        return jsonify({'success': False, 'error': 'غير موجود'})
    
    session = purchase.get('session')
    if not session:
        return jsonify({'success': True, 'messages': []})
    
    try:
        msgs = run_async(tg_get_messages(session))
        return jsonify({'success': True, 'messages': msgs})
    except:
        return jsonify({'success': True, 'messages': []})

@app.route('/api/complete', methods=['POST'])
@verify_token
def complete():
    data = request.json or {}
    purchase_id = data.get('purchaseId')
    
    purchase = fb_get(f'purchases/{purchase_id}')
    if not purchase or purchase.get('userId') != request.user_id:
        return jsonify({'success': False, 'error': 'غير موجود'})
    
    fb_update(f'purchases/{purchase_id}', {'status': 'completed', 'completedAt': datetime.now().isoformat()})
    return jsonify({'success': True})

@app.route('/api/my-numbers')
@verify_token
def my_numbers():
    purchases = fb_get('purchases') or {}
    result = []
    for pid, p in purchases.items():
        if p and p.get('userId') == request.user_id:
            result.append({'id': pid, 'phone': p.get('phone'), 'country': p.get('country'), 'status': p.get('status'), 'createdAt': p.get('createdAt')})
    result.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
    return jsonify({'success': True, 'numbers': result})

# Sell
@app.route('/api/sell/send-code', methods=['POST'])
@verify_token
def sell_send():
    data = request.json or {}
    phone = data.get('phone', '').strip()
    
    if not phone.startswith('+'):
        return jsonify({'success': False, 'error': 'الرقم يجب أن يبدأ بـ +'})
    
    country = detect_country(phone)
    if not country:
        return jsonify({'success': False, 'error': 'دولة غير مدعومة'})
    
    try:
        success, msg = run_async(tg_send_code(phone))
        if success:
            countries = get_countries()
            return jsonify({'success': True, 'country': country, 'countryName': countries[country]['name'], 'price': countries[country]['sell']})
        return jsonify({'success': False, 'error': msg})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/sell/verify', methods=['POST'])
@verify_token
def sell_verify():
    data = request.json or {}
    phone = data.get('phone', '').strip()
    code = data.get('code', '').strip()
    
    if not phone or not code:
        return jsonify({'success': False, 'error': 'بيانات ناقصة'})
    
    country = detect_country(phone)
    if not country:
        return jsonify({'success': False, 'error': 'دولة غير مدعومة'})
    
    try:
        success, msg, session = run_async(tg_verify(phone, code))
        if not success:
            return jsonify({'success': False, 'error': msg})
        
        countries = get_countries()
        price = countries[country]['sell']
        
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
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Deposit
@app.route('/api/deposit', methods=['POST'])
@verify_token
def deposit():
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
    
    fb_push('deposits', {'userId': request.user_id, 'txid': txid, 'amount': amount, 'status': 'approved', 'createdAt': datetime.now().isoformat()})
    
    new_balance = request.user.get('balance', 0) + amount
    fb_update(f'users/{request.user_id}', {'balance': new_balance})
    
    return jsonify({'success': True, 'amount': amount, 'newBalance': new_balance})

# Withdraw
@app.route('/api/withdraw', methods=['POST'])
@verify_token
def withdraw():
    data = request.json or {}
    amount = float(data.get('amount', 0))
    address = data.get('address', '').strip()
    
    if amount < 2:
        return jsonify({'success': False, 'error': 'الحد الأدنى $2'})
    if not address.startswith('0x') or len(address) != 42:
        return jsonify({'success': False, 'error': 'عنوان غير صحيح'})
    
    balance = request.user.get('balance', 0)
    if balance < amount:
        return jsonify({'success': False, 'error': 'رصيد غير كافٍ'})
    
    new_balance = balance - amount
    fb_update(f'users/{request.user_id}', {'balance': new_balance})
    
    fb_push('withdrawals', {
        'userId': request.user_id,
        'username': request.user.get('username'),
        'amount': amount,
        'address': address,
        'status': 'pending',
        'createdAt': datetime.now().isoformat()
    })
    
    return jsonify({'success': True, 'newBalance': new_balance})

# Admin Routes
@app.route('/api/admin/sells')
def admin_sells():
    sells = fb_get('sell_requests') or {}
    result = [{'id': k, **v} for k, v in sells.items() if v and v.get('status') == 'pending']
    return jsonify({'success': True, 'items': result})

@app.route('/api/admin/approve-sell', methods=['POST'])
def admin_approve_sell():
    data = request.json or {}
    sell_id = data.get('id')
    
    sell = fb_get(f'sell_requests/{sell_id}')
    if not sell:
        return jsonify({'success': False, 'error': 'غير موجود'})
    
    countries = get_countries()
    country = sell.get('country')
    buy_price = countries.get(country, {}).get('buy', 1.0)
    
    fb_push('numbers', {
        'phone': sell['phone'],
        'country': country,
        'price': buy_price,
        'session': sell.get('session'),
        'status': 'available',
        'createdAt': datetime.now().isoformat()
    })
    
    fb_update(f'sell_requests/{sell_id}', {'status': 'approved'})
    
    user = fb_get(f"users/{sell['userId']}")
    if user:
        new_bal = user.get('balance', 0) + sell['price']
        fb_update(f"users/{sell['userId']}", {'balance': new_bal})
    
    return jsonify({'success': True})

@app.route('/api/admin/reject-sell', methods=['POST'])
def admin_reject_sell():
    data = request.json or {}
    fb_update(f"sell_requests/{data.get('id')}", {'status': 'rejected'})
    return jsonify({'success': True})

@app.route('/api/admin/withdrawals')
def admin_withdrawals():
    wths = fb_get('withdrawals') or {}
    result = [{'id': k, **v} for k, v in wths.items() if v]
    result.sort(key=lambda x: x.get('createdAt', ''), reverse=True)
    return jsonify({'success': True, 'items': result})

@app.route('/api/admin/approve-withdrawal', methods=['POST'])
def admin_approve_wth():
    data = request.json or {}
    wid = data.get('id')
    txid = data.get('txid', '')
    fb_update(f"withdrawals/{wid}", {'status': 'approved', 'txid': txid, 'approvedAt': datetime.now().isoformat()})
    return jsonify({'success': True})

@app.route('/api/admin/reject-withdrawal', methods=['POST'])
def admin_reject_wth():
    data = request.json or {}
    wid = data.get('id')
    
    wth = fb_get(f'withdrawals/{wid}')
    if wth:
        user = fb_get(f"users/{wth['userId']}")
        if user:
            new_bal = user.get('balance', 0) + wth.get('amount', 0)
            fb_update(f"users/{wth['userId']}", {'balance': new_bal})
    
    fb_update(f"withdrawals/{wid}", {'status': 'rejected', 'reason': data.get('reason', '')})
    return jsonify({'success': True})

@app.route('/api/admin/users')
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
                'referralCount': u.get('referralCount', 0),
                'banned': u.get('banned', False)
            })
    return jsonify({'success': True, 'users': result})

@app.route('/api/admin/user/<uid>/ban', methods=['POST'])
def admin_ban(uid):
    data = request.json or {}
    fb_update(f'users/{uid}', {'banned': True, 'banReason': data.get('reason', '')})
    return jsonify({'success': True})

@app.route('/api/admin/user/<uid>/unban', methods=['POST'])
def admin_unban(uid):
    fb_update(f'users/{uid}', {'banned': False, 'banReason': None})
    return jsonify({'success': True})

@app.route('/api/admin/user/<uid>/add-balance', methods=['POST'])
def admin_add_balance(uid):
    data = request.json or {}
    amount = float(data.get('amount', 0))
    
    user = fb_get(f'users/{uid}')
    if not user:
        return jsonify({'success': False, 'error': 'غير موجود'})
    
    new_bal = user.get('balance', 0) + amount
    fb_update(f'users/{uid}', {'balance': new_bal})
    
    return jsonify({'success': True, 'newBalance': new_bal})

@app.route('/api/admin/numbers')
def admin_numbers():
    numbers = fb_get('numbers') or {}
    result = [{'id': k, **v} for k, v in numbers.items() if v]
    return jsonify({'success': True, 'items': result})

@app.route('/api/admin/delete-number', methods=['POST'])
def admin_del_number():
    data = request.json or {}
    fb_delete(f"numbers/{data.get('id')}")
    return jsonify({'success': True})

@app.route('/api/admin/add-send-code', methods=['POST'])
def admin_send_code():
    data = request.json or {}
    phone = data.get('phone', '').strip()
    
    try:
        success, msg = run_async(tg_send_code(phone))
        return jsonify({'success': success, 'message': msg})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/add-verify', methods=['POST'])
def admin_verify_code():
    data = request.json or {}
    phone = data.get('phone', '').strip()
    code = data.get('code', '').strip()
    
    country = detect_country(phone)
    if not country:
        return jsonify({'success': False, 'error': 'دولة غير مدعومة'})
    
    try:
        success, msg, session = run_async(tg_verify(phone, code))
        if not success:
            return jsonify({'success': False, 'error': msg})
        
        countries = get_countries()
        fb_push('numbers', {
            'phone': phone,
            'country': country,
            'price': countries[country]['buy'],
            'session': session,
            'status': 'available',
            'createdAt': datetime.now().isoformat()
        })
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Error handler
@app.errorhandler(Exception)
def handle_error(e):
    return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

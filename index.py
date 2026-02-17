from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import json
import hashlib
import secrets
import requests
import asyncio
import re
import os
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
MIN_DEPOSIT = 1.5
MIN_WITHDRAWAL = 2.0

# Firebase
FIREBASE_URL = "https://lolaminig-afea4-default-rtdb.firebaseio.com"

# Thread pool for async operations
executor = ThreadPoolExecutor(max_workers=4)

# Country Prices
COUNTRY_PRICES = {
    'US': {'sell': 0.75, 'buy': 0.95, 'name': 'الولايات المتحدة', 'flag': 'us', 'code': '+1'},
    'UK': {'sell': 0.80, 'buy': 1.00, 'name': 'المملكة المتحدة', 'flag': 'gb', 'code': '+44'},
    'CA': {'sell': 0.25, 'buy': 0.45, 'name': 'كندا', 'flag': 'ca', 'code': '+1'},
    'DE': {'sell': 1.50, 'buy': 1.70, 'name': 'ألمانيا', 'flag': 'de', 'code': '+49'},
    'FR': {'sell': 1.20, 'buy': 1.40, 'name': 'فرنسا', 'flag': 'fr', 'code': '+33'},
    'NL': {'sell': 1.00, 'buy': 1.20, 'name': 'هولندا', 'flag': 'nl', 'code': '+31'},
    'PL': {'sell': 0.90, 'buy': 1.10, 'name': 'بولندا', 'flag': 'pl', 'code': '+48'},
    'AU': {'sell': 1.00, 'buy': 1.20, 'name': 'أستراليا', 'flag': 'au', 'code': '+61'}
}

# Session storage
phone_sessions = {}

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
def fb_push(path, data): 
    r = fb_request('POST', path, data)
    return r.get('name') if r else None
def fb_update(path, data): return fb_request('PATCH', path, data)
def fb_delete(path): return fb_request('DELETE', path)

# ============== Helpers ==============
def generate_token():
    return secrets.token_hex(32)

def hash_password(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()

def detect_country(phone):
    phone = phone.replace(' ', '').replace('-', '')
    if phone.startswith('+49'): return 'DE'
    elif phone.startswith('+44'): return 'UK'
    elif phone.startswith('+33'): return 'FR'
    elif phone.startswith('+31'): return 'NL'
    elif phone.startswith('+48'): return 'PL'
    elif phone.startswith('+61'): return 'AU'
    elif phone.startswith('+1'):
        if len(phone) >= 5:
            area = phone[2:5]
            ca_codes = ['204','226','236','249','250','289','306','343','365','387',
                       '403','416','418','431','437','438','450','506','514','519',
                       '548','579','581','587','604','613','639','647','672','705',
                       '709','778','780','782','807','819','825','867','873','902','905']
            return 'CA' if area in ca_codes else 'US'
        return 'US'
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
                request.user_id = uid
                request.user = udata
                return f(*args, **kwargs)
        return jsonify({'success': False, 'error': 'جلسة غير صالحة'}), 401
    return decorated

# ============== Telegram Functions ==============
def run_telegram_async(coro):
    """Run async telegram operation in separate thread with new event loop"""
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
                    if amount >= MIN_DEPOSIT:
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

@app.route('/api/stats')
def get_stats():
    numbers = fb_get('numbers') or {}
    users = fb_get('users') or {}
    available = sum(1 for n in numbers.values() if n and n.get('status') == 'available')
    sold = sum(1 for n in numbers.values() if n and n.get('status') == 'sold')
    return jsonify({
        'availableNumbers': available,
        'soldNumbers': sold,
        'totalUsers': len(users)
    })

@app.route('/api/countries')
def get_countries():
    numbers = fb_get('numbers') or {}
    result = []
    for code, info in COUNTRY_PRICES.items():
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
    return jsonify({'countries': result})

# Auth
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json or {}
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not all([username, email, password]):
        return jsonify({'success': False, 'error': 'جميع الحقول مطلوبة'})
    if len(password) < 6:
        return jsonify({'success': False, 'error': 'كلمة المرور قصيرة'})
    
    users = fb_get('users') or {}
    for u in users.values():
        if u and u.get('email') == email:
            return jsonify({'success': False, 'error': 'البريد مستخدم'})
    
    token = generate_token()
    uid = fb_push('users', {
        'username': username,
        'email': email,
        'password': hash_password(password),
        'balance': 0.0,
        'token': token,
        'createdAt': datetime.now().isoformat()
    })
    
    if uid:
        return jsonify({
            'success': True,
            'user': {'id': uid, 'username': username, 'email': email, 'balance': 0.0, 'token': token}
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
            token = generate_token()
            fb_update(f'users/{uid}', {'token': token})
            return jsonify({
                'success': True,
                'user': {'id': uid, 'username': u.get('username'), 'email': email, 
                        'balance': u.get('balance', 0), 'token': token}
            })
    return jsonify({'success': False, 'error': 'بيانات غير صحيحة'})

# Buy
@app.route('/api/buy', methods=['POST'])
@verify_token_decorator
def buy_number():
    data = request.json or {}
    country = data.get('country')
    
    if country not in COUNTRY_PRICES:
        return jsonify({'success': False, 'error': 'دولة غير مدعومة'})
    
    price = COUNTRY_PRICES[country]['buy']
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

# Sell
@app.route('/api/sell/send-code', methods=['POST'])
@verify_token_decorator
def sell_send_code():
    data = request.json or {}
    phone = data.get('phone', '').strip()
    
    if not phone.startswith('+'):
        return jsonify({'success': False, 'error': 'الرقم يجب أن يبدأ بـ +'})
    
    country = detect_country(phone)
    if not country:
        return jsonify({'success': False, 'error': 'دولة غير مدعومة'})
    
    try:
        success, msg = run_telegram_async(tg_send_code(phone))
        if success:
            return jsonify({
                'success': True,
                'country': country,
                'countryName': COUNTRY_PRICES[country]['name'],
                'price': COUNTRY_PRICES[country]['sell']
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
    
    try:
        success, msg, session = run_telegram_async(tg_verify_code(phone, code))
        if not success:
            return jsonify({'success': False, 'error': msg})
        
        price = COUNTRY_PRICES[country]['sell']
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

# Deposit
@app.route('/api/deposit', methods=['POST'])
@verify_token_decorator
def verify_deposit():
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
    fb_update(f'users/{request.user_id}', {'balance': new_balance})
    
    return jsonify({'success': True, 'amount': amount, 'newBalance': new_balance})

# Admin
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
    
    country = sell.get('country')
    buy_price = COUNTRY_PRICES.get(country, {}).get('buy', 1.0)
    
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

@app.route('/api/admin/numbers')
def admin_numbers():
    numbers = fb_get('numbers') or {}
    result = [{'id': k, **v} for k, v in numbers.items() if v]
    return jsonify({'success': True, 'items': result})

@app.route('/api/admin/delete-number', methods=['POST'])
def admin_delete():
    data = request.json or {}
    fb_delete(f"numbers/{data.get('id')}")
    return jsonify({'success': True})

@app.route('/api/admin/add-send-code', methods=['POST'])
def admin_send_code():
    data = request.json or {}
    phone = data.get('phone', '').strip()
    try:
        success, msg = run_telegram_async(tg_send_code(phone))
        return jsonify({'success': success, 'message': msg})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/admin/add-verify', methods=['POST'])
def admin_verify():
    data = request.json or {}
    phone = data.get('phone', '').strip()
    code = data.get('code', '').strip()
    
    country = detect_country(phone)
    if not country:
        return jsonify({'success': False, 'error': 'دولة غير مدعومة'})
    
    try:
        success, msg, session = run_telegram_async(tg_verify_code(phone, code))
        if not success:
            return jsonify({'success': False, 'error': msg})
        
        fb_push('numbers', {
            'phone': phone,
            'country': country,
            'price': COUNTRY_PRICES[country]['buy'],
            'session': session,
            'status': 'available',
            'createdAt': datetime.now().isoformat()
        })
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

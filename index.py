from flask import Flask, request, jsonify, send_file
import json
import os
import hashlib
import secrets
import time
import requests
from datetime import datetime
from functools import wraps

# Telegram MTProto
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError
import asyncio

app = Flask(__name__)

# Configuration
TELEGRAM_API_ID = 27241932
TELEGRAM_API_HASH = "218edeae0f4cf9053d7dcbf3b1485048"
WALLET_ADDRESS = "0x8E00A980274Cfb22798290586d97F7D185E3092D"
BSCSCAN_API_KEY = "8BHURRRGKXD35BPGQZ8E94CVEVAUNMD9UF"
USDT_CONTRACT = "0x55d398326f99059fF775485246999027B3197955"  # BSC USDT
MIN_DEPOSIT = 1.5
MIN_WITHDRAWAL = 2.0

# Firebase configuration
FIREBASE_URL = "https://lolaminig-afea4-default-rtdb.firebaseio.com"
FIREBASE_API_KEY = "AIzaSyDNz-0UL60ZXQdSGte8Tcqz-ciNPYQjLJM"

# Country prices
COUNTRY_PRICES = {
    'US': {'sell': 0.75, 'buy': 0.95},
    'UK': {'sell': 0.80, 'buy': 1.00},
    'CA': {'sell': 0.25, 'buy': 0.45},
    'DE': {'sell': 1.50, 'buy': 1.70},
    'FR': {'sell': 1.20, 'buy': 1.40},
    'NL': {'sell': 1.00, 'buy': 1.20},
    'PL': {'sell': 0.90, 'buy': 1.10},
    'AU': {'sell': 1.00, 'buy': 1.20}
}

# In-memory session storage for phone code hash
phone_code_hashes = {}
telegram_clients = {}

# Helper functions
def firebase_get(path):
    """Get data from Firebase"""
    try:
        response = requests.get(f"{FIREBASE_URL}/{path}.json")
        return response.json() if response.status_code == 200 else None
    except:
        return None

def firebase_set(path, data):
    """Set data in Firebase"""
    try:
        response = requests.put(f"{FIREBASE_URL}/{path}.json", json=data)
        return response.status_code == 200
    except:
        return False

def firebase_push(path, data):
    """Push data to Firebase"""
    try:
        response = requests.post(f"{FIREBASE_URL}/{path}.json", json=data)
        if response.status_code == 200:
            return response.json().get('name')
        return None
    except:
        return None

def firebase_update(path, data):
    """Update data in Firebase"""
    try:
        response = requests.patch(f"{FIREBASE_URL}/{path}.json", json=data)
        return response.status_code == 200
    except:
        return False

def firebase_delete(path):
    """Delete data from Firebase"""
    try:
        response = requests.delete(f"{FIREBASE_URL}/{path}.json")
        return response.status_code == 200
    except:
        return False

def generate_token():
    """Generate auth token"""
    return secrets.token_hex(32)

def hash_password(password):
    """Hash password"""
    return hashlib.sha256(password.encode()).hexdigest()

def detect_country(phone):
    """Detect country from phone number"""
    if phone.startswith('+49'):
        return 'DE'
    elif phone.startswith('+44'):
        return 'UK'
    elif phone.startswith('+33'):
        return 'FR'
    elif phone.startswith('+31'):
        return 'NL'
    elif phone.startswith('+48'):
        return 'PL'
    elif phone.startswith('+61'):
        return 'AU'
    elif phone.startswith('+1'):
        area_code = phone[2:5] if len(phone) > 4 else ''
        canada_codes = ['204', '226', '236', '249', '250', '289', '306', '343', '365', '387', 
                       '403', '416', '418', '431', '437', '438', '450', '506', '514', '519',
                       '548', '579', '581', '587', '604', '613', '639', '647', '672', '705',
                       '709', '778', '780', '782', '807', '819', '825', '867', '873', '902', '905']
        return 'CA' if area_code in canada_codes else 'US'
    return None

def verify_token(f):
    """Token verification decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'success': False, 'error': 'No token provided'}), 401
        
        users = firebase_get('users') or {}
        for user_id, user_data in users.items():
            if user_data.get('token') == token:
                request.user_id = user_id
                request.user = user_data
                return f(*args, **kwargs)
        
        return jsonify({'success': False, 'error': 'Invalid token'}), 401
    return decorated

async def get_telegram_client(phone):
    """Get or create Telegram client"""
    if phone in telegram_clients:
        return telegram_clients[phone]
    
    client = TelegramClient(StringSession(), TELEGRAM_API_ID, TELEGRAM_API_HASH)
    await client.connect()
    telegram_clients[phone] = client
    return client

async def send_code_request(phone):
    """Send code request to Telegram"""
    client = await get_telegram_client(phone)
    try:
        result = await client.send_code_request(phone)
        phone_code_hashes[phone] = result.phone_code_hash
        return True, result.phone_code_hash
    except Exception as e:
        return False, str(e)

async def sign_in_with_code(phone, code):
    """Sign in with code"""
    client = await get_telegram_client(phone)
    try:
        phone_code_hash = phone_code_hashes.get(phone)
        if not phone_code_hash:
            return False, "No code request found", None
        
        await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
        session_string = client.session.save()
        return True, "Success", session_string
    except PhoneCodeInvalidError:
        return False, "Invalid code", None
    except SessionPasswordNeededError:
        return False, "2FA enabled - not allowed", None
    except Exception as e:
        return False, str(e), None

async def get_telegram_messages(session_string, limit=5):
    """Get messages from Telegram (verification codes)"""
    try:
        client = TelegramClient(StringSession(session_string), TELEGRAM_API_ID, TELEGRAM_API_HASH)
        await client.connect()
        
        messages = []
        async for message in client.iter_messages(777000, limit=limit):  # 777000 is Telegram's ID
            if message.message:
                # Extract code from message
                import re
                codes = re.findall(r'\b\d{5,6}\b', message.message)
                if codes:
                    messages.append({
                        'code': codes[0],
                        'timestamp': message.date.isoformat(),
                        'text': message.message[:100]
                    })
        
        await client.disconnect()
        return messages
    except Exception as e:
        print(f"Error getting messages: {e}")
        return []

async def terminate_other_sessions(session_string):
    """Terminate all other sessions"""
    try:
        client = TelegramClient(StringSession(session_string), TELEGRAM_API_ID, TELEGRAM_API_HASH)
        await client.connect()
        await client.disconnect()
        return True
    except:
        return False

def verify_bsc_transaction(txid):
    """Verify BSC transaction"""
    try:
        # Get transaction details
        url = f"https://api.bscscan.com/api?module=proxy&action=eth_getTransactionByHash&txhash={txid}&apikey={BSCSCAN_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if data.get('result'):
            tx = data['result']
            to_address = tx.get('to', '').lower()
            
            # Check if it's a token transfer to our wallet
            if to_address == USDT_CONTRACT.lower():
                # Decode input data for ERC20 transfer
                input_data = tx.get('input', '')
                if input_data.startswith('0xa9059cbb'):  # transfer method
                    # Extract recipient and amount
                    recipient = '0x' + input_data[34:74]
                    amount_hex = input_data[74:138]
                    amount = int(amount_hex, 16) / (10 ** 18)
                    
                    if recipient.lower() == WALLET_ADDRESS.lower() and amount >= MIN_DEPOSIT:
                        return True, amount
            
            # Check direct BNB transfer
            if to_address == WALLET_ADDRESS.lower():
                value = int(tx.get('value', '0'), 16) / (10 ** 18)
                if value >= MIN_DEPOSIT:
                    return True, value
        
        return False, 0
    except Exception as e:
        print(f"Error verifying transaction: {e}")
        return False, 0

# Routes
@app.route('/')
def index():
    return send_file('index.html')

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    if not username or not email or not password:
        return jsonify({'success': False, 'error': 'جميع الحقول مطلوبة'})
    
    # Check if email exists
    users = firebase_get('users') or {}
    for user_data in users.values():
        if user_data.get('email') == email:
            return jsonify({'success': False, 'error': 'البريد الإلكتروني مستخدم بالفعل'})
    
    # Create user
    token = generate_token()
    user_id = firebase_push('users', {
        'username': username,
        'email': email,
        'password': hash_password(password),
        'balance': 0.0,
        'token': token,
        'createdAt': datetime.now().isoformat()
    })
    
    if user_id:
        return jsonify({
            'success': True,
            'user': {
                'id': user_id,
                'username': username,
                'email': email,
                'balance': 0.0,
                'token': token
            }
        })
    
    return jsonify({'success': False, 'error': 'حدث خطأ في إنشاء الحساب'})

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    
    users = firebase_get('users') or {}
    for user_id, user_data in users.items():
        if user_data.get('email') == email and user_data.get('password') == hash_password(password):
            # Generate new token
            token = generate_token()
            firebase_update(f'users/{user_id}', {'token': token})
            
            return jsonify({
                'success': True,
                'user': {
                    'id': user_id,
                    'username': user_data.get('username'),
                    'email': email,
                    'balance': user_data.get('balance', 0.0),
                    'token': token
                }
            })
    
    return jsonify({'success': False, 'error': 'بيانات الدخول غير صحيحة'})

@app.route('/api/stats')
def get_stats():
    numbers = firebase_get('numbers') or {}
    users = firebase_get('users') or {}
    
    available = sum(1 for n in numbers.values() if n.get('status') == 'available')
    sold = sum(1 for n in numbers.values() if n.get('status') == 'sold')
    
    return jsonify({
        'availableNumbers': available,
        'soldNumbers': sold,
        'totalUsers': len(users)
    })

@app.route('/api/numbers/available')
def get_available_numbers():
    numbers = firebase_get('numbers') or {}
    
    counts = {}
    for num in numbers.values():
        if num.get('status') == 'available':
            country = num.get('country', 'US')
            counts[country] = counts.get(country, 0) + 1
    
    return jsonify({'counts': counts})

@app.route('/api/numbers/buy', methods=['POST'])
@verify_token
def buy_number():
    data = request.json
    country_code = data.get('countryCode')
    
    if country_code not in COUNTRY_PRICES:
        return jsonify({'success': False, 'error': 'Invalid country'})
    
    price = COUNTRY_PRICES[country_code]['buy']
    user = request.user
    
    if user.get('balance', 0) < price:
        return jsonify({'success': False, 'error': 'رصيد غير كافٍ'})
    
    # Find available number
    numbers = firebase_get('numbers') or {}
    available_number = None
    number_id = None
    
    for nid, num in numbers.items():
        if num.get('status') == 'available' and num.get('country') == country_code:
            available_number = num
            number_id = nid
            break
    
    if not available_number:
        return jsonify({'success': False, 'error': 'لا توجد أرقام متاحة لهذه الدولة'})
    
    # Deduct balance
    new_balance = user.get('balance', 0) - price
    firebase_update(f'users/{request.user_id}', {'balance': new_balance})
    
    # Create purchase record
    purchase_id = firebase_push('purchases', {
        'userId': request.user_id,
        'numberId': number_id,
        'phone': available_number.get('phone'),
        'country': country_code,
        'price': price,
        'status': 'active',
        'sessionString': available_number.get('sessionString'),
        'createdAt': datetime.now().isoformat()
    })
    
    # Update number status
    firebase_update(f'numbers/{number_id}', {'status': 'sold', 'soldTo': request.user_id})
    
    return jsonify({
        'success': True,
        'purchaseId': purchase_id,
        'phone': available_number.get('phone')
    })

@app.route('/api/messages/<purchase_id>')
@verify_token
def get_messages(purchase_id):
    purchase = firebase_get(f'purchases/{purchase_id}')
    
    if not purchase or purchase.get('userId') != request.user_id:
        return jsonify({'success': False, 'error': 'Not found'})
    
    session_string = purchase.get('sessionString')
    if not session_string:
        return jsonify({'success': False, 'error': 'No session'})
    
    # Get messages asynchronously
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    messages = loop.run_until_complete(get_telegram_messages(session_string))
    loop.close()
    
    return jsonify({'success': True, 'messages': messages})

@app.route('/api/numbers/confirm-usage', methods=['POST'])
@verify_token
def confirm_usage():
    data = request.json
    purchase_id = data.get('purchaseId')
    
    purchase = firebase_get(f'purchases/{purchase_id}')
    
    if not purchase or purchase.get('userId') != request.user_id:
        return jsonify({'success': False, 'error': 'Not found'})
    
    # Terminate session
    session_string = purchase.get('sessionString')
    if session_string:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(terminate_other_sessions(session_string))
        loop.close()
    
    # Update purchase status
    firebase_update(f'purchases/{purchase_id}', {
        'status': 'completed',
        'completedAt': datetime.now().isoformat()
    })
    
    return jsonify({'success': True})

@app.route('/api/my-numbers')
@verify_token
def get_my_numbers():
    purchases = firebase_get('purchases') or {}
    
    user_numbers = []
    for pid, purchase in purchases.items():
        if purchase.get('userId') == request.user_id:
            user_numbers.append({
                'id': pid,
                'phone': purchase.get('phone'),
                'country': purchase.get('country'),
                'status': purchase.get('status'),
                'createdAt': purchase.get('createdAt')
            })
    
    return jsonify({'numbers': user_numbers})

@app.route('/api/sell/request-code', methods=['POST'])
@verify_token
def sell_request_code():
    data = request.json
    phone = data.get('phone', '').strip()
    
    if not phone.startswith('+'):
        return jsonify({'success': False, 'error': 'يجب أن يبدأ الرقم بـ +'})
    
    country = detect_country(phone)
    if not country:
        return jsonify({'success': False, 'error': 'الدولة غير مدعومة'})
    
    # Send code request
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    success, result = loop.run_until_complete(send_code_request(phone))
    loop.close()
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': result})

@app.route('/api/sell/verify-code', methods=['POST'])
@verify_token
def sell_verify_code():
    data = request.json
    phone = data.get('phone', '').strip()
    code = data.get('code', '').strip()
    
    country = detect_country(phone)
    if not country:
        return jsonify({'success': False, 'error': 'الدولة غير مدعومة'})
    
    # Verify code and get session
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    success, message, session_string = loop.run_until_complete(sign_in_with_code(phone, code))
    loop.close()
    
    if not success:
        return jsonify({'success': False, 'error': message})
    
    # Create sell request
    price = COUNTRY_PRICES[country]['sell']
    sell_id = firebase_push('sell_requests', {
        'userId': request.user_id,
        'username': request.user.get('username'),
        'phone': phone,
        'country': country,
        'price': price,
        'sessionString': session_string,
        'status': 'pending',
        'createdAt': datetime.now().isoformat()
    })
    
    return jsonify({'success': True, 'sellId': sell_id})

@app.route('/api/deposit/verify', methods=['POST'])
@verify_token
def verify_deposit():
    data = request.json
    txid = data.get('txid', '').strip()
    
    if not txid.startswith('0x'):
        return jsonify({'success': False, 'error': 'TXID غير صحيح'})
    
    # Check if already used
    deposits = firebase_get('deposits') or {}
    for dep in deposits.values():
        if dep.get('txid') == txid:
            return jsonify({'success': False, 'error': 'هذه المعاملة مستخدمة بالفعل'})
    
    # Verify transaction
    valid, amount = verify_bsc_transaction(txid)
    
    if not valid:
        return jsonify({'success': False, 'error': 'لم يتم العثور على المعاملة أو المبلغ أقل من الحد الأدنى'})
    
    # Add deposit record
    firebase_push('deposits', {
        'userId': request.user_id,
        'username': request.user.get('username'),
        'txid': txid,
        'amount': amount,
        'status': 'approved',
        'createdAt': datetime.now().isoformat()
    })
    
    # Update user balance
    new_balance = request.user.get('balance', 0) + amount
    firebase_update(f'users/{request.user_id}', {'balance': new_balance})
    
    return jsonify({
        'success': True,
        'amount': amount,
        'newBalance': new_balance
    })

# Admin routes
@app.route('/api/admin/pending-sells')
def admin_pending_sells():
    sells = firebase_get('sell_requests') or {}
    
    pending = []
    for sid, sell in sells.items():
        if sell.get('status') == 'pending':
            pending.append({
                'id': sid,
                'phone': sell.get('phone'),
                'country': sell.get('country'),
                'price': sell.get('price'),
                'username': sell.get('username'),
                'createdAt': sell.get('createdAt')
            })
    
    return jsonify({'items': pending})

@app.route('/api/admin/approve-sell', methods=['POST'])
def admin_approve_sell():
    data = request.json
    sell_id = data.get('id')
    
    sell = firebase_get(f'sell_requests/{sell_id}')
    if not sell:
        return jsonify({'success': False, 'error': 'Not found'})
    
    # Create number for sale
    buy_price = COUNTRY_PRICES[sell['country']]['buy']
    firebase_push('numbers', {
        'phone': sell['phone'],
        'country': sell['country'],
        'price': buy_price,
        'sessionString': sell['sessionString'],
        'status': 'available',
        'createdAt': datetime.now().isoformat()
    })
    
    # Update sell request
    firebase_update(f'sell_requests/{sell_id}', {'status': 'approved'})
    
    # Add balance to seller
    user = firebase_get(f"users/{sell['userId']}")
    if user:
        new_balance = user.get('balance', 0) + sell['price']
        firebase_update(f"users/{sell['userId']}", {'balance': new_balance})
    
    return jsonify({'success': True})

@app.route('/api/admin/reject-sell', methods=['POST'])
def admin_reject_sell():
    data = request.json
    sell_id = data.get('id')
    
    firebase_update(f'sell_requests/{sell_id}', {'status': 'rejected'})
    
    return jsonify({'success': True})

@app.route('/api/admin/pending-deposits')
def admin_pending_deposits():
    deposits = firebase_get('deposits') or {}
    
    pending = []
    for did, dep in deposits.items():
        if dep.get('status') == 'pending':
            pending.append({
                'id': did,
                'txid': dep.get('txid'),
                'amount': dep.get('amount'),
                'username': dep.get('username'),
                'status': dep.get('status')
            })
    
    return jsonify({'items': pending})

@app.route('/api/admin/approve-deposit', methods=['POST'])
def admin_approve_deposit():
    data = request.json
    deposit_id = data.get('id')
    
    deposit = firebase_get(f'deposits/{deposit_id}')
    if not deposit:
        return jsonify({'success': False, 'error': 'Not found'})
    
    # Update deposit status
    firebase_update(f'deposits/{deposit_id}', {'status': 'approved'})
    
    # Add balance to user
    user = firebase_get(f"users/{deposit['userId']}")
    if user:
        new_balance = user.get('balance', 0) + deposit['amount']
        firebase_update(f"users/{deposit['userId']}", {'balance': new_balance})
    
    return jsonify({'success': True})

@app.route('/api/admin/all-numbers')
def admin_all_numbers():
    numbers = firebase_get('numbers') or {}
    
    items = []
    for nid, num in numbers.items():
        items.append({
            'id': nid,
            'phone': num.get('phone'),
            'country': num.get('country'),
            'status': num.get('status'),
            'price': num.get('price')
        })
    
    return jsonify({'items': items})

@app.route('/api/admin/delete-number', methods=['POST'])
def admin_delete_number():
    data = request.json
    number_id = data.get('id')
    
    firebase_delete(f'numbers/{number_id}')
    
    return jsonify({'success': True})

@app.route('/api/admin/send-code', methods=['POST'])
def admin_send_code():
    data = request.json
    phone = data.get('phone', '').strip()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    success, result = loop.run_until_complete(send_code_request(phone))
    loop.close()
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': result})

@app.route('/api/admin/add-number', methods=['POST'])
def admin_add_number():
    data = request.json
    phone = data.get('phone', '').strip()
    code = data.get('code', '').strip()
    
    country = detect_country(phone)
    if not country:
        return jsonify({'success': False, 'error': 'الدولة غير مدعومة'})
    
    # Verify code
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    success, message, session_string = loop.run_until_complete(sign_in_with_code(phone, code))
    loop.close()
    
    if not success:
        return jsonify({'success': False, 'error': message})
    
    # Add number
    price = COUNTRY_PRICES[country]['buy']
    firebase_push('numbers', {
        'phone': phone,
        'country': country,
        'price': price,
        'sessionString': session_string,
        'status': 'available',
        'createdAt': datetime.now().isoformat()
    })
    
    return jsonify({'success': True})

@app.route('/api/admin/withdrawals')
def admin_withdrawals():
    withdrawals = firebase_get('withdrawals') or {}
    
    items = []
    for wid, w in withdrawals.items():
        items.append({
            'id': wid,
            'username': w.get('username'),
            'amount': w.get('amount'),
            'address': w.get('address'),
            'status': w.get('status')
        })
    
    return jsonify({'items': items})

@app.route('/api/admin/approve-withdrawal', methods=['POST'])
def admin_approve_withdrawal():
    data = request.json
    withdrawal_id = data.get('id')
    
    firebase_update(f'withdrawals/{withdrawal_id}', {'status': 'approved'})
    
    return jsonify({'success': True})

# Error handler
@app.errorhandler(Exception)
def handle_error(e):
    return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)

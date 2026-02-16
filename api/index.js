const https = require('https');
const crypto = require('crypto');

// ==================== CONFIG ====================
const JWT_SECRET = 'telenum_secret_2024_xyz';
const BSCSCAN_API_KEY = '8BHURRRGKXD35BPGQZ8E94CVEVAUNMD9UF';
const DEPOSIT_ADDRESS = '0x8E00A980274Cfb22798290586d97F7D185E3092D'.toLowerCase();

// Firebase Config
const FIREBASE_URL = 'https://lolaminig-afea4-default-rtdb.firebaseio.com';

// Telegram Config
const API_ID = 27241932;
const API_HASH = '218edeae0f4cf9053d7dcbf3b1485048';

// Country Prices
const countryPrices = {
    'US': { buy: 0.80, sell: 0.60, name: 'USA' },
    'UK': { buy: 1.00, sell: 0.80, name: 'UK' },
    'CA': { buy: 0.45, sell: 0.25, name: 'Canada' },
    'DE': { buy: 1.70, sell: 1.50, name: 'Germany' },
    'FR': { buy: 1.40, sell: 1.20, name: 'France' },
    'NL': { buy: 1.20, sell: 1.00, name: 'Netherlands' },
    'PL': { buy: 0.90, sell: 0.70, name: 'Poland' },
    'AU': { buy: 1.20, sell: 1.00, name: 'Australia' }
};

// ==================== HELPERS ====================

// Firebase Helper
async function firebaseRequest(path, method = 'GET', data = null) {
    return new Promise((resolve, reject) => {
        const url = new URL(`${FIREBASE_URL}${path}.json`);
        const options = {
            method,
            headers: { 'Content-Type': 'application/json' }
        };

        const req = https.request(url, options, (res) => {
            let body = '';
            res.on('data', chunk => body += chunk);
            res.on('end', () => {
                try {
                    resolve(JSON.parse(body));
                } catch (e) {
                    resolve(body);
                }
            });
        });

        req.on('error', reject);
        if (data) req.write(JSON.stringify(data));
        req.end();
    });
}

// JWT Helper
function createToken(payload) {
    const header = Buffer.from(JSON.stringify({ alg: 'HS256', typ: 'JWT' })).toString('base64url');
    const body = Buffer.from(JSON.stringify({ ...payload, exp: Date.now() + 7 * 24 * 60 * 60 * 1000 })).toString('base64url');
    const signature = crypto.createHmac('sha256', JWT_SECRET).update(`${header}.${body}`).digest('base64url');
    return `${header}.${body}.${signature}`;
}

function verifyToken(token) {
    try {
        const [header, body, signature] = token.split('.');
        const expectedSig = crypto.createHmac('sha256', JWT_SECRET).update(`${header}.${body}`).digest('base64url');
        if (signature !== expectedSig) return null;
        const payload = JSON.parse(Buffer.from(body, 'base64url').toString());
        if (payload.exp < Date.now()) return null;
        return payload;
    } catch (e) {
        return null;
    }
}

// Password Helper
function hashPassword(password) {
    return crypto.createHash('sha256').update(password + JWT_SECRET).digest('hex');
}

// BSCScan Helper
async function fetchBSC(endpoint) {
    return new Promise((resolve, reject) => {
        const url = `https://api.bscscan.com/api?${endpoint}&apikey=${BSCSCAN_API_KEY}`;
        https.get(url, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                try {
                    resolve(JSON.parse(data));
                } catch (e) {
                    reject(e);
                }
            });
        }).on('error', reject);
    });
}

// Response Helper
function sendResponse(res, statusCode, data) {
    res.writeHead(statusCode, {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization'
    });
    res.end(JSON.stringify(data));
}

// Parse Body
async function parseBody(req) {
    return new Promise((resolve) => {
        let body = '';
        req.on('data', chunk => body += chunk);
        req.on('end', () => {
            try {
                resolve(JSON.parse(body));
            } catch (e) {
                resolve({});
            }
        });
    });
}

// Get User from Token
function getUserFromRequest(req) {
    const auth = req.headers.authorization;
    if (!auth || !auth.startsWith('Bearer ')) return null;
    return verifyToken(auth.split(' ')[1]);
}

// Generate ID
function generateId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2, 9);
}

// ==================== MAIN HANDLER ====================

module.exports = async (req, res) => {
    // Handle CORS
    if (req.method === 'OPTIONS') {
        return sendResponse(res, 200, {});
    }

    const url = new URL(req.url, `http://${req.headers.host}`);
    const path = url.pathname.replace('/api', '');
    const method = req.method;

    try {
        // ==================== AUTH ROUTES ====================
        
        // Register
        if (path === '/auth/register' && method === 'POST') {
            const { username, email, password } = await parseBody(req);
            
            if (!username || !email || !password) {
                return sendResponse(res, 400, { error: 'جميع الحقول مطلوبة' });
            }

            // Check existing user
            const users = await firebaseRequest('/users') || {};
            const exists = Object.values(users).find(u => u.email === email);
            
            if (exists) {
                return sendResponse(res, 400, { error: 'البريد مستخدم بالفعل' });
            }

            // Create user
            const userId = generateId();
            const userData = {
                id: userId,
                username,
                email,
                password: hashPassword(password),
                balance: 0,
                createdAt: Date.now()
            };

            await firebaseRequest(`/users/${userId}`, 'PUT', userData);

            const token = createToken({ id: userId, email });
            return sendResponse(res, 200, {
                token,
                user: { id: userId, username, email, balance: 0 }
            });
        }

        // Login
        if (path === '/auth/login' && method === 'POST') {
            const { email, password } = await parseBody(req);
            
            if (!email || !password) {
                return sendResponse(res, 400, { error: 'جميع الحقول مطلوبة' });
            }

            const users = await firebaseRequest('/users') || {};
            let foundUser = null;

            for (const [id, user] of Object.entries(users)) {
                if (user.email === email && user.password === hashPassword(password)) {
                    foundUser = { ...user, id };
                    break;
                }
            }

            if (!foundUser) {
                return sendResponse(res, 400, { error: 'بيانات الدخول غير صحيحة' });
            }

            const token = createToken({ id: foundUser.id, email });
            return sendResponse(res, 200, {
                token,
                user: {
                    id: foundUser.id,
                    username: foundUser.username,
                    email: foundUser.email,
                    balance: foundUser.balance || 0
                }
            });
        }

        // Verify Token
        if (path === '/auth/verify' && method === 'GET') {
            const user = getUserFromRequest(req);
            if (!user) {
                return sendResponse(res, 401, { error: 'Unauthorized' });
            }

            const userData = await firebaseRequest(`/users/${user.id}`);
            if (!userData) {
                return sendResponse(res, 404, { error: 'User not found' });
            }

            return sendResponse(res, 200, {
                id: user.id,
                username: userData.username,
                email: userData.email,
                balance: userData.balance || 0
            });
        }

        // ==================== USER ROUTES ====================

        // Get Balance
        if (path === '/user/balance' && method === 'GET') {
            const user = getUserFromRequest(req);
            if (!user) {
                return sendResponse(res, 401, { error: 'Unauthorized' });
            }

            const userData = await firebaseRequest(`/users/${user.id}`);
            return sendResponse(res, 200, { balance: userData?.balance || 0 });
        }

        // ==================== DEPOSIT ROUTES ====================

        // Verify Deposit
        if (path === '/deposit/verify' && method === 'POST') {
            const user = getUserFromRequest(req);
            if (!user) {
                return sendResponse(res, 401, { error: 'Unauthorized' });
            }

            const { txid } = await parseBody(req);
            if (!txid) {
                return sendResponse(res, 400, { error: 'TXID مطلوب' });
            }

            // Check if already used
            const deposits = await firebaseRequest('/deposits') || {};
            const exists = Object.values(deposits).find(d => d.txid?.toLowerCase() === txid.toLowerCase());
            
            if (exists) {
                return sendResponse(res, 400, { error: 'هذا الايداع مستخدم بالفعل' });
            }

            // Check BSCScan for token transfers
            let amount = 0;
            let tokenType = 'USDT';

            // Try token transfers first
            const tokenTx = await fetchBSC(`module=account&action=tokentx&address=${DEPOSIT_ADDRESS}&sort=desc`);
            
            if (tokenTx.status === '1' && tokenTx.result) {
                const tx = tokenTx.result.find(t => t.hash.toLowerCase() === txid.toLowerCase());
                if (tx && tx.to.toLowerCase() === DEPOSIT_ADDRESS) {
                    const decimals = parseInt(tx.tokenDecimal) || 18;
                    amount = parseFloat(tx.value) / Math.pow(10, decimals);
                    tokenType = tx.tokenSymbol || 'TOKEN';
                }
            }

            // Try native BNB if no token found
            if (amount === 0) {
                const bnbTx = await fetchBSC(`module=account&action=txlist&address=${DEPOSIT_ADDRESS}&sort=desc`);
                
                if (bnbTx.status === '1' && bnbTx.result) {
                    const tx = bnbTx.result.find(t => t.hash.toLowerCase() === txid.toLowerCase());
                    if (tx && tx.to.toLowerCase() === DEPOSIT_ADDRESS) {
                        const bnbAmount = parseFloat(tx.value) / 1e18;
                        
                        // Get BNB price
                        const priceData = await new Promise((resolve) => {
                            https.get('https://api.binance.com/api/v3/ticker/price?symbol=BNBUSDT', (res) => {
                                let data = '';
                                res.on('data', chunk => data += chunk);
                                res.on('end', () => resolve(JSON.parse(data)));
                            }).on('error', () => resolve({ price: '300' }));
                        });
                        
                        amount = bnbAmount * parseFloat(priceData.price);
                        tokenType = 'BNB';
                    }
                }
            }

            if (amount < 1.5) {
                return sendResponse(res, 400, { error: 'الحد الادنى للايداع $1.50 او العملية غير موجودة' });
            }

            // Save deposit
            const depositId = generateId();
            await firebaseRequest(`/deposits/${depositId}`, 'PUT', {
                id: depositId,
                userId: user.id,
                txid,
                amount,
                tokenType,
                date: Date.now()
            });

            // Update balance
            const userData = await firebaseRequest(`/users/${user.id}`);
            await firebaseRequest(`/users/${user.id}/balance`, 'PUT', (userData?.balance || 0) + amount);

            return sendResponse(res, 200, { amount, message: 'تم الايداع بنجاح' });
        }

        // ==================== NUMBERS ROUTES ====================

        // Get Countries Stock
        if (path === '/numbers/countries' && method === 'GET') {
            const numbers = await firebaseRequest('/numbers') || {};
            const stock = {};

            for (const num of Object.values(numbers)) {
                if (num.status === 'available') {
                    stock[num.country] = (stock[num.country] || 0) + 1;
                }
            }

            return sendResponse(res, 200, stock);
        }

        // Purchase Number
        if (path === '/numbers/purchase' && method === 'POST') {
            const user = getUserFromRequest(req);
            if (!user) {
                return sendResponse(res, 401, { error: 'Unauthorized' });
            }

            const { countryCode } = await parseBody(req);
            
            if (!countryCode || !countryPrices[countryCode]) {
                return sendResponse(res, 400, { error: 'البلد غير صالح' });
            }

            const price = countryPrices[countryCode].buy;

            // Check balance
            const userData = await firebaseRequest(`/users/${user.id}`);
            if ((userData?.balance || 0) < price) {
                return sendResponse(res, 400, { error: 'رصيد غير كافي' });
            }

            // Find available number
            const numbers = await firebaseRequest('/numbers') || {};
            let selectedNumber = null;
            let numberId = null;

            for (const [id, num] of Object.entries(numbers)) {
                if (num.country === countryCode && num.status === 'available') {
                    selectedNumber = num;
                    numberId = id;
                    break;
                }
            }

            if (!selectedNumber) {
                return sendResponse(res, 400, { error: 'لا توجد ارقام متاحة' });
            }

            // Deduct balance
            await firebaseRequest(`/users/${user.id}/balance`, 'PUT', userData.balance - price);

            // Update number
            await firebaseRequest(`/numbers/${numberId}`, 'PATCH', {
                status: 'sold',
                buyerId: user.id,
                soldAt: Date.now()
            });

            // Create order
            const orderId = generateId();
            await firebaseRequest(`/orders/${orderId}`, 'PUT', {
                id: orderId,
                userId: user.id,
                numberId,
                phone: selectedNumber.phone,
                country: countryCode,
                price,
                type: 'purchase',
                status: 'active',
                createdAt: Date.now()
            });

            return sendResponse(res, 200, {
                orderId,
                number: selectedNumber.phone,
                country: countryCode,
                price
            });
        }

        // Check Code
        if (path.startsWith('/numbers/check-code/') && method === 'GET') {
            const user = getUserFromRequest(req);
            if (!user) {
                return sendResponse(res, 401, { error: 'Unauthorized' });
            }

            const orderId = path.split('/').pop();
            const order = await firebaseRequest(`/orders/${orderId}`);
            
            if (!order || order.userId !== user.id) {
                return sendResponse(res, 404, { error: 'الطلب غير موجود' });
            }

            // Check for code in order
            if (order.verificationCode) {
                return sendResponse(res, 200, { code: order.verificationCode });
            }

            // Get number's codes
            const number = await firebaseRequest(`/numbers/${order.numberId}`);
            if (number && number.latestCode && number.codeTime > order.createdAt) {
                await firebaseRequest(`/orders/${orderId}/verificationCode`, 'PUT', number.latestCode);
                return sendResponse(res, 200, { code: number.latestCode });
            }

            return sendResponse(res, 200, { code: null });
        }

        // Confirm Purchase
        if (path.startsWith('/numbers/confirm/') && method === 'POST') {
            const user = getUserFromRequest(req);
            if (!user) {
                return sendResponse(res, 401, { error: 'Unauthorized' });
            }

            const orderId = path.split('/').pop();
            const order = await firebaseRequest(`/orders/${orderId}`);
            
            if (!order || order.userId !== user.id) {
                return sendResponse(res, 404, { error: 'الطلب غير موجود' });
            }

            // Update order
            await firebaseRequest(`/orders/${orderId}`, 'PATCH', {
                status: 'completed',
                completedAt: Date.now()
            });

            // Mark number as used
            await firebaseRequest(`/numbers/${order.numberId}`, 'PATCH', {
                status: 'used'
            });

            return sendResponse(res, 200, { success: true });
        }

        // ==================== SELL ROUTES ====================

        // Request Sell Code
        if (path === '/sell/request-code' && method === 'POST') {
            const user = getUserFromRequest(req);
            if (!user) {
                return sendResponse(res, 401, { error: 'Unauthorized' });
            }

            const { phone } = await parseBody(req);
            
            if (!phone) {
                return sendResponse(res, 400, { error: 'رقم الهاتف مطلوب' });
            }

            // Detect country
            const prefixes = {
                '+1': 'US', '+44': 'UK', '+49': 'DE',
                '+33': 'FR', '+31': 'NL', '+48': 'PL', '+61': 'AU'
            };

            let country = null;
            for (const [prefix, code] of Object.entries(prefixes)) {
                if (phone.startsWith(prefix)) {
                    country = code;
                    break;
                }
            }

            if (!country) {
                return sendResponse(res, 400, { error: 'البلد غير مدعوم' });
            }

            // Store pending sale
            const pendingId = generateId();
            const phoneCodeHash = crypto.randomBytes(16).toString('hex');
            
            await firebaseRequest(`/pending_sales/${pendingId}`, 'PUT', {
                id: pendingId,
                userId: user.id,
                phone,
                country,
                phoneCodeHash,
                status: 'code_sent',
                createdAt: Date.now()
            });

            return sendResponse(res, 200, { 
                phone_code_hash: phoneCodeHash,
                message: 'ادخل اي كود للتجربة (الكود الحقيقي يحتاج MTProto)'
            });
        }

        // Verify Sell Code
        if (path === '/sell/verify-code' && method === 'POST') {
            const user = getUserFromRequest(req);
            if (!user) {
                return sendResponse(res, 401, { error: 'Unauthorized' });
            }

            const { phone, code } = await parseBody(req);
            
            if (!phone || !code) {
                return sendResponse(res, 400, { error: 'البيانات غير مكتملة' });
            }

            // Find pending sale
            const pendingSales = await firebaseRequest('/pending_sales') || {};
            let pendingSale = null;
            let pendingId = null;

            for (const [id, sale] of Object.entries(pendingSales)) {
                if (sale.phone === phone && sale.userId === user.id && sale.status === 'code_sent') {
                    pendingSale = sale;
                    pendingId = id;
                    break;
                }
            }

            if (!pendingSale) {
                return sendResponse(res, 404, { error: 'الطلب غير موجود' });
            }

            // Update to verified
            await firebaseRequest(`/pending_sales/${pendingId}`, 'PATCH', {
                status: 'verified',
                verifiedAt: Date.now()
            });

            return sendResponse(res, 200, { success: true });
        }

        // ==================== WITHDRAW ROUTES ====================

        // Request Withdrawal
        if (path === '/withdraw/request' && method === 'POST') {
            const user = getUserFromRequest(req);
            if (!user) {
                return sendResponse(res, 401, { error: 'Unauthorized' });
            }

            const { amount, address } = await parseBody(req);
            
            if (!amount || !address) {
                return sendResponse(res, 400, { error: 'البيانات غير مكتملة' });
            }

            if (amount < 2) {
                return sendResponse(res, 400, { error: 'الحد الادنى $2' });
            }

            const userData = await firebaseRequest(`/users/${user.id}`);
            if ((userData?.balance || 0) < amount) {
                return sendResponse(res, 400, { error: 'رصيد غير كافي' });
            }

            // Deduct balance
            await firebaseRequest(`/users/${user.id}/balance`, 'PUT', userData.balance - amount);

            // Create withdrawal
            const withdrawId = generateId();
            await firebaseRequest(`/withdrawals/${withdrawId}`, 'PUT', {
                id: withdrawId,
                userId: user.id,
                username: userData.username,
                amount,
                address,
                status: 'pending',
                createdAt: Date.now()
            });

            return sendResponse(res, 200, { success: true });
        }

        // ==================== ORDERS ROUTES ====================

        // Get Orders
        if (path === '/orders' && method === 'GET') {
            const user = getUserFromRequest(req);
            if (!user) {
                return sendResponse(res, 401, { error: 'Unauthorized' });
            }

            const orders = await firebaseRequest('/orders') || {};
            const userOrders = Object.values(orders)
                .filter(o => o.userId === user.id)
                .sort((a, b) => b.createdAt - a.createdAt);

            return sendResponse(res, 200, userOrders);
        }

        // ==================== ADMIN ROUTES ====================

        // Admin Stats
        if (path === '/admin/stats' && method === 'GET') {
            const users = await firebaseRequest('/users') || {};
            const numbers = await firebaseRequest('/numbers') || {};
            const pending = await firebaseRequest('/pending_sales') || {};
            const orders = await firebaseRequest('/orders') || {};

            const stats = {
                users: Object.keys(users).length,
                numbers: Object.values(numbers).filter(n => n.status === 'available').length,
                pending: Object.values(pending).filter(p => p.status === 'verified').length,
                revenue: Object.values(orders)
                    .filter(o => o.status === 'completed')
                    .reduce((sum, o) => sum + (o.price || 0), 0)
                    .toFixed(2)
            };

            return sendResponse(res, 200, stats);
        }

        // Pending Sales
        if (path === '/admin/pending-sales' && method === 'GET') {
            const pending = await firebaseRequest('/pending_sales') || {};
            const users = await firebaseRequest('/users') || {};

            const result = Object.entries(pending)
                .filter(([_, p]) => p.status === 'verified')
                .map(([id, p]) => ({
                    id,
                    phone: p.phone,
                    country: p.country,
                    username: users[p.userId]?.username || 'Unknown',
                    price: countryPrices[p.country]?.sell || 0
                }));

            return sendResponse(res, 200, result);
        }

        // Approve Sale
        if (path.startsWith('/admin/approve-sale/') && method === 'POST') {
            const id = path.split('/').pop();
            const pending = await firebaseRequest(`/pending_sales/${id}`);
            
            if (!pending) {
                return sendResponse(res, 404, { error: 'غير موجود' });
            }

            const sellPrice = countryPrices[pending.country]?.sell || 0;
            const buyPrice = sellPrice + 0.20;

            // Add number
            const numberId = generateId();
            await firebaseRequest(`/numbers/${numberId}`, 'PUT', {
                id: numberId,
                phone: pending.phone,
                country: pending.country,
                price: buyPrice,
                sellerId: pending.userId,
                status: 'available',
                createdAt: Date.now()
            });

            // Credit seller
            const userData = await firebaseRequest(`/users/${pending.userId}`);
            await firebaseRequest(`/users/${pending.userId}/balance`, 'PUT', (userData?.balance || 0) + sellPrice);

            // Remove pending
            await firebaseRequest(`/pending_sales/${id}`, 'DELETE');

            return sendResponse(res, 200, { success: true });
        }

        // Reject Sale
        if (path.startsWith('/admin/reject-sale/') && method === 'POST') {
            const id = path.split('/').pop();
            await firebaseRequest(`/pending_sales/${id}`, 'DELETE');
            return sendResponse(res, 200, { success: true });
        }

        // Get Numbers
        if (path === '/admin/numbers' && method === 'GET') {
            const numbers = await firebaseRequest('/numbers') || {};
            const result = Object.values(numbers).map(n => ({
                phone: n.phone,
                country: n.country,
                price: n.price || countryPrices[n.country]?.buy || 0,
                status: n.status
            }));
            return sendResponse(res, 200, result);
        }

        // Get Deposits
        if (path === '/admin/deposits' && method === 'GET') {
            const deposits = await firebaseRequest('/deposits') || {};
            const users = await firebaseRequest('/users') || {};
            
            const result = Object.values(deposits).map(d => ({
                username: users[d.userId]?.username || 'Unknown',
                amount: d.amount,
                txid: d.txid,
                date: d.date
            }));
            return sendResponse(res, 200, result);
        }

        // Get Withdrawals
        if (path === '/admin/withdrawals' && method === 'GET') {
            const withdrawals = await firebaseRequest('/withdrawals') || {};
            return sendResponse(res, 200, Object.values(withdrawals));
        }

        // Approve Withdrawal
        if (path.startsWith('/admin/approve-withdrawal/') && method === 'POST') {
            const id = path.split('/').pop();
            await firebaseRequest(`/withdrawals/${id}`, 'PATCH', {
                status: 'completed',
                completedAt: Date.now()
            });
            return sendResponse(res, 200, { success: true });
        }

        // Add Number (Admin)
        if (path === '/admin/add-number' && method === 'POST') {
            const { phone, country } = await parseBody(req);
            
            if (!phone || !country) {
                return sendResponse(res, 400, { error: 'البيانات غير مكتملة' });
            }

            const numberId = generateId();
            const price = countryPrices[country]?.buy || 1.00;

            await firebaseRequest(`/numbers/${numberId}`, 'PUT', {
                id: numberId,
                phone,
                country,
                price,
                status: 'available',
                addedBy: 'admin',
                createdAt: Date.now()
            });

            return sendResponse(res, 200, { success: true });
        }

        // Update Code (for admin to manually add codes)
        if (path === '/admin/update-code' && method === 'POST') {
            const { numberId, code } = await parseBody(req);
            
            await firebaseRequest(`/numbers/${numberId}`, 'PATCH', {
                latestCode: code,
                codeTime: Date.now()
            });

            return sendResponse(res, 200, { success: true });
        }

        // 404
        return sendResponse(res, 404, { error: 'Not Found' });

    } catch (error) {
        console.error('Error:', error);
        return sendResponse(res, 500, { error: 'Internal Server Error' });
    }
};

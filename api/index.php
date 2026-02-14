<?php
/**
 * 🐕 DOGE MASTER - Verification Page (Debug Version)
 */

header('Content-Type: text/html; charset=utf-8');
header('X-Content-Type-Options: nosniff');
header('Access-Control-Allow-Origin: *');

// Get user ID
$userId = isset($_GET['userid']) ? preg_replace('/[^0-9]/', '', $_GET['userid']) : '';

if (empty($userId) || strlen($userId) < 5) {
    die('<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
    <body style="background:#111;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;font-family:Arial;">
    <h1>❌ Invalid User ID</h1></body></html>');
}

// Token - MUST match bot exactly
$secret = 'DOGE_MASTER_SECRET_2024';
$timestamp = time();
$token = hash('sha256', $userId . $timestamp . $secret);

// ⚠️ غير هذا لعنوان السيرفر الصحيح
$serverUrl = 'http://147.135.213.131:20084/verify';
?>
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>🔐 DOGE MASTER</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #0f0f1a, #1a1a2e);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            color: #fff;
        }
        .card {
            background: rgba(255,255,255,0.05);
            border-radius: 24px;
            padding: 40px 30px;
            text-align: center;
            max-width: 360px;
            width: 100%;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .logo { font-size: 70px; margin-bottom: 15px; }
        h1 {
            font-size: 24px;
            background: linear-gradient(135deg, #ffc107, #ff9800);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }
        .subtitle { color: rgba(255,255,255,0.6); font-size: 13px; margin-bottom: 25px; }
        .status-box {
            background: rgba(255,193,7,0.1);
            border: 2px solid rgba(255,193,7,0.3);
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 20px;
        }
        .status-box.success { background: rgba(76,175,80,0.1); border-color: rgba(76,175,80,0.4); }
        .status-box.error { background: rgba(244,67,54,0.1); border-color: rgba(244,67,54,0.4); }
        .loader {
            width: 40px; height: 40px;
            border: 3px solid rgba(255,255,255,0.1);
            border-top-color: #ffc107;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 15px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .icon { font-size: 45px; margin-bottom: 10px; display: none; }
        .text { font-size: 15px; font-weight: 600; margin-bottom: 5px; }
        .detail { color: rgba(255,255,255,0.6); font-size: 12px; }
        .progress { height: 4px; background: rgba(255,255,255,0.1); border-radius: 2px; margin-top: 15px; overflow: hidden; }
        .progress-bar { height: 100%; background: linear-gradient(90deg, #ffc107, #ff9800); width: 0%; transition: width 0.3s; }
        .btn {
            display: none; width: 100%; padding: 14px;
            background: linear-gradient(135deg, #ffc107, #ff9800);
            color: #000; border: none; border-radius: 50px;
            font-size: 15px; font-weight: 700; cursor: pointer;
        }
        .btn-retry {
            display: none; width: 100%; padding: 12px;
            background: transparent; color: #ffc107;
            border: 2px solid #ffc107; border-radius: 50px;
            font-size: 14px; cursor: pointer; margin-top: 10px;
        }
        .debug { 
            margin-top: 20px; padding: 15px; 
            background: rgba(0,0,0,0.3); border-radius: 10px;
            text-align: left; font-size: 11px; 
            font-family: monospace; color: #aaa;
            max-height: 150px; overflow-y: auto;
            display: none;
        }
        .debug.show { display: block; }
        .info { margin-top: 15px; font-size: 10px; color: rgba(255,255,255,0.3); }
    </style>
</head>
<body>
    <div class="card">
        <div class="logo">🐕</div>
        <h1>DOGE MASTER</h1>
        <p class="subtitle">التحقق الآمن • Secure Verification</p>
        
        <div id="box" class="status-box">
            <div id="loader" class="loader"></div>
            <div id="icon" class="icon"></div>
            <div id="text" class="text">جاري التحقق...</div>
            <div id="detail" class="detail">يرجى الانتظار</div>
            <div class="progress"><div id="bar" class="progress-bar"></div></div>
        </div>
        
        <button id="closeBtn" class="btn" onclick="closeApp()">✅ العودة للبوت</button>
        <button id="retryBtn" class="btn-retry" onclick="location.reload()">🔄 إعادة المحاولة</button>
        
        <div id="debug" class="debug"></div>
        
        <div class="info">
            User: <?php echo $userId; ?><br>
            Server: <?php echo $serverUrl; ?>
        </div>
    </div>

<script>
(function() {
    
    const CFG = {
        userId: '<?php echo $userId; ?>',
        token: '<?php echo $token; ?>',
        timestamp: <?php echo $timestamp; ?>,
        server: '<?php echo $serverUrl; ?>'
    };
    
    // Elements
    const box = document.getElementById('box');
    const loader = document.getElementById('loader');
    const icon = document.getElementById('icon');
    const text = document.getElementById('text');
    const detail = document.getElementById('detail');
    const bar = document.getElementById('bar');
    const closeBtn = document.getElementById('closeBtn');
    const retryBtn = document.getElementById('retryBtn');
    const debug = document.getElementById('debug');
    
    let logs = [];
    
    function log(msg) {
        const time = new Date().toLocaleTimeString();
        logs.push(`[${time}] ${msg}`);
        debug.innerHTML = logs.join('<br>');
        debug.scrollTop = debug.scrollHeight;
        console.log(msg);
    }
    
    function showDebug() {
        debug.classList.add('show');
    }
    
    function setProgress(p) {
        bar.style.width = p + '%';
    }
    
    function showStatus(ico, txt, det, type) {
        loader.style.display = 'none';
        icon.style.display = 'block';
        icon.textContent = ico;
        text.textContent = txt;
        detail.textContent = det;
        box.className = 'status-box ' + type;
    }
    
    function showError(msg) {
        showStatus('❌', 'فشل التحقق', msg, 'error');
        closeBtn.style.display = 'block';
        retryBtn.style.display = 'block';
        showDebug();
    }
    
    function showSuccess() {
        showStatus('✅', 'تم التحقق!', 'يمكنك العودة للبوت', 'success');
        closeBtn.style.display = 'block';
        setTimeout(closeApp, 2000);
    }
    
    window.closeApp = function() {
        try {
            if (window.Telegram && Telegram.WebApp) {
                Telegram.WebApp.close();
            } else {
                window.close();
            }
        } catch(e) {
            detail.textContent = 'أغلق الصفحة يدوياً';
        }
    };
    
    // Collect device data
    function getData() {
        return {
            userId: CFG.userId,
            verifyToken: CFG.token,
            timestamp: CFG.timestamp,
            
            userAgent: navigator.userAgent || '',
            platform: navigator.platform || '',
            language: navigator.language || '',
            hardwareConcurrency: navigator.hardwareConcurrency || 0,
            deviceMemory: navigator.deviceMemory || 0,
            screenWidth: screen.width || 0,
            screenHeight: screen.height || 0,
            timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || '',
            timezoneOffset: new Date().getTimezoneOffset(),
            
            canvasHash: getCanvas(),
            webglRenderer: getWebGL(),
            
            colorDepth: screen.colorDepth || 0,
            pixelRatio: window.devicePixelRatio || 1,
            touchPoints: navigator.maxTouchPoints || 0,
            online: navigator.onLine,
            cookieEnabled: navigator.cookieEnabled
        };
    }
    
    function getCanvas() {
        try {
            const c = document.createElement('canvas');
            const ctx = c.getContext('2d');
            ctx.textBaseline = 'top';
            ctx.font = '14px Arial';
            ctx.fillText('DOGE🐕' + CFG.userId, 2, 2);
            return c.toDataURL().slice(-50);
        } catch(e) {
            return 'error';
        }
    }
    
    function getWebGL() {
        try {
            const c = document.createElement('canvas');
            const gl = c.getContext('webgl');
            if (!gl) return 'none';
            const dbg = gl.getExtension('WEBGL_debug_renderer_info');
            if (!dbg) return 'no_debug';
            return gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) || 'unknown';
        } catch(e) {
            return 'error';
        }
    }
    
    // Send verification
    async function verify() {
        log('🚀 Starting verification...');
        log('📍 Server: ' + CFG.server);
        log('👤 User: ' + CFG.userId);
        
        setProgress(20);
        text.textContent = 'جاري جمع البيانات...';
        
        await sleep(300);
        
        const data = getData();
        log('📱 Data collected: ' + Object.keys(data).length + ' fields');
        
        setProgress(40);
        text.textContent = 'جاري الإرسال...';
        
        try {
            log('📤 Sending to server...');
            
            // Try fetch
            const response = await fetch(CFG.server, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify(data),
                mode: 'cors'
            });
            
            log('📥 Response status: ' + response.status);
            
            setProgress(80);
            
            if (!response.ok) {
                throw new Error('HTTP ' + response.status);
            }
            
            const result = await response.json();
            log('📦 Result: ' + JSON.stringify(result));
            
            setProgress(100);
            
            if (result.success) {
                log('✅ Success!');
                showSuccess();
            } else {
                log('❌ Failed: ' + (result.msg || 'Unknown'));
                showError(result.msg || 'فشل التحقق');
            }
            
        } catch (err) {
            log('❌ Error: ' + err.message);
            
            // Try XHR as fallback
            log('🔄 Trying XHR fallback...');
            
            try {
                const result = await sendXHR(data);
                log('📦 XHR Result: ' + JSON.stringify(result));
                
                if (result.success) {
                    showSuccess();
                } else {
                    showError(result.msg || 'فشل');
                }
            } catch (xhrErr) {
                log('❌ XHR Error: ' + xhrErr.message);
                showError('تعذر الاتصال بالسيرفر');
            }
        }
    }
    
    function sendXHR(data) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', CFG.server, true);
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.timeout = 30000;
            
            xhr.onload = function() {
                log('XHR status: ' + xhr.status);
                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        resolve(JSON.parse(xhr.responseText));
                    } catch(e) {
                        reject(new Error('Invalid JSON'));
                    }
                } else {
                    reject(new Error('XHR ' + xhr.status));
                }
            };
            
            xhr.onerror = function() {
                reject(new Error('Network error'));
            };
            
            xhr.ontimeout = function() {
                reject(new Error('Timeout'));
            };
            
            xhr.send(JSON.stringify(data));
        });
    }
    
    function sleep(ms) {
        return new Promise(r => setTimeout(r, ms));
    }
    
    // Init Telegram
    try {
        if (window.Telegram && Telegram.WebApp) {
            Telegram.WebApp.ready();
            Telegram.WebApp.expand();
            log('📱 Telegram WebApp ready');
        }
    } catch(e) {
        log('⚠️ Not in Telegram');
    }
    
    // Start
    setTimeout(verify, 500);
    
})();
</script>
</body>
</html>

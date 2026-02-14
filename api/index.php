<?php
header('Content-Type: text/html; charset=utf-8');
header('X-Content-Type-Options: nosniff');
header('X-Frame-Options: SAMEORIGIN');

// التحقق من وجود userid
if (!isset($_GET['userid']) || empty($_GET['userid'])) {
    http_response_code(400);
    die('<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Error</title></head><body style="background:#1a1a2e;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;font-family:Arial;"><h1>❌ Invalid Link</h1></body></html>');
}

$userId = preg_replace('/[^0-9]/', '', $_GET['userid']);

if (strlen($userId) < 5 || strlen($userId) > 15) {
    http_response_code(400);
    die('<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Error</title></head><body style="background:#1a1a2e;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;font-family:Arial;"><h1>❌ Invalid User ID</h1></body></html>');
}

// إنشاء توكن
$secretKey = 'DOGE_MASTER_SECRET_2024';
$timestamp = time();
$verifyToken = hash('sha256', $userId . $timestamp . $secretKey);
?>
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="robots" content="noindex, nofollow">
    <title>🔐 DOGE MASTER - Verify</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        :root {
            --bg-primary: #0f0f1a;
            --bg-secondary: #1a1a2e;
            --accent: #ffc107;
            --accent-dark: #ff9800;
            --success: #4caf50;
            --error: #f44336;
            --text: #ffffff;
            --text-muted: rgba(255,255,255,0.6);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }
        
        html, body {
            height: 100%;
            overflow: hidden;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 35px 25px;
            text-align: center;
            max-width: 360px;
            width: 100%;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.08);
            animation: slideUp 0.5s ease;
        }
        
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .logo {
            font-size: 70px;
            margin-bottom: 15px;
            animation: float 3s ease-in-out infinite;
            filter: drop-shadow(0 10px 30px rgba(255, 193, 7, 0.3));
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-12px); }
        }
        
        h1 {
            font-size: 26px;
            font-weight: 700;
            margin-bottom: 6px;
            background: linear-gradient(135deg, var(--accent), var(--accent-dark));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        
        .subtitle {
            color: var(--text-muted);
            font-size: 13px;
            margin-bottom: 25px;
        }
        
        .status-box {
            background: rgba(255, 193, 7, 0.08);
            border: 2px solid rgba(255, 193, 7, 0.2);
            border-radius: 16px;
            padding: 25px 20px;
            margin-bottom: 20px;
            transition: all 0.4s ease;
        }
        
        .status-box.success {
            background: rgba(76, 175, 80, 0.1);
            border-color: rgba(76, 175, 80, 0.4);
        }
        
        .status-box.error {
            background: rgba(244, 67, 54, 0.1);
            border-color: rgba(244, 67, 54, 0.4);
        }
        
        .loader {
            width: 45px;
            height: 45px;
            border: 3px solid rgba(255, 255, 255, 0.1);
            border-top-color: var(--accent);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 15px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .status-icon {
            font-size: 45px;
            margin-bottom: 12px;
            display: none;
        }
        
        .status-text {
            color: var(--text);
            font-size: 15px;
            font-weight: 600;
            margin-bottom: 6px;
        }
        
        .status-detail {
            color: var(--text-muted);
            font-size: 12px;
        }
        
        .progress {
            width: 100%;
            height: 4px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 2px;
            overflow: hidden;
            margin-top: 15px;
        }
        
        .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, var(--accent), var(--accent-dark));
            border-radius: 2px;
            width: 0%;
            transition: width 0.3s ease;
        }
        
        .btn {
            display: none;
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, var(--accent), var(--accent-dark));
            color: #000;
            border: none;
            border-radius: 50px;
            font-size: 15px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 8px 25px rgba(255, 193, 7, 0.25);
        }
        
        .btn:active {
            transform: scale(0.98);
        }
        
        .retry-btn {
            display: none;
            width: 100%;
            padding: 12px;
            background: transparent;
            color: var(--accent);
            border: 2px solid var(--accent);
            border-radius: 50px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 10px;
            transition: all 0.3s ease;
        }
        
        .retry-btn:hover {
            background: var(--accent);
            color: #000;
        }
        
        .security {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            margin-top: 20px;
            color: rgba(255, 255, 255, 0.3);
            font-size: 10px;
        }
        
        .hidden { display: none !important; }
    </style>
</head>
<body>
    <div class="card">
        <div class="logo">🐕</div>
        <h1>DOGE MASTER</h1>
        <p class="subtitle">نظام التحقق الآمن • Secure Verification</p>
        
        <div id="statusBox" class="status-box">
            <div id="loader" class="loader"></div>
            <div id="statusIcon" class="status-icon">⏳</div>
            <div id="statusText" class="status-text">جاري تجهيز البيانات...</div>
            <div id="statusDetail" class="status-detail">يرجى الانتظار</div>
            <div class="progress">
                <div id="progressBar" class="progress-bar"></div>
            </div>
        </div>
        
        <button id="closeBtn" class="btn" onclick="closeApp()">✅ العودة للبوت</button>
        <button id="retryBtn" class="retry-btn" onclick="retry()">🔄 إعادة المحاولة</button>
        
        <div class="security">
            <span>🔒</span>
            <span>Protected by DOGE MASTER Security</span>
        </div>
    </div>

    <script>
    (function() {
        'use strict';
        
        // ═══════════════════════════════════════════════════════════════
        // CONFIG
        // ═══════════════════════════════════════════════════════════════
        
        const CFG = {
            userId: '<?php echo $userId; ?>',
            token: '<?php echo $verifyToken; ?>',
            ts: <?php echo $timestamp; ?>,
            server: 'http://147.135.213.131:20084/verify',
            maxRetries: 3,
            timeout: 20000
        };
        
        let currentRetry = 0;
        let isProcessing = false;
        
        // Elements
        const $ = id => document.getElementById(id);
        const statusBox = $('statusBox');
        const loader = $('loader');
        const statusIcon = $('statusIcon');
        const statusText = $('statusText');
        const statusDetail = $('statusDetail');
        const progressBar = $('progressBar');
        const closeBtn = $('closeBtn');
        const retryBtn = $('retryBtn');
        
        // ═══════════════════════════════════════════════════════════════
        // SECURITY CHECKS
        // ═══════════════════════════════════════════════════════════════
        
        function securityChecks() {
            return {
                js: true,
                cookies: checkCookies(),
                notBot: !isBot(),
                screen: screen.width > 0 && screen.height > 0,
                timing: true
            };
        }
        
        function checkCookies() {
            try {
                document.cookie = "test=1;SameSite=Strict";
                const ok = document.cookie.indexOf("test=1") !== -1;
                document.cookie = "test=1;expires=Thu, 01 Jan 1970 00:00:00 GMT";
                return ok;
            } catch(e) {
                return false;
            }
        }
        
        function isBot() {
            const dominated = [
                navigator.webdriver,
                window._phantom,
                window.__nightmare,
                window.callPhantom,
                window._selenium,
                document.__selenium_unwrapped,
                document.__webdriver_evaluate
            ];
            return dominated.some(Boolean);
        }
        
        // ═══════════════════════════════════════════════════════════════
        // DEVICE DATA COLLECTION
        // ═══════════════════════════════════════════════════════════════
        
        async function collectData() {
            const sec = securityChecks();
            
            const data = {
                // Auth
                userId: CFG.userId,
                verifyToken: CFG.token,
                timestamp: CFG.ts,
                
                // Security
                jsEnabled: sec.js,
                cookiesOk: sec.cookies,
                notBot: sec.notBot,
                honeypotOk: true,
                
                // Browser
                userAgent: navigator.userAgent || '',
                platform: navigator.platform || '',
                language: navigator.language || '',
                languages: (navigator.languages || []).join(','),
                cookieEnabled: navigator.cookieEnabled,
                doNotTrack: navigator.doNotTrack || '',
                maxTouchPoints: navigator.maxTouchPoints || 0,
                
                // Hardware
                hardwareConcurrency: navigator.hardwareConcurrency || 0,
                deviceMemory: navigator.deviceMemory || 0,
                
                // Screen
                screenWidth: screen.width || 0,
                screenHeight: screen.height || 0,
                screenDepth: screen.colorDepth || 0,
                screenAvailWidth: screen.availWidth || 0,
                screenAvailHeight: screen.availHeight || 0,
                innerWidth: window.innerWidth || 0,
                innerHeight: window.innerHeight || 0,
                outerWidth: window.outerWidth || 0,
                outerHeight: window.outerHeight || 0,
                devicePixelRatio: window.devicePixelRatio || 1,
                
                // Time
                timezone: getTimezone(),
                timezoneOffset: new Date().getTimezoneOffset(),
                clientTime: Date.now(),
                
                // Fingerprints
                canvasHash: getCanvasHash(),
                webglVendor: getWebGL('vendor'),
                webglRenderer: getWebGL('renderer'),
                fontsHash: getFontsHash(),
                audioHash: 'audio_' + Math.random().toString(36).substr(2, 8),
                
                // Connection
                connectionType: getConnection(),
                online: navigator.onLine,
                
                // Device type
                isMobile: /Mobile|Android|iPhone|iPad|iPod/i.test(navigator.userAgent),
                isTouch: ('ontouchstart' in window) || navigator.maxTouchPoints > 0,
                
                // Plugins
                pluginsCount: navigator.plugins ? navigator.plugins.length : 0
            };
            
            return data;
        }
        
        function getTimezone() {
            try {
                return Intl.DateTimeFormat().resolvedOptions().timeZone || 'Unknown';
            } catch(e) {
                return 'Unknown';
            }
        }
        
        function getCanvasHash() {
            try {
                const c = document.createElement('canvas');
                c.width = 200;
                c.height = 50;
                const ctx = c.getContext('2d');
                
                ctx.textBaseline = 'top';
                ctx.font = '16px Arial';
                ctx.fillStyle = '#f60';
                ctx.fillRect(80, 1, 60, 20);
                ctx.fillStyle = '#069';
                ctx.fillText('DOGE🐕', 2, 15);
                ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
                ctx.fillText('DOGE🐕', 4, 17);
                
                return hashCode(c.toDataURL().slice(-100));
            } catch(e) {
                return 'canvas_err';
            }
        }
        
        function getWebGL(type) {
            try {
                const c = document.createElement('canvas');
                const gl = c.getContext('webgl') || c.getContext('experimental-webgl');
                if (!gl) return 'no_webgl';
                
                const dbg = gl.getExtension('WEBGL_debug_renderer_info');
                if (!dbg) return 'no_dbg';
                
                return gl.getParameter(type === 'vendor' ? dbg.UNMASKED_VENDOR_WEBGL : dbg.UNMASKED_RENDERER_WEBGL) || 'unknown';
            } catch(e) {
                return 'webgl_err';
            }
        }
        
        function getFontsHash() {
            const fonts = ['Arial', 'Verdana', 'Times New Roman', 'Courier New', 'Georgia'];
            const detected = [];
            
            try {
                const c = document.createElement('canvas');
                const ctx = c.getContext('2d');
                const testStr = 'mmmmmmmmlli';
                
                const baseWidth = (font) => {
                    ctx.font = '72px ' + font;
                    return ctx.measureText(testStr).width;
                };
                
                const mono = baseWidth('monospace');
                
                fonts.forEach(f => {
                    ctx.font = '72px "' + f + '", monospace';
                    if (ctx.measureText(testStr).width !== mono) {
                        detected.push(f);
                    }
                });
            } catch(e) {}
            
            return hashCode(detected.join(','));
        }
        
        function getConnection() {
            try {
                if (navigator.connection) {
                    return navigator.connection.effectiveType || 'unknown';
                }
                return 'not_supported';
            } catch(e) {
                return 'error';
            }
        }
        
        function hashCode(str) {
            let hash = 0;
            for (let i = 0; i < str.length; i++) {
                const char = str.charCodeAt(i);
                hash = ((hash << 5) - hash) + char;
                hash = hash & hash;
            }
            return Math.abs(hash).toString(16);
        }
        
        // ═══════════════════════════════════════════════════════════════
        // UPDATE UI
        // ═══════════════════════════════════════════════════════════════
        
        function setProgress(percent) {
            progressBar.style.width = percent + '%';
        }
        
        function setStatus(icon, text, detail, type = '') {
            if (icon) {
                loader.classList.add('hidden');
                statusIcon.style.display = 'block';
                statusIcon.textContent = icon;
            }
            statusText.textContent = text;
            statusDetail.textContent = detail;
            
            statusBox.className = 'status-box';
            if (type) statusBox.classList.add(type);
        }
        
        function showLoader(text, detail) {
            loader.classList.remove('hidden');
            statusIcon.style.display = 'none';
            statusText.textContent = text;
            statusDetail.textContent = detail;
        }
        
        // ═══════════════════════════════════════════════════════════════
        // SEND VERIFICATION
        // ═══════════════════════════════════════════════════════════════
        
        async function sendVerification() {
            if (isProcessing) return;
            isProcessing = true;
            
            retryBtn.style.display = 'none';
            closeBtn.style.display = 'none';
            
            try {
                // Step 1: Collect
                showLoader('جاري جمع البيانات...', 'الخطوة 1 من 3');
                setProgress(20);
                
                await sleep(400);
                
                const data = await collectData();
                
                // Step 2: Validate
                showLoader('جاري التحقق...', 'الخطوة 2 من 3');
                setProgress(50);
                
                await sleep(300);
                
                // Step 3: Send
                showLoader('جاري الإرسال...', 'الخطوة 3 من 3');
                setProgress(75);
                
                const result = await sendRequest(data);
                
                setProgress(100);
                await sleep(200);
                
                if (result.success) {
                    setStatus('✅', 'تم التحقق بنجاح!', 'يمكنك العودة للبوت الآن', 'success');
                    closeBtn.style.display = 'block';
                    
                    // Auto close
                    setTimeout(closeApp, 2000);
                } else {
                    setStatus('❌', result.message || 'فشل التحقق', result.banned ? '⛔ تم اكتشاف مخالفة' : 'حاول مرة أخرى', 'error');
                    
                    if (!result.banned) {
                        retryBtn.style.display = 'block';
                    }
                }
                
            } catch (error) {
                console.error('Error:', error);
                
                currentRetry++;
                
                if (currentRetry < CFG.maxRetries) {
                    setStatus('⏳', 'جاري إعادة المحاولة...', `المحاولة ${currentRetry + 1} من ${CFG.maxRetries}`, '');
                    setProgress(0);
                    
                    await sleep(1500);
                    isProcessing = false;
                    return sendVerification();
                }
                
                setStatus('⚠️', 'تعذر الاتصال بالسيرفر', 'تحقق من اتصالك بالإنترنت', 'error');
                retryBtn.style.display = 'block';
            }
            
            isProcessing = false;
        }
        
        async function sendRequest(data) {
            // Method 1: Fetch with timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), CFG.timeout);
            
            try {
                const response = await fetch(CFG.server, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify(data),
                    signal: controller.signal,
                    mode: 'cors',
                    cache: 'no-cache'
                });
                
                clearTimeout(timeoutId);
                
                if (!response.ok) {
                    throw new Error('HTTP ' + response.status);
                }
                
                return await response.json();
                
            } catch (fetchError) {
                clearTimeout(timeoutId);
                console.log('Fetch failed, trying XHR...', fetchError.message);
                
                // Method 2: XMLHttpRequest fallback
                return new Promise((resolve, reject) => {
                    const xhr = new XMLHttpRequest();
                    xhr.open('POST', CFG.server, true);
                    xhr.setRequestHeader('Content-Type', 'application/json');
                    xhr.timeout = CFG.timeout;
                    
                    xhr.onload = function() {
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
                        reject(new Error('Network Error'));
                    };
                    
                    xhr.ontimeout = function() {
                        reject(new Error('Timeout'));
                    };
                    
                    xhr.send(JSON.stringify(data));
                });
            }
        }
        
        function sleep(ms) {
            return new Promise(r => setTimeout(r, ms));
        }
        
        function closeApp() {
            try {
                if (window.Telegram && Telegram.WebApp) {
                    Telegram.WebApp.close();
                } else {
                    window.close();
                }
            } catch(e) {
                history.back();
            }
        }
        
        function retry() {
            currentRetry = 0;
            setProgress(0);
            sendVerification();
        }
        
        // Global functions
        window.closeApp = closeApp;
        window.retry = retry;
        
        // ═══════════════════════════════════════════════════════════════
        // INIT
        // ═══════════════════════════════════════════════════════════════
        
        window.addEventListener('load', function() {
            // Telegram WebApp
            if (window.Telegram && Telegram.WebApp) {
                try {
                    Telegram.WebApp.ready();
                    Telegram.WebApp.expand();
                    Telegram.WebApp.setHeaderColor('#0f0f1a');
                    Telegram.WebApp.setBackgroundColor('#0f0f1a');
                } catch(e) {}
            }
            
            // Start verification
            setTimeout(sendVerification, 600);
        });
        
        // Disable right-click
        document.addEventListener('contextmenu', e => e.preventDefault());
        
    })();
    </script>
</body>
</html>

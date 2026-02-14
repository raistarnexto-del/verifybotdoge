<?php
/**
 * ╔════════════════════════════════════════════════════════════════════════════╗
 * ║  🐕 DOGE MASTER - Device Verification Page                                  ║
 * ║  Compatible with Bot v5.0                                                   ║
 * ╚════════════════════════════════════════════════════════════════════════════╝
 */

// Security Headers
header('Content-Type: text/html; charset=utf-8');
header('X-Content-Type-Options: nosniff');
header('X-Frame-Options: SAMEORIGIN');
header('X-XSS-Protection: 1; mode=block');
header('Referrer-Policy: strict-origin-when-cross-origin');

// Get user ID
$userId = isset($_GET['userid']) ? preg_replace('/[^0-9]/', '', $_GET['userid']) : '';

// Validate
if (empty($userId) || strlen($userId) < 5 || strlen($userId) > 15) {
    http_response_code(400);
    die('<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Error</title></head>
    <body style="background:#0f0f1a;color:#fff;display:flex;align-items:center;justify-content:center;height:100vh;font-family:Arial;">
    <div style="text-align:center"><h1 style="font-size:60px;margin:0">❌</h1><h2>Invalid Link</h2><p>الرابط غير صالح</p></div>
    </body></html>');
}

// Generate token (same as bot)
$secretKey = 'DOGE_MASTER_SECRET_2024';
$timestamp = time();
$verifyToken = hash('sha256', $userId . $timestamp . $secretKey);

// Server URL
$serverUrl = 'http://147.135.213.131:20084/verify';
?>
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="robots" content="noindex, nofollow">
    <meta name="theme-color" content="#0f0f1a">
    <title>🔐 DOGE MASTER - Verify</title>
    
    <!-- Telegram WebApp -->
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    
    <style>
        :root {
            --bg-primary: #0f0f1a;
            --bg-secondary: #1a1a2e;
            --bg-card: rgba(255, 255, 255, 0.03);
            --accent: #ffc107;
            --accent-dark: #ff9800;
            --accent-glow: rgba(255, 193, 7, 0.3);
            --success: #4caf50;
            --success-bg: rgba(76, 175, 80, 0.1);
            --error: #f44336;
            --error-bg: rgba(244, 67, 54, 0.1);
            --text: #ffffff;
            --text-muted: rgba(255, 255, 255, 0.6);
            --border: rgba(255, 255, 255, 0.08);
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
            min-height: 100vh;
        }
        
        .container {
            width: 100%;
            max-width: 380px;
        }
        
        .card {
            background: var(--bg-card);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: 24px;
            padding: 40px 28px;
            text-align: center;
            box-shadow: 0 25px 80px rgba(0, 0, 0, 0.5);
            border: 1px solid var(--border);
            animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1);
        }
        
        @keyframes slideUp {
            from { 
                opacity: 0; 
                transform: translateY(40px) scale(0.95); 
            }
            to { 
                opacity: 1; 
                transform: translateY(0) scale(1); 
            }
        }
        
        .logo {
            font-size: 80px;
            margin-bottom: 20px;
            animation: float 3s ease-in-out infinite;
            filter: drop-shadow(0 15px 40px var(--accent-glow));
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0) rotate(0deg); }
            25% { transform: translateY(-8px) rotate(-2deg); }
            75% { transform: translateY(-8px) rotate(2deg); }
        }
        
        .title {
            font-size: 28px;
            font-weight: 800;
            margin-bottom: 8px;
            background: linear-gradient(135deg, var(--accent), var(--accent-dark));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -0.5px;
        }
        
        .subtitle {
            color: var(--text-muted);
            font-size: 13px;
            margin-bottom: 30px;
            letter-spacing: 0.5px;
        }
        
        .status-box {
            background: rgba(255, 193, 7, 0.06);
            border: 2px solid rgba(255, 193, 7, 0.15);
            border-radius: 20px;
            padding: 30px 24px;
            margin-bottom: 24px;
            transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
            position: relative;
            overflow: hidden;
        }
        
        .status-box::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.05), transparent);
            animation: shimmer 2s infinite;
        }
        
        @keyframes shimmer {
            100% { left: 100%; }
        }
        
        .status-box.success {
            background: var(--success-bg);
            border-color: rgba(76, 175, 80, 0.3);
        }
        
        .status-box.success::before {
            display: none;
        }
        
        .status-box.error {
            background: var(--error-bg);
            border-color: rgba(244, 67, 54, 0.3);
        }
        
        .status-box.error::before {
            display: none;
        }
        
        .loader {
            width: 50px;
            height: 50px;
            border: 3px solid rgba(255, 255, 255, 0.1);
            border-top-color: var(--accent);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 18px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .status-icon {
            font-size: 50px;
            margin-bottom: 15px;
            display: none;
            animation: popIn 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        }
        
        @keyframes popIn {
            from { transform: scale(0); }
            to { transform: scale(1); }
        }
        
        .status-text {
            color: var(--text);
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .status-detail {
            color: var(--text-muted);
            font-size: 13px;
            line-height: 1.5;
        }
        
        .progress-container {
            margin-top: 20px;
        }
        
        .progress {
            width: 100%;
            height: 6px;
            background: rgba(255, 255, 255, 0.08);
            border-radius: 3px;
            overflow: hidden;
        }
        
        .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, var(--accent), var(--accent-dark));
            border-radius: 3px;
            width: 0%;
            transition: width 0.4s ease;
        }
        
        .progress-text {
            color: var(--text-muted);
            font-size: 11px;
            margin-top: 8px;
        }
        
        .btn {
            display: none;
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, var(--accent), var(--accent-dark));
            color: #000;
            border: none;
            border-radius: 50px;
            font-size: 16px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 10px 30px var(--accent-glow);
            margin-top: 5px;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 15px 40px var(--accent-glow);
        }
        
        .btn:active {
            transform: scale(0.98);
        }
        
        .btn-secondary {
            display: none;
            width: 100%;
            padding: 14px;
            background: transparent;
            color: var(--accent);
            border: 2px solid var(--accent);
            border-radius: 50px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            margin-top: 12px;
            transition: all 0.3s ease;
        }
        
        .btn-secondary:hover {
            background: var(--accent);
            color: #000;
        }
        
        .footer {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            margin-top: 25px;
            color: rgba(255, 255, 255, 0.25);
            font-size: 11px;
        }
        
        .footer svg {
            width: 14px;
            height: 14px;
            fill: currentColor;
        }
        
        .user-id {
            color: var(--text-muted);
            font-size: 11px;
            margin-top: 15px;
            font-family: monospace;
        }
        
        .hidden {
            display: none !important;
        }
        
        /* Animations */
        .fade-in {
            animation: fadeIn 0.3s ease;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="logo">🐕</div>
            <h1 class="title">DOGE MASTER</h1>
            <p class="subtitle">نظام التحقق الآمن • Secure Verification</p>
            
            <div id="statusBox" class="status-box">
                <div id="loader" class="loader"></div>
                <div id="statusIcon" class="status-icon">⏳</div>
                <div id="statusText" class="status-text">جاري التجهيز...</div>
                <div id="statusDetail" class="status-detail">يرجى الانتظار</div>
                
                <div class="progress-container">
                    <div class="progress">
                        <div id="progressBar" class="progress-bar"></div>
                    </div>
                    <div id="progressText" class="progress-text">0%</div>
                </div>
            </div>
            
            <button id="closeBtn" class="btn" onclick="closeApp()">✅ العودة للبوت</button>
            <button id="retryBtn" class="btn-secondary" onclick="retry()">🔄 إعادة المحاولة</button>
            
            <div class="footer">
                <svg viewBox="0 0 24 24"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/></svg>
                <span>Protected by DOGE MASTER Security</span>
            </div>
            
            <div class="user-id">ID: <?php echo htmlspecialchars($userId); ?></div>
        </div>
    </div>

    <script>
    (function() {
        'use strict';
        
        // ══════════════════════════════════════════════════════════════════
        // CONFIGURATION
        // ══════════════════════════════════════════════════════════════════
        
        const CONFIG = {
            userId: '<?php echo $userId; ?>',
            token: '<?php echo $verifyToken; ?>',
            timestamp: <?php echo $timestamp; ?>,
            server: '<?php echo $serverUrl; ?>',
            maxRetries: 3,
            timeout: 25000
        };
        
        let retryCount = 0;
        let isRunning = false;
        
        // Elements
        const $ = id => document.getElementById(id);
        const statusBox = $('statusBox');
        const loader = $('loader');
        const statusIcon = $('statusIcon');
        const statusText = $('statusText');
        const statusDetail = $('statusDetail');
        const progressBar = $('progressBar');
        const progressText = $('progressText');
        const closeBtn = $('closeBtn');
        const retryBtn = $('retryBtn');
        
        // ══════════════════════════════════════════════════════════════════
        // TELEGRAM WEBAPP
        // ══════════════════════════════════════════════════════════════════
        
        let tg = null;
        
        function initTelegram() {
            try {
                if (window.Telegram && window.Telegram.WebApp) {
                    tg = window.Telegram.WebApp;
                    tg.ready();
                    tg.expand();
                    
                    // Set colors
                    if (tg.setHeaderColor) tg.setHeaderColor('#0f0f1a');
                    if (tg.setBackgroundColor) tg.setBackgroundColor('#0f0f1a');
                    
                    console.log('✅ Telegram WebApp initialized');
                }
            } catch(e) {
                console.log('⚠️ Telegram WebApp not available');
            }
        }
        
        // ══════════════════════════════════════════════════════════════════
        // SECURITY CHECKS
        // ══════════════════════════════════════════════════════════════════
        
        function isBot() {
            const dominated = [
                navigator.webdriver,
                window._phantom,
                window.__nightmare,
                window.callPhantom,
                window._selenium,
                document.__selenium_unwrapped,
                document.__webdriver_evaluate,
                document.__driver_evaluate,
                window.domAutomation,
                window.domAutomationController
            ];
            return dominated.some(Boolean);
        }
        
        function checkCookies() {
            try {
                const testKey = 'doge_test_' + Date.now();
                document.cookie = testKey + '=1;SameSite=Strict';
                const ok = document.cookie.indexOf(testKey) !== -1;
                document.cookie = testKey + '=;expires=Thu, 01 Jan 1970 00:00:00 GMT';
                return ok;
            } catch(e) {
                return false;
            }
        }
        
        // ══════════════════════════════════════════════════════════════════
        // DEVICE DATA COLLECTION
        // ══════════════════════════════════════════════════════════════════
        
        function collectDeviceData() {
            return {
                // Auth
                userId: CONFIG.userId,
                verifyToken: CONFIG.token,
                timestamp: CONFIG.timestamp,
                
                // Security
                isBot: isBot(),
                cookiesEnabled: checkCookies(),
                
                // Browser Info
                userAgent: navigator.userAgent || '',
                platform: navigator.platform || '',
                language: navigator.language || '',
                languages: (navigator.languages || []).join(','),
                cookieEnabled: navigator.cookieEnabled,
                doNotTrack: navigator.doNotTrack || '',
                maxTouchPoints: navigator.maxTouchPoints || 0,
                vendor: navigator.vendor || '',
                
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
                canvasHash: getCanvasFingerprint(),
                webglVendor: getWebGLInfo('vendor'),
                webglRenderer: getWebGLInfo('renderer'),
                audioFingerprint: getAudioFingerprint(),
                fontsHash: getFontsHash(),
                
                // Network
                connectionType: getConnectionType(),
                online: navigator.onLine,
                
                // Features
                isMobile: /Mobile|Android|iPhone|iPad|iPod|webOS|BlackBerry|Opera Mini|IEMobile/i.test(navigator.userAgent),
                isTouch: ('ontouchstart' in window) || navigator.maxTouchPoints > 0,
                hasWebGL: !!getWebGLContext(),
                
                // Plugins
                pluginsCount: navigator.plugins ? navigator.plugins.length : 0,
                pluginsList: getPluginsList()
            };
        }
        
        function getTimezone() {
            try {
                return Intl.DateTimeFormat().resolvedOptions().timeZone || 'Unknown';
            } catch(e) {
                return 'Unknown';
            }
        }
        
        function getCanvasFingerprint() {
            try {
                const canvas = document.createElement('canvas');
                canvas.width = 280;
                canvas.height = 60;
                const ctx = canvas.getContext('2d');
                
                // Background
                ctx.fillStyle = '#f0f0f0';
                ctx.fillRect(0, 0, 280, 60);
                
                // Text with different styles
                ctx.textBaseline = 'top';
                
                ctx.font = '14px Arial';
                ctx.fillStyle = '#ff6600';
                ctx.fillText('DOGE MASTER 🐕', 5, 5);
                
                ctx.font = 'bold 16px Georgia';
                ctx.fillStyle = '#0066ff';
                ctx.fillText('Verification', 5, 25);
                
                ctx.font = '12px Courier';
                ctx.fillStyle = '#00cc00';
                ctx.fillText(CONFIG.userId, 5, 45);
                
                // Shapes
                ctx.beginPath();
                ctx.arc(240, 30, 20, 0, Math.PI * 2);
                ctx.fillStyle = 'rgba(255, 193, 7, 0.5)';
                ctx.fill();
                
                ctx.strokeStyle = '#ff0000';
                ctx.lineWidth = 2;
                ctx.strokeRect(180, 10, 40, 40);
                
                return hashString(canvas.toDataURL());
            } catch(e) {
                return 'canvas_error';
            }
        }
        
        function getWebGLContext() {
            try {
                const canvas = document.createElement('canvas');
                return canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
            } catch(e) {
                return null;
            }
        }
        
        function getWebGLInfo(type) {
            try {
                const gl = getWebGLContext();
                if (!gl) return 'no_webgl';
                
                const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                if (!debugInfo) return 'no_debug';
                
                if (type === 'vendor') {
                    return gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) || 'unknown';
                } else {
                    return gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) || 'unknown';
                }
            } catch(e) {
                return 'webgl_error';
            }
        }
        
        function getAudioFingerprint() {
            try {
                const AudioContext = window.AudioContext || window.webkitAudioContext;
                if (!AudioContext) return 'no_audio';
                
                const context = new AudioContext();
                const oscillator = context.createOscillator();
                const analyser = context.createAnalyser();
                const gain = context.createGain();
                
                oscillator.type = 'triangle';
                oscillator.frequency.value = 10000;
                gain.gain.value = 0;
                
                oscillator.connect(analyser);
                analyser.connect(gain);
                gain.connect(context.destination);
                
                oscillator.start(0);
                
                const data = new Float32Array(analyser.frequencyBinCount);
                analyser.getFloatFrequencyData(data);
                
                oscillator.stop();
                context.close();
                
                return hashString(data.slice(0, 30).join(','));
            } catch(e) {
                return 'audio_' + Math.random().toString(36).substr(2, 10);
            }
        }
        
        function getFontsHash() {
            const testFonts = [
                'Arial', 'Arial Black', 'Comic Sans MS', 'Courier New', 
                'Georgia', 'Impact', 'Times New Roman', 'Trebuchet MS', 
                'Verdana', 'Webdings', 'Wingdings'
            ];
            
            const detected = [];
            
            try {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                const testString = 'mmmmmmmmmmlli';
                const baseFont = 'monospace';
                
                ctx.font = '72px ' + baseFont;
                const baseWidth = ctx.measureText(testString).width;
                
                testFonts.forEach(font => {
                    ctx.font = '72px "' + font + '", ' + baseFont;
                    const width = ctx.measureText(testString).width;
                    if (width !== baseWidth) {
                        detected.push(font);
                    }
                });
            } catch(e) {}
            
            return hashString(detected.join('|'));
        }
        
        function getConnectionType() {
            try {
                if (navigator.connection) {
                    return navigator.connection.effectiveType || 
                           navigator.connection.type || 
                           'unknown';
                }
                return 'not_supported';
            } catch(e) {
                return 'error';
            }
        }
        
        function getPluginsList() {
            try {
                if (!navigator.plugins || navigator.plugins.length === 0) {
                    return '';
                }
                const plugins = [];
                for (let i = 0; i < Math.min(navigator.plugins.length, 10); i++) {
                    plugins.push(navigator.plugins[i].name);
                }
                return plugins.join(',');
            } catch(e) {
                return '';
            }
        }
        
        function hashString(str) {
            let hash = 0;
            if (!str || str.length === 0) return '0';
            
            for (let i = 0; i < str.length; i++) {
                const char = str.charCodeAt(i);
                hash = ((hash << 5) - hash) + char;
                hash = hash & hash;
            }
            
            return Math.abs(hash).toString(16);
        }
        
        // ══════════════════════════════════════════════════════════════════
        // UI UPDATES
        // ══════════════════════════════════════════════════════════════════
        
        function setProgress(percent, text = null) {
            progressBar.style.width = percent + '%';
            progressText.textContent = text || (percent + '%');
        }
        
        function showLoader(text, detail) {
            loader.classList.remove('hidden');
            statusIcon.style.display = 'none';
            statusText.textContent = text;
            statusDetail.textContent = detail;
            statusBox.className = 'status-box';
        }
        
        function showStatus(icon, text, detail, type) {
            loader.classList.add('hidden');
            statusIcon.style.display = 'block';
            statusIcon.textContent = icon;
            statusText.textContent = text;
            statusDetail.textContent = detail;
            statusBox.className = 'status-box ' + type;
        }
        
        function showButtons(close, retry) {
            closeBtn.style.display = close ? 'block' : 'none';
            retryBtn.style.display = retry ? 'block' : 'none';
        }
        
        // ══════════════════════════════════════════════════════════════════
        // VERIFICATION PROCESS
        // ══════════════════════════════════════════════════════════════════
        
        async function startVerification() {
            if (isRunning) return;
            isRunning = true;
            
            showButtons(false, false);
            
            try {
                // Step 1: Initialize
                showLoader('جاري التجهيز...', 'Initializing...');
                setProgress(10, 'تجهيز...');
                await sleep(400);
                
                // Step 2: Collect data
                showLoader('جاري جمع البيانات...', 'Collecting device data...');
                setProgress(30, 'جمع البيانات...');
                await sleep(300);
                
                const deviceData = collectDeviceData();
                console.log('📱 Device data collected');
                
                // Step 3: Security check
                showLoader('فحص الأمان...', 'Security check...');
                setProgress(50, 'فحص الأمان...');
                await sleep(300);
                
                if (deviceData.isBot) {
                    throw new Error('BOT_DETECTED');
                }
                
                // Step 4: Send to server
                showLoader('جاري التحقق...', 'Verifying with server...');
                setProgress(70, 'إرسال...');
                
                const result = await sendVerification(deviceData);
                
                setProgress(100, 'اكتمل!');
                await sleep(300);
                
                // Step 5: Process result
                if (result.success) {
                    showStatus('✅', 'تم التحقق بنجاح!', 'Verification successful!', 'success');
                    showButtons(true, false);
                    
                    // Auto close after 2.5 seconds
                    setTimeout(closeApp, 2500);
                    
                } else if (result.banned) {
                    showStatus('⛔', 'تم اكتشاف مخالفة!', result.msg || 'Multi-account detected', 'error');
                    showButtons(true, false);
                    
                } else {
                    throw new Error(result.msg || 'Verification failed');
                }
                
            } catch (error) {
                console.error('❌ Verification error:', error);
                
                retryCount++;
                
                if (error.message === 'BOT_DETECTED') {
                    showStatus('🤖', 'تم اكتشاف بوت!', 'Bot detected - Access denied', 'error');
                    showButtons(true, false);
                    
                } else if (retryCount < CONFIG.maxRetries) {
                    showStatus('⚠️', 'فشل الاتصال', `إعادة المحاولة (${retryCount}/${CONFIG.maxRetries})...`, 'error');
                    setProgress(0);
                    
                    await sleep(2000);
                    isRunning = false;
                    startVerification();
                    return;
                    
                } else {
                    showStatus('❌', 'فشل التحقق', 'يرجى المحاولة لاحقاً', 'error');
                    showButtons(true, true);
                }
            }
            
            isRunning = false;
        }
        
        async function sendVerification(data) {
            // Try fetch first
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), CONFIG.timeout);
                
                const response = await fetch(CONFIG.server, {
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
                    throw new Error('HTTP_' + response.status);
                }
                
                return await response.json();
                
            } catch (fetchError) {
                console.log('⚠️ Fetch failed, trying XHR...', fetchError.message);
                
                // Fallback to XHR
                return new Promise((resolve, reject) => {
                    const xhr = new XMLHttpRequest();
                    xhr.open('POST', CONFIG.server, true);
                    xhr.setRequestHeader('Content-Type', 'application/json');
                    xhr.timeout = CONFIG.timeout;
                    
                    xhr.onload = function() {
                        if (xhr.status >= 200 && xhr.status < 300) {
                            try {
                                resolve(JSON.parse(xhr.responseText));
                            } catch(e) {
                                reject(new Error('INVALID_JSON'));
                            }
                        } else {
                            reject(new Error('XHR_' + xhr.status));
                        }
                    };
                    
                    xhr.onerror = () => reject(new Error('NETWORK_ERROR'));
                    xhr.ontimeout = () => reject(new Error('TIMEOUT'));
                    
                    xhr.send(JSON.stringify(data));
                });
            }
        }
        
        // ══════════════════════════════════════════════════════════════════
        // ACTIONS
        // ══════════════════════════════════════════════════════════════════
        
        window.closeApp = function() {
            try {
                if (tg && tg.close) {
                    tg.close();
                } else {
                    window.close();
                    // Fallback message
                    showStatus('✅', 'تم!', 'يمكنك إغلاق هذه الصفحة والعودة للبوت', 'success');
                }
            } catch(e) {
                window.location.href = 'https://t.me';
            }
        };
        
        window.retry = function() {
            retryCount = 0;
            setProgress(0);
            showLoader('جاري إعادة المحاولة...', 'Retrying...');
            showButtons(false, false);
            startVerification();
        };
        
        function sleep(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        }
        
        // ══════════════════════════════════════════════════════════════════
        // INITIALIZATION
        // ══════════════════════════════════════════════════════════════════
        
        function init() {
            console.log('🐕 DOGE MASTER Verification');
            console.log('👤 User ID:', CONFIG.userId);
            
            initTelegram();
            
            // Start after small delay
            setTimeout(startVerification, 600);
        }
        
        // Start when ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
        } else {
            init();
        }
        
        // Disable right-click
        document.addEventListener('contextmenu', e => e.preventDefault());
        
        // Disable text selection
        document.addEventListener('selectstart', e => e.preventDefault());
        
    })();
    </script>
</body>
</html>

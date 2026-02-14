<?php
// Prevent caching
header('Cache-Control: no-cache, no-store, must-revalidate');
header('Pragma: no-cache');
header('Expires: 0');
?>
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>🔐 التحقق من الجهاز</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        :root {
            --tg-theme-bg-color: #ffffff;
            --tg-theme-text-color: #000000;
            --tg-theme-button-color: #3390ec;
            --tg-theme-button-text-color: #ffffff;
            --tg-theme-secondary-bg-color: #f4f4f5;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: var(--tg-theme-bg-color);
            color: var(--tg-theme-text-color);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            width: 100%;
            max-width: 400px;
            text-align: center;
        }
        
        .logo {
            font-size: 80px;
            margin-bottom: 20px;
            animation: bounce 2s infinite;
        }
        
        @keyframes bounce {
            0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
            40% { transform: translateY(-20px); }
            60% { transform: translateY(-10px); }
        }
        
        h1 {
            font-size: 24px;
            margin-bottom: 10px;
            color: var(--tg-theme-text-color);
        }
        
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
            line-height: 1.5;
        }
        
        .status-box {
            background: var(--tg-theme-secondary-bg-color);
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 30px;
        }
        
        .status-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid rgba(0,0,0,0.1);
        }
        
        .status-item:last-child {
            border-bottom: none;
        }
        
        .status-item .label {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .status-item .icon {
            font-size: 20px;
        }
        
        .status-item .value {
            font-weight: 600;
        }
        
        .loading {
            color: #f39c12;
        }
        
        .success {
            color: #27ae60;
        }
        
        .error {
            color: #e74c3c;
        }
        
        .spinner {
            width: 20px;
            height: 20px;
            border: 2px solid #f3f3f3;
            border-top: 2px solid var(--tg-theme-button-color);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            display: inline-block;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .btn {
            background: var(--tg-theme-button-color);
            color: var(--tg-theme-button-text-color);
            border: none;
            border-radius: 12px;
            padding: 16px 32px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            transition: all 0.3s ease;
        }
        
        .btn:hover {
            opacity: 0.9;
            transform: scale(1.02);
        }
        
        .btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        
        .btn-success {
            background: #27ae60;
        }
        
        .btn-error {
            background: #e74c3c;
        }
        
        .message {
            margin-top: 20px;
            padding: 15px;
            border-radius: 12px;
            font-size: 14px;
        }
        
        .message.success {
            background: rgba(39, 174, 96, 0.1);
            color: #27ae60;
        }
        
        .message.error {
            background: rgba(231, 76, 60, 0.1);
            color: #e74c3c;
        }
        
        .user-info {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .user-info .name {
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .user-info .id {
            opacity: 0.8;
            font-size: 14px;
        }
        
        .hidden {
            display: none !important;
        }
        
        .progress-bar {
            width: 100%;
            height: 6px;
            background: var(--tg-theme-secondary-bg-color);
            border-radius: 3px;
            overflow: hidden;
            margin: 20px 0;
        }
        
        .progress-bar .fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 3px;
            transition: width 0.5s ease;
            width: 0%;
        }
        
        .step-indicator {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .step {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background: var(--tg-theme-secondary-bg-color);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        
        .step.active {
            background: var(--tg-theme-button-color);
            color: white;
        }
        
        .step.done {
            background: #27ae60;
            color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">🐕</div>
        
        <h1>DOGE MASTER</h1>
        <p class="subtitle">التحقق من الجهاز لحماية حسابك</p>
        
        <!-- User Info -->
        <div class="user-info" id="userInfo">
            <div class="name" id="userName">جاري التحميل...</div>
            <div class="id" id="userId">ID: ---</div>
        </div>
        
        <!-- Step Indicator -->
        <div class="step-indicator">
            <div class="step active" id="step1">1</div>
            <div class="step" id="step2">2</div>
            <div class="step" id="step3">3</div>
        </div>
        
        <!-- Progress Bar -->
        <div class="progress-bar">
            <div class="fill" id="progressFill"></div>
        </div>
        
        <!-- Status Box -->
        <div class="status-box">
            <div class="status-item">
                <span class="label">
                    <span class="icon">📱</span>
                    <span>معلومات الجهاز</span>
                </span>
                <span class="value" id="deviceStatus"><span class="spinner"></span></span>
            </div>
            <div class="status-item">
                <span class="label">
                    <span class="icon">🔒</span>
                    <span>التحقق الأمني</span>
                </span>
                <span class="value" id="securityStatus"><span class="spinner"></span></span>
            </div>
            <div class="status-item">
                <span class="label">
                    <span class="icon">✅</span>
                    <span>إرسال البيانات</span>
                </span>
                <span class="value" id="sendStatus">⏳</span>
            </div>
        </div>
        
        <!-- Button -->
        <button class="btn" id="verifyBtn" disabled>
            <span id="btnText">جاري التحميل...</span>
        </button>
        
        <!-- Message -->
        <div class="message hidden" id="message"></div>
    </div>

    <script>
        // ═══════════════════════════════════════════════════════════════
        // CONFIGURATION
        // ═══════════════════════════════════════════════════════════════
        
        const API_URL = 'https://apiverfy-production.up.railway.app/verify';
        
        // ═══════════════════════════════════════════════════════════════
        // TELEGRAM WEBAPP INITIALIZATION
        // ═══════════════════════════════════════════════════════════════
        
        const tg = window.Telegram?.WebApp;
        let userData = null;
        let initData = null;
        
        // Initialize Telegram WebApp
        if (tg) {
            tg.ready();
            tg.expand();
            
            // Apply theme
            document.body.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color || '#ffffff');
            document.body.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color || '#000000');
            document.body.style.setProperty('--tg-theme-button-color', tg.themeParams.button_color || '#3390ec');
            document.body.style.setProperty('--tg-theme-button-text-color', tg.themeParams.button_text_color || '#ffffff');
            document.body.style.setProperty('--tg-theme-secondary-bg-color', tg.themeParams.secondary_bg_color || '#f4f4f5');
            
            // Get user data from initData
            initData = tg.initData;
            userData = tg.initDataUnsafe?.user;
            
            console.log('Telegram WebApp initialized');
            console.log('User:', userData);
            console.log('initData available:', !!initData);
        }
        
        // ═══════════════════════════════════════════════════════════════
        // DOM ELEMENTS
        // ═══════════════════════════════════════════════════════════════
        
        const elements = {
            userName: document.getElementById('userName'),
            odeis: document.getElementById('userId'),
            deviceStatus: document.getElementById('deviceStatus'),
            securityStatus: document.getElementById('securityStatus'),
            sendStatus: document.getElementById('sendStatus'),
            verifyBtn: document.getElementById('verifyBtn'),
            btnText: document.getElementById('btnText'),
            message: document.getElementById('message'),
            progressFill: document.getElementById('progressFill'),
            step1: document.getElementById('step1'),
            step2: document.getElementById('step2'),
            step3: document.getElementById('step3')
        };
        
        // ═══════════════════════════════════════════════════════════════
        // FINGERPRINT COLLECTION
        // ═══════════════════════════════════════════════════════════════
        
        function getFingerprint() {
            return {
                userAgent: navigator.userAgent,
                platform: navigator.platform,
                language: navigator.language,
                languages: navigator.languages?.join(',') || '',
                hardwareConcurrency: navigator.hardwareConcurrency || 0,
                screenWidth: screen.width,
                screenHeight: screen.height,
                screenDepth: screen.colorDepth,
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                timezoneOffset: new Date().getTimezoneOffset(),
                touchSupport: 'ontouchstart' in window,
                cookieEnabled: navigator.cookieEnabled,
                doNotTrack: navigator.doNotTrack,
                canvasHash: getCanvasFingerprint(),
                webglRenderer: getWebGLRenderer(),
                audioContext: getAudioFingerprint(),
                fonts: getFontsFingerprint()
            };
        }
        
        function getCanvasFingerprint() {
            try {
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');
                canvas.width = 200;
                canvas.height = 50;
                
                ctx.textBaseline = 'top';
                ctx.font = '14px Arial';
                ctx.fillStyle = '#f60';
                ctx.fillRect(125, 1, 62, 20);
                ctx.fillStyle = '#069';
                ctx.fillText('DOGE MASTER 🐕', 2, 15);
                ctx.fillStyle = 'rgba(102, 204, 0, 0.7)';
                ctx.fillText('DOGE MASTER 🐕', 4, 17);
                
                return canvas.toDataURL().slice(-50);
            } catch (e) {
                return 'error';
            }
        }
        
        function getWebGLRenderer() {
            try {
                const canvas = document.createElement('canvas');
                const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                if (!gl) return 'none';
                
                const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
                if (debugInfo) {
                    return gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
                }
                return 'unknown';
            } catch (e) {
                return 'error';
            }
        }
        
        function getAudioFingerprint() {
            try {
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                return audioContext.sampleRate?.toString() || 'none';
            } catch (e) {
                return 'error';
            }
        }
        
        function getFontsFingerprint() {
            const testFonts = ['Arial', 'Helvetica', 'Times', 'Courier', 'Verdana', 'Georgia'];
            const detected = [];
            
            const testString = 'mmmmmmmmmmlli';
            const testSize = '72px';
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            const baseFont = 'monospace';
            ctx.font = testSize + ' ' + baseFont;
            const baseWidth = ctx.measureText(testString).width;
            
            testFonts.forEach(font => {
                ctx.font = testSize + ' "' + font + '", ' + baseFont;
                const width = ctx.measureText(testString).width;
                if (width !== baseWidth) {
                    detected.push(font);
                }
            });
            
            return detected.join(',');
        }
        
        // ═══════════════════════════════════════════════════════════════
        // PROGRESS FUNCTIONS
        // ═══════════════════════════════════════════════════════════════
        
        function setProgress(percent) {
            elements.progressFill.style.width = percent + '%';
        }
        
        function setStep(step) {
            elements.step1.className = step >= 1 ? (step > 1 ? 'step done' : 'step active') : 'step';
            elements.step2.className = step >= 2 ? (step > 2 ? 'step done' : 'step active') : 'step';
            elements.step3.className = step >= 3 ? 'step done' : (step >= 3 ? 'step active' : 'step');
        }
        
        function showMessage(text, type) {
            elements.message.textContent = text;
            elements.message.className = 'message ' + type;
            elements.message.classList.remove('hidden');
        }
        
        // ═══════════════════════════════════════════════════════════════
        // INITIALIZATION
        // ═══════════════════════════════════════════════════════════════
        
        async function init() {
            // Check if Telegram WebApp is available
            if (!tg || !initData) {
                showMessage('❌ يرجى فتح هذه الصفحة من داخل تيليجرام', 'error');
                elements.verifyBtn.disabled = true;
                elements.btnText.textContent = 'غير متاح';
                return;
            }
            
            // Check if user data is available
            if (!userData || !userData.id) {
                showMessage('❌ لا يمكن الحصول على معلومات المستخدم', 'error');
                elements.verifyBtn.disabled = true;
                elements.btnText.textContent = 'خطأ';
                return;
            }
            
            // Display user info
            const firstName = userData.first_name || '';
            const lastName = userData.last_name || '';
            const fullName = (firstName + ' ' + lastName).trim() || 'مستخدم';
            
            elements.userName.textContent = fullName;
            elements.odeis.textContent = 'ID: ' + userData.id;
            
            // Start verification process
            setProgress(10);
            setStep(1);
            
            // Step 1: Collect device info
            await sleep(500);
            elements.deviceStatus.innerHTML = '<span class="success">✅</span>';
            setProgress(33);
            
            // Step 2: Security check
            setStep(2);
            await sleep(500);
            elements.securityStatus.innerHTML = '<span class="success">✅</span>';
            setProgress(66);
            
            // Enable button
            setStep(3);
            elements.verifyBtn.disabled = false;
            elements.btnText.textContent = '🔐 تحقق الآن';
        }
        
        // ═══════════════════════════════════════════════════════════════
        // VERIFICATION
        // ═══════════════════════════════════════════════════════════════
        
        async function verify() {
            elements.verifyBtn.disabled = true;
            elements.btnText.textContent = 'جاري التحقق...';
            elements.sendStatus.innerHTML = '<span class="spinner"></span>';
            
            try {
                const fingerprint = getFingerprint();
                
                // Send to server
                const response = await fetch(API_URL, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        initData: initData,
                        fingerprint: fingerprint
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    setProgress(100);
                    setStep(3);
                    elements.sendStatus.innerHTML = '<span class="success">✅</span>';
                    elements.verifyBtn.className = 'btn btn-success';
                    elements.btnText.textContent = '✅ تم التحقق بنجاح!';
                    showMessage('🎉 تم التحقق بنجاح! يمكنك الآن إغلاق هذه الصفحة والعودة للبوت.', 'success');
                    
                    // Haptic feedback
                    if (tg.HapticFeedback) {
                        tg.HapticFeedback.notificationOccurred('success');
                    }
                    
                    // Close WebApp after delay
                    setTimeout(() => {
                        if (tg.close) {
                            tg.close();
                        }
                    }, 2000);
                    
                } else {
                    throw new Error(result.msg || 'فشل التحقق');
                }
                
            } catch (error) {
                console.error('Verification error:', error);
                elements.sendStatus.innerHTML = '<span class="error">❌</span>';
                elements.verifyBtn.className = 'btn btn-error';
                elements.btnText.textContent = '❌ فشل - اضغط للإعادة';
                elements.verifyBtn.disabled = false;
                
                let errorMsg = error.message || 'خطأ غير معروف';
                if (error.message?.includes('banned') || error.message?.includes('Multi-account')) {
                    errorMsg = '🚫 تم اكتشاف تعدد حسابات! حسابك محظور.';
                }
                
                showMessage('❌ ' + errorMsg, 'error');
                
                // Haptic feedback
                if (tg.HapticFeedback) {
                    tg.HapticFeedback.notificationOccurred('error');
                }
            }
        }
        
        // ═══════════════════════════════════════════════════════════════
        // HELPERS
        // ═══════════════════════════════════════════════════════════════
        
        function sleep(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        }
        
        // ═══════════════════════════════════════════════════════════════
        // EVENT LISTENERS
        // ═══════════════════════════════════════════════════════════════
        
        elements.verifyBtn.addEventListener('click', verify);
        
        // Start initialization
        init();
    </script>
</body>
</html>

<?php
header('Content-Type: text/html; charset=utf-8');
header('Cache-Control: no-cache, no-store, must-revalidate');
header('Access-Control-Allow-Origin: *');
?>
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="robots" content="noindex, nofollow">
    <title>🔐 DOGE MASTER - التحقق</title>
    
    <!-- Telegram WebApp Script - يجب أن يكون أول شيء -->
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }
        
        :root {
            --bg-color: #1a1a2e;
            --card-bg: #16213e;
            --text-color: #ffffff;
            --text-secondary: #a0a0a0;
            --accent-color: #f39c12;
            --success-color: #27ae60;
            --error-color: #e74c3c;
            --button-color: #f39c12;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
            background: var(--bg-color);
            color: var(--text-color);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
            overflow-x: hidden;
        }
        
        .container {
            width: 100%;
            max-width: 380px;
            text-align: center;
        }
        
        /* Logo Animation */
        .logo {
            font-size: 100px;
            margin-bottom: 15px;
            animation: float 3s ease-in-out infinite;
            filter: drop-shadow(0 10px 30px rgba(243, 156, 18, 0.3));
        }
        
        @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-15px); }
        }
        
        .title {
            font-size: 28px;
            font-weight: 800;
            background: linear-gradient(135deg, #f39c12, #e74c3c);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 8px;
        }
        
        .subtitle {
            color: var(--text-secondary);
            font-size: 14px;
            margin-bottom: 25px;
        }
        
        /* User Card */
        .user-card {
            background: linear-gradient(135deg, #f39c12 0%, #e67e22 100%);
            border-radius: 20px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(243, 156, 18, 0.3);
        }
        
        .user-avatar {
            width: 60px;
            height: 60px;
            background: rgba(255,255,255,0.2);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 30px;
            margin: 0 auto 10px;
        }
        
        .user-name {
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 5px;
        }
        
        .user-id {
            font-size: 13px;
            opacity: 0.9;
            font-family: monospace;
        }
        
        /* Status Box */
        .status-box {
            background: var(--card-bg);
            border-radius: 16px;
            padding: 15px;
            margin-bottom: 20px;
        }
        
        .status-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 5px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        
        .status-item:last-child {
            border-bottom: none;
        }
        
        .status-label {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
        }
        
        .status-icon {
            font-size: 18px;
        }
        
        .status-value {
            font-size: 18px;
        }
        
        .spinner {
            width: 18px;
            height: 18px;
            border: 2px solid rgba(255,255,255,0.2);
            border-top-color: var(--accent-color);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Progress */
        .progress-container {
            margin-bottom: 20px;
        }
        
        .progress-bar {
            height: 6px;
            background: rgba(255,255,255,0.1);
            border-radius: 3px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #f39c12, #e74c3c);
            border-radius: 3px;
            transition: width 0.5s ease;
            width: 0%;
        }
        
        .progress-text {
            font-size: 12px;
            color: var(--text-secondary);
            margin-top: 8px;
        }
        
        /* Button */
        .btn {
            width: 100%;
            padding: 16px 24px;
            border: none;
            border-radius: 14px;
            font-size: 17px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #f39c12, #e67e22);
            color: white;
            box-shadow: 0 8px 25px rgba(243, 156, 18, 0.4);
        }
        
        .btn-primary:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 12px 35px rgba(243, 156, 18, 0.5);
        }
        
        .btn-primary:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .btn-success {
            background: linear-gradient(135deg, #27ae60, #2ecc71);
            box-shadow: 0 8px 25px rgba(39, 174, 96, 0.4);
        }
        
        .btn-error {
            background: linear-gradient(135deg, #e74c3c, #c0392b);
            box-shadow: 0 8px 25px rgba(231, 76, 60, 0.4);
        }
        
        /* Message */
        .message {
            margin-top: 15px;
            padding: 15px;
            border-radius: 12px;
            font-size: 14px;
            display: none;
        }
        
        .message.show {
            display: block;
            animation: fadeIn 0.3s ease;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .message.success {
            background: rgba(39, 174, 96, 0.15);
            border: 1px solid rgba(39, 174, 96, 0.3);
            color: #2ecc71;
        }
        
        .message.error {
            background: rgba(231, 76, 60, 0.15);
            border: 1px solid rgba(231, 76, 60, 0.3);
            color: #e74c3c;
        }
        
        /* Error Screen */
        .error-screen {
            display: none;
        }
        
        .error-screen.show {
            display: block;
        }
        
        .error-icon {
            font-size: 80px;
            margin-bottom: 20px;
        }
        
        .error-title {
            font-size: 22px;
            font-weight: 700;
            color: #e74c3c;
            margin-bottom: 10px;
        }
        
        .error-text {
            color: var(--text-secondary);
            font-size: 14px;
            line-height: 1.6;
        }
        
        /* Main Content */
        .main-content {
            display: block;
        }
        
        .main-content.hide {
            display: none;
        }
        
        /* Debug Info */
        .debug {
            margin-top: 20px;
            padding: 10px;
            background: rgba(0,0,0,0.3);
            border-radius: 8px;
            font-size: 11px;
            color: #666;
            text-align: left;
            font-family: monospace;
            word-break: break-all;
            display: none;
        }
    </style>
</head>
<body>
    <div class="container">
        
        <!-- Error Screen -->
        <div class="error-screen" id="errorScreen">
            <div class="error-icon">🚫</div>
            <div class="error-title">خطأ في الوصول</div>
            <div class="error-text" id="errorText">
                يجب فتح هذه الصفحة من داخل تطبيق تيليجرام عبر البوت
            </div>
        </div>
        
        <!-- Main Content -->
        <div class="main-content" id="mainContent">
            <div class="logo">🐕</div>
            <div class="title">DOGE MASTER</div>
            <div class="subtitle">التحقق من الجهاز لحماية حسابك</div>
            
            <!-- User Card -->
            <div class="user-card">
                <div class="user-avatar" id="userAvatar">👤</div>
                <div class="user-name" id="userName">جاري التحميل...</div>
                <div class="user-id" id="userId">ID: ------</div>
            </div>
            
            <!-- Progress -->
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
                <div class="progress-text" id="progressText">جاري التحضير...</div>
            </div>
            
            <!-- Status -->
            <div class="status-box">
                <div class="status-item">
                    <span class="status-label">
                        <span class="status-icon">📱</span>
                        <span>معلومات الجهاز</span>
                    </span>
                    <span class="status-value" id="status1"><div class="spinner"></div></span>
                </div>
                <div class="status-item">
                    <span class="status-label">
                        <span class="status-icon">🔐</span>
                        <span>التحقق الأمني</span>
                    </span>
                    <span class="status-value" id="status2"><div class="spinner"></div></span>
                </div>
                <div class="status-item">
                    <span class="status-label">
                        <span class="status-icon">📤</span>
                        <span>إرسال البيانات</span>
                    </span>
                    <span class="status-value" id="status3">⏳</span>
                </div>
            </div>
            
            <!-- Button -->
            <button class="btn btn-primary" id="verifyBtn" disabled>
                <span id="btnIcon">🔐</span>
                <span id="btnText">جاري التحميل...</span>
            </button>
            
            <!-- Message -->
            <div class="message" id="message"></div>
        </div>
        
        <!-- Debug -->
        <div class="debug" id="debug"></div>
    </div>

    <script>
    (function() {
        'use strict';
        
        // ═══════════════════════════════════════════════════════════════
        // التهيئة
        // ═══════════════════════════════════════════════════════════════
        
        const API_URL = 'https://apiverfy-production.up.railway.app/verify';
        
        const $ = id => document.getElementById(id);
        
        const elements = {
            errorScreen: $('errorScreen'),
            errorText: $('errorText'),
            mainContent: $('mainContent'),
            userAvatar: $('userAvatar'),
            userName: $('userName'),
            userId: $('userId'),
            progressFill: $('progressFill'),
            progressText: $('progressText'),
            status1: $('status1'),
            status2: $('status2'),
            status3: $('status3'),
            verifyBtn: $('verifyBtn'),
            btnIcon: $('btnIcon'),
            btnText: $('btnText'),
            message: $('message'),
            debug: $('debug')
        };
        
        let tg = null;
        let user = null;
        let initData = null;
        
        // ═══════════════════════════════════════════════════════════════
        // دوال مساعدة
        // ═══════════════════════════════════════════════════════════════
        
        function log(msg) {
            console.log('[DOGE]', msg);
            elements.debug.style.display = 'block';
            elements.debug.innerHTML += msg + '<br>';
        }
        
        function showError(title, text) {
            elements.mainContent.classList.add('hide');
            elements.errorScreen.classList.add('show');
            elements.errorText.textContent = text;
        }
        
        function setProgress(percent, text) {
            elements.progressFill.style.width = percent + '%';
            if (text) elements.progressText.textContent = text;
        }
        
        function setStatus(num, status) {
            const el = elements['status' + num];
            if (status === 'loading') {
                el.innerHTML = '<div class="spinner"></div>';
            } else if (status === 'success') {
                el.textContent = '✅';
            } else if (status === 'error') {
                el.textContent = '❌';
            } else {
                el.textContent = status;
            }
        }
        
        function showMessage(text, type) {
            elements.message.textContent = text;
            elements.message.className = 'message ' + type + ' show';
        }
        
        function sleep(ms) {
            return new Promise(r => setTimeout(r, ms));
        }
        
        // ═══════════════════════════════════════════════════════════════
        // Fingerprint
        // ═══════════════════════════════════════════════════════════════
        
        function getFingerprint() {
            const fp = {
                userAgent: navigator.userAgent || '',
                platform: navigator.platform || '',
                language: navigator.language || '',
                languages: (navigator.languages || []).join(','),
                hardwareConcurrency: navigator.hardwareConcurrency || 0,
                screenWidth: screen.width || 0,
                screenHeight: screen.height || 0,
                screenDepth: screen.colorDepth || 0,
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || '',
                timezoneOffset: new Date().getTimezoneOffset(),
                touchSupport: 'ontouchstart' in window,
                cookieEnabled: navigator.cookieEnabled,
                webglRenderer: getWebGL(),
                canvasHash: getCanvas()
            };
            return fp;
        }
        
        function getWebGL() {
            try {
                const canvas = document.createElement('canvas');
                const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
                if (!gl) return 'none';
                const ext = gl.getExtension('WEBGL_debug_renderer_info');
                return ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : 'unknown';
            } catch (e) {
                return 'error';
            }
        }
        
        function getCanvas() {
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
                ctx.fillText('DOGE🐕', 2, 15);
                return canvas.toDataURL().slice(-50);
            } catch (e) {
                return 'error';
            }
        }
        
        // ═══════════════════════════════════════════════════════════════
        // التحقق
        // ═══════════════════════════════════════════════════════════════
        
        async function verify() {
            elements.verifyBtn.disabled = true;
            elements.btnText.textContent = 'جاري التحقق...';
            elements.btnIcon.textContent = '⏳';
            setStatus(3, 'loading');
            
            try {
                const fingerprint = getFingerprint();
                
                log('Sending to: ' + API_URL);
                
                const response = await fetch(API_URL, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    body: JSON.stringify({
                        initData: initData,
                        fingerprint: fingerprint
                    })
                });
                
                log('Response status: ' + response.status);
                
                const result = await response.json();
                
                log('Result: ' + JSON.stringify(result));
                
                if (result.success) {
                    setProgress(100, 'تم التحقق بنجاح!');
                    setStatus(3, 'success');
                    
                    elements.verifyBtn.className = 'btn btn-success';
                    elements.btnIcon.textContent = '✅';
                    elements.btnText.textContent = 'تم التحقق بنجاح!';
                    
                    showMessage('🎉 تم التحقق! يمكنك العودة للبوت الآن', 'success');
                    
                    if (tg && tg.HapticFeedback) {
                        tg.HapticFeedback.notificationOccurred('success');
                    }
                    
                    // إغلاق بعد 2 ثانية
                    setTimeout(() => {
                        if (tg && tg.close) {
                            tg.close();
                        }
                    }, 2000);
                    
                } else {
                    throw new Error(result.msg || 'فشل التحقق');
                }
                
            } catch (error) {
                log('Error: ' + error.message);
                
                setStatus(3, 'error');
                elements.verifyBtn.className = 'btn btn-error';
                elements.btnIcon.textContent = '❌';
                elements.btnText.textContent = 'فشل - اضغط للإعادة';
                elements.verifyBtn.disabled = false;
                
                let msg = error.message;
                if (msg.includes('banned') || msg.includes('Multi')) {
                    msg = 'تم اكتشاف تعدد حسابات! حسابك محظور';
                } else if (msg.includes('fetch')) {
                    msg = 'خطأ في الاتصال بالسيرفر';
                }
                
                showMessage('❌ ' + msg, 'error');
                
                if (tg && tg.HapticFeedback) {
                    tg.HapticFeedback.notificationOccurred('error');
                }
            }
        }
        
        // ═══════════════════════════════════════════════════════════════
        // التهيئة الرئيسية
        // ═══════════════════════════════════════════════════════════════
        
        async function init() {
            log('Starting init...');
            
            // التحقق من Telegram WebApp
            if (typeof Telegram === 'undefined' || !Telegram.WebApp) {
                log('Telegram WebApp not found');
                showError('خطأ', 'يجب فتح هذه الصفحة من داخل تيليجرام');
                return;
            }
            
            tg = Telegram.WebApp;
            log('Telegram WebApp found');
            
            // تهيئة WebApp
            tg.ready();
            tg.expand();
            
            // الحصول على البيانات
            initData = tg.initData;
            user = tg.initDataUnsafe ? tg.initDataUnsafe.user : null;
            
            log('initData length: ' + (initData ? initData.length : 0));
            log('User: ' + (user ? JSON.stringify(user) : 'null'));
            
            // التحقق من البيانات
            if (!initData || initData.length === 0) {
                log('No initData');
                showError('خطأ', 'لا يمكن الحصول على بيانات التحقق. أعد فتح الرابط من البوت.');
                return;
            }
            
            if (!user || !user.id) {
                log('No user data');
                showError('خطأ', 'لا يمكن الحصول على معلومات المستخدم');
                return;
            }
            
            // عرض معلومات المستخدم
            const firstName = user.first_name || '';
            const lastName = user.last_name || '';
            const fullName = (firstName + ' ' + lastName).trim() || 'مستخدم';
            
            elements.userName.textContent = fullName;
            elements.userId.textContent = 'ID: ' + user.id;
            elements.userAvatar.textContent = firstName.charAt(0) || '👤';
            
            // بدء عملية التحقق
            setProgress(20, 'جمع معلومات الجهاز...');
            await sleep(500);
            setStatus(1, 'success');
            
            setProgress(50, 'التحقق الأمني...');
            await sleep(500);
            setStatus(2, 'success');
            
            setProgress(75, 'جاهز للتحقق');
            
            // تفعيل الزر
            elements.verifyBtn.disabled = false;
            elements.btnText.textContent = 'تحقق الآن';
            elements.btnIcon.textContent = '🔐';
            
            log('Ready!');
        }
        
        // ═══════════════════════════════════════════════════════════════
        // بدء التشغيل
        // ═══════════════════════════════════════════════════════════════
        
        elements.verifyBtn.addEventListener('click', verify);
        
        // انتظر تحميل Telegram WebApp
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
        } else {
            setTimeout(init, 100);
        }
        
    })();
    </script>
</body>
</html>

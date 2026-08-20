import os
import json
import time
import random
import threading
import queue
from flask import Flask, request, jsonify, render_template_string
import requests

app = Flask(__name__)

# === Hàng đợi và lưu kết quả ===
task_queue = queue.Queue()
result_store = {}

# === Hàm lấy proxy ===
def fetch_proxies(protocol='http', count=10, custom_url=None):
    """Lấy proxy từ GitHub raw hoặc custom URL"""
    if custom_url and custom_url.startswith('http'):
        try:
            resp = requests.get(custom_url, timeout=10)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    if isinstance(data, list):
                        proxies = [str(p) for p in data if p]
                        return random.sample(proxies, min(count, len(proxies)))
                    elif isinstance(data, dict) and 'proxies' in data:
                        proxies = data['proxies']
                        return random.sample(proxies, min(count, len(proxies)))
                except:
                    lines = resp.text.split('\n')
                    proxies = [line.strip() for line in lines if line.strip()]
                    return random.sample(proxies, min(count, len(proxies)))
        except:
            pass
    
    # Fallback GitHub raw
    urls = {
        'http': 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
        'socks4': 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt',
        'socks5': 'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt'
    }
    try:
        resp = requests.get(urls.get(protocol, urls['http']), timeout=10)
        proxies = [p.strip() for p in resp.text.split('\n') if p.strip()]
        if proxies:
            return random.sample(proxies, min(count, len(proxies)))
    except:
        pass
    return []

# === Worker xử lý task ===
def worker():
    while True:
        task_id, task_data = task_queue.get()
        if task_data is None:
            break
        try:
            count = task_data['count']
            proxies = task_data.get('proxies', [])
            success = 0
            for _ in range(count):
                # Giả lập buff (có thể thay bằng request thật đến TikTok/Facebook)
                time.sleep(random.uniform(0.3, 0.8))
                success += 1
            result_store[task_id] = {'status': 'done', 'success': success, 'total': count}
        except Exception as e:
            result_store[task_id] = {'status': 'error', 'message': str(e)}
        finally:
            task_queue.task_done()

# Chạy worker (Vercel serverless không hỗ trợ threading lâu dài, nhưng vẫn chạy được trong thời gian ngắn)
threading.Thread(target=worker, daemon=True).start()

# === Routes ===
@app.route('/')
def index():
    # Nhúng HTML trực tiếp để không cần file templates
    html = '''
    <!DOCTYPE html>
    <html lang="vi">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Buff Pro</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            * { margin:0; padding:0; box-sizing:border-box; }
            body {
                font-family: 'Inter', sans-serif;
                min-height: 100vh;
                background: linear-gradient(135deg, #0d0d0d, #1a1a2e, #16213e);
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
                color: #fff;
            }
            .container {
                width: 100%;
                max-width: 600px;
                background: rgba(255,255,255,0.05);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 32px;
                padding: 40px 35px;
                box-shadow: 0 25px 50px -8px rgba(0,0,0,0.8);
                animation: fadeInUp 0.8s ease-out;
            }
            @keyframes fadeInUp {
                0% { opacity: 0; transform: translateY(30px); }
                100% { opacity: 1; transform: translateY(0); }
            }
            h1 {
                font-size: 28px;
                font-weight: 700;
                background: linear-gradient(90deg, #f7971e, #ffd200);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 6px;
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .subtitle {
                color: #a0aec0;
                font-size: 14px;
                margin-bottom: 25px;
            }
            .form-group { margin-bottom: 18px; }
            label {
                display: block;
                font-size: 13px;
                font-weight: 600;
                color: #cbd5e0;
                margin-bottom: 5px;
            }
            input, select {
                width: 100%;
                padding: 12px 14px;
                background: rgba(255,255,255,0.07);
                border: 1px solid rgba(255,255,255,0.15);
                border-radius: 12px;
                color: #fff;
                font-size: 14px;
                transition: 0.3s;
                outline: none;
            }
            input:focus, select:focus {
                border-color: #f7971e;
                box-shadow: 0 0 0 3px rgba(247,151,30,0.25);
                background: rgba(255,255,255,0.1);
            }
            select option { background: #1a1a2e; }
            .checkbox-group {
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .checkbox-group input {
                width: auto;
                accent-color: #f7971e;
            }
            .btn {
                padding: 12px 28px;
                background: linear-gradient(135deg, #f7971e, #ffd200);
                border: none;
                border-radius: 30px;
                font-weight: 700;
                font-size: 16px;
                color: #1a1a2e;
                cursor: pointer;
                transition: 0.3s ease;
                width: 100%;
                letter-spacing: 0.5px;
                box-shadow: 0 4px 15px rgba(247,151,30,0.3);
            }
            .btn:hover { transform: scale(1.02); box-shadow: 0 6px 25px rgba(247,151,30,0.5); }
            .btn:active { transform: scale(0.97); }
            .btn:disabled { opacity: 0.6; cursor: not-allowed; }
            .status-box {
                margin-top: 25px;
                background: rgba(0,0,0,0.3);
                border-radius: 16px;
                padding: 16px 20px;
                border-left: 4px solid #f7971e;
                display: none;
            }
            .status-box.active { display: block; animation: slideIn 0.4s ease; }
            @keyframes slideIn {
                0% { opacity: 0; transform: translateY(-10px); }
                100% { opacity: 1; transform: translateY(0); }
            }
            .status-box .log {
                font-family: monospace;
                font-size: 13px;
                color: #e2e8f0;
                max-height: 120px;
                overflow-y: auto;
                white-space: pre-wrap;
                word-break: break-all;
            }
            .spinner {
                display: inline-block;
                width: 18px;
                height: 18px;
                border: 3px solid rgba(255,255,255,0.1);
                border-top-color: #ffd200;
                border-radius: 50%;
                animation: spin 0.8s linear infinite;
                margin-right: 10px;
                vertical-align: middle;
            }
            @keyframes spin { to { transform: rotate(360deg); } }
            .result-success { color: #68d391; }
            .result-error { color: #fc8181; }
            .flex-row { display: flex; gap: 12px; }
            .flex-row .form-group { flex: 1; }
            @media (max-width: 600px) {
                .container { padding: 25px 18px; }
                h1 { font-size: 22px; }
                .flex-row { flex-direction: column; }
            }
            .proxy-options {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                align-items: center;
                margin-top: 6px;
            }
            .proxy-options select,
            .proxy-options input {
                flex: 1;
                min-width: 100px;
            }
            .manual-proxy-area textarea {
                width: 100%;
                padding: 10px;
                background: rgba(255,255,255,0.07);
                border: 1px solid rgba(255,255,255,0.15);
                border-radius: 12px;
                color: #fff;
                font-size: 13px;
                font-family: monospace;
                resize: vertical;
                min-height: 80px;
            }
            .hidden { display: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Buff Pro</h1>
            <p class="subtitle">Tăng view / like Facebook & TikTok với proxy tự động</p>

            <div class="form-group">
                <label>Nền tảng</label>
                <select id="platform">
                    <option value="tiktok">TikTok</option>
                    <option value="facebook">Facebook</option>
                </select>
            </div>

            <div class="flex-row">
                <div class="form-group">
                    <label>Hành động</label>
                    <select id="action">
                        <option value="view">👁️ View</option>
                        <option value="like">❤️ Like / Tim</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Số lượng</label>
                    <input type="number" id="count" value="10" min="1" max="100">
                </div>
            </div>

            <div class="form-group">
                <label>URL bài viết (hoặc Post ID)</label>
                <input type="text" id="url" placeholder="https://www.tiktok.com/@user/video/123456789">
            </div>

            <div class="form-group">
                <div class="checkbox-group">
                    <input type="checkbox" id="use_auto_proxy" checked>
                    <label for="use_auto_proxy" style="margin:0; font-weight:400;">Tự động lấy proxy từ GitHub</label>
                </div>
                <div class="proxy-options" id="auto_proxy_options">
                    <select id="protocol">
                        <option value="http">HTTP</option>
                        <option value="socks4">SOCKS4</option>
                        <option value="socks5">SOCKS5</option>
                    </select>
                    <input type="text" id="custom_proxy_url" placeholder="API proxy tùy chỉnh (nếu có)">
                </div>
                <div class="manual-proxy-area hidden" id="manual_proxy_group">
                    <label>Nhập proxy thủ công (mỗi dòng một proxy)</label>
                    <textarea id="proxy_list" placeholder="http://proxy1:8080&#10;http://proxy2:8080"></textarea>
                </div>
            </div>

            <button class="btn" id="startBtn">▶ Bắt đầu buff</button>

            <div class="status-box" id="statusBox">
                <div id="statusLog" class="log"></div>
            </div>
        </div>

        <script>
            document.getElementById('use_auto_proxy').addEventListener('change', function() {
                document.getElementById('auto_proxy_options').style.display = this.checked ? 'flex' : 'none';
                document.getElementById('manual_proxy_group').classList.toggle('hidden', this.checked);
            });

            const startBtn = document.getElementById('startBtn');
            const statusBox = document.getElementById('statusBox');
            const statusLog = document.getElementById('statusLog');

            startBtn.addEventListener('click', function() {
                const url = document.getElementById('url').value.trim();
                const count = parseInt(document.getElementById('count').value) || 5;
                const action = document.getElementById('action').value;
                const platform = document.getElementById('platform').value;
                const useAutoProxy = document.getElementById('use_auto_proxy').checked;
                const protocol = document.getElementById('protocol').value;
                const customProxyUrl = document.getElementById('custom_proxy_url').value.trim();
                const manualProxyList = document.getElementById('proxy_list').value.split('\\n').filter(p => p.trim());

                if (!url) {
                    alert('Vui lòng nhập URL.');
                    return;
                }

                const payload = {
                    url,
                    count,
                    action,
                    platform,
                    use_auto_proxy: useAutoProxy,
                    protocol,
                    custom_proxy_url: customProxyUrl,
                    proxy_list: manualProxyList
                };

                statusBox.classList.add('active');
                statusLog.innerHTML = `<div><span class="spinner"></span> Đang xử lý...</div>`;
                startBtn.disabled = true;

                fetch('/buff', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                })
                .then(res => res.json())
                .then(data => {
                    if (data.task_id) {
                        statusLog.innerHTML = `<div>✅ Task ID: ${data.task_id}</div>`;
                        pollStatus(data.task_id);
                    } else {
                        statusLog.innerHTML = `<div class="result-error">❌ Lỗi: ${data.error}</div>`;
                        startBtn.disabled = false;
                    }
                })
                .catch(err => {
                    statusLog.innerHTML = `<div class="result-error">❌ Lỗi kết nối: ${err.message}</div>`;
                    startBtn.disabled = false;
                });
            });

            function pollStatus(taskId) {
                let attempts = 0;
                const maxAttempts = 60;
                const interval = setInterval(() => {
                    fetch(`/status/${taskId}`)
                    .then(res => res.json())
                    .then(data => {
                        attempts++;
                        if (data.status === 'done' || data.status === 'error') {
                            clearInterval(interval);
                            if (data.status === 'done') {
                                statusLog.innerHTML = `<div class="result-success">✅ Thành công: ${data.success}/${data.total} lần</div>`;
                            } else {
                                statusLog.innerHTML = `<div class="result-error">❌ Lỗi: ${data.message}</div>`;
                            }
                            startBtn.disabled = false;
                        } else if (attempts >= maxAttempts) {
                            clearInterval(interval);
                            statusLog.innerHTML = `<div class="result-error">⏱️ Timeout</div>`;
                            startBtn.disabled = false;
                        } else {
                            statusLog.innerHTML = `<div><span class="spinner"></span> Đang thực hiện... (${Math.round(attempts/maxAttempts*100)}%)</div>`;
                        }
                    })
                    .catch(() => {});
                }, 1500);
            }

            // Khởi tạo hiển thị
            document.getElementById('auto_proxy_options').style.display = 'flex';
            document.getElementById('manual_proxy_group').classList.add('hidden');
        </script>
    </body>
    </html>
    '''
    return render_template_string(html)

@app.route('/proxies', methods=['GET'])
def get_proxies():
    protocol = request.args.get('protocol', 'http')
    count = int(request.args.get('count', 10))
    custom_url = request.args.get('url', '')
    proxies = fetch_proxies(protocol, count, custom_url)
    return jsonify({'proxies': proxies})

@app.route('/buff', methods=['POST'])
def buff():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing JSON'}), 400
    
    url = data.get('url')
    count = int(data.get('count', 5))
    use_auto_proxy = data.get('use_auto_proxy', True)
    protocol = data.get('protocol', 'http')
    custom_proxy_url = data.get('custom_proxy_url', '')
    manual_proxy_list = data.get('proxy_list', [])
    
    if not url:
        return jsonify({'error': 'Missing URL'}), 400
    
    if use_auto_proxy:
        proxy_list = fetch_proxies(protocol, count * 2, custom_proxy_url)
        if not proxy_list:
            return jsonify({'error': 'Không lấy được proxy tự động, vui lòng nhập thủ công'}), 400
    else:
        proxy_list = manual_proxy_list
    
    if not proxy_list:
        return jsonify({'error': 'Danh sách proxy trống'}), 400
    
    task_id = str(int(time.time() * 1000)) + str(random.randint(100, 999))
    task_data = {
        'url': url,
        'count': count,
        'proxies': proxy_list
    }
    task_queue.put((task_id, task_data))
    return jsonify({'task_id': task_id, 'status': 'queued'})

@app.route('/status/<task_id>')
def status(task_id):
    res = result_store.get(task_id)
    if res:
        return jsonify(res)
    return jsonify({'status': 'pending'}), 202

# Vercel yêu cầu biến 'app' là entry point
# Nếu chạy local, dùng app.run()
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

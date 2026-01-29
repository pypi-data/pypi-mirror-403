"""Main server implementation"""

import base64
import io
import json
import socket
import threading
import time
import webbrowser
from pathlib import Path

from flask import Flask, render_template_string, request, jsonify
from flask_socketio import SocketIO, emit
import mss
import qrcode
from PIL import Image
import pyautogui

# Disable PyAutoGUI failsafe
pyautogui.FAILSAFE = False


class ScreenSharer:
    def __init__(self):
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='threading', 
                                 engineio_logger=False, logger=False)
        
        self.active_viewers = set()
        self.current_frame = None
        self.screen_dimensions = None
        self.frame_lock = threading.Lock()
        self.local_ip = self.get_local_ip()
        self.port = 5000
        
        self.setup_routes()
        self.setup_socketio()
    
    def get_local_ip(self):
        """Get local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def generate_qr_code(self, url):
        """Generate QR code as base64 string"""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return base64.b64encode(buffer.getvalue()).decode()
    
    def capture_screen(self):
        """Capture screen and return as JPEG base64"""
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # Primary monitor
            screenshot = sct.grab(monitor)
            
            # Convert to PIL Image
            img = Image.frombytes('RGB', screenshot.size, screenshot.rgb)
            
            # Store dimensions
            self.screen_dimensions = {'width': img.width, 'height': img.height}
            
            # Compress to JPEG
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG', quality=70, optimize=True)
            buffer.seek(0)
            
            return base64.b64encode(buffer.getvalue()).decode()
    
    def screen_capture_loop(self):
        """Continuously capture and broadcast screen"""
        while True:
            if self.active_viewers:
                try:
                    frame_data = self.capture_screen()
                    with self.frame_lock:
                        self.current_frame = frame_data
                    
                    self.socketio.emit('screen_frame', {
                        'frame': frame_data,
                        'dimensions': self.screen_dimensions
                    }, namespace='/screen')
                    
                    time.sleep(0.0167)  # ~60 FPS
                except Exception as e:
                    print(f"Capture error: {e}")
                    time.sleep(1)
            else:
                time.sleep(0.5)
    
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def host():
            viewer_url = f"http://{self.local_ip}:{self.port}/view"
            qr_data = self.generate_qr_code(viewer_url)
            
            return render_template_string(HOST_HTML, 
                                        viewer_url=viewer_url,
                                        qr_code=qr_data,
                                        local_ip=self.local_ip,
                                        viewer_count=len(self.active_viewers))
        
        @self.app.route('/view')
        def view():
            return render_template_string(VIEWER_HTML)
        
        @self.app.route('/api/stats')
        def stats():
            return jsonify({
                'viewers': len(self.active_viewers),
                'dimensions': self.screen_dimensions
            })
    
    def setup_socketio(self):
        """Setup SocketIO event handlers"""
        
        @self.socketio.on('connect', namespace='/screen')
        def handle_connect():
            self.active_viewers.add(request.sid)
            print(f"✓ Viewer connected: {request.sid} (Total: {len(self.active_viewers)})")
            
            # Send current frame immediately
            with self.frame_lock:
                if self.current_frame:
                    emit('screen_frame', {
                        'frame': self.current_frame,
                        'dimensions': self.screen_dimensions
                    })
        
        @self.socketio.on('disconnect', namespace='/screen')
        def handle_disconnect():
            self.active_viewers.discard(request.sid)
            print(f"✗ Viewer disconnected: {request.sid} (Total: {len(self.active_viewers)})")
        
        @self.socketio.on('click', namespace='/screen')
        def handle_click(data):
            """Handle remote click events"""
            try:
                # Convert relative coordinates to absolute screen coordinates
                x_percent = data['x']
                y_percent = data['y']
                
                if self.screen_dimensions:
                    x = int(x_percent * self.screen_dimensions['width'])
                    y = int(y_percent * self.screen_dimensions['height'])
                    
                    # Perform the click
                    pyautogui.click(x, y)
                    print(f"Click at ({x}, {y})")
                    
            except Exception as e:
                print(f"Click error: {e}")
    
    def run(self):
        """Start the server"""
        # Start capture thread
        capture_thread = threading.Thread(target=self.screen_capture_loop, daemon=True)
        capture_thread.start()
        
        # Print startup info
        viewer_url = f"http://{self.local_ip}:{self.port}/view"
        print("\n" + "="*60)
        print("🚀 Sharer - Screen Sharing Started!")
        print("="*60)
        print(f"\n📱 Scan QR code or visit: {viewer_url}")
        print(f"🖥️  Control panel: http://{self.local_ip}:{self.port}/")
        print(f"\n💡 Viewers can tap/click the screen to control your mouse")
        print("\n⌨️  Press Ctrl+C to stop\n")
        
        # Open control panel in browser
        threading.Thread(target=lambda: webbrowser.open(f"http://{self.local_ip}:{self.port}/"), daemon=True).start()
        
        # Start server
        self.socketio.run(self.app, host='0.0.0.0', port=self.port, debug=False, allow_unsafe_werkzeug=True)


# HTML Templates
HOST_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sharer - Control Panel</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
            max-width: 600px;
            width: 100%;
            text-align: center;
        }
        h1 {
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .subtitle {
            color: #666;
            font-size: 1.1em;
            margin-bottom: 30px;
        }
        .qr-section {
            background: #f8f9fa;
            border-radius: 15px;
            padding: 30px;
            margin: 30px 0;
        }
        .qr-code {
            background: white;
            padding: 20px;
            border-radius: 10px;
            display: inline-block;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .qr-code img {
            display: block;
            max-width: 250px;
            height: auto;
        }
        .url {
            background: #667eea;
            color: white;
            padding: 15px 25px;
            border-radius: 10px;
            font-size: 1.1em;
            margin: 20px 0;
            word-break: break-all;
            font-family: 'Courier New', monospace;
        }
        .stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 30px;
        }
        .stat-box {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border: 2px solid #e9ecef;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }
        .instructions {
            background: #fff3cd;
            border: 2px solid #ffc107;
            border-radius: 10px;
            padding: 20px;
            margin-top: 30px;
            text-align: left;
        }
        .instructions h3 {
            color: #856404;
            margin-bottom: 15px;
        }
        .instructions ul {
            list-style-position: inside;
            color: #856404;
        }
        .instructions li {
            margin: 8px 0;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }
        .live-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            background: #28a745;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📡 Sharer</h1>
        <p class="subtitle">Screen sharing is active</p>
        
        <div class="qr-section">
            <h2 style="margin-bottom: 20px; color: #333;">Scan to View</h2>
            <div class="qr-code">
                <img src="data:image/png;base64,{{ qr_code }}" alt="QR Code">
            </div>
        </div>
        
        <div class="url">{{ viewer_url }}</div>
        
        <div class="stats">
            <div class="stat-box">
                <div class="stat-number" id="viewer-count">{{ viewer_count }}</div>
                <div class="stat-label"><span class="live-indicator"></span>Active Viewers</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{{ local_ip }}</div>
                <div class="stat-label">Local IP</div>
            </div>
        </div>
        
        <div class="instructions">
            <h3>🎯 How It Works</h3>
            <ul>
                <li>Scan the QR code with any device</li>
                <li>Your screen appears in their browser</li>
                <li>They can tap/click to control your mouse</li>
                <li>No apps needed - works in any browser!</li>
            </ul>
        </div>
    </div>
    
    <script>
        // Update viewer count periodically
        setInterval(() => {
            fetch('/api/stats')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('viewer-count').textContent = data.viewers;
                });
        }, 2000);
    </script>
</body>
</html>
"""

VIEWER_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Sharer Viewer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: #000;
            overflow: hidden;
            touch-action: none;
            -webkit-user-select: none;
            user-select: none;
        }
        #screen-container {
            width: 100vw;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            position: relative;
        }
        #screen {
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
            cursor: pointer;
        }
        #status {
            position: fixed;
            top: 10px;
            left: 10px;
            background: rgba(0,0,0,0.7);
            color: #fff;
            padding: 10px 15px;
            border-radius: 8px;
            font-family: monospace;
            font-size: 12px;
            z-index: 1000;
        }
        .click-indicator {
            position: absolute;
            width: 40px;
            height: 40px;
            border: 3px solid #667eea;
            border-radius: 50%;
            pointer-events: none;
            animation: clickPulse 0.6s ease-out;
        }
        @keyframes clickPulse {
            0% { transform: scale(0.5); opacity: 1; }
            100% { transform: scale(2); opacity: 0; }
        }
        .connected { color: #28a745; }
        .disconnected { color: #dc3545; }
    </style>
</head>
<body>
    <div id="status">
        <span id="connection-status" class="disconnected">● Connecting...</span>
    </div>
    
    <div id="screen-container">
        <img id="screen" alt="Remote Screen">
    </div>
    
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <script>
        const screen = document.getElementById('screen');
        const container = document.getElementById('screen-container');
        const statusEl = document.getElementById('connection-status');
        
        let screenDimensions = null;
        
        const socket = io('/screen', {
            transports: ['websocket', 'polling']
        });
        
        socket.on('connect', () => {
            statusEl.textContent = '● Connected';
            statusEl.className = 'connected';
        });
        
        socket.on('disconnect', () => {
            statusEl.textContent = '● Disconnected';
            statusEl.className = 'disconnected';
        });
        
        socket.on('screen_frame', (data) => {
            screen.src = 'data:image/jpeg;base64,' + data.frame;
            screenDimensions = data.dimensions;
        });
        
        function handleClick(e) {
            if (!screenDimensions) return;
            
            e.preventDefault();
            
            // Get click position relative to image
            const rect = screen.getBoundingClientRect();
            const x = e.clientX || (e.touches && e.touches[0].clientX);
            const y = e.clientY || (e.touches && e.touches[0].clientY);
            
            const relX = (x - rect.left) / rect.width;
            const relY = (y - rect.top) / rect.height;
            
            // Send click to server
            socket.emit('click', { x: relX, y: relY });
            
            // Visual feedback
            const indicator = document.createElement('div');
            indicator.className = 'click-indicator';
            indicator.style.left = (x - 20) + 'px';
            indicator.style.top = (y - 20) + 'px';
            document.body.appendChild(indicator);
            setTimeout(() => indicator.remove(), 600);
        }
        
        screen.addEventListener('click', handleClick);
        screen.addEventListener('touchstart', handleClick);
    </script>
</body>
</html>
"""


def start_server():
    """Main entry point"""
    try:
        sharer = ScreenSharer()
        sharer.run()
    except KeyboardInterrupt:
        print("\n\n👋 Sharer stopped. Thanks for using!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
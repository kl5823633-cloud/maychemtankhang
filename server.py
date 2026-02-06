# server.py
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import threading
import subprocess
import os
import json
import time
from datetime import datetime
import signal

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# Biến toàn cục để quản lý bot process
bot_process = None
bot_status = "stopped"
bot_start_time = None
bot_stats = {
    "servers": 0,
    "users": 0,
    "commands": 0,
    "uptime": "0s"
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/bot/status', methods=['GET'])
def get_bot_status():
    """API lấy trạng thái bot"""
    return jsonify({
        "status": bot_status,
        "servers": bot_stats["servers"],
        "users": bot_stats["users"],
        "commands": bot_stats["commands"],
        "uptime": bot_stats["uptime"],
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/bot/start', methods=['POST'])
def start_bot():
    """API khởi động bot"""
    global bot_process, bot_status, bot_start_time
    
    if bot_status == "running":
        return jsonify({"success": False, "message": "Bot đang chạy rồi"})
    
    try:
        # Kiểm tra file bot.py tồn tại
        if not os.path.exists("bot.py"):
            return jsonify({"success": False, "message": "Không tìm thấy file bot.py"})
        
        # Kiểm tra .env
        if not os.path.exists(".env"):
            return jsonify({"success": False, "message": "Không tìm thấy file .env"})
        
        # Khởi động bot trong process riêng
        bot_process = subprocess.Popen(
            ["python", "bot.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        bot_status = "running"
        bot_start_time = datetime.now()
        bot_stats["uptime"] = "0s"
        
        # Thread để đọc output bot
        threading.Thread(target=read_bot_output, daemon=True).start()
        
        return jsonify({
            "success": True, 
            "message": "Bot đang khởi động...",
            "pid": bot_process.pid
        })
        
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi: {str(e)}"})

@app.route('/api/bot/stop', methods=['POST'])
def stop_bot():
    """API dừng bot"""
    global bot_process, bot_status
    
    if bot_status != "running" or not bot_process:
        return jsonify({"success": False, "message": "Bot chưa chạy"})
    
    try:
        # Dừng process bot
        bot_process.terminate()
        bot_process.wait(timeout=5)
        
        bot_status = "stopped"
        return jsonify({"success": True, "message": "Bot đã dừng"})
        
    except Exception as e:
        # Force kill nếu cần
        try:
            bot_process.kill()
        except:
            pass
        bot_status = "stopped"
        return jsonify({"success": True, "message": "Bot đã dừng (force)"})

@app.route('/api/bot/restart', methods=['POST'])
def restart_bot():
    """API khởi động lại bot"""
    stop_result = stop_bot()
    time.sleep(2)
    start_result = start_bot()
    return start_result

@app.route('/api/bot/command', methods=['POST'])
def send_command():
    """API gửi command đến bot"""
    data = request.json
    command = data.get("command", "")
    
    if not command:
        return jsonify({"success": False, "message": "Thiếu command"})
    
    # Ghi command vào file để bot đọc
    try:
        with open("commands.txt", "a") as f:
            f.write(f"{datetime.now()}: {command}\n")
        bot_stats["commands"] += 1
        return jsonify({"success": True, "message": "Command đã gửi"})
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi: {str(e)}"})

def read_bot_output():
    """Đọc output từ bot process"""
    global bot_process, bot_stats
    
    while bot_process and bot_process.poll() is None:
        try:
            line = bot_process.stdout.readline()
            if line:
                print(f"[BOT] {line.strip()}")
                
                # Parse thông tin từ bot output
                if "Server count:" in line:
                    try:
                        count = int(line.split(":")[1].strip())
                        bot_stats["servers"] = count
                    except:
                        pass
                elif "Total users:" in line:
                    try:
                        count = int(line.split(":")[1].strip())
                        bot_stats["users"] = count
                    except:
                        pass
                        
        except:
            pass

def update_uptime():
    """Cập nhật thời gian uptime"""
    global bot_start_time, bot_stats
    
    while True:
        if bot_start_time and bot_status == "running":
            delta = datetime.now() - bot_start_time
            days = delta.days
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            seconds = delta.seconds % 60
            
            if days > 0:
                bot_stats["uptime"] = f"{days}d {hours}h"
            elif hours > 0:
                bot_stats["uptime"] = f"{hours}h {minutes}m"
            elif minutes > 0:
                bot_stats["uptime"] = f"{minutes}m {seconds}s"
            else:
                bot_stats["uptime"] = f"{seconds}s"
        
        time.sleep(1)

if __name__ == "__main__":
    # Bắt đầu thread cập nhật uptime
    threading.Thread(target=update_uptime, daemon=True).start()
    
    # Khởi động web server
    print("🚀 Web server đang khởi động...")
    print("📡 Dashboard: http://localhost:5000")
    print("📡 API: http://localhost:5000/api/bot/status")
    
    app.run(host='0.0.0.0', port=5000, debug=False)s

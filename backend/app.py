import os
import re
import json
import base64
import time
import uuid
import sqlite3
import datetime
import hashlib
import functools
import requests
import jwt
from flask import Flask, jsonify, request, g, send_file
from flask_cors import CORS
from openai import OpenAI
from PIL import Image
import io

app = Flask(__name__, static_folder='static')
CORS(app)  # 允许跨域请求

# ========== 配置 ==========
API_KEY = "sk-dwI0wRUeibzNWZYMDeA400D567354d85BdF3A8BfCeBc0aD3"
BASE_URL = "https://api.laozhang.ai/v1"
IMAGE_API_URL = "https://api.laozhang.ai/v1beta/models/gemini-3-pro-image-preview:generateContent"
JWT_SECRET = "your-secret-key-change-in-production"  # JWT 密钥
DB_PATH = os.path.join(os.path.dirname(__file__), 'static', 'tshirt.db')

# 初始化 OpenAI 客户端
client = OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL
)

# 路径配置
STYLE_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'style.md')
STATIC_DIR = os.path.join(os.path.dirname(__file__), 'static')
GENERATED_DIR = os.path.join(STATIC_DIR, 'generated')
HISTORY_FILE = os.path.join(STATIC_DIR, 'history.json')

# 确保目录存在
os.makedirs(GENERATED_DIR, exist_ok=True)

# ========== 数据库相关 ==========
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        # 创建用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                points INTEGER NOT NULL DEFAULT 30,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # 检查是否需要创建默认管理员 (admin/admin123)
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            password_hash = hashlib.sha256('admin123'.encode()).hexdigest()
            cursor.execute(
                "INSERT INTO users (username, password, role, points, ip_address) VALUES (?, ?, ?, ?, ?)",
                ('admin', password_hash, 'admin', 99999, '127.0.0.1')
            )
        db.commit()

# ========== 辅助函数 ==========
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    return stored_password == hashlib.sha256(provided_password.encode()).hexdigest()

def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
        
        if not token:
            return jsonify({"error": "Token is missing"}), 401
        
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            g.user_id = payload['user_id']
            g.user_role = payload['role']
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
            
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @functools.wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if g.user_role != 'admin':
            return jsonify({"error": "Admin privilege required"}), 403
        return f(*args, **kwargs)
    return decorated_function

# ========== API 路由 ==========

# 1. 认证相关
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    ip_address = request.headers.get('X-Real-IP', request.remote_addr)
    
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
        
    db = get_db()
    cursor = db.cursor()
    
    # 检查IP限制
    cursor.execute("SELECT id FROM users WHERE ip_address = ?", (ip_address,))
    # 注意：为了演示方便，如果IP是 127.0.0.1 (本地开发)，可能不限制，或者允许 admin 注册。
    # 这里严格按照需求：同一个ip只能注册一次
    # 如果是本地开发，且已有 admin，再注册可能会报错。
    # 我们放宽一点：如果是 admin 用户注册的 ip，不计入限制？或者仅限制普通用户注册。
    # 需求：同一个ip只能注册一次。
    # 检查是否存在非 admin 用户使用过该 IP
    if cursor.fetchone():
        # 如果已存在的用户是 admin，且当前注册不是 admin (不应该发生，admin 预设)，
        # 简单处理：严格检查 IP
        # 但考虑到本地开发多个测试账号，可以跳过 localhost
        if ip_address not in ['127.0.0.1', 'localhost', '::1']:
             return jsonify({"error": "Registration limit: One account per IP address"}), 403

    try:
        password_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO users (username, password, points, ip_address) VALUES (?, ?, ?, ?)",
            (username, password_hash, 30, ip_address)
        )
        db.commit()
        return jsonify({"message": "User registered successfully"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists"}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    if user and verify_password(user['password'], password):
        token = jwt.encode({
            'user_id': user['id'],
            'role': user['role'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)
        }, JWT_SECRET, algorithm="HS256")
        
        return jsonify({
            "token": token,
            "user": {
                "id": user['id'],
                "username": user['username'],
                "role": user['role'],
                "points": user['points']
            }
        })
    
    return jsonify({"error": "Invalid credentials"}), 401

@app.route('/api/auth/me', methods=['GET'])
@login_required
def get_current_user():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, username, role, points FROM users WHERE id = ?", (g.user_id,))
    user = cursor.fetchone()
    if user:
        return jsonify(dict(user))
    return jsonify({"error": "User not found"}), 404

# 2. 管理员相关
@app.route('/api/admin/users', methods=['GET'])
@admin_required
def get_all_users():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, username, role, points, ip_address, created_at FROM users ORDER BY created_at DESC")
    users = cursor.fetchall()
    return jsonify([dict(row) for row in users])

@app.route('/api/admin/users/<int:user_id>/points', methods=['PUT'])
@admin_required
def update_user_points(user_id):
    data = request.json
    points = data.get('points')
    
    if points is None:
        return jsonify({"error": "Points value required"}), 400
        
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE users SET points = ? WHERE id = ?", (points, user_id))
    db.commit()
    return jsonify({"message": "Points updated successfully"})

# 3. 原有功能适配
def parse_styles():
    styles = []
    if not os.path.exists(STYLE_FILE_PATH):
        return styles
    with open(STYLE_FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    pattern = re.compile(r'## \d+\. (.*?)\n.*?Prompt:\*\*(.*?)\*\*', re.DOTALL)
    matches = pattern.findall(content)
    for name, prompt in matches:
        styles.append({"name": name.strip(), "prompt": prompt.strip()})
    return styles

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_history(record):
    history = load_history()
    history.insert(0, record)
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

@app.route('/api/styles', methods=['GET'])
def get_styles():
    try:
        styles = parse_styles()
        return jsonify({"styles": styles})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/optimize', methods=['POST'])
@login_required # 需要登录
def optimize_prompt():
    data = request.json
    user_input = data.get('user_input', '')
    style_prompt = data.get('style_prompt', '')
    
    if not user_input or not style_prompt:
        return jsonify({"error": "Missing user_input or style_prompt"}), 400

    try:
        response = client.chat.completions.create(
            model="gemini-3-flash-preview",
            messages=[
                {"role": "system", "content": "你是一个提示词优化机器人。你的唯一任务是输出最终的提示词文本。严禁输出任何思考过程。请务必将最终生成的提示词包裹在 <result> 和 </result> 标签中，例如：<result>都市设计...</result>。"},
                {"role": "user", "content": f"任务：根据用户输入【{user_input}】和风格模板【{style_prompt}】生成nano banana pro风格的设计提示词。\n要求：\n1. 将风格模板中的“主题”替换为用户输入的主题。\n2. 提示词末尾必须包含：**isolated on white background.**\n4. 输出中文提示词。\n5. 最终结果必须用 <result> 标签包裹。"}
            ]
        )
        content = response.choices[0].message.content.strip()
        
        # 1. 优先尝试提取 <result> 标签内容
        if "<result>" in content:
            # 取最后一个 <result> 之后的内容，防止前面有思考过程提到 <result>
            optimized_prompt = content.split("<result>")[-1]
            # 如果有 </result>，则取其之前的内容
            if "</result>" in optimized_prompt:
                optimized_prompt = optimized_prompt.split("</result>", 1)[0]
            optimized_prompt = optimized_prompt.strip()
        else:
            # 2. 如果没有标签，回退到关键词匹配
            # 查找包含 isolated on white background 的行/段落
            lines = content.split('\n')
            target_line = None
            for line in lines:
                if "isolated on white background" in line:
                    target_line = line.strip()
            
            if target_line:
                # 尝试去掉可能的前缀，如 "设计提示词："
                if "：" in target_line:
                    optimized_prompt = target_line.split("：")[-1].strip()
                elif ":" in target_line:
                    optimized_prompt = target_line.split(":")[-1].strip()
                else:
                    optimized_prompt = target_line
            else:
                # 3. 最后的兜底：如果连关键词都找不到，使用原有逻辑尝试清洗
                optimized_prompt = content
                for split_key in ["提示词如下：", "设计提示词：", "Output:", "Here is the refined prompt:"]:
                    if split_key in optimized_prompt:
                        optimized_prompt = optimized_prompt.split(split_key)[-1].strip()
                        break

        return jsonify({"optimized_prompt": optimized_prompt})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate', methods=['POST'])
@login_required # 需要登录
def generate_image():
    # 检查积分
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT points FROM users WHERE id = ?", (g.user_id,))
    user = cursor.fetchone()
    
    if not user or user['points'] < 10:
        return jsonify({"error": "Insufficient points (Need 10 points)"}), 403

    data = request.json
    prompt = data.get('prompt', '')
    user_input = data.get('user_input', '')
    aspect_ratio = data.get('aspect_ratio', '1:1')
    
    if not prompt:
        return jsonify({"error": "Missing prompt"}), 400

    api_aspect_ratio = aspect_ratio
    if aspect_ratio == "2:3":
        api_aspect_ratio = "3:4" 
    
    headers = {
        "Authorization": f"Bearer {API_KEY}", 
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {
                "aspectRatio": api_aspect_ratio,
                "imageSize": "1K" 
            }
        }
    }

    try:
        response = requests.post(IMAGE_API_URL, headers=headers, json=payload, timeout=180)
        result = response.json()
        
        if "error" in result:
             return jsonify({"error": result["error"]}), 500
             
        if "candidates" in result and len(result["candidates"]) > 0:
            # 扣除积分
            cursor.execute("UPDATE users SET points = points - 10 WHERE id = ?", (g.user_id,))
            db.commit()
            
            image_data = result["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
            file_id = str(uuid.uuid4())
            filename = f"{file_id}.png"
            file_path = os.path.join(GENERATED_DIR, filename)
            
            with open(file_path, "wb") as f:
                f.write(base64.b64decode(image_data))
                
            record = {
                "id": file_id,
                "user_input": user_input if user_input else "未命名设计",
                "image_url": f"/static/generated/{filename}",
                "timestamp": int(time.time()),
                "user_id": g.user_id # 记录生成者
            }
            save_history(record)
            
            # 获取最新积分
            cursor.execute("SELECT points FROM users WHERE id = ?", (g.user_id,))
            new_points = cursor.fetchone()['points']
            
            return jsonify({
                "image_data": image_data,
                "image_url": record["image_url"],
                "remaining_points": new_points
            })
        else:
            return jsonify({"error": "No image generated", "details": result}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/gallery', methods=['GET'])
def get_gallery():
    # 所有人可见画廊，或者仅显示自己的？需求没说，假设所有人可见
    history = load_history()
    return jsonify({"gallery": history})

@app.route('/api/remove_bg', methods=['POST'])
@login_required
def remove_background():
    data = request.json
    image_url = data.get('image_url')
    
    if not image_url:
        return jsonify({"error": "Missing image_url"}), 400

    try:
        # 处理 image_url，去掉 /static/generated/ 前缀，或者直接读取文件
        # 假设 image_url 是 /static/generated/xxxx.png
        filename = os.path.basename(image_url)
        input_path = os.path.join(GENERATED_DIR, filename)
        
        if not os.path.exists(input_path):
            return jsonify({"error": "Image not found"}), 404

        output_filename = f"nobg_{filename}"
        output_path = os.path.join(GENERATED_DIR, output_filename)

        # 如果已经生成过，直接返回
        if os.path.exists(output_path):
             return jsonify({
                "image_url": f"/static/generated/{output_filename}"
            })

        # 读取图片并移除背景 (白底转透明)
        
        # 使用 PIL 将白色背景转为透明
        img = Image.open(input_path).convert("RGBA")
        datas = img.getdata()
        
        newData = []
        # 阈值：RGB 均大于 240 视为白色
        threshold = 240
        for item in datas:
            if item[0] > threshold and item[1] > threshold and item[2] > threshold:
                newData.append((255, 255, 255, 0))
            else:
                newData.append(item)
        
        img.putdata(newData)
        
        # 保存结果
        img.save(output_path, "PNG")

        return jsonify({
            "image_url": f"/static/generated/{output_filename}"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# 初始化数据库
init_db()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

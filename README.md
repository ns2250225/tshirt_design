# 👕 AI T-Shirt Design Generator (AI T恤图案生成器)

这是一个基于 AI 的 T 恤图案设计生成平台。用户可以通过输入简单的创意描述，结合预设的艺术风格，利用 AI 模型生成高质量的 T 恤设计图案。系统包含提示词优化、图像生成、自动抠图、实时预览以及用户积分管理等功能。

## ✨ 功能特性

- **🎨 风格化设计**：提供多种预设艺术风格（如像素风、复古风、极简线条等），让设计更具个性。
- **🧠 智能提示词优化**：内置 Gemini 模型，自动将用户的简单描述转化为专业的绘画提示词。
- **⚡️ 高速出图**：利用 Gemini-3-Pro-Image 模型快速生成高质量设计图（支持 1:1 和 2:3 比例）。
- **✂️ 智能抠图**：集成 `rembg` 工具，支持一键去除图片背景，方便直接用于 T 恤印制。
- **👥 用户系统**：
  - 注册/登录（JWT 认证）。
  - 积分管理系统（新用户赠送 30 积分，生成消耗 10 积分）。
  - 管理员后台（可修改用户积分）。
  - IP 注册限制（防止刷号）。
- **🖼 灵感画廊**：展示生成的优秀设计，支持“做同款”功能，一键复用提示词。
- **🐳 一键部署**：提供 Docker 和 Docker Compose 配置，支持一键部署到服务器。

## 🛠 技术栈

- **前端**：Vue 3, Vite, Vue Router
- **后端**：Python Flask, SQLite, PyJWT, Gunicorn
- **AI 能力**：
  - Google Gemini API (Prompt Optimization & Image Generation)
  - Rembg (Background Removal)
- **部署**：Docker, Docker Compose, Nginx

## 📂 目录结构

```
tshirt_design/
├── backend/                # 后端代码 (Flask)
│   ├── app.py              # 主应用程序逻辑
│   ├── static/             # 静态文件 (生成的图片、DB)
│   ├── requirements.txt    # Python 依赖
│   └── Dockerfile          # 后端 Docker 构建文件
├── frontend/               # 前端代码 (Vue3)
│   ├── src/                # Vue 源码
│   ├── public/             # 公共资源
│   ├── nginx.conf          # 前端 Nginx 配置
│   └── Dockerfile          # 前端 Docker 构建文件
├── docker-compose.yml      # Docker Compose 编排文件
├── deploy.sh               # 一键部署脚本
├── style.md                # 风格预设配置文件
├── prd.md                  # 产品需求文档
└── README.md               # 项目说明文档
```

## 🚀 快速开始

### 方式一：Docker 一键部署（推荐）

确保本地已安装 Docker 和 Docker Compose。

1. **克隆项目**
   ```bash
   git clone <repository_url>
   cd tshirt_design
   ```

2. **运行部署脚本**
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```
   脚本会自动构建镜像并启动服务。

3. **访问应用**
   - 前端页面：`http://localhost` (或服务器 IP)
   - 后端 API：`http://localhost:5000`

### 方式二：本地开发运行

#### 后端 (Backend)

1. 进入后端目录：
   ```bash
   cd backend
   ```
2. 创建并激活虚拟环境（可选）：
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # macOS/Linux
   # venv\Scripts\activate   # Windows
   ```
3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
4. 启动服务：
   ```bash
   python app.py
   ```
   服务将在 `http://localhost:5000` 启动。

#### 前端 (Frontend)

1. 进入前端目录：
   ```bash
   cd frontend
   ```
2. 安装依赖：
   ```bash
   npm install
   ```
3. 启动开发服务器：
   ```bash
   npm run dev
   ```
   服务将在 `http://localhost:5173` 启动。

## ⚙️ 配置说明

- **API Key**：目前 API Key 硬编码在 `backend/app.py` 中，生产环境建议迁移至环境变量。
- **管理员账号**：系统初始化时会自动创建默认管理员账号。
  - 用户名：`admin`
  - 密码：`admin123`
  - 权限：可访问 `/admin` 页面管理用户积分。

## 📝 注意事项

- **模型加载**：后端启动时会自动下载 `rembg` 抠图模型（约 100MB+），首次启动可能需要较长时间，请保持网络通畅。
- **数据库**：默认使用 SQLite，数据文件存储在 `backend/static/tshirt.db`。Docker 部署时请确保挂载了该卷以持久化数据。

## 📄 License

MIT

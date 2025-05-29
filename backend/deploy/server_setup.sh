#!/bin/bash
# πlot 服务器部署脚本

set -e

echo "🚀 开始部署 πlot 后端服务器..."

# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装基础依赖
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    nginx \
    certbot \
    python3-certbot-nginx \
    git \
    curl \
    htop \
    ufw \
    fail2ban

# 配置防火墙
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# 创建应用用户
sudo adduser --disabled-password --gecos "" pilot
sudo usermod -aG sudo pilot

# 切换到应用用户
sudo su - pilot << 'EOF'

# 创建应用目录
mkdir -p /home/pilot/app
cd /home/pilot/app

# 克隆代码（您需要替换为您的仓库地址）
git clone https://github.com/yourusername/pilot-backend.git .

# 创建Python虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装Python依赖
pip install -r requirements.txt

# 创建环境变量文件
cat > .env << 'ENVEOF'
DEBUG=False
HOST=0.0.0.0
PORT=8000
API_V1_STR=/api/v1
PROJECT_NAME=πlot Backend

# 请替换为您的实际配置
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SUPABASE_SERVICE_KEY=your_supabase_service_key

CLERK_SECRET_KEY=your_clerk_secret_key
CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
CLERK_JWT_ISSUER=your_clerk_issuer

OPENROUTER_API_KEY=your_openrouter_api_key

SECRET_KEY=your_super_secret_key_change_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

BACKEND_CORS_ORIGINS=https://same-ublsviolz5y-latest.netlify.app
ENVEOF

EOF

echo "✅ 基础设置完成！"

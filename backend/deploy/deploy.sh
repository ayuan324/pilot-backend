#!/bin/bash
# πlot 完整部署脚本

set -e

DOMAIN="your-domain.com"  # 请替换为您的域名
EMAIL="your-email@example.com"  # 请替换为您的邮箱

echo "🚀 开始部署 πlot 到生产服务器..."

# 1. 安装系统服务
echo "📦 安装系统服务..."
sudo cp pilot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pilot
sudo systemctl start pilot

# 2. 配置 Nginx
echo "🌐 配置 Nginx..."
sudo cp nginx.conf /etc/nginx/sites-available/pilot
sudo ln -sf /etc/nginx/sites-available/pilot /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 测试 Nginx 配置
sudo nginx -t

# 3. 获取 SSL 证书
echo "🔒 获取 SSL 证书..."
sudo certbot --nginx -d $DOMAIN -d api.$DOMAIN --email $EMAIL --agree-tos --non-interactive

# 4. 启动服务
echo "🔄 启动服务..."
sudo systemctl restart nginx
sudo systemctl restart pilot

# 5. 设置防火墙
echo "🛡️ 配置防火墙..."
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 8000

# 6. 设置自动更新SSL证书
echo "🔄 设置SSL证书自动更新..."
echo "0 12 * * * /usr/bin/certbot renew --quiet" | sudo crontab -

# 7. 检查服务状态
echo "✅ 检查服务状态..."
sudo systemctl status pilot --no-pager
sudo systemctl status nginx --no-pager

echo "🎉 部署完成！"
echo "📍 后端API地址: https://$DOMAIN"
echo "📊 健康检查: https://$DOMAIN/health"
echo "📖 API文档: https://$DOMAIN/docs"

# 8. 显示有用的管理命令
echo ""
echo "📋 常用管理命令："
echo "sudo systemctl status pilot     # 查看服务状态"
echo "sudo systemctl restart pilot    # 重启服务"
echo "sudo journalctl -u pilot -f     # 查看实时日志"
echo "sudo nginx -t && sudo systemctl reload nginx  # 重载Nginx配置"

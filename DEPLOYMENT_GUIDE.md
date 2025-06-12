# 🚀 πlot 部署指南

## 项目概述

πlot 是一个基于 AI 的工作流构建平台，支持自然语言生成工作流、可视化编辑和实时执行。

### 技术栈
- **前端**: React + TypeScript + React Flow
- **后端**: FastAPI + Python
- **数据库**: Supabase (PostgreSQL)
- **AI服务**: OpenRouter (支持多种LLM模型)
- **部署**: Docker + Railway/Vercel

---

## 🏗️ 架构改进

### 已完成的增强功能

1. **完整的节点定义系统**
   - 参考 Dify 架构，支持 15+ 种节点类型
   - 包括 LLM、代码执行、HTTP请求、条件判断等
   - 完整的节点配置和属性定义

2. **智能工作流生成**
   - 增强的意图分析，支持更多场景识别
   - 详细的工作流结构生成，包含实用的节点配置
   - 自动验证和优化生成的工作流

3. **实际工作流执行引擎**
   - 支持节点间数据传递和变量替换
   - 实时执行进度跟踪
   - 错误处理和日志记录
   - 流式执行结果返回

4. **工作流验证系统**
   - 结构完整性检查
   - 节点配置验证
   - 变量依赖分析

---

## 🚀 部署方案

### 方案一：Railway 部署（推荐）

#### 后端部署
```bash
# 1. 安装 Railway CLI
npm install -g @railway/cli

# 2. 登录 Railway
railway login

# 3. 进入后端目录
cd backend

# 4. 初始化 Railway 项目
railway init

# 5. 设置环境变量
railway variables set OPENROUTER_API_KEY=your_openrouter_key
railway variables set SUPABASE_URL=your_supabase_url
railway variables set SUPABASE_ANON_KEY=your_supabase_anon_key
railway variables set SECRET_KEY=your_secret_key

# 6. 部署
railway up
```

#### 前端部署到 Vercel
```bash
# 1. 安装 Vercel CLI
npm install -g vercel

# 2. 进入前端目录
cd aiflow-homepage

# 3. 部署
vercel

# 4. 设置环境变量
vercel env add REACT_APP_BACKEND_URL production
# 输入你的 Railway 后端 URL
```

### 方案二：Docker 自托管

#### 构建和运行
```bash
# 后端
cd backend
docker build -t pilot-backend .
docker run -p 8000:8000 \
  -e OPENROUTER_API_KEY=your_key \
  -e SUPABASE_URL=your_url \
  -e SUPABASE_ANON_KEY=your_key \
  pilot-backend

# 前端
cd aiflow-homepage
docker build -t pilot-frontend .
docker run -p 3000:3000 pilot-frontend
```

#### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
      - SECRET_KEY=${SECRET_KEY}
    
  frontend:
    build: ./aiflow-homepage
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_BACKEND_URL=http://localhost:8000
    depends_on:
      - backend
```

---

## 🔧 环境配置

### 必需的环境变量

#### 后端 (.env)
```bash
# AI 服务
OPENROUTER_API_KEY=sk-or-v1-your_openrouter_api_key

# 数据库
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# 安全
SECRET_KEY=your_very_long_secret_key_here
CLERK_SECRET_KEY=your_clerk_secret_key

# 应用配置
DEBUG=False
HOST=0.0.0.0
PORT=8000
```

#### 前端 (.env)
```bash
REACT_APP_BACKEND_URL=https://your-backend-url.railway.app
REACT_APP_CLERK_PUBLISHABLE_KEY=your_clerk_publishable_key
```

---

## 🧪 功能测试

### 1. 测试工作流生成
```bash
curl -X POST "https://your-backend-url/api/v1/ai/generate-workflow" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token" \
  -d '{
    "prompt": "创建一个客户服务聊天机器人",
    "preferences": {}
  }'
```

### 2. 测试工作流执行
```bash
curl -X POST "https://your-backend-url/api/v1/workflows/execute/workflow_id" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token" \
  -d '{
    "input_data": {
      "user_input": "你好，我需要帮助"
    }
  }'
```

### 3. 测试流式执行
```bash
curl -X POST "https://your-backend-url/api/v1/workflows/execute-stream/workflow_id" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_token" \
  -d '{
    "input_data": {
      "user_input": "分析这个数据"
    }
  }'
```

---

## 📊 监控和维护

### 1. 日志监控
- Railway 提供内置日志查看
- 可集成 Sentry 进行错误跟踪
- 使用 Supabase 仪表板监控数据库

### 2. 性能优化
- 启用 Redis 缓存（可选）
- 配置 CDN 加速前端资源
- 数据库查询优化

### 3. 扩展性考虑
- 使用 Celery + Redis 处理长时间运行的工作流
- 实现工作流执行的队列系统
- 添加负载均衡器

---

## 🔒 安全配置

### 1. API 安全
- 所有 API 端点都需要认证
- 使用 HTTPS 加密传输
- 实现请求频率限制

### 2. 代码执行安全
- 当前代码执行节点使用受限环境
- 生产环境建议使用 Docker 沙箱
- 限制可用的 Python 模块和函数

### 3. 数据安全
- 敏感数据加密存储
- 定期备份数据库
- 实现用户数据隔离

---

## 🚨 故障排除

### 常见问题

1. **工作流生成失败**
   - 检查 OpenRouter API 密钥是否有效
   - 确认账户有足够的额度
   - 查看后端日志获取详细错误信息

2. **工作流执行失败**
   - 验证工作流结构是否完整
   - 检查节点配置是否正确
   - 确认输入数据格式匹配

3. **前端连接失败**
   - 检查后端 URL 配置
   - 确认 CORS 设置正确
   - 验证认证令牌有效性

### 调试命令
```bash
# 检查后端健康状态
curl https://your-backend-url/health

# 查看可用模型
curl https://your-backend-url/api/v1/ai/models

# 测试 AI 连接
curl -X POST https://your-backend-url/api/v1/ai/test-connection
```

---

## 📈 下一步计划

1. **短期目标**
   - 完善前端工作流编辑器
   - 添加更多节点类型
   - 实现工作流模板市场

2. **中期目标**
   - 集成更多 AI 服务提供商
   - 添加工作流版本控制
   - 实现团队协作功能

3. **长期目标**
   - 构建插件生态系统
   - 支持自定义节点开发
   - 企业级功能和部署选项

---

## 💡 最佳实践

1. **开发环境**
   - 使用虚拟环境隔离依赖
   - 定期更新依赖包
   - 遵循代码规范和注释

2. **生产环境**
   - 使用环境变量管理配置
   - 实现健康检查和监控
   - 定期备份和更新

3. **用户体验**
   - 提供清晰的错误信息
   - 实现进度指示器
   - 优化响应时间

---

## 📞 支持

如果在部署过程中遇到问题，请：

1. 查看项目文档和日志
2. 检查环境变量配置
3. 验证网络连接和权限
4. 参考故障排除指南

项目已经具备了完整的 MVP 功能，可以进行生产部署和使用。 
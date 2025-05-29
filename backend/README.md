# πlot Backend

AI Workflow Builder Backend - FastAPI + Clerk + Supabase

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Copy environment variables
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run Development Server

```bash
python run.py
```

The API will be available at `http://localhost:8000`

## 📋 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `CLERK_SECRET_KEY` | Clerk secret key for authentication | ✅ |
| `CLERK_PUBLISHABLE_KEY` | Clerk publishable key | ✅ |
| `CLERK_JWT_ISSUER` | Clerk JWT issuer URL | ✅ |
| `SUPABASE_URL` | Supabase project URL | ✅ |
| `SUPABASE_KEY` | Supabase anon key | ✅ |
| `SUPABASE_SERVICE_KEY` | Supabase service role key | ✅ |
| `OPENROUTER_API_KEY` | OpenRouter API key for LLM access | ✅ |
| `SENTRY_DSN` | Sentry DSN for error monitoring | ❌ |
| `DEBUG` | Enable debug mode | ❌ |

## 🏗️ Architecture

### Core Components

- **FastAPI**: High-performance async web framework
- **Clerk**: User authentication and management
- **Supabase**: PostgreSQL database with real-time features
- **LiteLLM**: Universal LLM API client
- **Sentry**: Error monitoring and performance tracking

### Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── workflows.py
│   │       │   └── executions.py
│   │       └── api.py
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── database/
│   │   └── supabase_client.py
│   ├── models/
│   │   ├── workflow.py
│   │   └── execution.py
│   ├── services/
│   │   ├── workflow_service.py
│   │   └── execution_service.py
│   └── main.py
├── requirements.txt
├── .env.example
└── run.py
```

## 🔐 Authentication

The API uses Clerk for authentication. All protected endpoints require a valid JWT token:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:8000/api/v1/workflows
```

## 📡 API Endpoints

### Workflows

- `POST /api/v1/workflows` - Create workflow
- `GET /api/v1/workflows` - List workflows
- `GET /api/v1/workflows/{id}` - Get workflow
- `PUT /api/v1/workflows/{id}` - Update workflow
- `DELETE /api/v1/workflows/{id}` - Delete workflow
- `POST /api/v1/workflows/{id}/execute` - Execute workflow

### Executions

- `GET /api/v1/executions` - List executions
- `GET /api/v1/executions/{id}` - Get execution
- `POST /api/v1/executions/{id}/cancel` - Cancel execution

### WebSocket

- `WS /ws/{user_id}` - Real-time execution updates

## 🎯 Workflow Models

### Node Types

- `start` - Workflow entry point
- `llm` - Large Language Model processing
- `condition` - Conditional branching
- `code` - Custom code execution
- `http` - HTTP API calls
- `variable` - Variable manipulation
- `output` - Workflow output

### Example Workflow

```json
{
  "name": "Simple Chatbot",
  "description": "Basic conversational AI",
  "nodes": [
    {
      "id": "start",
      "type": "start",
      "position": {"x": 100, "y": 100},
      "config": {"name": "User Input"}
    },
    {
      "id": "llm",
      "type": "llm",
      "position": {"x": 300, "y": 100},
      "config": {
        "name": "AI Response",
        "model": "gpt-3.5-turbo",
        "prompt_template": "Respond to: {input}"
      }
    },
    {
      "id": "output",
      "type": "output",
      "position": {"x": 500, "y": 100},
      "config": {"name": "Bot Response"}
    }
  ],
  "edges": [
    {"source": "start", "target": "llm"},
    {"source": "llm", "target": "output"}
  ]
}
```

## 🔄 Real-time Execution

Workflows execute asynchronously with real-time progress updates via WebSocket:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/user123');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Execution update:', data);
};
```

## 🛠️ Development

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest
```

### Code Quality

```bash
# Format code
black app/

# Type checking
mypy app/

# Linting
flake8 app/
```

### Database Migrations

The backend uses Supabase's built-in migration system. See the frontend project for SQL schema files.

## 📊 Monitoring

### Sentry Integration

Error monitoring is automatically enabled when `SENTRY_DSN` is provided:

```python
# Errors are automatically captured
raise HTTPException(status_code=400, detail="Invalid workflow")
```

### Health Checks

- `GET /` - Basic health check
- `GET /health` - Detailed health status

## 🚀 Deployment

### Docker

```bash
# Build image
docker build -t pilot-backend .

# Run container
docker run -p 8000:8000 --env-file .env pilot-backend
```

### Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy
railway login
railway link
railway up
```

## 🔧 Configuration

### Environment Modes

- **Development**: `DEBUG=True` - Enables auto-reload, detailed errors
- **Production**: `DEBUG=False` - Optimized for performance and security

### CORS

Configure allowed origins in `BACKEND_CORS_ORIGINS`:

```env
BACKEND_CORS_ORIGINS=http://localhost:3000,https://myapp.com
```

## 📈 Performance

- **Async/Await**: All I/O operations are asynchronous
- **Connection Pooling**: Supabase handles database connections
- **Caching**: Redis integration for session and execution caching
- **Rate Limiting**: Built-in protection against abuse

## 🔍 Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify Clerk configuration
   - Check JWT token validity

2. **Database Connection Issues**
   - Confirm Supabase credentials
   - Check network connectivity

3. **WebSocket Connection Failed**
   - Verify CORS settings
   - Check firewall rules

### Debugging

Enable debug mode for detailed error messages:

```env
DEBUG=True
```

## 📚 API Documentation

When running in debug mode, interactive API documentation is available:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

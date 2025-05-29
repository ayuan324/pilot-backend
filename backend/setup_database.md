# Database Setup Instructions

## πlot Supabase Database Setup

### 1. Create Supabase Project

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Click "New Project"
3. Choose organization and set project details:
   - **Name**: `pilot-ai-workflows`
   - **Database Password**: Generate a strong password
   - **Region**: Choose closest to your users

### 2. Run Database Schema

1. In your Supabase project, go to **SQL Editor**
2. Copy and paste the entire content of `database/supabase_schema.sql`
3. Click **Run** to execute the schema

This will create:
- All necessary tables (`workflows`, `workflow_executions`, etc.)
- Indexes for performance
- Row Level Security (RLS) policies
- Triggers for automatic updates
- Default workflow templates
- Analytics views

### 3. Configure Environment Variables

Update your `.env` file with Supabase credentials:

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-public-key
SUPABASE_SERVICE_KEY=your-service-role-key
```

### 4. Test Database Connection

Run the backend server and test the connection:

```bash
cd backend
python run.py
```

Visit `http://localhost:8000/docs` and test the following endpoints:
- `GET /health` - Should return healthy status
- `GET /api/v1/workflows/templates` - Should return default templates

### 5. Database Structure Overview

#### Core Tables

**workflows**
- Stores user-created workflows
- Includes workflow data (nodes, edges, variables)
- RLS: Users can only access their own workflows + public ones

**workflow_executions**
- Individual execution instances
- Tracks status, timing, costs, tokens
- RLS: Users can only access their own executions

**node_execution_logs**
- Detailed logs for each node execution
- Input/output data, timing, errors
- RLS: Inherited from parent execution

**execution_events**
- Real-time events during execution
- Used for WebSocket streaming
- RLS: Inherited from parent execution

**workflow_templates**
- System-defined workflow templates
- Public read access for all users

**user_workflow_stats**
- Aggregated user statistics
- RLS: Users can only access their own stats

#### Features

- **Automatic Timestamps**: `created_at`, `updated_at` auto-updated
- **Computed Columns**: Duration calculated automatically
- **Triggers**: Execution counts, user stats updated automatically
- **Full Text Search**: Workflows searchable by name/description
- **Analytics Views**: Pre-built views for reporting

### 6. Sample Data

The schema includes 3 default templates:
- **Simple Chatbot**: Basic conversational AI
- **Content Generator**: Blog/article generation
- **Data Analyzer**: Data analysis with insights

### 7. Testing the Setup

Use these SQL queries to verify setup:

```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';

-- Check templates loaded
SELECT id, name, category FROM workflow_templates;

-- Check RLS policies
SELECT schemaname, tablename, policyname
FROM pg_policies WHERE schemaname = 'public';

-- Test user stats trigger (after creating test data)
SELECT * FROM user_workflow_stats;
```

### 8. Backup and Maintenance

#### Daily Cleanup (Optional)
```sql
-- Clean old execution events (older than 30 days)
SELECT cleanup_old_execution_events();
```

#### Regular Backups
- Supabase automatically backs up your database
- For additional safety, consider exporting critical data periodically

### 9. Monitoring

Monitor database performance in Supabase Dashboard:
- **Database** → **Metrics**: Query performance, connections
- **Database** → **Extensions**: Ensure `uuid-ossp` and `pg_trgm` are enabled
- **Authentication** → **Settings**: RLS policies working correctly

### 10. Troubleshooting

#### Common Issues

**RLS Policy Errors**
```
permission denied for table workflows
```
- Ensure `auth.jwt() ->> 'sub'` returns correct user ID
- Check Clerk JWT token format

**Performance Issues**
```sql
-- Check slow queries
SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;

-- Check index usage
SELECT * FROM pg_stat_user_indexes WHERE idx_scan = 0;
```

**Connection Issues**
- Verify environment variables are correct
- Check Supabase project is not paused
- Ensure database password is correct

#### Reset Database (Development Only)
```sql
-- WARNING: This will delete all data
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
-- Then re-run the schema file
```

### 11. Production Considerations

- **Connection Pooling**: Supabase handles this automatically
- **SSL**: Always enabled on Supabase
- **Backups**: Automatic daily backups
- **Monitoring**: Use Supabase metrics + Sentry for application monitoring
- **Scaling**: Supabase Pro automatically scales

The database is now ready for πlot workflows! 🚀

# Troubleshooting Guide

## Common Issues and Solutions

### 🐳 Docker Issues

#### Services Won't Start
```bash
# Check if ports are already in use
lsof -i :3000
lsof -i :8000
lsof -i :5432

# Kill processes using these ports if needed
kill -9 <PID>

# Restart with clean build
docker-compose down -v
docker-compose up --build
```

#### Database Connection Errors
```bash
# Check database container status
docker-compose ps db

# View database logs
docker-compose logs db

# Connect to database directly
docker-compose exec db psql -U postgres -d sdrdb

# Reset database completely
docker-compose down -v
docker volume rm sdr-grok-demo_sdr_pgdata
docker-compose up --build
```

#### Frontend Build Failures
```bash
# Clear node modules and rebuild
docker-compose exec frontend rm -rf node_modules
docker-compose exec frontend npm install
docker-compose restart frontend
```

### 🔑 API Configuration Issues

#### Grok API Errors
```bash
# Test API connectivity
curl -H "Authorization: Bearer $GROK_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "Hello", "max_tokens": 10}' \
     $GROK_API_URL

# Check environment variables
docker-compose exec backend env | grep GROK

# Verify .env file format
cat .env | grep -v "^#"
```

#### JSON Parsing Errors
- **Symptom**: "Could not parse Grok output" errors
- **Cause**: Grok returning non-JSON responses
- **Solution**: 
  1. Improve prompts in `backend/app/prompts.py`
  2. Add stricter JSON formatting instructions
  3. Review evaluation results for patterns

### 🌐 Network Issues

#### Frontend Can't Connect to Backend
```bash
# Check if backend is accessible
curl http://localhost:8000/

# Check proxy configuration
cat frontend/vite.config.js

# Test direct API call
curl http://localhost:8000/leads
```

#### CORS Errors
- **Symptom**: Browser console shows CORS errors
- **Solution**: Backend CORS is configured for all origins in development
- **Production**: Update CORS settings in `backend/app/main.py`

### 📊 Data Issues

#### No Leads Showing
```bash
# Seed the database
python scripts/seed_data.py

# Or create a lead manually
curl -X POST http://localhost:8000/leads \
  -H "Content-Type: application/json" \
  -d '{"company": "Test Corp", "name": "Test User"}'
```

#### Qualification Not Working
```bash
# Check if Grok API is configured
curl -X POST http://localhost:8000/leads/qualify \
  -H "Content-Type: application/json" \
  -d '{"lead_id": 1}' | jq

# Check backend logs
docker-compose logs backend
```

### 🔍 Debugging Commands

#### Check Service Health
```bash
# All services
docker-compose ps

# Individual service logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs db

# Service health checks
curl http://localhost:8000/  # Backend health
curl http://localhost:3000/  # Frontend health
```

#### Database Debugging
```bash
# Connect to database
docker-compose exec db psql -U postgres -d sdrdb

# List tables
\dt

# Check leads table
SELECT * FROM lead;

# Check activity logs
SELECT * FROM activitylog;
```

#### API Testing
```bash
# Test all endpoints
./scripts/demo_commands.sh

# Individual endpoint tests
curl http://localhost:8000/leads
curl http://localhost:8000/evals/run
```

### 🚨 Error Messages

#### "lead not found"
- **Cause**: Lead ID doesn't exist
- **Solution**: Check available leads with `GET /leads`

#### "Network error contacting Grok"
- **Cause**: Grok API is unreachable
- **Solution**: Check API URL and network connectivity

#### "Unexpected Grok response format"
- **Cause**: Grok API response structure changed
- **Solution**: Update `grok_client.py` to handle new format

#### "Could not parse Grok output"
- **Cause**: Grok returned non-JSON response
- **Solution**: Improve prompts or add better parsing logic

### 🔧 Performance Issues

#### Slow API Responses
```bash
# Check database performance
docker-compose exec db psql -U postgres -d sdrdb -c "EXPLAIN ANALYZE SELECT * FROM lead;"

# Monitor resource usage
docker stats

# Check Grok API response times
time curl -X POST http://localhost:8000/leads/qualify \
  -H "Content-Type: application/json" \
  -d '{"lead_id": 1}'
```

#### Frontend Loading Issues
```bash
# Check bundle size
docker-compose exec frontend npm run build
ls -la frontend/dist/

# Check for JavaScript errors
# Open browser dev tools and check console
```

### 🛠️ Development Tips

#### Hot Reloading Not Working
```bash
# Ensure volumes are mounted correctly
docker-compose exec backend ls -la /app
docker-compose exec frontend ls -la /app

# Restart with volume mounts
docker-compose restart backend frontend
```

#### Environment Variable Issues
```bash
# Check if .env file is loaded
docker-compose config

# Verify environment in container
docker-compose exec backend env | grep GROK
```

### 📝 Logging

#### Enable Debug Logging
```bash
# Add to .env file
LOG_LEVEL=DEBUG

# Or set in docker-compose.yml
environment:
  - LOG_LEVEL=DEBUG
```

#### View Real-time Logs
```bash
# Follow all logs
docker-compose logs -f

# Follow specific service
docker-compose logs -f backend
```

### 🆘 Getting Help

If you're still experiencing issues:

1. **Check the logs**: `docker-compose logs`
2. **Verify configuration**: Ensure `.env` file is correct
3. **Test components individually**: Use the demo commands script
4. **Check system resources**: Ensure Docker has enough memory/CPU
5. **Review the README**: Check setup instructions

### 🔄 Reset Everything

If all else fails, reset the entire environment:

```bash
# Stop and remove everything
docker-compose down -v
docker system prune -f

# Remove all volumes
docker volume prune -f

# Rebuild from scratch
docker-compose up --build
```

This will give you a completely fresh start.

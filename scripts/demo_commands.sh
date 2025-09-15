#!/bin/bash

# Demo Commands for Grok SDR System
# Run these commands to demonstrate the system functionality

echo "🚀 Grok SDR Demo Commands"
echo "========================="

# Check if services are running
echo "📋 Checking service status..."
curl -s http://localhost:8000/ > /dev/null && echo "✅ Backend is running" || echo "❌ Backend is not running"
curl -s http://localhost:3000/ > /dev/null && echo "✅ Frontend is running" || echo "❌ Frontend is not running"

echo ""
echo "📊 1. List all leads:"
curl -s http://localhost:8000/leads | jq '.[] | {id, company, name, score, stage}'

echo ""
echo "🎯 2. Create a new lead:"
curl -X POST http://localhost:8000/leads \
  -H "Content-Type: application/json" \
  -d '{
    "company": "Demo Corp",
    "name": "John Demo",
    "title": "VP Engineering",
    "email": "john@democorp.com",
    "website": "https://democorp.com",
    "metadata": {
      "company_size": 100,
      "industry": "Technology",
      "recent_funding": "Series B"
    }
  }' | jq '{id, company, name, stage}'

echo ""
echo "🧠 3. Run AI qualification on lead ID 1:"
curl -X POST http://localhost:8000/leads/qualify \
  -H "Content-Type: application/json" \
  -d '{
    "lead_id": 1,
    "scoring_weights": {
      "company_size": 2,
      "industry_fit": 3,
      "funding": 2
    }
  }' | jq '{lead_id, score, stage, grok_output}'

echo ""
echo "✉️ 4. Generate outreach message for lead ID 1:"
curl -X POST http://localhost:8000/leads/outreach/1 \
  -H "Content-Type: application/json" | jq '{lead_id, outreach}'

echo ""
echo "🧪 5. Run evaluation framework:"
curl -s http://localhost:8000/evals/run | jq '{results_summary}'

echo ""
echo "📈 6. Check lead status after qualification:"
curl -s http://localhost:8000/leads/1 | jq '{id, company, score, stage}'

echo ""
echo "🎉 Demo complete! Visit http://localhost:3000 for the full UI experience."

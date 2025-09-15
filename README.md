# Grok-powered SDR Demo

A prototype Sales Development Representative (SDR) system that uses Grok as the intelligence layer to qualify leads, generate personalized outreach, and manage pipeline progression.

## 🚀 Features

- **Grok API Integration**: Core intelligence layer for lead qualification and outreach generation
- **Lead Qualification**: AI-powered scoring with customizable weights and automated pipeline progression
- **Personalized Outreach**: Generate tailored email subject lines and body content
- **Pipeline Management**: Track leads through defined stages with activity logging
- **Evaluation Framework**: Systematic prompt engineering with test cases and metrics
- **Modern UI**: Clean, responsive interface built with React and Tailwind CSS
- **Containerized Deployment**: Easy setup with Docker and docker-compose

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend│    │  FastAPI Backend│    │  PostgreSQL DB  │
│   (Port 3000)   │◄──►│   (Port 8000)   │◄──►│   (Port 5432)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Grok API      │
                       │  (External)     │
                       └─────────────────┘
```

## 🛠️ Quick Start

### Prerequisites

- Docker and Docker Compose
- Grok API access (API key and endpoint)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd sdr-grok-demo
```

### 2. Configure Environment

```bash
cp env.example .env
```

Edit `.env` with your Grok API credentials:
```env
GROK_API_URL=https://api.grok.example/v1/generate
GROK_API_KEY=your_actual_grok_api_key
```

### 3. Start the System

```bash
docker-compose up --build
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📊 Demo Script (5 Minutes)

### 1. Dashboard Overview (1 minute)
- Show the clean, modern interface
- Explain the pipeline stages and lead scoring
- Highlight the AI-powered features

### 2. Lead Qualification (2 minutes)
- Click on a lead to open details
- Click "Run AI Qualification"
- Show the Grok-generated score and justification
- Demonstrate automated pipeline progression (score ≥ 70 → Qualified)

### 3. Outreach Generation (1.5 minutes)
- Click "Generate Outreach"
- Show personalized subject line and email body
- Highlight how Grok uses lead metadata for personalization

### 4. Evaluation Framework (30 seconds)
- Show the evaluation system for prompt engineering
- Demonstrate how to improve prompts based on test results

## 🔧 API Endpoints

### Leads
- `GET /leads` - List all leads
- `POST /leads` - Create new lead
- `GET /leads/{id}` - Get lead details
- `POST /leads/qualify` - Run AI qualification
- `POST /leads/outreach/{id}` - Generate outreach message

### Evaluations
- `GET /evals/run` - Run evaluation framework

## 🧪 Evaluation Framework

The system includes a comprehensive evaluation framework for prompt engineering:

### Test Cases
Located in `evals/cases.json`, includes:
- Small startup scenarios
- Enterprise leads
- Various industry types
- Different scoring weights

### Running Evaluations

```bash
# Via API
curl http://localhost:8000/evals/run

# Direct script
cd evals
python run_evals.py
```

### Evaluation Metrics
- Score accuracy within tolerance
- JSON parsing success rate
- Response quality assessment
- Prompt iteration recommendations

## 🎯 Key Features Deep Dive

### Lead Qualification
- **Scoring**: 0-100 scale with customizable weights
- **Breakdown**: Detailed criteria analysis
- **Justification**: Human-readable reasoning
- **Auto-progression**: Automatic stage advancement based on score

### Outreach Generation
- **Personalization**: Uses company metadata and lead information
- **Tone Control**: Configurable communication style
- **Goal-oriented**: Tailored to specific objectives (meetings, demos, etc.)
- **Structured Output**: Consistent JSON format for easy parsing

### Pipeline Management
- **Stages**: New → Qualified → Contacted → Meeting → Won/Lost
- **Activity Logging**: Complete audit trail of all actions
- **Progress Tracking**: Visual pipeline representation
- **Automated Rules**: Score-based progression logic

## 🔒 Security Considerations

- API keys stored in environment variables
- CORS configured for development
- Input validation on all endpoints
- SQL injection protection via SQLModel
- Error handling without sensitive data exposure

## 🚀 Deployment

### Production Considerations

1. **Environment Variables**: Use secure secret management
2. **Database**: Consider managed PostgreSQL service
3. **API Keys**: Rotate regularly and monitor usage
4. **Monitoring**: Add logging and metrics collection
5. **Scaling**: Consider load balancing for high traffic

### Docker Production Build

```bash
# Build production images
docker-compose -f docker-compose.prod.yml up --build
```

## 🐛 Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check if database is running
docker-compose ps

# View database logs
docker-compose logs db

# Reset database
docker-compose down -v
docker-compose up --build
```

#### Grok API Errors
- Verify `GROK_API_KEY` and `GROK_API_URL` in `.env`
- Check API endpoint accessibility
- Review rate limits and quotas
- Test with curl: `curl -H "Authorization: Bearer $GROK_API_KEY" $GROK_API_URL`

#### Frontend Not Loading
- Ensure backend is running on port 8000
- Check browser console for errors
- Verify proxy configuration in `vite.config.js`

#### JSON Parsing Errors
- Grok may return non-JSON responses
- System includes fallback parsing
- Improve prompts to enforce JSON output
- Review evaluation results for patterns

### Debug Mode

```bash
# Enable debug logging
export PYTHONPATH=/app
export LOG_LEVEL=DEBUG
docker-compose up
```

## 📈 Performance Optimization

### Backend
- Database connection pooling
- Response caching for repeated requests
- Async processing for long-running tasks
- Rate limiting for API calls

### Frontend
- Component lazy loading
- Image optimization
- Bundle size reduction
- CDN for static assets

## 🔮 Future Enhancements

### Short Term
- [ ] Email integration (SendGrid/SES)
- [ ] Calendar scheduling (Calendly integration)
- [ ] Advanced analytics dashboard
- [ ] Bulk lead import/export

### Medium Term
- [ ] Multi-channel outreach (LinkedIn, phone)
- [ ] A/B testing for outreach messages
- [ ] CRM integration (Salesforce, HubSpot)
- [ ] Advanced lead scoring models

### Long Term
- [ ] Machine learning model training
- [ ] Predictive analytics
- [ ] Voice and video outreach
- [ ] Multi-language support

## 📝 Development

### Local Development Setup

```bash
# Backend development
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend development
cd frontend
npm install
npm run dev
```

### Code Structure

```
sdr-grok-demo/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI application
│   │   ├── models.py        # Database models
│   │   ├── schemas.py       # Pydantic schemas
│   │   ├── database.py      # Database configuration
│   │   ├── grok_client.py   # Grok API client
│   │   ├── prompts.py       # Prompt templates
│   │   ├── evals.py         # Evaluation framework
│   │   └── routers/         # API route handlers
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main application
│   │   ├── pages/           # Page components
│   │   └── components/      # Reusable components
│   ├── Dockerfile
│   └── package.json
├── evals/
│   ├── cases.json           # Test cases
│   └── run_evals.py         # Evaluation runner
├── docker-compose.yml
└── README.md
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with FastAPI, React, and Tailwind CSS
- Powered by Grok AI
- Database powered by PostgreSQL
- Containerized with Docker

---

**Note**: This is a demo prototype. For production use, implement proper authentication, error handling, monitoring, and security measures.

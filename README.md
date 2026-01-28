# sample-ai-aem-chatbot-v1

# AEM Compliance Chatbot 🤖

A comprehensive AI-powered chatbot for Adobe Experience Manager (AEM) compliance checking, content analysis, and interactive assistance using Ollama with Gemma models.

## 🌟 Features

### ✅ Implemented Features

1. **Multi-Mode Chat Interface**
   - Chat Mode: General AI conversation
   - File Upload Mode: PDF, DOCX, TXT analysis
   - Web Search Mode: Real-time web search with summarization
   - AEM Mode: Full AEM integration and compliance checking

2. **NLU Intent Detection**
   - Automatic mode switching based on user intent
   - High-confidence intent classification
   - Entity extraction from user queries

3. **AEM Integration**
   - Page discovery and querying via QueryBuilder API
   - Hierarchical page browsing
   - Template filtering
   - Content retrieval

4. **Comprehensive Compliance Checking**
   - **Accessibility**: WCAG 2.1 compliance (alt text, ARIA, headings, contrast)
   - **SEO**: Meta tags, titles, canonical URLs, structured data
   - **Performance**: Script loading, lazy loading, resource optimization
   - **Security**: CSP, external links, form validation, HTTPS
   - **Content Quality**: Broken links, readability, semantic HTML
   - **AEM Best Practices**: Component structure, clientlibs, responsive grid

5. **Scoring & Weighting System**
   - Category-based weighted scoring
   - Check-level granular scoring
   - Overall compliance grade (A-F)
   - Severity classification (high/medium/low)

6. **Export Functionality**
   - CSV export with detailed results
   - PDF export with formatted reports
   - Summary statistics
   - Downloadable compliance reports

7. **LangChain Integration**
   - Conversation memory management
   - Multi-turn context retention
   - Conversation history tracking

8. **Vector Embeddings + Qdrant**
   - AEM content indexing
   - Semantic search capabilities
   - RAG (Retrieval-Augmented Generation)
   - Document similarity search

9. **Beautiful Modern UI**
   - Dark/Light theme toggle
   - Gradient backgrounds
   - Smooth animations
   - Responsive design
   - Professional styling

10. **Advanced Features**
    - Adjustable temperature
    - Multiple model support
    - Copy responses
    - Export chat history
    - Keyboard shortcuts
    - Health monitoring
    - Error handling with helpful messages

## 📋 Requirements

### System Requirements
- Python 3.8+
- Node.js 16+
- Docker (for Qdrant)
- Ollama
- AEM instance (for AEM features)

### Python Dependencies
```
flask==3.0.0
flask-cors==4.0.0
requests==2.31.0
python-dotenv==1.0.0
langchain==0.1.0
langchain-community==0.0.10
qdrant-client==1.7.0
sentence-transformers==2.3.1
pypdf2==3.0.1
python-docx==1.1.0
pandas==2.1.4
reportlab==4.0.7
beautifulsoup4==4.12.2
lxml==5.1.0
pydantic==2.5.3
aiohttp==3.9.1
```

### Node.js Dependencies
```json
{
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "lucide-react": "^0.294.0",
  "tailwindcss": "^3.4.0",
  "autoprefixer": "^10.4.16",
  "postcss": "^8.4.32"
}
```

## 🚀 Quick Start

### Automated Setup

```bash
chmod +x setup.sh
./setup.sh
```

### Manual Setup

#### 1. Install Ollama
```bash
# macOS/Linux
curl https://ollama.ai/install.sh | sh

# Pull Gemma model
ollama pull gemma:2b
```

#### 2. Setup Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Create directories
mkdir -p uploads services models utils
touch services/__init__.py models/__init__.py utils/__init__.py
```

#### 3. Setup Qdrant
```bash
docker-compose up -d
```

#### 4. Setup Frontend
```bash
cd frontend
npm install
```

#### 5. Start Services

Terminal 1 (Backend):
```bash
cd backend
source venv/bin/activate
python app.py
```

Terminal 2 (Frontend):
```bash
cd frontend
npm start
```

Access at: http://localhost:3000

## 🏗️ Architecture

### Backend Structure
```
backend/
├── app.py                      # Main Flask application
├── config.py                   # Configuration management
├── services/                   # Business logic services
│   ├── ollama_service.py       # Ollama LLM integration
│   ├── aem_service.py          # AEM API integration
│   ├── intent_service.py       # NLU intent detection
│   ├── compliance_service.py   # Compliance checking
│   ├── export_service.py       # CSV/PDF export
│   ├── file_service.py         # File processing
│   ├── web_search_service.py   # Web search
│   ├── langchain_service.py    # Memory management
│   └── vector_service.py       # Vector embeddings
├── models/                     # Data models
│   ├── compliance_rules.py     # Compliance rule definitions
│   └── schemas.py              # Pydantic schemas
└── utils/                      # Utility functions
```

### Frontend Structure
```
frontend/src/
├── App.jsx                     # Main application
├── components/                 # React components
│   ├── Header.jsx
│   ├── ModeSelector.jsx
│   ├── Chat.jsx
│   ├── Message.jsx
│   ├── FileUpload.jsx
│   ├── AEMPagePicker.jsx
│   ├── ComplianceReport.jsx
│   └── SettingsPanel.jsx
├── hooks/                      # Custom React hooks
│   ├── useChat.js
│   └── useAEM.js
├── services/
│   └── api.js                  # API client
└── utils/
    ├── constants.js
    └── helpers.js
```

## 🔧 Configuration

### Environment Variables (.env)

```env
# AEM Configuration
AEM_HOST=http://localhost:4502
AEM_USERNAME=admin
AEM_PASSWORD=admin

# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
DEFAULT_MODEL=gemma:2b

# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Application Settings
FLASK_PORT=5000
FLASK_DEBUG=True
UPLOAD_FOLDER=./uploads
MAX_FILE_SIZE=10485760
```

## 📡 API Endpoints

### Chat Endpoints
- `POST /api/chat` - Main chat interface with intent detection
- `POST /api/conversation/clear/:id` - Clear conversation memory
- `GET /api/conversation/list` - List all conversations

### File Endpoints
- `POST /api/file/upload` - Upload and analyze files

### AEM Endpoints
- `POST /api/aem/query` - Query AEM pages
- `GET /api/aem/page/:path` - Get page content
- `POST /api/aem/compliance/check` - Run compliance check
- `POST /api/aem/compliance/export` - Export results (CSV/PDF)

### Web Search Endpoints
- `POST /api/search/web` - Search web with summarization

### Vector/RAG Endpoints
- `POST /api/vector/add` - Add document to vector store
- `POST /api/vector/search` - Semantic search

### Utility Endpoints
- `GET /api/health` - Health check (all services)
- `GET /api/models` - List available Ollama models

## 🎯 Usage Examples

### 1. Chat Mode
```
User: "How do I create a component in AEM?"
Bot: [Provides detailed explanation about AEM component creation]
```

### 2. File Upload Mode
```
User uploads: compliance-report.pdf
User: "Summarize the key findings"
Bot: [Analyzes and summarizes the PDF content]
```

### 3. Web Search Mode
```
User: "Latest AEM updates 2024"
Bot: [Searches web and provides summary with sources]
```

### 4. AEM Mode
```
User: "Check compliance for /content/mysite/en/home"
Bot: [Automatically switches to AEM mode]
     [Shows page picker]
     [Runs compliance check]
     [Displays results with export options]
```

## 🔍 Compliance Rules

### Accessibility (25% weight)
- Image alt text
- Heading hierarchy
- ARIA labels
- Color contrast
- Keyboard navigation

### SEO (20% weight)
- Title tags
- Meta descriptions
- H1 tags
- Canonical URLs
- Image optimization

### Performance (20% weight)
- Async scripts
- Lazy loading
- Resource hints
- Compression

### Security (15% weight)
- Content Security Policy
- External link security
- Form validation
- HTTPS resources

### Content Quality (10% weight)
- Broken links
- Duplicate content
- Readability
- Language tags

### AEM Best Practices (10% weight)
- Component structure
- Client libraries
- Responsive grid
- Sling models

## 🚧 Error Handling

The application includes comprehensive error handling:

1. **Connection Errors**: Clear messages for service unavailability
2. **Validation Errors**: User-friendly input validation
3. **AEM Errors**: Specific guidance for AEM connection issues
4. **File Processing Errors**: Helpful messages for file upload issues
5. **Compliance Errors**: Graceful degradation with partial results

## 🎨 UI Features

- **Themes**: Dark and light mode with smooth transitions
- **Animations**: Fade-in messages, hover effects, smooth scrolling
- **Responsive**: Works on desktop, tablet, and mobile
- **Keyboard Shortcuts**:
  - `Enter`: Send message
  - `Shift + Enter`: New line
  - `Ctrl/Cmd + K`: Clear chat

## 📊 Future Enhancements

### Suggested Improvements

1. **Advanced Analytics**
   - Compliance trend tracking over time
   - Multi-site comparison dashboards
   - Historical compliance scoring
   - Automated scheduling for periodic checks

2. **Enhanced Reporting**
   - Executive summary generation
   - Customizable report templates
   - Email delivery of reports
   - Integration with project management tools

3. **AI Improvements**
   - Fine-tuned models for AEM-specific tasks
   - Multi-language support
   - Voice interaction
   - Image analysis for accessibility

4. **Integration Enhancements**
   - JIRA integration for issue tracking
   - Slack/Teams notifications
   - CI/CD pipeline integration
   - Git integration for version tracking

5. **Collaboration Features**
   - Multi-user support
   - Shared compliance sessions
   - Comment and annotation system
   - Role-based access control

6. **Advanced Compliance**
   - Custom rule definition UI
   - Industry-specific compliance templates (GDPR, HIPAA, etc.)
   - Automated fix suggestions
   - Before/after comparison

7. **Performance Optimization**
   - Caching layer for AEM queries
   - Parallel compliance checking
   - Progressive results display
   - Background processing queue

8. **Developer Tools**
   - AEM component code generator
   - Template scaffolding
   - GraphQL query builder
   - API testing interface

9. **Content Intelligence**
   - Content gap analysis
   - SEO optimization suggestions
   - Readability improvements
   - A/B testing recommendations

10. **Monitoring & Alerting**
    - Real-time compliance monitoring
    - Automated alerts for violations
    - SLA tracking
    - Performance metrics dashboard

## 🐛 Troubleshooting

### Ollama Connection Issues
```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Restart Ollama
ollama serve

# Pull models
ollama pull gemma:2b
```

### AEM Connection Issues
- Verify AEM is running: http://localhost:4502
- Check credentials in `.env`
- Ensure CORS is enabled on AEM

### Qdrant Issues
```bash
# Check Qdrant status
curl http://localhost:6333/collections

# Restart Qdrant
docker-compose restart qdrant
```

### Port Conflicts
- Backend (5000): Change `FLASK_PORT` in `.env`
- Frontend (3000): Set `PORT=3001` in frontend `.env`
- Qdrant (6333): Modify `docker-compose.yml`

## 📝 License

This project is provided as-is for educational and development purposes.

## 🤝 Contributing

Contributions are welcome! Please ensure:
- Code follows existing patterns
- All tests pass
- Documentation is updated
- Commit messages are clear

## 📧 Support

For issues and questions:
- Check troubleshooting section
- Review API documentation
- Check service health endpoints
- Review application logs

---

**Built with ❤️ using Ollama, Gemma, React, Flask, and modern web technologies.**
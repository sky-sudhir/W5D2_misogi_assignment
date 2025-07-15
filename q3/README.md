# Smart Code Tutor with AI Agent

A full-stack code interpreter with a web-based code editor that can execute Python & JavaScript code and provide intelligent, step-by-step explanations using RAG-retrieved documentation and real-time streaming.

## Features

- **Code Editor**: Monaco Editor with syntax highlighting for Python and JavaScript
- **Code Execution**: Sandboxed code execution using E2B SDK
- **AI Explanations**: Intelligent code analysis using LangChain + LangGraph + Groq
- **Document Upload**: RAG pipeline with ChromaDB for context-aware explanations
- **Real-time Streaming**: WebSocket-based communication for live updates
- **Modern UI**: Beautiful, responsive interface built with Next.js and Tailwind CSS

## Tech Stack

### Backend
- **FastAPI**: Async web framework with WebSocket support
- **LangChain**: Document processing and RAG pipeline
- **LangGraph**: AI agent workflow orchestration
- **Groq**: Large language model for explanations
- **ChromaDB**: Vector database for document storage
- **E2B SDK**: Sandboxed code execution
- **HuggingFace**: Embeddings model

### Frontend
- **Next.js 14**: React framework with App Router
- **Tailwind CSS**: Utility-first CSS framework
- **Monaco Editor**: VS Code editor in the browser
- **Lucide React**: Icon library
- **WebSocket**: Real-time communication

## Project Structure

```
W5D2_q3/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── config.py              # Configuration management
│   ├── requirements.txt       # Python dependencies
│   ├── models/
│   │   └── schemas.py         # Pydantic models
│   └── services/
│       ├── code_executor.py   # E2B code execution
│       ├── document_manager.py # LangChain document processing
│       ├── rag_service.py     # ChromaDB RAG pipeline
│       └── langgraph_agent.py # LangGraph AI agent
├── frontend/
│   ├── app/
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx           # Main page component
│   │   └── globals.css        # Global styles
│   ├── package.json           # Node.js dependencies
│   ├── next.config.js         # Next.js configuration
│   ├── tailwind.config.js     # Tailwind CSS configuration
│   └── tsconfig.json          # TypeScript configuration
└── README.md                  # This file
```

## Setup Instructions

### Prerequisites

1. **Python 3.8+** and **Node.js 18+**
2. **Groq API Key** - Get from [Groq Console](https://console.groq.com/)
3. **E2B API Key** - Get from [E2B Platform](https://e2b.dev/)

### Backend Setup

1. **Navigate to backend directory**:
   ```bash
   cd backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables**:
   ```bash
   # Create .env file
   echo "GROQ_API_KEY=your_groq_api_key_here" > .env
   echo "E2B_API_KEY=your_e2b_api_key_here" >> .env
   ```

5. **Run the backend**:
   ```bash
   python main.py
   ```

   The backend will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Run the development server**:
   ```bash
   npm run dev
   ```

   The frontend will be available at `http://localhost:3000`

## Usage

1. **Open the application** in your browser at `http://localhost:3000`

2. **Select a language** (Python or JavaScript) from the dropdown

3. **Write or modify code** in the Monaco Editor

4. **Upload documentation** (optional) using the "Upload Doc" button to enhance AI explanations

5. **Run the code** by clicking the "Run Code" button

6. **View results** in the console output and AI explanation panels

## API Endpoints

### REST Endpoints

- `GET /` - Health check
- `GET /health` - Service status
- `POST /upload-document` - Upload documentation for RAG

### WebSocket Endpoints

- `WS /ws/{client_id}` - Real-time communication

#### WebSocket Message Types

**Client → Server:**
- `run_code`: Execute code
- `ping`: Keep-alive

**Server → Client:**
- `execution_output`: Streaming code output
- `execution_complete`: Execution finished
- `rag_explanation`: AI explanation chunks
- `status`: Status updates
- `execution_error`: Error messages

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Groq API key for LLM | Yes |
| `E2B_API_KEY` | E2B API key for code execution | Yes |
| `DEBUG` | Enable debug mode | No |
| `LOG_LEVEL` | Logging level (INFO, DEBUG, ERROR) | No |
| `CHROMA_PERSIST_DIR` | ChromaDB storage directory | No |
| `UPLOAD_DIR` | File upload directory | No |
| `MAX_FILE_SIZE` | Maximum file upload size in bytes | No |

## Development

### Adding New Languages

1. **Update the backend** `code_executor.py`:
   - Add language to `sandbox_templates`
   - Implement execution method

2. **Update the frontend** `page.tsx`:
   - Add language option to dropdown
   - Add sample code template

### Extending AI Capabilities

1. **Modify the LangGraph workflow** in `langgraph_agent.py`:
   - Add new nodes for additional analysis
   - Implement custom prompts
   - Add new data sources

2. **Enhance RAG pipeline** in `rag_service.py`:
   - Add new document loaders
   - Implement custom embeddings
   - Add metadata filtering

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failed**
   - Ensure backend is running on port 8000
   - Check CORS settings in `main.py`

2. **Code Execution Timeout**
   - Check E2B API key and quota
   - Verify sandbox templates are available

3. **AI Explanation Not Working**
   - Verify Groq API key is valid
   - Check if documents are uploaded for RAG

4. **Monaco Editor Not Loading**
   - Ensure all frontend dependencies are installed
   - Check browser console for errors

### Logs

Backend logs are available in the console where you run `python main.py`.
Frontend logs are available in the browser developer console.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please create an issue in the repository or contact the development team. 
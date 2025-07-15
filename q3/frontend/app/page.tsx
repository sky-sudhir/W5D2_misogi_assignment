'use client'

import { useState, useEffect, useRef } from 'react'
import dynamic from 'next/dynamic'
import { Play, Upload, FileText, Loader2 } from 'lucide-react'
import { v4 as uuidv4 } from 'uuid'

// Dynamically import Monaco Editor to avoid SSR issues
const MonacoEditor = dynamic(() => import('@monaco-editor/react'), {
  ssr: false,
  loading: () => <div className="h-96 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center">Loading editor...</div>
})

// Types
interface ExecutionOutput {
  type: 'stdout' | 'stderr'
  data: string
}

interface WebSocketMessage {
  type: string
  data?: any
  message?: string
  result?: any
}

const SAMPLE_PYTHON_CODE = `# Welcome to Smart Code Tutor!
# Try running this sample code

def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Calculate first 10 Fibonacci numbers
for i in range(10):
    print(f"F({i}) = {fibonacci(i)}")

print("\\nCode execution completed!")
`

const SAMPLE_JAVASCRIPT_CODE = `// Welcome to Smart Code Tutor!
// Try running this sample JavaScript code

function fibonacci(n) {
    if (n <= 1) return n;
    return fibonacci(n - 1) + fibonacci(n - 2);
}

// Calculate first 10 Fibonacci numbers
for (let i = 0; i < 10; i++) {
    console.log(\`F(\${i}) = \${fibonacci(i)}\`);
}

console.log("\\nCode execution completed!");
`

export default function Home() {
  const [code, setCode] = useState(SAMPLE_PYTHON_CODE)
  const [language, setLanguage] = useState<'python' | 'javascript'>('python')
  const [output, setOutput] = useState<ExecutionOutput[]>([])
  const [explanation, setExplanation] = useState('')
  const [status, setStatus] = useState('Ready')
  const [isRunning, setIsRunning] = useState(false)
  const [clientId] = useState(() => uuidv4())
  
  const wsRef = useRef<WebSocket | null>(null)
  const outputRef = useRef<HTMLDivElement>(null)

  // WebSocket connection
  useEffect(() => {
    const connectWebSocket = () => {
      const ws = new WebSocket(`ws://localhost:8000/ws/${clientId}`)
      
      ws.onopen = () => {
        console.log('WebSocket connected')
        setStatus('Connected')
      }
      
      ws.onmessage = (event) => {
        const message: WebSocketMessage = JSON.parse(event.data)
        handleWebSocketMessage(message)
      }
      
      ws.onclose = () => {
        console.log('WebSocket disconnected')
        setStatus('Disconnected')
        // Reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000)
      }
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setStatus('Error')
      }
      
      wsRef.current = ws
    }

    connectWebSocket()

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [clientId])

  const handleWebSocketMessage = (message: WebSocketMessage) => {
    switch (message.type) {
      case 'execution_output':
        setOutput(prev => [...prev, message.data])
        break
      case 'execution_complete':
        setIsRunning(false)
        setStatus('Execution completed')
        break
      case 'rag_explanation':
        setExplanation(prev => prev + message.data)
        break
      case 'status':
        setStatus(message.message || 'Unknown status')
        break
      case 'execution_error':
        setIsRunning(false)
        setStatus('Error')
        setOutput(prev => [...prev, { type: 'stderr', data: message.message || 'Unknown error' }])
        break
      case 'pong':
        // Handle ping/pong
        break
      default:
        console.log('Unknown message type:', message.type)
    }
  }

  // Auto-scroll output
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight
    }
  }, [output])

  const handleRunCode = () => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      setStatus('WebSocket not connected')
      return
    }

    setIsRunning(true)
    setOutput([])
    setExplanation('')
    setStatus('Running code...')

    const message = {
      type: 'run_code',
      payload: {
        code,
        language
      }
    }

    wsRef.current.send(JSON.stringify(message))
  }

  const handleLanguageChange = (newLanguage: 'python' | 'javascript') => {
    setLanguage(newLanguage)
    setCode(newLanguage === 'python' ? SAMPLE_PYTHON_CODE : SAMPLE_JAVASCRIPT_CODE)
    setOutput([])
    setExplanation('')
  }

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('http://localhost:8000/upload-document', {
        method: 'POST',
        body: formData
      })

      if (response.ok) {
        const result = await response.json()
        setStatus(`Document uploaded: ${result.chunks_created} chunks created`)
      } else {
        setStatus('Failed to upload document')
      }
    } catch (error) {
      console.error('Upload error:', error)
      setStatus('Upload error')
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-full">
      {/* Left Panel - Code Editor */}
      <div className="space-y-4">
        <div className="card p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-4">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Code Editor
              </h2>
              <select
                value={language}
                onChange={(e) => handleLanguageChange(e.target.value as 'python' | 'javascript')}
                className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
              >
                <option value="python">Python</option>
                <option value="javascript">JavaScript</option>
              </select>
            </div>
            <div className="flex items-center space-x-2">
              <label className="btn-secondary cursor-pointer">
                <Upload className="w-4 h-4 mr-2" />
                Upload Doc
                <input
                  type="file"
                  accept=".txt,.md,.pdf,.docx,.html"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </label>
              <button
                onClick={handleRunCode}
                disabled={isRunning}
                className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isRunning ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Play className="w-4 h-4 mr-2" />
                )}
                Run Code
              </button>
            </div>
          </div>

          <div className="h-96 border border-gray-300 dark:border-gray-600 rounded-lg overflow-hidden">
            <MonacoEditor
              height="100%"
              language={language}
              theme="vs-dark"
              value={code}
              onChange={(value) => setCode(value || '')}
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                lineNumbers: 'on',
                automaticLayout: true,
                wordWrap: 'on',
                scrollBeyondLastLine: false,
              }}
            />
          </div>
        </div>

        {/* Console Output */}
        <div className="card p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              Console Output
            </h3>
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Status: {status}
            </span>
          </div>
          <div
            ref={outputRef}
            className="console-output h-48 overflow-y-auto"
          >
            {output.length === 0 ? (
              <div className="text-gray-500">No output yet. Run some code to see results!</div>
            ) : (
              output.map((item, index) => (
                <div
                  key={index}
                  className={`${
                    item.type === 'stderr' ? 'text-red-400' : 'text-green-400'
                  }`}
                >
                  {item.data}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Right Panel - AI Explanation */}
      <div className="space-y-4">
        <div className="card p-4">
          <div className="flex items-center mb-4">
            <FileText className="w-5 h-5 mr-2 text-blue-600" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
              AI Explanation
            </h3>
          </div>
          <div className="explanation-panel h-[600px] overflow-y-auto">
            {explanation ? (
              <div className="prose dark:prose-invert max-w-none">
                <pre className="whitespace-pre-wrap text-sm leading-relaxed">
                  {explanation}
                </pre>
              </div>
            ) : (
              <div className="text-gray-500 text-center py-8">
                <FileText className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                <p>Run some code to get an AI explanation!</p>
                <p className="text-sm mt-2">
                  The AI will analyze your code, explain what it does, and provide helpful insights.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
} 
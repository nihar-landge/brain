import { useState, useRef, useEffect } from 'react'
import { Send, Sparkles, Loader2, Trash2 } from 'lucide-react'
import { sendChatMessage, getChatHistory, clearChatHistory } from '../api'

const quickPrompts = [
    'How was my week?',
    'Show mood trends',
    'What patterns do you see?',
    'Give me advice',
]

export default function ChatPage() {
    const [messages, setMessages] = useState([])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [initialLoad, setInitialLoad] = useState(true)
    const messagesEnd = useRef(null)

    useEffect(() => {
        const loadHistory = async () => {
            try {
                const res = await getChatHistory()
                if (res.data?.length) {
                    setMessages(res.data.map(m => ({
                        role: m.role,
                        content: m.message,
                        time: new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                    })))
                } else {
                    setMessages([{
                        role: 'assistant',
                        content: 'Hello! I can help you reflect on patterns, track moods, and provide insights based on your journal entries. What would you like to explore?',
                        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                    }])
                }
            } catch {
                setMessages([{
                    role: 'assistant',
                    content: 'Ready to assist. Ask me about your journal, mood, habits, or goals.',
                    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                }])
            } finally { setInitialLoad(false) }
        }
        loadHistory()
    }, [])

    useEffect(() => {
        messagesEnd.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    const handleSend = async (text) => {
        const msg = text || input.trim()
        if (!msg || loading) return
        const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        setMessages(prev => [...prev, { role: 'user', content: msg, time }])
        setInput('')
        setLoading(true)
        try {
            const res = await sendChatMessage(msg)
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: res.data.response,
                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            }])
        } catch {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: 'Something went wrong. Please try again.',
                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            }])
        } finally { setLoading(false) }
    }

    const handleClear = async () => {
        if (!confirm('Clear all chat history?')) return
        try {
            await clearChatHistory()
            setMessages([{
                role: 'assistant',
                content: 'Chat cleared. How can I help you?',
                time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            }])
        } catch { }
    }

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault()
            handleSend()
        }
    }

    return (
        <div className="flex flex-col h-[calc(100dvh-10rem)] sm:h-[calc(100dvh-7rem)] max-w-3xl mx-auto">
            {/* Header */}
            <div className="flex justify-between items-center mb-4">
                <div>
                    <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Chat with AI</h1>
                    <p className="text-sm text-gray-500 mt-1 hidden sm:block">AI assistant with memory of your journal</p>
                </div>
                <button onClick={handleClear} className="btn-ghost flex items-center gap-2 text-sm text-gray-500">
                    <Trash2 className="w-4 h-4" />
                    <span className="hidden sm:inline">Clear Chat</span>
                </button>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto space-y-4 pb-4">
                {initialLoad ? (
                    <div className="flex items-center justify-center h-full">
                        <Loader2 className="w-5 h-5 text-gray-400 animate-spin" />
                    </div>
                ) : messages.map((msg, i) => (
                    <div key={i}>
                        {msg.role === 'user' ? (
                            /* User Message */
                            <div className="flex justify-end mb-4">
                                <div className="max-w-[70%] bg-black text-white rounded-lg rounded-br-sm p-4">
                                    <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                                    <span className="text-xs text-gray-300 mt-2 block">{msg.time}</span>
                                </div>
                            </div>
                        ) : (
                            /* AI Message */
                            <div className="flex justify-start mb-4">
                                <div className="max-w-[80%]">
                                    <div className="flex items-start gap-3">
                                        <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                                            <Sparkles className="w-4 h-4 text-white" />
                                        </div>
                                        <div className="bg-gray-100 rounded-lg rounded-bl-sm p-4 flex-1">
                                            <p className="text-sm text-gray-900 whitespace-pre-wrap">{msg.content}</p>
                                            <span className="text-xs text-gray-400 mt-2 block">{msg.time}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                ))}

                {/* Typing indicator */}
                {loading && (
                    <div className="flex justify-start mb-4">
                        <div className="flex items-start gap-3">
                            <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center flex-shrink-0">
                                <Sparkles className="w-4 h-4 text-white" />
                            </div>
                            <div className="bg-gray-100 rounded-lg rounded-bl-sm px-4 py-3 flex gap-1.5">
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEnd} />
            </div>

            {/* Quick Prompts */}
            <div className="flex flex-wrap gap-2 mb-3">
                {quickPrompts.map((prompt, i) => (
                    <button
                        key={i}
                        onClick={() => handleSend(prompt)}
                        className="px-3 py-2 text-sm border border-gray-200 rounded-full hover:bg-gray-50 text-gray-600 transition-colors"
                    >
                        {prompt}
                    </button>
                ))}
            </div>

            {/* Input Area */}
            <div className="flex gap-2 border-t border-gray-200 pt-4">
                <textarea
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={handleKeyPress}
                    placeholder="Type your message..."
                    className="input-field flex-1 resize-none"
                    rows={1}
                    disabled={loading}
                />
                <button
                    onClick={() => handleSend()}
                    disabled={loading || !input.trim()}
                    className="btn-primary px-4 disabled:opacity-30 disabled:cursor-not-allowed"
                >
                    {loading ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                        <Send className="w-4 h-4" />
                    )}
                </button>
            </div>
        </div>
    )
}

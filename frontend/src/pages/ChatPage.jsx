import { useState, useRef, useEffect } from 'react'
import { Send, Sparkles, Loader2, Trash2, Users, ChevronDown, Heart, TrendingUp, BarChart3 } from 'lucide-react'
import { sendChatMessage, getChatHistory, clearChatHistory, singleAgentChat, multiAgentChat } from '../api'

const quickPrompts = [
    'How was my week?',
    'Show mood trends',
    'What patterns do you see?',
    'Give me advice',
]

const agentMeta = {
    standard: { icon: Sparkles, label: 'Standard', color: 'bg-accent' },
    therapist: { icon: Heart, label: 'Therapist', color: 'bg-rose-500' },
    coach: { icon: TrendingUp, label: 'Coach', color: 'bg-emerald-500' },
    analyst: { icon: BarChart3, label: 'Analyst', color: 'bg-blue-500' },
    multi: { icon: Users, label: 'Multi-Agent', color: 'bg-purple-500' },
}

function renderInlineText(text) {
    const parts = text.split(/(\*\*[^*]+\*\*|\*[^*\n]+\*|`[^`]+`)/g).filter(Boolean)
    return parts.map((part, idx) => {
        if (part.startsWith('**') && part.endsWith('**')) {
            return <strong key={idx} className="font-semibold text-gray-900">{part.slice(2, -2)}</strong>
        }
        if (part.startsWith('*') && part.endsWith('*')) {
            return <em key={idx} className="italic text-gray-800">{part.slice(1, -1)}</em>
        }
        if (part.startsWith('`') && part.endsWith('`')) {
            return <code key={idx} className="px-1.5 py-0.5 rounded bg-gray-200 text-gray-900 text-[0.85em]">{part.slice(1, -1)}</code>
        }
        return <span key={idx}>{part}</span>
    })
}

function renderAiContent(content) {
    const lines = String(content || '').split('\n').map((line) => line.trimEnd())
    const blocks = []
    let listItems = []

    const flushList = () => {
        if (listItems.length) {
            blocks.push({ type: 'list', items: listItems })
            listItems = []
        }
    }

    for (const rawLine of lines) {
        const line = rawLine.trim()
        if (!line) {
            flushList()
            continue
        }

        if (/^[-*•]\s+/.test(line)) {
            listItems.push(line.replace(/^[-*•]\s+/, ''))
            continue
        }

        flushList()
        if (/^#{1,3}\s+/.test(line)) {
            blocks.push({ type: 'heading', text: line.replace(/^#{1,3}\s+/, '') })
        } else {
            blocks.push({ type: 'p', text: line })
        }
    }
    flushList()

    return blocks.map((block, idx) => {
        if (block.type === 'heading') {
            return <p key={idx} className="text-sm font-semibold text-gray-900 mt-1">{renderInlineText(block.text)}</p>
        }
        if (block.type === 'list') {
            return (
                <ul key={idx} className="list-disc pl-5 space-y-1 text-sm text-gray-800">
                    {block.items.map((item, i) => (
                        <li key={i}>{renderInlineText(item)}</li>
                    ))}
                </ul>
            )
        }
        return <p key={idx} className="text-sm text-gray-800 leading-relaxed">{renderInlineText(block.text)}</p>
    })
}

export default function ChatPage() {
    const [messages, setMessages] = useState([])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [initialLoad, setInitialLoad] = useState(true)
    const [mode, setMode] = useState('standard') // standard | therapist | coach | analyst | multi
    const [showModeMenu, setShowModeMenu] = useState(false)
    const [expandedPerspectives, setExpandedPerspectives] = useState({})
    const messagesEnd = useRef(null)
    const modeMenuRef = useRef(null)

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

    // Close mode menu on outside click
    useEffect(() => {
        const handleClick = (e) => {
            if (modeMenuRef.current && !modeMenuRef.current.contains(e.target)) {
                setShowModeMenu(false)
            }
        }
        if (showModeMenu) document.addEventListener('mousedown', handleClick)
        return () => document.removeEventListener('mousedown', handleClick)
    }, [showModeMenu])

    const handleSend = async (text) => {
        const msg = text || input.trim()
        if (!msg || loading) return
        const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        setMessages(prev => [...prev, { role: 'user', content: msg, time }])
        setInput('')
        setLoading(true)
        try {
            let assistantMsg
            if (mode === 'standard') {
                const res = await sendChatMessage(msg)
                assistantMsg = {
                    role: 'assistant',
                    content: res.data.response,
                    agent: 'standard',
                    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                }
            } else if (mode === 'multi') {
                const res = await multiAgentChat(msg)
                const data = res.data
                assistantMsg = {
                    role: 'assistant',
                    content: data.synthesis,
                    agent: 'multi',
                    perspectives: data.agents || [],
                    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                }
            } else {
                // Single agent mode
                const res = await singleAgentChat(msg, mode)
                assistantMsg = {
                    role: 'assistant',
                    content: res.data.response,
                    agent: mode,
                    time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                }
            }
            setMessages(prev => [...prev, assistantMsg])
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

    const togglePerspectives = (msgIndex) => {
        setExpandedPerspectives(prev => ({ ...prev, [msgIndex]: !prev[msgIndex] }))
    }

    const currentMode = agentMeta[mode]
    const ModeIcon = currentMode.icon
    const showQuickPrompts = !loading && !messages.some((m) => m.role === 'user')

    return (
        <div className="flex flex-col h-[calc(100dvh-10rem)] sm:h-[calc(100dvh-7rem)] max-w-4xl mx-auto rounded-2xl border border-gray-200 bg-gradient-to-b from-white to-gray-100/50 p-3 sm:p-5 shadow-sm">
            {/* Header */}
            <div className="flex justify-between items-center mb-4">
                <div className="flex items-center gap-3">
                    <div>
                        <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Chat with AI</h1>
                        <p className="text-sm text-gray-500 mt-1 hidden sm:block">AI assistant with memory of your journal</p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    {/* Agent Mode Selector */}
                    <div className="relative" ref={modeMenuRef}>
                        <button
                            onClick={() => setShowModeMenu(!showModeMenu)}
                            className="flex items-center gap-2 px-3 py-2 text-sm border border-gray-200 rounded-lg bg-white hover:bg-gray-100 transition-colors"
                        >
                            <ModeIcon className="w-4 h-4" />
                            <span className="hidden sm:inline">{currentMode.label}</span>
                            <ChevronDown className="w-3 h-3" />
                        </button>
                        {showModeMenu && (
                            <div className="absolute right-0 top-full mt-1 w-52 bg-white border border-gray-200 rounded-lg shadow-lg z-30 py-1">
                                {Object.entries(agentMeta).map(([key, meta]) => {
                                    const Icon = meta.icon
                                    return (
                                        <button
                                            key={key}
                                            onClick={() => { setMode(key); setShowModeMenu(false) }}
                                            className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm text-left hover:bg-gray-100 transition-colors ${mode === key ? 'bg-gray-100 font-medium' : ''}`}
                                        >
                                            <div className={`w-6 h-6 ${meta.color} rounded-full flex items-center justify-center`}>
                                                <Icon className="w-3 h-3 text-white" />
                                            </div>
                                            <div>
                                                <div className="text-gray-900">{meta.label}</div>
                                                <div className="text-[10px] text-gray-500">
                                                    {key === 'standard' && 'General AI assistant'}
                                                    {key === 'therapist' && 'CBT/DBT therapeutic support'}
                                                    {key === 'coach' && 'Accountability & motivation'}
                                                    {key === 'analyst' && 'Data-driven insights'}
                                                    {key === 'multi' && 'All agents combined'}
                                                </div>
                                            </div>
                                        </button>
                                    )
                                })}
                            </div>
                        )}
                    </div>
                    <button onClick={handleClear} className="btn-ghost flex items-center gap-2 text-sm text-gray-500">
                        <Trash2 className="w-4 h-4" />
                        <span className="hidden sm:inline">Clear</span>
                    </button>
                </div>
            </div>

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto space-y-4 pb-4 pr-1">
                {initialLoad ? (
                    <div className="flex items-center justify-center h-full">
                        <Loader2 className="w-5 h-5 text-gray-500 animate-spin" />
                    </div>
                ) : messages.map((msg, i) => (
                    <div key={i}>
                        {msg.role === 'user' ? (
                            /* User Message */
                            <div className="flex justify-end mb-4">
                                <div className="max-w-[84%] sm:max-w-[74%] bg-black text-white rounded-2xl rounded-br-sm px-4 py-3 shadow-sm">
                                    <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                                    <span className="text-xs text-gray-300 mt-2 block">{msg.time}</span>
                                </div>
                            </div>
                        ) : (
                            /* AI Message */
                            <div className="flex justify-start mb-4">
                                <div className="max-w-[80%]">
                                    <div className="flex items-start gap-3">
                                        {(() => {
                                            const agent = msg.agent || 'standard'
                                            const meta = agentMeta[agent] || agentMeta.standard
                                            const AgentIcon = meta.icon
                                            return (
                                                <div className={`w-8 h-8 ${meta.color} rounded-full flex items-center justify-center flex-shrink-0 mt-0.5`}>
                                                    <AgentIcon className="w-4 h-4 text-white" />
                                                </div>
                                            )
                                        })()}
                                        <div className="flex-1">
                                            {/* Agent label for non-standard messages */}
                                            {msg.agent && msg.agent !== 'standard' && (
                                                <span className="text-xs font-medium text-gray-500 mb-1 block">
                                                    {agentMeta[msg.agent]?.label || 'AI'}
                                                    {msg.agent === 'multi' && ' (Synthesized)'}
                                                </span>
                                            )}
                                            <div className="bg-white/90 border border-gray-200 rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm backdrop-blur-sm space-y-2">
                                                {renderAiContent(msg.content)}
                                                <span className="text-xs text-gray-500 mt-2 block">{msg.time}</span>
                                            </div>

                                            {/* Multi-agent perspectives */}
                                            {msg.perspectives && msg.perspectives.length > 0 && (
                                                <div className="mt-2">
                                                    <button
                                                        onClick={() => togglePerspectives(i)}
                                                        className="text-xs text-accent hover:underline flex items-center gap-1"
                                                    >
                                                        <Users className="w-3 h-3" />
                                                        {expandedPerspectives[i] ? 'Hide' : 'Show'} individual perspectives ({msg.perspectives.length})
                                                    </button>
                                                    {expandedPerspectives[i] && (
                                                        <div className="mt-2 space-y-2">
                                                            {msg.perspectives.map((p, pi) => {
                                                                const pMeta = agentMeta[p.agent] || agentMeta.standard
                                                                const PIcon = pMeta.icon
                                                                return (
                                                                    <div key={pi} className="border border-gray-200 rounded-lg p-3 bg-white">
                                                                        <div className="flex items-center gap-2 mb-2">
                                                                            <div className={`w-5 h-5 ${pMeta.color} rounded-full flex items-center justify-center`}>
                                                                                <PIcon className="w-3 h-3 text-white" />
                                                                            </div>
                                                                            <span className="text-xs font-medium text-gray-900">{pMeta.label}</span>
                                                                        </div>
                                                                        <div className="text-xs text-gray-700 space-y-1">{renderAiContent(p.response)}</div>
                                                                    </div>
                                                                )
                                                            })}
                                                        </div>
                                                    )}
                                                </div>
                                            )}
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
                            <div className={`w-8 h-8 ${currentMode.color} rounded-full flex items-center justify-center flex-shrink-0`}>
                                <ModeIcon className="w-4 h-4 text-white" />
                            </div>
                            <div className="bg-white border border-gray-200 rounded-2xl rounded-bl-sm px-4 py-3 flex gap-1.5 shadow-sm">
                                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEnd} />
            </div>

            {/* Quick Prompts */}
            {showQuickPrompts && (
                <div className="flex flex-wrap gap-2 mb-3">
                    {quickPrompts.map((prompt, i) => (
                        <button
                            key={i}
                            onClick={() => handleSend(prompt)}
                            disabled={loading}
                            className="px-3 py-2 text-sm border border-gray-200 bg-white rounded-full hover:bg-gray-100 text-gray-600 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                        >
                            {prompt}
                        </button>
                    ))}
                </div>
            )}

            {/* Input Area */}
            <div className="flex gap-2 border border-gray-200 bg-white rounded-2xl p-2 sm:p-3 shadow-sm">
                <textarea
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={handleKeyPress}
                    placeholder={mode === 'multi' ? 'Ask all agents...' : mode === 'standard' ? 'Type your message...' : `Ask the ${currentMode.label}...`}
                    className="input-field flex-1 resize-none !border-0 !shadow-none !bg-transparent"
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

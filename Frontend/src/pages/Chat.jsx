// ─────────────────────────────────────────────────────────────────────────────
// Chat.jsx — AI Coach chat page (connected to Groq backend)
// ─────────────────────────────────────────────────────────────────────────────
import { useState, useRef, useEffect } from 'react'
import { apiFetch } from '../api/clients'
import { suggestedChips } from '../data/mockData'

function now() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export default function Chat() {
  const [messages, setMessages] = useState([
    {
      role: 'ai',
      text: "Hey! I'm your FITT AI Coach. Ask me anything about training, recovery, or nutrition.",
      time: 'Just now',
    },
  ])
  const [input, setInput]   = useState('')
  const [typing, setTyping] = useState(false)
  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, typing])

  const sendMessage = async (text = input.trim()) => {
    if (!text || typing) return

    // Add user message
    const userMsg = { role: 'user', text, time: now() }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setTyping(true)

    // Build history for the API — only include user/assistant roles
    // (current messages + the new one we just added)
    const history = [...messages, userMsg]
      .map(m => ({
        role: m.role === 'ai' ? 'assistant' : 'user',
        content: m.text,
      }))

    try {
      const data = await apiFetch('/groq/chat', {
        method: 'POST',
        body: JSON.stringify({ messages: history }),
      })
      setMessages(prev => [...prev, { role: 'ai', text: data.response, time: now() }])
    } catch (e) {
      setMessages(prev => [...prev, {
        role: 'ai',
        text: "Sorry, I couldn't reach the server. Please try again.",
        time: now(),
      }])
    } finally {
      setTyping(false)
    }
  }

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }
  }

  return (
    <div className="page fade-in">

      <div className="page-header">
        <div>
          <h1>AI Coach</h1>
          <div style={{ fontSize: 12, color: typing ? 'var(--muted)' : 'var(--green)', marginTop: 2 }}>
            {typing ? 'Thinking...' : 'Online'}
          </div>
        </div>
      </div>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', paddingBottom: 80 }}>

        {/* Suggested chips */}
        <div className="chips" style={{ paddingTop: 12 }}>
          {suggestedChips.map(chip => (
            <div key={chip} className="chip" onClick={() => sendMessage(chip)}>{chip}</div>
          ))}
        </div>

        {/* Message thread */}
        <div className="chat-messages">
          {messages.map((msg, i) => (
            <div key={i} className={`msg ${msg.role} fade-in`}>
              <div className="msg-bubble">{msg.text}</div>
              <div className="msg-time">{msg.time}</div>
            </div>
          ))}

          {typing && (
            <div className="msg ai fade-in">
              <div className="msg-bubble" style={{ padding: '12px 14px' }}>
                <div className="typing-indicator">
                  <div className="dot" /><div className="dot" /><div className="dot" />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input bar */}
        <div className="chat-input-bar">
          <textarea
            className="chat-input"
            placeholder="Ask your AI coach..."
            rows={1}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
          />
          <button className="chat-send" onClick={() => sendMessage()} disabled={typing}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13"/>
              <polygon points="22 2 15 22 11 13 2 9 22 2"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  )
}
// ─────────────────────────────────────────────────────────────────────────────
// Chat.jsx — AI Coach chat page
//
// A conversational interface where users can ask questions about their training,
// recovery, and nutrition. Currently uses a keyword-matching mock AI.
//
// Sections:
//   - Suggested chips: quick-tap preset questions at the top
//   - Message list: scrollable conversation thread (user + AI bubbles)
//   - Typing indicator: animated 3-dot bounce while AI is "thinking"
//   - Input bar: textarea + send button
//
// State:
//   messages  — array of { role: 'user'|'ai', text: string, time: string }
//               New messages are appended to the end (chronological order)
//   input     — current text in the textarea (controlled input)
//   typing    — whether the AI typing indicator is visible
//
// messagesEndRef — a zero-height div at the bottom of the message list.
//                  useEffect scrolls it into view whenever messages or typing changes.
//
// TODO: When backend is connected:
//   - Replace getAIResponse() with a real POST to the Groq API (via backend proxy)
//   - Stream the response token-by-token for a better UX
//   - Include workout/nutrition/recovery context in the system prompt
// ─────────────────────────────────────────────────────────────────────────────

import { useState, useRef, useEffect } from 'react'
import { aiResponses, defaultAIResponse, suggestedChips } from '../data/mockData'

// ── getAIResponse — mock keyword-based AI response lookup ────────────────────
// Converts the user's message to lowercase, then checks each key in aiResponses
// (from mockData.js) to see if it appears anywhere in the text.
// Returns the first match found, or defaultAIResponse if nothing matches.
//
// TODO: Replace with a real API call to Groq (or similar LLM provider) that
//       receives the user's message + structured context about their workouts,
//       nutrition, and recovery data for a personalized response.
function getAIResponse(text) {
  const lower = text.toLowerCase()
  for (const [key, response] of Object.entries(aiResponses)) {
    if (lower.includes(key)) return response
  }
  return defaultAIResponse
}

// Returns the current local time formatted as "HH:MM AM/PM" (e.g. "2:34 PM")
// Used to timestamp each message when it's sent.
function now() {
  return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export default function Chat() {
  // Messages array — starts with the AI's greeting message.
  // Each object has: role ('user' | 'ai'), text (content), time (display timestamp)
  const [messages, setMessages] = useState([
    {
      role: 'ai',
      text: "Hey Dylan! I've reviewed your recent workout data, sleep logs, and nutrition. Ask me anything about your training, recovery, or nutrition — I'll give you data-backed answers.",
      time: 'Just now',
    },
  ])

  // Controlled textarea value — cleared after each send
  const [input, setInput]   = useState('')

  // Controls visibility of the typing indicator (3-dot bounce animation)
  const [typing, setTyping] = useState(false)

  // Ref to the invisible div at the bottom of the message list.
  // scrollIntoView() on this div keeps the latest message always visible.
  const messagesEndRef = useRef(null)

  // Auto-scroll to the bottom whenever a new message appears OR typing starts/stops.
  // 'smooth' behavior animates the scroll instead of snapping.
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, typing])

  // ── sendMessage — adds user message, triggers mock AI response ──────────────
  // Accepts an optional text argument (used by chip taps) or falls back to
  // the current textarea value. Shows typing indicator for a random 1.2–1.8s
  // delay before appending the AI response — simulates natural thinking time.
  const sendMessage = (text = input.trim()) => {
    if (!text) return

    // Append the user's message to the conversation
    setMessages(prev => [...prev, { role: 'user', text, time: now() }])
    setInput('')    // Clear the input field
    setTyping(true) // Show the "..." typing indicator

    // After a randomized delay, hide the indicator and append the AI response.
    // TODO: Replace this setTimeout block with an actual Groq API call.
    setTimeout(() => {
      setTyping(false)
      setMessages(prev => [...prev, { role: 'ai', text: getAIResponse(text), time: now() }])
    }, 1200 + Math.random() * 600) // Random delay between 1200ms and 1800ms
  }

  // Sends on Enter key press (without Shift, which would add a newline instead)
  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }
  }

  return (
    <div className="page fade-in">

      {/* ── Page header ── */}
      <div className="page-header">
        <div>
          <h1>AI Coach</h1>
          {/* Green "Online" status — TODO: show "Thinking..." while awaiting real API */}
          <div style={{ fontSize: 12, color: 'var(--green)', marginTop: 2 }}>Online</div>
        </div>
      </div>

      {/* Flex column fills remaining height, with padding for the bottom nav bar */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', paddingBottom: 80 }}>

        {/* ── Suggested chips ── */}
        {/* Quick-tap preset questions from suggestedChips in mockData.js.
            Clicking a chip calls sendMessage() directly, bypassing the textarea. */}
        <div className="chips" style={{ paddingTop: 12 }}>
          {suggestedChips.map(chip => (
            <div key={chip} className="chip" onClick={() => sendMessage(chip)}>{chip}</div>
          ))}
        </div>

        {/* ── Message thread ── */}
        {/* Scrollable area containing all chat bubbles.
            CSS class "msg user" aligns right; "msg ai" aligns left. */}
        <div className="chat-messages">
          {messages.map((msg, i) => (
            <div key={i} className={`msg ${msg.role} fade-in`}>
              <div className="msg-bubble">{msg.text}</div>
              <div className="msg-time">{msg.time}</div>
            </div>
          ))}

          {/* ── Typing indicator ── */}
          {/* Three dots animate with a staggered bounce (defined in index.css).
              Visible only while typing=true (between user send and AI response). */}
          {typing && (
            <div className="msg ai fade-in">
              <div className="msg-bubble" style={{ padding: '12px 14px' }}>
                <div className="typing-indicator">
                  <div className="dot" /><div className="dot" /><div className="dot" />
                </div>
              </div>
            </div>
          )}

          {/* Invisible anchor div — scrolled into view by the useEffect above */}
          <div ref={messagesEndRef} />
        </div>

        {/* ── Chat input bar ── */}
        {/* Textarea expands with content (rows=1 default, CSS handles growth).
            Send button submits the current input via sendMessage(). */}
        <div className="chat-input-bar">
          <textarea
            className="chat-input"
            placeholder="Ask your AI coach..."
            rows={1}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
          />
          {/* Paper-plane send icon */}
          <button className="chat-send" onClick={() => sendMessage()}>
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

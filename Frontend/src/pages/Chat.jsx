// ─────────────────────────────────────────────────────────────────────────────
// Chat.jsx — AI Coach chat page with chat history (connected to Groq backend)
// ─────────────────────────────────────────────────────────────────────────────
import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { apiFetch } from "../api/clients";
import { API_BASE } from "../config";
import { suggestedChips } from "../data/mockData";

function now() {
  return new Date().toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function Chat() {
  // Chat list and management
  const [chats, setChats] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [showChatList, setShowChatList] = useState(false);

  // Messages for current chat
  const [messages, setMessages] = useState([
    {
      role: "ai",
      text: "Hey! I'm your FITT AI Coach. Ask me anything about training, recovery, or nutrition.",
      time: "Just now",
    },
  ]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const messagesEndRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const [recording, setRecording] = useState(false);

  // Load chats on mount
  useEffect(() => {
    loadChats();
  }, []);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing]);

  const loadChats = async () => {
    try {
      const data = await apiFetch("/groq/chats", { method: "GET" });
      setChats(data.chats || []);
      
      // If no chats exist, create one
      if (!data.chats || data.chats.length === 0) {
        await createNewChat();
      } else {
        // Load the most recent chat
        setCurrentChatId(data.chats[0].id);
        await loadChatMessages(data.chats[0].id);
      }
    } catch (e) {
      console.error("Error loading chats:", e);
    }
  };

  const loadChatMessages = async (chatId) => {
    try {
      const data = await apiFetch(`/groq/chats/${chatId}`, { method: "GET" });
      const dbMessages = data.messages || [];
      
      if (dbMessages.length === 0) {
        // Initialize with greeting
        setMessages([
          {
            role: "ai",
            text: "Hey! I'm your FITT AI Coach. Ask me anything about training, recovery, or nutrition.",
            time: "Just now",
          },
        ]);
      } else {
        // Convert DB messages to display format
        setMessages(
          dbMessages.map((m) => ({
            role: m.role === "assistant" ? "ai" : "user",
            text: m.content,
            time: new Date(m.created_at).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            }),
          }))
        );
      }
    } catch (e) {
      console.error("Error loading chat messages:", e);
    }
  };

  const createNewChat = async () => {
    try {
      const data = await apiFetch("/groq/chats", { method: "POST" });
      const newChat = data;
      
      // Reload chats
      const chatsData = await apiFetch("/groq/chats", { method: "GET" });
      setChats(chatsData.chats || []);
      
      // Switch to new chat
      setCurrentChatId(newChat.id);
      setMessages([
        {
          role: "ai",
          text: "Hey! I'm your FITT AI Coach. Ask me anything about training, recovery, or nutrition.",
          time: "Just now",
        },
      ]);
      setShowChatList(false);
    } catch (e) {
      console.error("Error creating chat:", e);
    }
  };

  const switchChat = async (chatId) => {
    setCurrentChatId(chatId);
    await loadChatMessages(chatId);
    setShowChatList(false);
  };

  const deleteChat = async (chatIdToDelete, e) => {
    e.stopPropagation();
    try {
      await apiFetch(`/groq/chats/${chatIdToDelete}`, { method: "DELETE" });
      
      // Remove from list
      const updatedChats = chats.filter((c) => c.id !== chatIdToDelete);
      setChats(updatedChats);
      
      // If we deleted current chat, switch to first remaining or create new
      if (currentChatId === chatIdToDelete) {
        if (updatedChats.length > 0) {
          await switchChat(updatedChats[0].id);
        } else {
          await createNewChat();
        }
      }
    } catch (e) {
      console.error("Error deleting chat:", e);
    }
  };

  const sendMessage = async (text = input.trim()) => {
    if (!text || typing || !currentChatId) return;

    // Add user message to UI
    const userMsg = { role: "user", text, time: now() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setTyping(true);

    // Build history from current messages + new message
    const history = [...messages, userMsg].map((m) => ({
      role: m.role === "ai" ? "assistant" : "user",
      content: m.text,
    }));

    try {
      const data = await apiFetch(`/groq/chats/${currentChatId}/messages`, {
        method: "POST",
        body: JSON.stringify({ messages: history }),
      });
      setMessages((prev) => [
        ...prev,
        { role: "ai", text: data.response, time: now() },
      ]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        {
          role: "ai",
          text: "Sorry, I couldn't reach the server. Please try again.",
          time: now(),
        },
      ]);
    } finally {
      setTyping(false);
    }
  };

  const handleKey = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleRecord = async () => {
    if (!recording) {
      setRecording(true);

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);

      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        audioChunksRef.current.push(e.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, {
          type: "audio/webm",
        });

        const formData = new FormData();
        formData.append("file", audioBlob, "recording.webm");

        try {
          const res = await fetch(`${API_BASE}/groq/transcribe`, {
            method: "POST",
            body: formData,
          });

          const data = await res.json();

          // 👇 fills input box
          setInput(data.transcription);

          // optional:
          // sendMessage(data.transcription)
        } catch (err) {
          console.error(err);
        }
      };

      mediaRecorder.start();
    } else {
      setRecording(false);
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current = null;
    }
  };

  return (
    <div className="page fade-in">
      <div className="page-header">
        <div style={{ flex: 1 }}>
          <h1>AI Coach</h1>
          <div
            style={{
              fontSize: 12,
              color: typing ? "var(--muted)" : "var(--green)",
              marginTop: 2,
            }}
          >
            {typing ? "Thinking..." : "Online"}
          </div>
        </div>
        <button
          onClick={() => setShowChatList(!showChatList)}
          style={{
            background: "var(--card)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            padding: "8px 12px",
            cursor: "pointer",
            color: "var(--text)",
            fontSize: 12,
            fontWeight: 600,
          }}
        >
          ☰
        </button>
      </div>

      {/* Chat list sidebar */}
      {showChatList && (
        <div
          style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: "rgba(0,0,0,0.5)",
            zIndex: 300,
            display: "flex",
            alignItems: "flex-start",
            paddingTop: 60,
          }}
          onClick={() => setShowChatList(false)}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: "var(--surface)",
              width: "100%",
              maxWidth: 320,
              maxHeight: "calc(100vh - 100px)",
              overflowY: "auto",
              borderRight: "1px solid var(--border)",
            }}
          >
            <div style={{ padding: 16 }}>
              <button
                onClick={createNewChat}
                style={{
                  width: "100%",
                  padding: "10px 14px",
                  background: "var(--accent)",
                  color: "#fff",
                  border: "none",
                  borderRadius: 8,
                  cursor: "pointer",
                  fontWeight: 600,
                  marginBottom: 14,
                }}
              >
                + New Chat
              </button>

              <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 8 }}>
                CHATS
              </div>
              {chats.map((chat) => (
                <div
                  key={chat.id}
                  onClick={() => switchChat(chat.id)}
                  style={{
                    padding: "10px 12px",
                    marginBottom: 6,
                    background:
                      currentChatId === chat.id ? "var(--card)" : "transparent",
                    border:
                      currentChatId === chat.id
                        ? "1px solid var(--border)"
                        : "none",
                    borderRadius: 8,
                    cursor: "pointer",
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    fontSize: 13,
                  }}
                >
                  <div style={{ flex: 1, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                    {chat.title}
                  </div>
                  <button
                    onClick={(e) => deleteChat(chat.id, e)}
                    style={{
                      background: "transparent",
                      border: "none",
                      color: "var(--red)",
                      cursor: "pointer",
                      padding: 0,
                      marginLeft: 6,
                      fontSize: 14,
                    }}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      <div
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          paddingBottom: 80,
        }}
      >
        {/* Suggested chips */}
        <div className="chips" style={{ paddingTop: 12 }}>
          {suggestedChips.map((chip) => (
            <div key={chip} className="chip" onClick={() => sendMessage(chip)}>
              {chip}
            </div>
          ))}
        </div>

        {/* Message thread */}
        <div className="chat-messages">
          {messages.map((msg, i) => (
            <div key={i} className={`msg ${msg.role} fade-in`}>
              <div className="msg-bubble">
                {msg.role === "ai" ? (
                  <ReactMarkdown>{msg.text}</ReactMarkdown>
                ) : (
                  msg.text
                )}
              </div>
              <div className="msg-time">{msg.time}</div>
            </div>
          ))}

          {typing && (
            <div className="msg ai fade-in">
              <div className="msg-bubble" style={{ padding: "12px 14px" }}>
                <div className="typing-indicator">
                  <div className="dot" />
                  <div className="dot" />
                  <div className="dot" />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input bar */}
        <div className="chat-input-bar">
          <button
            onClick={handleRecord}
            style={{
              marginRight: 8,
              background: recording ? "red" : "var(--card)",
              border: "none",
              borderRadius: 8,
              padding: "8px",
              cursor: "pointer",
            }}
          >
            🎤
          </button>
          <textarea
            className="chat-input"
            placeholder="Ask your AI coach..."
            rows={1}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
          />
          <button
            className="chat-send"
            onClick={() => sendMessage()}
            disabled={typing}
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="#fff"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}

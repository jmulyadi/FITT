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

  useEffect(() => {
    loadChats();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, typing]);

  const loadChats = async () => {
    try {
      const data = await apiFetch("/groq/chats", { method: "GET" });
      setChats(data.chats || []);
      
      if (!data.chats || data.chats.length === 0) {
        await createNewChat();
      } else {
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
        setMessages([
          {
            role: "ai",
            text: "Hey! I'm your FITT AI Coach. Ask me anything about training, recovery, or nutrition.",
            time: "Just now",
          },
        ]);
      } else {
        setMessages(
          dbMessages.map((m) => {
            let text = m.content;
            let workoutData = null;
            
            // Extract JSON blocks so they don't show as text, turning them into data
            let mealData = null;
            const jsonMatch = text.match(/```json\n([\s\S]*?)\n```/);
            if (jsonMatch) {
              // Inside loadChatMessages
              try {
                const parsedData = JSON.parse(jsonMatch[1]);
                if (parsedData.recommended_workout) {
                  workoutData = parsedData.recommended_workout;
                }
                
                // Add the check for meal plans here:
                if (parsedData.recommended_meal) {
                  mealData = parsedData.recommended_meal;
                } else if (parsedData.recommended_meal_plan) {
                  // Wrap it in the object structure Nutrition.jsx expects
                  mealData = { type: 'plan', meals: parsedData.recommended_meal_plan };
                }
                
                text = text.replace(/```json\n[\s\S]*?\n```/, '').trim();
              } catch (e) {
                console.error("Failed to parse historical AI JSON", e);
              }
            }

            return {
              role: m.role === "assistant" ? "ai" : "user",
              text: text,
              workoutData,
              mealData,
              time: new Date(m.created_at).toLocaleTimeString([], {
                hour: "2-digit",
                minute: "2-digit",
              }),
            };
          })
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
      
      const chatsData = await apiFetch("/groq/chats", { method: "GET" });
      setChats(chatsData.chats || []);
      
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
      
      const updatedChats = chats.filter((c) => c.id !== chatIdToDelete);
      setChats(updatedChats);
      
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

    const userMsg = { role: "user", text, time: now() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setTyping(true);

    const history = [...messages, userMsg].map((m) => ({
      role: m.role === "ai" ? "assistant" : "user",
      content: m.text,
    }));

    try {
      const data = await apiFetch(`/groq/chats/${currentChatId}/messages`, {
        method: "POST",
        body: JSON.stringify({ messages: history }),
      });
      
      const aiText = data.response;
      let parsedWorkout = null;
      let parsedMeal = null;
      let displayText = aiText;

      const jsonMatch = aiText.match(/```json\n([\s\S]*?)\n```/);
      if (jsonMatch) {
        try {
          const jsonStr = jsonMatch[1];
          const parsedData = JSON.parse(jsonStr);
          if (parsedData.recommended_workout) {
            parsedWorkout = parsedData.recommended_workout;
          }
          if (parsedData.recommended_meal) {
            parsedMeal = parsedData.recommended_meal;
          } else if (parsedData.recommended_meal_plan) {
            // Wrap it in the object structure Nutrition.jsx expects
            parsedMeal = { type: 'plan', meals: parsedData.recommended_meal_plan };
          }
          displayText = aiText.replace(/```json\n[\s\S]*?\n```/, '').trim();
        } catch (e) {
          console.error("Failed to parse AI JSON", e);
        }
      }

      setMessages((prev) => [
        ...prev,
        { role: "ai", text: displayText, workoutData: parsedWorkout, mealData: parsedMeal, time: now() },
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
          const token = localStorage.getItem("access_token");
          const userId = token ? JSON.parse(atob(token.split(".")[1]
            .replace(/-/g, "+").replace(/_/g, "/")))?.sub : null;
        
          const res = await fetch(`${API_BASE}/users/${userId}/groq/transcribe`, {
            method: "POST",
            headers: {
              Authorization: `Bearer ${token}`,
            },
            body: formData,
          });
        
          const data = await res.json();
          setInput(data.transcription);
        } catch (err) {
          console.error("Transcription error:", err);
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
        <div className="chips" style={{ paddingTop: 12 }}>
          {suggestedChips.map((chip) => (
            <div key={chip} className="chip" onClick={() => sendMessage(chip)}>
              {chip}
            </div>
          ))}
        </div>

        <div className="chat-messages">
          {messages.map((msg, i) => (
            <div key={i} className={`msg ${msg.role} fade-in`}>
              <div className="msg-bubble">
                {msg.role === "ai" ? (
                  <div>
                    <ReactMarkdown>{msg.text}</ReactMarkdown>
                    {msg.workoutData && (
                      <button 
                        className="btn btn-green"
                        style={{ marginTop: '12px', fontSize: '13px', padding: '8px 12px', width: '100%' }}
                        onClick={() => {
                          localStorage.setItem("fitt_pending_workout", JSON.stringify(msg.workoutData));
                          alert("Workout imported! Switch over to the Workout tab to see it.");
                        }}
                      >
                        Import to Active Workout
                      </button>
                    )}
                    {msg.mealData && (
                      <button
                        className="btn btn-green"
                        style={{ marginTop: '8px', fontSize: '13px', padding: '8px 12px', width: '100%' }}
                        onClick={() => {
                          localStorage.setItem("fitt_pending_meal", JSON.stringify(msg.mealData));
                          alert("Meal imported! Switch over to the Nutrition tab to see it.");
                        }}
                      >
                        Import to Meal Log
                      </button>
                    )}
                  </div>
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

        <div className="chat-input-bar">
          <button
            onClick={handleRecord}
            title={recording ? "Stop recording" : "Record voice message"}
            aria-label={recording ? "Stop recording" : "Record voice message"}
            style={{
              marginRight: 8,
              background: recording ? "var(--red)" : "var(--card)",
              border: `1px solid ${recording ? "var(--red)" : "var(--border)"}`,
              borderRadius: "50%",
              width: 40,
              height: 40,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
              transition: "background 0.15s, border-color 0.15s, transform 0.1s",
              boxShadow: recording ? "0 0 0 4px rgba(239, 68, 68, 0.18)" : "none",
              animation: recording ? "mic-pulse 1.4s ease-in-out infinite" : "none",
              flexShrink: 0,
            }}
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke={recording ? "#fff" : "var(--text)"}
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <rect x="9" y="2" width="6" height="12" rx="3" />
              <path d="M5 11a7 7 0 0 0 14 0" />
              <line x1="12" y1="18" x2="12" y2="22" />
              <line x1="8" y1="22" x2="16" y2="22" />
            </svg>
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
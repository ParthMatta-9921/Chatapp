import React, { useState, useEffect, useRef, useCallback } from "react";
import axios from "axios";

const API_BASE = "http://127.0.0.1:8000";

function App() {
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [form, setForm] = useState({ email: "", username: "", password: "" });
  const [isLogin, setIsLogin] = useState(true);
  const [error, setError] = useState("");
  const [friends, setFriends] = useState([]);
  const [incomingRequests, setIncomingRequests] = useState([]);
  const [chatFriend, setChatFriend] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const wsRef = useRef(null);

  // Save token in localStorage and state
  function storeToken(tok) {
    localStorage.setItem("token", tok);
    setToken(tok);
  }

  // Clear token and data on logout
  function logout() {
    localStorage.removeItem("token");
    setToken("");
    setFriends([]);
    setIncomingRequests([]);
    setChatFriend(null);
    setChatMessages([]);
  }

  // API helpers with Authorization header
  const axiosAuth = axios.create({
    baseURL: API_BASE,
    headers: { Authorization: `Bearer ${token}` },
  });

  // --- Auth ---

  async function login() {
    setError("");
    try {
      const res = await axios.post(`${API_BASE}/auth/login`, {
        email: form.email,
        password: form.password,
      });
      storeToken(res.data.access_token);
      setForm({ email: "", username: "", password: "" });
    } catch (e) {
      setError(e.response?.data?.detail || "Login failed");
    }
  }

  async function signup() {
    setError("");
    try {
      await axios.post(`${API_BASE}/auth/signup`, {
        username: form.username,
        email: form.email,
        password: form.password,
      });
      setIsLogin(true);
      setForm({ email: "", username: "", password: "" });
    } catch (e) {
      setError(e.response?.data?.detail || "Signup failed");
    }
  }

  // --- Friends ---

  const loadFriends = useCallback(async () => {
    try {
      const res = await axiosAuth.get("/friends/list");
      setFriends(res.data);
    } catch {
      setFriends([]);
    }
  }, [axiosAuth]);

  const loadIncomingRequests = useCallback(async () => {
    try {
      const res = await axiosAuth.get("/friends/requests/incoming");
      setIncomingRequests(res.data);
    } catch {
      setIncomingRequests([]);
    }
  }, [axiosAuth]);

  const setupWebSocket = useCallback(() => {
    if (!token) return;

    if (wsRef.current) {
      wsRef.current.close();
    }

    const ws = new WebSocket(`${API_BASE.replace("http", "ws")}/chat/ws?token=${token}`);

    ws.onopen = () => {
      console.log("WebSocket connected");
      if (chatFriend) {
        ws.send(
          JSON.stringify({
            type: "history",
            friend_id: chatFriend.friend_id,
          })
        );
      }
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "message") {
        setChatMessages((msgs) => [...msgs, data]);
      } else if (data.type === "history") {
        setChatMessages(data.messages || []);
      } else if (data.error) {
        alert("WS Error: " + data.error);
      }
    };

    ws.onclose = () => {
      console.log("WebSocket closed");
    };

    wsRef.current = ws;
  }, [token, chatFriend]);

  useEffect(() => {
    if (token) {
      loadFriends();
      loadIncomingRequests();
      setupWebSocket();
    }
  }, [token, loadFriends, loadIncomingRequests, setupWebSocket]);

  useEffect(() => {
    if (wsRef.current && chatFriend) {
      wsRef.current.send(
        JSON.stringify({
          type: "history",
          friend_id: chatFriend.friend_id,
        })
      );
      setChatMessages([]);
    }
  }, [chatFriend]);
  // Remove friend
async function removeFriend(friendId) {
  try {
    await axiosAuth.delete(`/friends/remove/${friendId}`);
    alert("Friend removed");
    loadFriends();
  } catch (e) {
    alert(e.response?.data?.detail || "Error removing friend");
  }
}

// Respond to friend request (accept or reject)
async function respondFriendRequest(friendId, action) {
  try {
    await axiosAuth.post("/friends/respond", { sender_id: friendId, action });
    alert(`Friend request ${action}ed`);
    loadFriends();
    loadIncomingRequests();
  } catch (e) {
    alert(e.response?.data?.detail || "Error responding to friend request");
  }
}


  // Send chat message
  function sendMessage(content) {
    if (!chatFriend || !content.trim()) return;
    const msg = {
      type: "message",
      to: chatFriend.friend_id,
      content,
    };
    wsRef.current.send(JSON.stringify(msg));
  }

  // --- UI ---

  if (!token) {
    return (
      <div style={{ maxWidth: 400, margin: "auto", padding: 20 }}>
        <h2>{isLogin ? "Login" : "Signup"}</h2>
        {!isLogin && (
          <input
            placeholder="Username"
            value={form.username}
            onChange={(e) => setForm({ ...form, username: e.target.value })}
            style={{ width: "100%", marginBottom: 8 }}
          />
        )}
        <input
          placeholder="Email"
          type="email"
          value={form.email}
          onChange={(e) => setForm({ ...form, email: e.target.value })}
          style={{ width: "100%", marginBottom: 8 }}
        />
        <input
          placeholder="Password"
          type="password"
          value={form.password}
          onChange={(e) => setForm({ ...form, password: e.target.value })}
          style={{ width: "100%", marginBottom: 8 }}
        />
        <button onClick={isLogin ? login : signup} style={{ width: "100%", padding: 10 }}>
          {isLogin ? "Login" : "Signup"}
        </button>
        <p style={{ marginTop: 10 }}>
          {isLogin ? "Don't have an account?" : "Already have an account?"}{" "}
          <button
            onClick={() => {
              setIsLogin(!isLogin);
              setError("");
              setForm({ email: "", username: "", password: "" });
            }}
          >
            {isLogin ? "Signup" : "Login"}
          </button>
        </p>
        {error && <p style={{ color: "red" }}>{error}</p>}
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 600, margin: "auto", padding: 20 }}>
      <h2>Welcome</h2>
      <button onClick={logout} style={{ float: "right" }}>
        Logout
      </button>

      <h3>Friends</h3>
      <ul>
        {friends.map((f) => (
          <li key={f.friend_id}>
            {f.friend_username}{" "}
            <button onClick={() => removeFriend(f.friend_id)}>Remove</button>{" "}
            <button onClick={() => setChatFriend(f)}>Chat</button>
          </li>
        ))}
      </ul>

      <h3>Incoming Friend Requests</h3>
      <ul>
        {incomingRequests.map((req) => (
          <li key={req.id}>
            {req.friend_username}{" "}
            <button onClick={() => respondFriendRequest(req.friend_id, "accept")}>Accept</button>{" "}
            <button onClick={() => respondFriendRequest(req.friend_id, "reject")}>Reject</button>
          </li>
        ))}
      </ul>

      <h3>Chat {chatFriend ? `with ${chatFriend.friend_username}` : ""}</h3>
      {chatFriend && <ChatBox messages={chatMessages} onSend={sendMessage} />}
    </div>
  );
}

function ChatBox({ messages, onSend }) {
  const [input, setInput] = useState("");

  function handleSend() {
    onSend(input);
    setInput("");
  }

  return (
    <div style={{ border: "1px solid #ccc", padding: 10 }}>
      <div
        style={{
          height: 200,
          overflowY: "auto",
          border: "1px solid #999",
          padding: 5,
          marginBottom: 10,
        }}
      >
        {messages.map((msg, i) => (
          <div key={i} style={{ marginBottom: 5 }}>
            <b>{msg.from === msg.to ? "You" : `User ${msg.from}`}</b>: {msg.content} <br />
            <small>{new Date(msg.timestamp).toLocaleString()}</small>
          </div>
        ))}
      </div>
      <input
        style={{ width: "80%" }}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Type your message..."
        onKeyDown={(e) => {
          if (e.key === "Enter") handleSend();
        }}
      />
      <button onClick={handleSend} style={{ width: "18%" }}>
        Send
      </button>
    </div>
  );
}

export default App;

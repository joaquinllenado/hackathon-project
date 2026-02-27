import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [message, setMessage] = useState("");

  useEffect(() => {
    fetch("/api/hello")
      .then((res) => res.json())
      .then((data) => setMessage(data.message))
      .catch(() => setMessage("Failed to connect to backend"));
  }, []);

  return (
    <div className="app">
      <h1>🚀 Hackathon App</h1>
      <p>{message || "Loading..."}</p>
    </div>
  );
}

export default App;

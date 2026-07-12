import { useEffect, useState } from "react";
import ActivityPanel from "./LiveActivityPanel";
import React from "react";

export default function CommandBar() {
  const [command, setCommand] = useState("");

  const [taskId, setTaskId] = useState(-1);

  const [taskStatus, setTaskStatus] = useState("TASK NOT YET SEND");

  const handleSubmit = async function (e) {
    e.preventDefault();

    console.log("SENDING REQUEST");

    const res = await fetch("http://127.0.0.1:8000/commands/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ command: command }),
    });

    const data = await res.json();

    console.log(data);
    setTaskId(data.task_id);
  };

  useEffect(() => {
    if (taskId === -1) return; // no task yet, don't connect

    const ws = new WebSocket(`ws://127.0.0.1:8000/commands/ws/${taskId}`);
    console.log("in iseEffect");

    ws.onmessage = (event) => {
      const statusTask = event.data;
      console.log("received progress", statusTask);
      setTaskStatus(statusTask);
    };

    ws.onerror = (err) => console.error("WebSocket error:", err);

    return () => {
      ws.close(); // cleanup on unmount / taskId change
    };
  }, [taskId]);
  return (
    <div className="command-bar">
      <form onSubmit={handleSubmit}>
        <label htmlFor="command-input">Command:</label>
        <input
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          id="command-input"
          placeholder="Enter command..."
        />
        <button type="submit">Submit</button>
      </form>
      <ActivityPanel taskStatus={taskStatus} />
    </div>
  );
}

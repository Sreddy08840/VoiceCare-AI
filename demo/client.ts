import WebSocket from "ws";

const ws = new WebSocket("ws://127.0.0.1:8000/ws/voice");

ws.on("open", () => {
  console.log("connected");
  ws.send(
    JSON.stringify({
      session_id: "demo-session",
      patient_id: "p003",
      audio_text: "Book appointment with Dr Meena at 2026-04-28T10:00:00",
    }),
  );
});

ws.on("message", (data) => {
  const parsed = JSON.parse(data.toString());
  console.log("assistant:", parsed.text);
  console.log("trace:", parsed.trace);
  ws.close();
});

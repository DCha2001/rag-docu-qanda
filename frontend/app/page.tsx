"use client";

import { useCallback, useEffect, useState } from "react";
import Sidebar, { Doc } from "./components/Sidebar";
import ChatPanel, { Message } from "./components/ChatPanel";

const API = "http://localhost:8000";

export default function Home() {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [uploading, setUploading] = useState(false);
  const [chatLoading, setChatLoading] = useState(false);

  const fetchDocs = useCallback(async () => {
    try {
      const res = await fetch(`${API}/documents`);
      if (res.ok) setDocs(await res.json());
    } catch {
      // backend not running yet — silently ignore
    }
  }, []);

  // Poll documents every 3s to pick up in-progress status changes
  useEffect(() => {
    fetchDocs();
    const id = setInterval(fetchDocs, 3000);
    return () => clearInterval(id);
  }, [fetchDocs]);

  async function handleUpload(file: File) {
    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(`${API}/ingest`, { method: "POST", body: form });
      if (!res.ok) throw new Error(await res.text());
      await fetchDocs();
    } catch (err) {
      console.error("Upload failed:", err);
    } finally {
      setUploading(false);
    }
  }

  async function handleSend(query: string) {
    setMessages((prev) => [...prev, { role: "user", text: query }]);
    setChatLoading(true);
    try {
      const res = await fetch(`${API}/query?query=${encodeURIComponent(query)}`, {
        method: "POST",
      });
      const data = await res.json();

      if (data.error) {
        setMessages((prev) => [
          ...prev,
          { role: "assistant", text: `Error: ${data.error}` },
        ]);
        return;
      }

      // The API returns content blocks: [{type: "text", text: "..."}]
      const text = Array.isArray(data.response)
        ? data.response
            .filter((b: { type: string }) => b.type === "text")
            .map((b: { text: string }) => b.text)
            .join("")
        : String(data.response);

      setMessages((prev) => [...prev, { role: "assistant", text }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "Failed to reach the server." },
      ]);
      console.error(err);
    } finally {
      setChatLoading(false);
    }
  }

  const hasCompleted = docs.some((d) => d.status === "completed");

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar docs={docs} uploading={uploading} onUpload={handleUpload} />
      <ChatPanel
        messages={messages}
        loading={chatLoading}
        onSend={handleSend}
        hasDocuments={hasCompleted}
      />
    </div>
  );
}

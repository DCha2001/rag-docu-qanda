"use client";

import { useCallback, useEffect, useState } from "react";
import Sidebar, { Doc } from "./components/Sidebar";
import ChatPanel, { Message } from "./components/ChatPanel";
import { api } from "@/lib/fetchapi";

export default function Home() {
  const [docs, setDocs] = useState<Doc[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [uploading, setUploading] = useState(false);
  const [chatLoading, setChatLoading] = useState(false);

  const fetchDocs = useCallback(async () => {
    try {
      const data = await api.documents.list();
      setDocs(data);
    } catch {
      setDocs([])
    }
  }, []);

  // Poll documents every 3s to pick up in-progress status changes
  useEffect(() => {
    fetchDocs();
    // const id = setInterval(fetchDocs, 3000);
    // return () => clearInterval(id);
  }, [fetchDocs]);

  async function handleDelete(id: string) {
    try {
      await api.documents.delete(id);
      await fetchDocs();
    } catch (err) {
      console.error("Delete failed:", err);
    }
  }

  async function handleUpload(file: File) {
    setUploading(true);
    try {
      await api.documents.upload(file);
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
      const data = await api.query.send(query);

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
            .filter((b) => b.type === "text")
            .map((b) => b.text)
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
      <Sidebar docs={docs} uploading={uploading} onUpload={handleUpload} onDelete={handleDelete} />
      <ChatPanel
        messages={messages}
        loading={chatLoading}
        onSend={handleSend}
        hasDocuments={hasCompleted}
      />
    </div>
  );
}

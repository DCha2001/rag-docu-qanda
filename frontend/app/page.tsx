"use client";

import { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import Sidebar from "./components/Sidebar";
import ChatPanel, { Message } from "./components/ChatPanel";
import { api } from "@/lib/fetchapi";
import type { Doc } from "./components/Sidebar";
import type { SessionResponse } from "./models/session";

export default function Home() {
  const [sessions, setSessions] = useState<SessionResponse[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [docs, setDocs] = useState<Doc[]>([]);
  const [sessionDocs, setSessionDocs] = useState<Doc[]>([]);
  const [uploading, setUploading] = useState(false);
  const [chatLoading, setChatLoading] = useState(false);

  const fetchSessions = useCallback(async () => {
    try {
      const data = await api.sessions.list();
      setSessions(data);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to load sessions");
      setSessions([]);
    }
  }, []);

  const fetchDocs = useCallback(async () => {
    try {
      const data = await api.documents.list();
      setDocs(data);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to load documents");
      setDocs([]);
    }
  }, []);

  const fetchSessionDocs = useCallback(async (sessionId: string) => {
    try {
      const data = await api.sessions.getDocuments(sessionId);
      setSessionDocs(data);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to load session documents");
      setSessionDocs([]);
    }
  }, []);

  const fetchSessionMessages = useCallback(async (sessionId: string) => {
    try {
      const data = await api.sessions.getMessages(sessionId);
      const mapped: Message[] = data.map((m) => ({
        role: m.role,
        text: m.content,
      }));
      setMessages(mapped);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to load session messages");
      setMessages([]);
    }
  }, []);

  // On mount: load sessions and docs
  useEffect(() => {
    fetchSessions();
    fetchDocs();
  }, [fetchSessions, fetchDocs]);

  // When activeSessionId changes: load messages and session docs
  useEffect(() => {
    if (activeSessionId) {
      fetchSessionMessages(activeSessionId);
      fetchSessionDocs(activeSessionId);
    } else {
      setMessages([]);
      setSessionDocs([]);
    }
  }, [activeSessionId, fetchSessionMessages, fetchSessionDocs]);

  async function handleNewSession() {
    try {
      const session = await api.sessions.create(null);
      setSessions((prev) => [session, ...prev]);
      setActiveSessionId(session.id);
      toast.success("New session created");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to create session");
    }
  }

  function handleSelectSession(id: string) {
    setActiveSessionId(id);
  }

  async function handleDeleteSession(id: string) {
    try {
      await api.sessions.delete(id);
      if (activeSessionId === id) {
        setActiveSessionId(null);
      }
      await fetchSessions();
      toast.success("Session deleted");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to delete session");
    }
  }

  async function handleUpload(file: File) {
    setUploading(true);
    try {
      const uploaded = await api.documents.upload(file);
      await fetchDocs();
      toast.success("Document uploaded successfully");

      // Auto-attach to active session if one is selected
      if (activeSessionId) {
        try {
          await api.sessions.attachDocument(activeSessionId, uploaded.id);
          await fetchSessionDocs(activeSessionId);
        } catch {
          // Non-fatal: doc uploaded but auto-attach failed
          toast.error("Uploaded but could not auto-attach to session");
        }
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to upload document");
    } finally {
      setUploading(false);
    }
  }

  async function handleDeleteDoc(id: string) {
    try {
      await api.documents.delete(id);
      await fetchDocs();
      if (activeSessionId) {
        await fetchSessionDocs(activeSessionId);
      }
      toast.success("Document deleted");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to delete document");
    }
  }

  async function handleAttachDoc(docId: string) {
    if (!activeSessionId) return;
    try {
      await api.sessions.attachDocument(activeSessionId, docId);
      await fetchSessionDocs(activeSessionId);
      toast.success("Document added to session");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to attach document");
    }
  }

  async function handleDetachDoc(docId: string) {
    if (!activeSessionId) return;
    try {
      await api.sessions.detachDocument(activeSessionId, docId);
      await fetchSessionDocs(activeSessionId);
      toast.success("Document removed from session");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to detach document");
    }
  }

  async function handleSend(query: string) {
    if (!activeSessionId) return;

    setMessages((prev) => [...prev, { role: "user", text: query }]);
    // Add empty assistant message that we'll fill in as chunks arrive
    setMessages((prev) => [...prev, { role: "assistant", text: "" }]);
    setChatLoading(true);

    try {
      const res = await fetch("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, session_id: activeSessionId }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        const detail = body?.error ?? res.statusText;
        toast.error(detail);
        setMessages((prev) => {
          const msgs = [...prev];
          msgs[msgs.length - 1] = { role: "assistant", text: `Error: ${detail}` };
          return msgs;
        });
        return;
      }

      const reader = res.body!.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const lines = decoder.decode(value).split("\n\n").filter(Boolean);
        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const payload = JSON.parse(line.slice(6));

          if (payload.error) {
            toast.error(payload.error);
            setMessages((prev) => {
              const msgs = [...prev];
              msgs[msgs.length - 1] = { role: "assistant", text: `Error: ${payload.error}` };
              return msgs;
            });
          } else if (payload.text) {
            // Hide loading dots once first chunk arrives
            setChatLoading(false);
            setMessages((prev) => {
              const msgs = [...prev];
              msgs[msgs.length - 1] = {
                role: "assistant",
                text: msgs[msgs.length - 1].text + payload.text,
              };
              return msgs;
            });
          } else if (payload.done) {
            await fetchSessions();
          }
        }
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to reach the server");
      setMessages((prev) => {
        const msgs = [...prev];
        msgs[msgs.length - 1] = { role: "assistant", text: "Failed to reach the server." };
        return msgs;
      });
    } finally {
      setChatLoading(false);
    }
  }

  const activeSession = sessions.find((s) => s.id === activeSessionId) ?? null;
  const hasDocuments = sessionDocs.some((d) => d.status === "completed");

  return (
    <div className="flex h-screen bg-background">
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onNewSession={handleNewSession}
        onSelectSession={handleSelectSession}
        onDeleteSession={handleDeleteSession}
        docs={docs}
        sessionDocs={sessionDocs}
        uploading={uploading}
        onUpload={handleUpload}
        onDeleteDoc={handleDeleteDoc}
        onAttachDoc={handleAttachDoc}
        onDetachDoc={handleDetachDoc}
      />
      <ChatPanel
        messages={messages}
        loading={chatLoading}
        onSend={handleSend}
        hasDocuments={hasDocuments}
        activeSession={activeSession}
      />
    </div>
  );
}

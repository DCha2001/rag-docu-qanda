"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import Sidebar from "./components/Sidebar";
import ChatPanel, { Message } from "./components/ChatPanel";
import { api } from "@/lib/fetchapi";
import type { Doc } from "./components/Sidebar";
import type { SessionResponse } from "./models/session";
import { createClient } from "@/lib/supabase/client";

export default function Home() {
  const router = useRouter();
  const supabase = createClient();
  const [userEmail, setUserEmail] = useState<string | null>(null);
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

  // On mount: load user, sessions, and docs
  useEffect(() => {
    supabase.auth.getUser().then(({ data: { user } }) => {
      setUserEmail(user?.email ?? null);
    });
    fetchSessions();
    fetchDocs();
  }, [fetchSessions, fetchDocs]); // eslint-disable-line react-hooks/exhaustive-deps

  async function handleSignOut() {
    await supabase.auth.signOut();
    router.push("/login");
    router.refresh();
  }

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

    // Optimistically append the user message
    setMessages((prev) => [...prev, { role: "user", text: query }]);
    setChatLoading(true);

    try {
      const data = await api.query.send(query, activeSessionId);

      if (data.error) {
        toast.error(data.error);
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

      // Refresh sessions list so any auto-generated title shows up
      await fetchSessions();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to reach the server");
      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: "Failed to reach the server." },
      ]);
    } finally {
      setChatLoading(false);
    }
  }

  const activeSession = sessions.find((s) => s.id === activeSessionId) ?? null;
  const hasDocuments = sessionDocs.some((d) => d.status === "completed");

  return (
    <div className="flex h-screen flex-col bg-background">
      {/* Top bar: user info + sign out */}
      <header className="flex items-center justify-end gap-3 border-b border-border px-4 py-2 text-sm">
        {userEmail && <span className="text-muted-foreground">{userEmail}</span>}
        <button
          onClick={handleSignOut}
          className="rounded-md px-3 py-1 text-sm font-medium hover:bg-accent transition-colors"
        >
          Sign out
        </button>
      </header>
      <div className="flex flex-1 overflow-hidden">
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
    </div>
  );
}

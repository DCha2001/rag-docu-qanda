"use client";

import { useEffect, useRef, useState } from "react";
import { Send, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import type { SessionResponse } from "@/app/models/session";

export interface Message {
  role: "user" | "assistant";
  text: string;
}

interface ChatPanelProps {
  messages: Message[];
  loading: boolean;
  onSend: (query: string) => void;
  hasDocuments: boolean;
  activeSession: SessionResponse | null;
}

export default function ChatPanel({
  messages,
  loading,
  onSend,
  hasDocuments,
  activeSession,
}: ChatPanelProps) {
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, loading]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || loading) return;
    onSend(trimmed);
    setInput("");
  }

  // Determine empty-state message based on session and document state
  function getEmptyStateMessage(): { heading: string; body: string } {
    if (!activeSession) {
      return {
        heading: "No session selected",
        body: "Select or create a session to start chatting.",
      };
    }
    if (!hasDocuments) {
      return {
        heading: "No documents in this session",
        body: "Attach a document to this session to get started.",
      };
    }
    return {
      heading: "Ask about your documents",
      body: "Type a question below to search across the session's documents.",
    };
  }

  const isDisabled = !activeSession || !hasDocuments || loading;
  const emptyState = getEmptyStateMessage();

  return (
    <div className="flex flex-1 flex-col h-full bg-background">
      {/* Session header bar */}
      {activeSession && (
        <div className="px-6 py-3 border-b text-sm font-medium text-foreground truncate">
          {activeSession.title ?? "New session"}
        </div>
      )}

      {/* Messages */}
      <div ref={scrollRef} className="flex-1 min-h-0 overflow-y-auto">
        <div className="flex flex-col gap-4 px-6 py-6">
          {messages.length === 0 && (
            <div className="flex h-full min-h-[60vh] items-center justify-center">
              <div className="text-center max-w-sm">
                <div className="mx-auto mb-4 flex size-14 items-center justify-center rounded-2xl bg-muted">
                  <MessageSquare className="size-7 text-muted-foreground" />
                </div>
                <h2 className="text-base font-semibold text-foreground">
                  {emptyState.heading}
                </h2>
                <p className="mt-1.5 text-sm text-muted-foreground">
                  {emptyState.body}
                </p>
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              {msg.role === "assistant" && (
                <div className="mr-2.5 mt-0.5 flex size-7 flex-shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold">
                  AI
                </div>
              )}
              <div
                className={`max-w-[70%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground rounded-br-sm"
                    : "bg-muted text-foreground rounded-bl-sm"
                }`}
              >
                {msg.text}
              </div>
            </div>
          ))}

          {loading && messages[messages.length - 1]?.text === "" && (
            <div className="flex justify-start">
              <div className="mr-2.5 mt-0.5 flex size-7 flex-shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-xs font-bold">
                AI
              </div>
              <div className="rounded-2xl rounded-bl-sm bg-muted px-4 py-3">
                <span className="flex gap-1">
                  <span className="size-2 rounded-full bg-muted-foreground animate-bounce [animation-delay:-0.3s]" />
                  <span className="size-2 rounded-full bg-muted-foreground animate-bounce [animation-delay:-0.15s]" />
                  <span className="size-2 rounded-full bg-muted-foreground animate-bounce" />
                </span>
              </div>
            </div>
          )}

        </div>
      </div>

      <Separator />

      {/* Input */}
      <div className="px-5 py-4">
        <form onSubmit={handleSubmit} className="flex items-end gap-3">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e as unknown as React.FormEvent);
              }
            }}
            placeholder={
              !activeSession
                ? "Select a session to start…"
                : hasDocuments
                ? "Ask a question about your documents…"
                : "Attach a document to this session first…"
            }
            disabled={isDisabled}
            rows={1}
            className="flex-1 min-h-0 resize-none"
          />
          <Button
            type="submit"
            size="icon"
            disabled={isDisabled || !input.trim()}
          >
            <Send data-icon="inline-start" />
          </Button>
        </form>
        <p className="mt-2 text-center text-[11px] text-muted-foreground">
          Press Enter to send · Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}

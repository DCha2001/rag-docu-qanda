"use client";

import { useEffect, useRef, useState } from "react";
import { Send, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";

export interface Message {
  role: "user" | "assistant";
  text: string;
}

interface ChatPanelProps {
  messages: Message[];
  loading: boolean;
  onSend: (query: string) => void;
  hasDocuments: boolean;
}

export default function ChatPanel({
  messages,
  loading,
  onSend,
  hasDocuments,
}: ChatPanelProps) {
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || loading) return;
    onSend(trimmed);
    setInput("");
  }

  return (
    <div className="flex flex-1 flex-col h-full bg-background">
      {/* Messages */}
      <ScrollArea className="flex-1">
        <div className="flex flex-col gap-4 px-6 py-6">
          {messages.length === 0 && (
            <div className="flex h-full min-h-[60vh] items-center justify-center">
              <div className="text-center max-w-sm">
                <div className="mx-auto mb-4 flex size-14 items-center justify-center rounded-2xl bg-muted">
                  <MessageSquare className="size-7 text-muted-foreground" />
                </div>
                <h2 className="text-base font-semibold text-foreground">
                  Ask about your documents
                </h2>
                <p className="mt-1.5 text-sm text-muted-foreground">
                  {hasDocuments
                    ? "Type a question below to search across all uploaded documents."
                    : "Upload a document on the left to get started."}
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

          {loading && (
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

          <div ref={bottomRef} />
        </div>
      </ScrollArea>

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
              hasDocuments
                ? "Ask a question about your documents…"
                : "Upload a document first…"
            }
            disabled={!hasDocuments || loading}
            rows={1}
            className="flex-1 min-h-0 resize-none"
          />
          <Button
            type="submit"
            size="icon"
            disabled={!hasDocuments || loading || !input.trim()}
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

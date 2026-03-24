"use client";

import { useRef } from "react";
import { Upload, X, Plus, MessageSquare } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import type { SessionResponse } from "@/app/models/session";

export interface Doc {
  id: string;
  filename: string;
  status: string;
  chunk_count: number;
  created_at: string | null;
}

type BadgeVariant = "default" | "secondary" | "destructive" | "outline";

const STATUS_VARIANT: Record<string, BadgeVariant> = {
  completed: "default",
  failed: "destructive",
  parsing: "secondary",
  chunking: "secondary",
  embedding: "secondary",
  uploaded: "outline",
};

const IN_PROGRESS = new Set(["parsing", "chunking", "embedding"]);

interface SidebarProps {
  // Sessions
  sessions: SessionResponse[];
  activeSessionId: string | null;
  onNewSession: () => void;
  onSelectSession: (id: string) => void;
  onDeleteSession: (id: string) => void;
  // Documents
  docs: Doc[];
  sessionDocs: Doc[];
  uploading: boolean;
  onUpload: (file: File) => void;
  onDeleteDoc: (id: string) => void;
  onAttachDoc: (docId: string) => void;
  onDetachDoc: (docId: string) => void;
}

function formatSessionDate(dateStr: string | null): string {
  if (!dateStr) return "";
  const date = new Date(dateStr);
  const now = new Date();
  const isToday =
    date.getFullYear() === now.getFullYear() &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate();

  if (isToday) {
    return date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
  }
  return date.toLocaleDateString([], { month: "short", day: "numeric" });
}

export default function Sidebar({
  sessions,
  activeSessionId,
  onNewSession,
  onSelectSession,
  onDeleteSession,
  docs,
  sessionDocs,
  uploading,
  onUpload,
  onDeleteDoc,
  onAttachDoc,
  onDetachDoc,
}: SidebarProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) {
      onUpload(file);
      e.target.value = "";
    }
  }

  // Docs attached to active session
  const sessionDocIds = new Set(sessionDocs.map((d) => d.id));

  // Completed docs not yet in this session (available to add)
  const attachableDocs = docs.filter(
    (d) => d.status === "completed" && !sessionDocIds.has(d.id)
  );

  return (
    <aside className="flex h-full w-72 flex-col border-r border-border bg-muted/30">
      {/* Header */}
      <div className="px-5 py-5">
        <h1 className="text-base font-semibold tracking-tight text-foreground">
          AIDocuReader
        </h1>
        <p className="text-xs text-muted-foreground mt-0.5">Document Q&amp;A</p>
      </div>

      <Separator />

      {/* Sessions section */}
      <div className="px-4 pt-3 pb-1">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Sessions
          </span>
          <Button
            variant="outline"
            size="sm"
            className="h-6 px-2 text-xs"
            onClick={onNewSession}
          >
            <Plus className="size-3 mr-1" />
            New
          </Button>
        </div>
      </div>

      {/* Session list */}
      <ScrollArea className="max-h-[35vh] px-2">
        <div className="pb-2">
          {sessions.length === 0 ? (
            <p className="text-center text-xs text-muted-foreground px-2 py-3">
              No sessions yet. Create one to start chatting.
            </p>
          ) : (
            <ul className="flex flex-col gap-0.5">
              {sessions.map((session) => {
                const isActive = session.id === activeSessionId;
                return (
                  <li
                    key={session.id}
                    className={cn(
                      "group relative flex items-center gap-2 rounded-md px-2.5 py-2 cursor-pointer transition-colors border",
                      isActive
                        ? "bg-primary/10 border-primary/30 text-foreground"
                        : "border-transparent hover:bg-muted/60 text-muted-foreground hover:text-foreground"
                    )}
                    onClick={() => onSelectSession(session.id)}
                  >
                    <MessageSquare
                      className={cn(
                        "size-3.5 flex-shrink-0",
                        isActive ? "text-primary" : "text-muted-foreground"
                      )}
                    />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-xs font-medium">
                        {session.title ?? "New session"}
                      </p>
                      <p className="text-[10px] text-muted-foreground">
                        {formatSessionDate(session.created_at)}
                      </p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDeleteSession(session.id);
                      }}
                      className="flex-shrink-0 rounded p-0.5 text-muted-foreground opacity-0 transition-opacity hover:text-destructive group-hover:opacity-100"
                      aria-label="Delete session"
                    >
                      <X className="size-3" />
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </ScrollArea>

      <Separator />

      {/* Documents section */}
      <div className="px-4 pt-3 pb-1">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Documents
          </span>
          <div>
            <input
              ref={inputRef}
              type="file"
              className="hidden"
              onChange={handleFileChange}
              accept=".pdf,.docx,.txt,.md,.csv,.xlsx,.pptx"
            />
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              disabled={uploading}
              onClick={() => inputRef.current?.click()}
              title="Upload document"
            >
              {uploading ? (
                <span className="size-3 rounded-full border-2 border-muted-foreground/30 border-t-muted-foreground animate-spin" />
              ) : (
                <Upload className="size-3.5" />
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Document list */}
      <ScrollArea className="flex-1">
        <div className="px-3 pb-4">
          {activeSessionId ? (
            <>
              {/* In this session */}
              {sessionDocs.length > 0 && (
                <div className="mb-3">
                  <p className="mb-1.5 px-1 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                    In this session
                  </p>
                  <ul className="flex flex-col gap-1">
                    {sessionDocs.map((doc) => {
                      const inProgress = IN_PROGRESS.has(doc.status);
                      return (
                        <li
                          key={doc.id}
                          className="group rounded-lg bg-background px-2.5 py-2 border border-border"
                        >
                          <div className="flex items-start gap-2">
                            <span
                              className={cn(
                                "mt-1.5 size-2 flex-shrink-0 rounded-full bg-muted-foreground/40",
                                doc.status === "completed" && "bg-emerald-500",
                                doc.status === "failed" && "bg-destructive",
                                inProgress && "bg-secondary-foreground animate-pulse"
                              )}
                            />
                            <div className="min-w-0 flex-1">
                              <p
                                className="truncate text-xs font-medium text-foreground"
                                title={doc.filename}
                              >
                                {doc.filename}
                              </p>
                              <div className="mt-1 flex items-center gap-1.5">
                                <Badge
                                  variant={STATUS_VARIANT[doc.status] ?? "outline"}
                                  className="text-[9px] px-1 py-0 h-4"
                                >
                                  {doc.status}
                                </Badge>
                                {doc.status === "completed" && (
                                  <span className="text-[10px] text-muted-foreground">
                                    {doc.chunk_count} chunks
                                  </span>
                                )}
                                {inProgress && <Skeleton className="h-1.5 w-10" />}
                              </div>
                            </div>
                            <button
                              onClick={() => onDetachDoc(doc.id)}
                              className="ml-auto flex-shrink-0 rounded p-0.5 text-muted-foreground opacity-0 transition-opacity hover:text-destructive group-hover:opacity-100"
                              aria-label="Remove from session"
                            >
                              <X className="size-3" />
                            </button>
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                </div>
              )}

              {/* Add to session */}
              {attachableDocs.length > 0 && (
                <div>
                  <p className="mb-1.5 px-1 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
                    Add to session
                  </p>
                  <ul className="flex flex-col gap-1">
                    {attachableDocs.map((doc) => (
                      <li
                        key={doc.id}
                        className="group rounded-lg bg-background px-2.5 py-2 border border-border hover:bg-muted/50 transition-colors"
                      >
                        <div className="flex items-center gap-2">
                          <span className="size-2 flex-shrink-0 rounded-full bg-emerald-500" />
                          <p
                            className="min-w-0 flex-1 truncate text-xs text-muted-foreground group-hover:text-foreground"
                            title={doc.filename}
                          >
                            {doc.filename}
                          </p>
                          <button
                            onClick={() => onAttachDoc(doc.id)}
                            className="flex-shrink-0 rounded p-0.5 text-muted-foreground opacity-0 transition-opacity hover:text-primary group-hover:opacity-100"
                            aria-label="Add to session"
                          >
                            <Plus className="size-3.5" />
                          </button>
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {sessionDocs.length === 0 && attachableDocs.length === 0 && (
                <p className="text-center text-xs text-muted-foreground mt-4 px-2">
                  No documents yet.
                  <br />
                  Upload one to get started.
                </p>
              )}

              {sessionDocs.length === 0 && attachableDocs.length > 0 && (
                <p className="text-center text-xs text-muted-foreground mt-2 mb-3 px-2">
                  No documents in this session yet.
                </p>
              )}
            </>
          ) : (
            // No active session: flat list of all docs with delete only
            <>
              {docs.length === 0 ? (
                <p className="text-center text-xs text-muted-foreground mt-6 px-2">
                  No documents yet.
                  <br />
                  Upload one to get started.
                </p>
              ) : (
                <ul className="flex flex-col gap-1.5">
                  {docs.map((doc) => {
                    const variant = STATUS_VARIANT[doc.status] ?? "outline";
                    const inProgress = IN_PROGRESS.has(doc.status);
                    return (
                      <li
                        key={doc.id}
                        className="group rounded-lg bg-background px-3 py-2.5 border border-border hover:bg-muted/50 transition-colors"
                      >
                        <div className="flex items-start gap-2.5">
                          <span
                            className={cn(
                              "mt-1.5 size-2 flex-shrink-0 rounded-full bg-muted-foreground/40",
                              doc.status === "completed" && "bg-primary",
                              doc.status === "failed" && "bg-destructive",
                              inProgress && "bg-secondary-foreground animate-pulse"
                            )}
                          />
                          <div className="min-w-0 flex-1">
                            <p
                              className="truncate text-sm font-medium text-foreground"
                              title={doc.filename}
                            >
                              {doc.filename}
                            </p>
                            <div className="mt-1.5 flex items-center gap-2">
                              <Badge variant={variant}>{doc.status}</Badge>
                              {doc.status === "completed" && (
                                <span className="text-[10px] text-muted-foreground">
                                  {doc.chunk_count} chunks
                                </span>
                              )}
                              {inProgress && <Skeleton className="h-2 w-12" />}
                            </div>
                          </div>
                          <button
                            onClick={() => onDeleteDoc(doc.id)}
                            className="ml-auto flex-shrink-0 rounded p-0.5 text-muted-foreground opacity-0 transition-opacity hover:text-destructive group-hover:opacity-100"
                            aria-label="Delete document"
                          >
                            <X className="size-3.5" />
                          </button>
                        </div>
                      </li>
                    );
                  })}
                </ul>
              )}
            </>
          )}
        </div>
      </ScrollArea>
    </aside>
  );
}

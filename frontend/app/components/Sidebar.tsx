"use client";

import { useRef } from "react";
import { Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

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
  docs: Doc[];
  uploading: boolean;
  onUpload: (file: File) => void;
}

export default function Sidebar({ docs, uploading, onUpload }: SidebarProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) {
      onUpload(file);
      e.target.value = "";
    }
  }

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

      {/* Upload */}
      <div className="px-4 py-4">
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          onChange={handleFileChange}
          accept=".pdf,.docx,.txt,.md,.csv,.xlsx,.pptx"
        />
        <Button
          className="w-full"
          disabled={uploading}
          onClick={() => inputRef.current?.click()}
        >
          {uploading ? (
            <>
              <span className="size-4 rounded-full border-2 border-primary-foreground/30 border-t-primary-foreground animate-spin" />
              Uploading…
            </>
          ) : (
            <>
              <Upload data-icon="inline-start" />
              Upload Document
            </>
          )}
        </Button>
      </div>

      <Separator />

      {/* Document list */}
      <ScrollArea className="flex-1">
        <div className="px-3 py-3">
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
                    className="rounded-lg bg-background px-3 py-2.5 border border-border hover:bg-muted/50 transition-colors"
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
                          {inProgress && (
                            <Skeleton className="h-2 w-12" />
                          )}
                        </div>
                      </div>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </ScrollArea>
    </aside>
  );
}

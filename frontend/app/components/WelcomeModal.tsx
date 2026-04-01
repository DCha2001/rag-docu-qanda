"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { MessageSquare, Upload, FolderOpen, X } from "lucide-react";

const STORAGE_KEY = "welcome_modal_seen";

export default function WelcomeModal() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!localStorage.getItem(STORAGE_KEY)) {
      setOpen(true);
    }
  }, []);

  function dismiss() {
    localStorage.setItem(STORAGE_KEY, "1");
    setOpen(false);
  }

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={dismiss}
    >
      <div
        className="relative mx-4 w-full max-w-md rounded-xl border border-border bg-background p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={dismiss}
          className="absolute right-4 top-4 rounded-md p-1 text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
        >
          <X className="size-4" />
        </button>

        <h2 className="text-lg font-semibold text-foreground">Welcome to AIDocuReader</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Chat with your documents using AI. Here&apos;s how to get started:
        </p>

        <ol className="mt-5 space-y-4">
          <li className="flex gap-3">
            <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
              <FolderOpen className="size-4" />
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">Create a session</p>
              <p className="text-sm text-muted-foreground">
                Click <span className="font-medium">New Session</span> in the sidebar to start a new conversation workspace.
              </p>
            </div>
          </li>

          <li className="flex gap-3">
            <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
              <Upload className="size-4" />
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">Upload documents</p>
              <p className="text-sm text-muted-foreground">
                Upload PDFs, Word docs, spreadsheets, or text files. Drag documents from your library into a session to attach them.
              </p>
            </div>
          </li>

          <li className="flex gap-3">
            <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
              <MessageSquare className="size-4" />
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">Ask questions</p>
              <p className="text-sm text-muted-foreground">
                Type any question and the AI will answer using only the documents attached to your session, with citations.
              </p>
            </div>
          </li>
        </ol>

        <Button className="mt-6 w-full" onClick={dismiss}>
          Get started
        </Button>
      </div>
    </div>
  );
}

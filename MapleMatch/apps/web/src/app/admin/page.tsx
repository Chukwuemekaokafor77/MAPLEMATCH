"use client";

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  useMe,
  usePendingDocuments,
  useReviewDocument,
  useTriggerSync,
  useSyncLogs,
} from "@/hooks/useApi";
import type { DocumentItem, SyncLog } from "@/lib/api";
import {
  FileText,
  ExternalLink,
  CheckCircle,
  XCircle,
  RefreshCw,
  ShieldAlert,
  Database,
} from "lucide-react";

export default function AdminPage() {
  const { t } = useTranslation();
  const { data: me, isLoading: meLoading } = useMe();
  const [section, setSection] = useState<"documents" | "sync">("documents");

  if (meLoading) {
    return (
      <main className="max-w-4xl mx-auto px-4 py-8 space-y-4">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-64" />
      </main>
    );
  }

  if (me?.role !== "admin") {
    return (
      <main className="flex flex-col items-center justify-center min-h-[calc(100vh-4rem)] text-center px-4">
        <ShieldAlert className="size-12 text-muted-foreground mb-4" />
        <h1 className="text-xl font-bold">{t("admin.accessDenied")}</h1>
        <p className="text-muted-foreground mt-1 text-sm">
          {t("admin.accessDeniedDesc")}
        </p>
      </main>
    );
  }

  return (
    <main className="max-w-4xl mx-auto px-4 py-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">{t("admin.title")}</h1>
        <p className="text-muted-foreground mt-1">{t("admin.subtitle")}</p>
      </div>

      {/* Section tabs */}
      <div className="flex gap-2 border-b pb-0">
        <Button
          variant={section === "documents" ? "default" : "ghost"}
          size="sm"
          onClick={() => setSection("documents")}
          className="rounded-b-none"
        >
          <FileText className="size-4 mr-1.5" />
          {t("admin.pendingDocs")}
        </Button>
        <Button
          variant={section === "sync" ? "default" : "ghost"}
          size="sm"
          onClick={() => setSection("sync")}
          className="rounded-b-none"
        >
          <Database className="size-4 mr-1.5" />
          {t("admin.cmhcSync")}
        </Button>
      </div>

      {section === "documents" && <PendingDocsSection />}
      {section === "sync" && <SyncSection />}
    </main>
  );
}

/* ─── Pending Documents ─────────────────────────────────────────── */

function PendingDocsSection() {
  const { t } = useTranslation();
  const { data: docs, isLoading } = usePendingDocuments();
  const review = useReviewDocument();
  const [notes, setNotes] = useState<Record<string, string>>({});

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-24 rounded-lg" />
        ))}
      </div>
    );
  }

  if (!docs || docs.length === 0) {
    return (
      <p className="text-muted-foreground text-center py-12">
        {t("admin.pendingDocsEmpty")}
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {docs.map((doc) => (
        <DocReviewCard
          key={doc.id}
          doc={doc}
          note={notes[doc.id] ?? ""}
          onNoteChange={(v) => setNotes((n) => ({ ...n, [doc.id]: v }))}
          onApprove={() =>
            review.mutate({ id: doc.id, status: "verified", notes: notes[doc.id] })
          }
          onReject={() =>
            review.mutate({ id: doc.id, status: "rejected", notes: notes[doc.id] })
          }
          isPending={review.isPending}
        />
      ))}
    </div>
  );
}

function DocReviewCard({
  doc,
  note,
  onNoteChange,
  onApprove,
  onReject,
  isPending,
}: {
  doc: DocumentItem;
  note: string;
  onNoteChange: (v: string) => void;
  onApprove: () => void;
  onReject: () => void;
  isPending: boolean;
}) {
  const { t } = useTranslation();
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <FileText className="size-5 text-muted-foreground shrink-0" />
            <div>
              <CardTitle className="text-sm font-semibold">
                {doc.original_filename || doc.doc_type}
              </CardTitle>
              <CardDescription className="capitalize">
                {t(`documents.types.${doc.doc_type}`)}
              </CardDescription>
            </div>
          </div>
          <Button asChild variant="ghost" size="sm">
            <a
              href={doc.file_url}
              target="_blank"
              rel="noopener noreferrer"
              aria-label={t("documents.viewFile")}
            >
              <ExternalLink className="size-4" />
            </a>
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="space-y-1">
          <Label htmlFor={`notes-${doc.id}`} className="text-xs">
            {t("admin.notes")}
          </Label>
          <Input
            id={`notes-${doc.id}`}
            placeholder={t("admin.notesPlaceholder")}
            value={note}
            onChange={(e) => onNoteChange(e.target.value)}
            className="h-8 text-sm"
          />
        </div>
        <div className="flex gap-2">
          <Button
            size="sm"
            disabled={isPending}
            onClick={onApprove}
            className="gap-1.5"
          >
            <CheckCircle className="size-3.5" />
            {t("admin.approve")}
          </Button>
          <Button
            size="sm"
            variant="destructive"
            disabled={isPending}
            onClick={onReject}
            className="gap-1.5"
          >
            <XCircle className="size-3.5" />
            {t("admin.reject")}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

/* ─── CMHC Sync ─────────────────────────────────────────────────── */

function SyncSection() {
  const { t } = useTranslation();
  const triggerSync = useTriggerSync();
  const { data: logs, isLoading } = useSyncLogs();
  const [province, setProvince] = useState("");
  const [city, setCity] = useState("");
  const [lastResult, setLastResult] = useState<SyncLog | null>(null);

  const handleSync = async () => {
    const result = await triggerSync.mutateAsync({
      province: province || undefined,
      city: city || undefined,
    });
    setLastResult(result);
  };

  return (
    <div className="space-y-6">
      {/* Trigger */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">{t("admin.triggerSync")}</CardTitle>
          <CardDescription>{t("admin.triggerSyncDesc")}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <Label htmlFor="sync-province">{t("listings.province")}</Label>
              <Input
                id="sync-province"
                placeholder="ON"
                value={province}
                onChange={(e) => setProvince(e.target.value.toUpperCase())}
                maxLength={2}
              />
            </div>
            <div className="space-y-1">
              <Label htmlFor="sync-city">{t("listings.city")}</Label>
              <Input
                id="sync-city"
                placeholder="Toronto"
                value={city}
                onChange={(e) => setCity(e.target.value)}
              />
            </div>
          </div>

          <Button
            onClick={handleSync}
            disabled={triggerSync.isPending}
            className="gap-2"
          >
            <RefreshCw
              className={`size-4 ${triggerSync.isPending ? "animate-spin" : ""}`}
            />
            {triggerSync.isPending ? t("common.loading") : t("admin.runSync")}
          </Button>

          {triggerSync.isError && (
            <p className="text-sm text-destructive" role="alert">
              {triggerSync.error.message}
            </p>
          )}

          {lastResult && (
            <div className="rounded-md bg-muted px-4 py-3 text-sm space-y-1">
              <div className="flex items-center gap-2 font-medium">
                <SyncStatusDot status={lastResult.status} />
                {lastResult.source}
              </div>
              <div className="text-muted-foreground">
                {t("admin.syncResult", {
                  fetched: lastResult.records_fetched,
                  upserted: lastResult.records_upserted,
                })}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Logs */}
      <div>
        <h2 className="text-base font-semibold mb-3">{t("admin.syncLogs")}</h2>
        {isLoading && (
          <div className="space-y-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-12 rounded-md" />
            ))}
          </div>
        )}
        {logs && logs.length === 0 && (
          <p className="text-muted-foreground text-center py-8">
            {t("admin.noLogs")}
          </p>
        )}
        {logs && logs.length > 0 && (
          <div className="space-y-2">
            {logs.map((log, i) => (
              <div key={log.id ?? i}>
                <div className="flex items-center justify-between py-2 text-sm">
                  <div className="flex items-center gap-2">
                    <SyncStatusDot status={log.status} />
                    <span className="font-medium">{log.source}</span>
                    <span className="text-muted-foreground">
                      {t("admin.syncResult", {
                        fetched: log.records_fetched,
                        upserted: log.records_upserted,
                      })}
                    </span>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {new Date(log.created_at).toLocaleString()}
                  </span>
                </div>
                {i < logs.length - 1 && <Separator />}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function SyncStatusDot({ status }: { status: string }) {
  const colors: Record<string, string> = {
    success: "bg-green-500",
    error: "bg-destructive",
    partial: "bg-yellow-500",
  };
  return (
    <span
      className={`inline-block size-2 rounded-full ${colors[status] ?? "bg-muted-foreground"}`}
    />
  );
}

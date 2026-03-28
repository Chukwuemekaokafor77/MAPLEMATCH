"use client";

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  useMyDocuments,
  useUploadDocument,
  useDeleteDocument,
} from "@/hooks/useApi";
import { FileText, Trash2, ExternalLink, UploadCloud } from "lucide-react";

const DOC_TYPES = [
  "income_proof",
  "government_id",
  "residency_proof",
  "other",
] as const;

export default function DocumentsPage() {
  const { t } = useTranslation();
  const { data: docs, isLoading } = useMyDocuments();
  const upload = useUploadDocument();
  const deleteDoc = useDeleteDocument();
  const [form, setForm] = useState({
    doc_type: "income_proof",
    file_url: "",
    original_filename: "",
  });

  const handleUpload = async () => {
    if (!form.file_url) return;
    await upload.mutateAsync(form);
    setForm({ doc_type: "income_proof", file_url: "", original_filename: "" });
  };

  return (
    <main className="max-w-3xl mx-auto px-4 py-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">{t("documents.title")}</h1>
        <p className="text-muted-foreground mt-1">{t("documents.subtitle")}</p>
      </div>

      {/* Upload form */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center gap-2">
            <UploadCloud className="size-4" />
            {t("documents.upload")}
          </CardTitle>
          <CardDescription>{t("documents.uploadDesc")}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>{t("documents.docType")}</Label>
            <Select
              value={form.doc_type}
              onValueChange={(v) => setForm((f) => ({ ...f, doc_type: v }))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {DOC_TYPES.map((dt) => (
                  <SelectItem key={dt} value={dt}>
                    {t(`documents.types.${dt}`)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="filename">{t("documents.filename")}</Label>
            <Input
              id="filename"
              placeholder="income_statement_2024.pdf"
              value={form.original_filename}
              onChange={(e) =>
                setForm((f) => ({ ...f, original_filename: e.target.value }))
              }
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="url">{t("documents.fileUrl")}</Label>
            <Input
              id="url"
              placeholder="https://drive.google.com/file/..."
              value={form.file_url}
              onChange={(e) =>
                setForm((f) => ({ ...f, file_url: e.target.value }))
              }
            />
            <p className="text-xs text-muted-foreground">
              {t("documents.urlHint")}
            </p>
          </div>

          {upload.isError && (
            <p className="text-sm text-destructive" role="alert">
              {upload.error.message}
            </p>
          )}

          <Button
            onClick={handleUpload}
            disabled={!form.file_url || upload.isPending}
          >
            {upload.isPending ? t("common.loading") : t("documents.submit")}
          </Button>
        </CardContent>
      </Card>

      {/* Document list */}
      <div>
        <h2 className="text-lg font-semibold mb-3">{t("documents.myDocs")}</h2>

        {isLoading && (
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-16 rounded-lg" />
            ))}
          </div>
        )}

        {docs && docs.length === 0 && (
          <p className="text-muted-foreground text-center py-10">
            {t("documents.empty")}
          </p>
        )}

        {docs && docs.length > 0 && (
          <div className="space-y-3">
            {docs.map((doc) => (
              <Card key={doc.id}>
                <CardContent className="py-3 flex items-center justify-between gap-4">
                  <div className="flex items-center gap-3 min-w-0">
                    <FileText className="size-5 text-muted-foreground shrink-0" />
                    <div className="min-w-0">
                      <div className="font-medium text-sm truncate">
                        {doc.original_filename || doc.doc_type}
                      </div>
                      <div className="text-xs text-muted-foreground capitalize">
                        {t(`documents.types.${doc.doc_type}`)}
                      </div>
                      {doc.reviewer_notes && (
                        <div className="text-xs text-muted-foreground mt-0.5 italic">
                          {doc.reviewer_notes}
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <StatusBadge status={doc.status} />
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
                    {doc.status === "pending" && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-destructive hover:text-destructive"
                        disabled={deleteDoc.isPending}
                        onClick={() => deleteDoc.mutate(doc.id)}
                        aria-label={t("documents.delete")}
                      >
                        <Trash2 className="size-4" />
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}

function StatusBadge({ status }: { status: string }) {
  const { t } = useTranslation();
  const variants: Record<string, "secondary" | "default" | "destructive"> = {
    pending: "secondary",
    verified: "default",
    rejected: "destructive",
  };
  return (
    <Badge variant={variants[status] ?? "outline"}>
      {t(`documents.status.${status}`)}
    </Badge>
  );
}

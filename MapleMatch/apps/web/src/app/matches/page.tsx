"use client";

import { useState } from "react";
import { useTranslation } from "react-i18next";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useSmartMatch } from "@/hooks/useApi";
import type { SmartMatchResult } from "@/lib/api";
import {
  Sparkles,
  Clock,
  Target,
  Brain,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

export default function MatchesPage() {
  const { t } = useTranslation();
  const smartMatch = useSmartMatch();
  const [results, setResults] = useState<SmartMatchResult[]>([]);
  const [hasRun, setHasRun] = useState(false);

  const handleMatch = async () => {
    const data = await smartMatch.mutateAsync({
      use_semantic: false,
      use_ml: true,
      limit: 20,
    });
    setResults(data);
    setHasRun(true);
  };

  return (
    <main className="max-w-4xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Sparkles className="size-7" />
            {t("matches.title")}
          </h1>
          <p className="text-muted-foreground mt-1">
            {t("matches.subtitle")}
          </p>
        </div>
        <Button onClick={handleMatch} disabled={smartMatch.isPending} size="lg">
          {smartMatch.isPending
            ? t("common.loading")
            : t("matches.findMatches")}
        </Button>
      </div>

      {smartMatch.isError && (
        <Card className="border-destructive mb-4">
          <CardContent className="py-4">
            <p className="text-destructive" role="alert">
              {smartMatch.error.message}
            </p>
            {smartMatch.error.message.includes("profile") && (
              <Button asChild variant="outline" className="mt-2">
                <Link href="/eligibility">
                  {t("matches.completeProfile")}
                </Link>
              </Button>
            )}
          </CardContent>
        </Card>
      )}

      {smartMatch.isPending && (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-52 rounded-lg" />
          ))}
        </div>
      )}

      {hasRun && results.length === 0 && !smartMatch.isPending && (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            {t("matches.noResults")}
          </CardContent>
        </Card>
      )}

      {results.length > 0 && (
        <div className="space-y-4">
          {results.map((r, idx) => (
            <MatchCard key={r.listing_id} result={r} rank={idx + 1} />
          ))}
        </div>
      )}
    </main>
  );
}

function MatchCard({
  result,
  rank,
}: {
  result: SmartMatchResult;
  rank: number;
}) {
  const { t } = useTranslation();
  const [expanded, setExpanded] = useState(false);
  const pct = Math.round(result.final_score * 100);

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <span className="flex size-8 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-bold">
              {rank}
            </span>
            <div>
              <CardTitle className="text-lg">
                {result.listing_title}
              </CardTitle>
              <CardDescription className="flex items-center gap-2 mt-0.5">
                <Badge
                  variant={result.eligible ? "default" : "destructive"}
                >
                  {result.eligible
                    ? t("matches.eligible")
                    : t("matches.ineligible")}
                </Badge>
              </CardDescription>
            </div>
          </div>
          <div className="text-right">
            <span className="text-2xl font-bold">{pct}%</span>
            <p className="text-xs text-muted-foreground">
              {t("matches.matchScore")}
            </p>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Score bars */}
        <div className="grid grid-cols-3 gap-4">
          <ScoreBar
            icon={<Target className="size-3.5" />}
            label={t("matches.rules")}
            value={result.rule_score}
          />
          <ScoreBar
            icon={<Brain className="size-3.5" />}
            label={t("matches.semantic")}
            value={result.semantic_score}
          />
          <ScoreBar
            icon={<Sparkles className="size-3.5" />}
            label={t("matches.ml")}
            value={result.ml_score}
          />
        </div>

        {/* Wait time */}
        {result.wait_time_days != null && (
          <div className="flex items-center gap-2 text-sm rounded-md bg-muted px-3 py-2">
            <Clock className="size-4 text-muted-foreground" />
            <span>
              {t("matches.estimatedWait")}:{" "}
              <strong>
                ~{result.wait_time_days} {t("matches.days")}
              </strong>
              {result.wait_time_lower != null &&
                result.wait_time_upper != null && (
                  <span className="text-muted-foreground">
                    {" "}
                    ({result.wait_time_lower}–{result.wait_time_upper}{" "}
                    {t("matches.days")})
                  </span>
                )}
            </span>
            {result.wait_time_confidence != null && (
              <Badge variant="outline" className="ml-auto text-xs">
                {Math.round(result.wait_time_confidence * 100)}%{" "}
                {t("matches.confidence")}
              </Badge>
            )}
          </div>
        )}

        {/* Expandable details */}
        <Button
          variant="ghost"
          size="sm"
          className="w-full"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? (
            <ChevronUp className="size-4 mr-1" />
          ) : (
            <ChevronDown className="size-4 mr-1" />
          )}
          {expanded ? t("matches.hideDetails") : t("matches.showDetails")}
        </Button>

        {expanded && (
          <div className="space-y-3 text-sm">
            <Separator />
            <div>
              <h4 className="font-medium mb-1">
                {t("matches.scoringFactors")}
              </h4>
              {result.factors.map((f, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between py-1"
                >
                  <span>{f.name}</span>
                  <span className="text-muted-foreground">
                    {Math.round(f.score * 100)}% ×{" "}
                    {Math.round(f.weight * 100)}%
                  </span>
                </div>
              ))}
            </div>
            {result.wait_time_factors.length > 0 && (
              <div>
                <h4 className="font-medium mb-1">
                  {t("matches.waitFactors")}
                </h4>
                <ul className="list-disc ml-4 text-muted-foreground space-y-0.5">
                  {result.wait_time_factors.map((f, i) => (
                    <li key={i}>{f}</li>
                  ))}
                </ul>
              </div>
            )}
            <div>
              <h4 className="font-medium mb-1">
                {t("matches.explanation")}
              </h4>
              <pre className="whitespace-pre-wrap text-muted-foreground text-xs bg-muted p-2 rounded">
                {result.explanation}
              </pre>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function ScoreBar({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
}) {
  const pct = Math.round(value * 100);
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-1 text-xs text-muted-foreground">
        {icon}
        {label}
      </div>
      <Progress value={pct} className="h-2" />
      <span className="text-xs font-medium">{pct}%</span>
    </div>
  );
}

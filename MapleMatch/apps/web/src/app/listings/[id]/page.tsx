"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useListing, useCheckEligibility, useEstimateWaitTime } from "@/hooks/useApi";
import type { EligibilityCheckResult, WaitTimeResponse } from "@/lib/api";
import {
  MapPin,
  DollarSign,
  Bed,
  Bath,
  Accessibility,
  Clock,
  ChevronLeft,
  CheckCircle,
  XCircle,
} from "lucide-react";

export default function ListingDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { t } = useTranslation();
  const { data: listing, isLoading, isError } = useListing(id);
  const checkEligibility = useCheckEligibility();
  const estimateWait = useEstimateWaitTime();
  const [eligibility, setEligibility] = useState<EligibilityCheckResult | null>(null);
  const [waitTime, setWaitTime] = useState<WaitTimeResponse | null>(null);

  if (isLoading) return <LoadingSkeleton />;

  if (isError || !listing) {
    return (
      <main className="max-w-3xl mx-auto px-4 py-8">
        <p className="text-destructive">{t("common.error")}</p>
        <Button asChild variant="outline" className="mt-4">
          <Link href="/listings">
            <ChevronLeft className="size-4 mr-1" />
            {t("listings.backToListings")}
          </Link>
        </Button>
      </main>
    );
  }

  const amenities = listing.amenities
    ? listing.amenities.split(",").map((a) => a.trim()).filter(Boolean)
    : [];
  const priorityGroups = listing.priority_groups
    ? listing.priority_groups.split(",").map((p) => p.trim()).filter(Boolean)
    : [];

  return (
    <main className="max-w-3xl mx-auto px-4 py-8 space-y-6">
      <Button asChild variant="ghost" size="sm" className="-ml-2">
        <Link href="/listings">
          <ChevronLeft className="size-4 mr-1" />
          {t("listings.backToListings")}
        </Link>
      </Button>

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">{listing.title}</h1>
        <div className="flex items-center gap-1.5 text-muted-foreground mt-1">
          <MapPin className="size-4 shrink-0" />
          <span>
            {listing.address}, {listing.city}, {listing.province}{" "}
            {listing.postal_code}
          </span>
        </div>
        <div className="flex flex-wrap gap-2 mt-3">
          {listing.is_rgi && (
            <Badge variant="secondary">{t("listings.rgi")}</Badge>
          )}
          {listing.is_accessible && (
            <Badge variant="secondary">
              <Accessibility className="size-3 mr-0.5" />
              {t("listings.accessible")}
            </Badge>
          )}
          {listing.status !== "active" && (
            <Badge variant="outline">{listing.status}</Badge>
          )}
        </div>
      </div>

      {/* Key stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatBox
          icon={<DollarSign className="size-4" />}
          label={t("listings.rent")}
          value={`$${listing.rent_amount.toLocaleString()}/mo`}
        />
        <StatBox
          icon={<Bed className="size-4" />}
          label={t("listings.bedrooms")}
          value={String(listing.bedrooms)}
        />
        <StatBox
          icon={<Bath className="size-4" />}
          label={t("listings.bathrooms")}
          value={String(listing.bathrooms)}
        />
        {listing.estimated_wait_days != null && (
          <StatBox
            icon={<Clock className="size-4" />}
            label={t("listings.estWait")}
            value={`~${listing.estimated_wait_days} ${t("matches.days")}`}
          />
        )}
      </div>

      {/* Description */}
      {listing.description && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t("listings.description")}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{listing.description}</p>
          </CardContent>
        </Card>
      )}

      {/* Eligibility Requirements */}
      {(listing.max_income ||
        listing.min_household_size ||
        listing.max_household_size ||
        priorityGroups.length > 0) && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t("listings.requirements")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {listing.max_income && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">
                  {t("listings.maxIncome")}
                </span>
                <span className="font-medium">
                  ${listing.max_income.toLocaleString()}/yr
                </span>
              </div>
            )}
            {(listing.min_household_size || listing.max_household_size) && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">
                  {t("listings.householdSize")}
                </span>
                <span className="font-medium">
                  {listing.min_household_size ?? 1}–
                  {listing.max_household_size ?? "∞"} {t("listings.people")}
                </span>
              </div>
            )}
            {priorityGroups.length > 0 && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">
                  {t("listings.priorityGroups")}
                </span>
                <span className="font-medium capitalize">
                  {priorityGroups.join(", ")}
                </span>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Amenities */}
      {amenities.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t("listings.amenities")}</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {amenities.map((a) => (
                <Badge key={a} variant="outline">
                  {a}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* AI tools */}
      <div className="grid sm:grid-cols-2 gap-4">
        {/* Eligibility check */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              {t("listings.eligibilityCheck")}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {eligibility ? (
              <div>
                <div className="flex items-center gap-2 mb-2">
                  {eligibility.eligible ? (
                    <CheckCircle className="size-5 text-green-500" />
                  ) : (
                    <XCircle className="size-5 text-destructive" />
                  )}
                  <span className="font-medium">
                    {eligibility.eligible
                      ? t("listings.eligible")
                      : t("listings.ineligible")}
                  </span>
                  <span className="ml-auto text-sm text-muted-foreground">
                    {Math.round(eligibility.score * 100)}%
                  </span>
                </div>
                <ul className="text-xs text-muted-foreground list-disc ml-4 space-y-0.5">
                  {eligibility.reasons.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                {t("listings.eligibilityDesc")}
              </p>
            )}
            <Button
              size="sm"
              variant={eligibility ? "outline" : "default"}
              disabled={checkEligibility.isPending}
              onClick={async () => {
                const result = await checkEligibility.mutateAsync(id);
                setEligibility(result);
              }}
            >
              {checkEligibility.isPending
                ? t("common.loading")
                : t("listings.checkEligibility")}
            </Button>
            {checkEligibility.isError && (
              <p className="text-xs text-destructive">
                {checkEligibility.error.message}
              </p>
            )}
          </CardContent>
        </Card>

        {/* Wait time estimate */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              {t("listings.waitTimeEstimate")}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {waitTime ? (
              <div>
                <div className="text-2xl font-bold">
                  ~{waitTime.estimated_days}{" "}
                  <span className="text-sm font-normal text-muted-foreground">
                    {t("matches.days")}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground">
                  {waitTime.lower_bound_days}–{waitTime.upper_bound_days}{" "}
                  {t("matches.days")} ·{" "}
                  {Math.round(waitTime.confidence * 100)}%{" "}
                  {t("matches.confidence")}
                </p>
                {waitTime.factors.length > 0 && (
                  <ul className="text-xs text-muted-foreground mt-2 list-disc ml-4 space-y-0.5">
                    {waitTime.factors.map((f, i) => (
                      <li key={i}>{f}</li>
                    ))}
                  </ul>
                )}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                {t("listings.waitTimeDesc")}
              </p>
            )}
            <Button
              size="sm"
              variant={waitTime ? "outline" : "default"}
              disabled={estimateWait.isPending}
              onClick={async () => {
                const result = await estimateWait.mutateAsync(id);
                setWaitTime(result);
              }}
            >
              {estimateWait.isPending
                ? t("common.loading")
                : t("listings.estimateWait")}
            </Button>
            {estimateWait.isError && (
              <p className="text-xs text-destructive">
                {estimateWait.error.message}
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </main>
  );
}

function StatBox({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="flex flex-col gap-1 p-3 rounded-lg border bg-card">
      <div className="text-muted-foreground">{icon}</div>
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="font-semibold text-sm">{value}</div>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <main className="max-w-3xl mx-auto px-4 py-8 space-y-6">
      <Skeleton className="h-8 w-32" />
      <Skeleton className="h-10 w-2/3" />
      <div className="grid grid-cols-4 gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-20" />
        ))}
      </div>
      <Skeleton className="h-28" />
      <Skeleton className="h-36" />
      <div className="grid sm:grid-cols-2 gap-4">
        <Skeleton className="h-40" />
        <Skeleton className="h-40" />
      </div>
    </main>
  );
}

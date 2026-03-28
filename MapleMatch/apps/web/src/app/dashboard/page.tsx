"use client";

import { useUser } from "@clerk/nextjs";
import { useTranslation } from "react-i18next";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useMyProfile, useMyMatches } from "@/hooks/useApi";
import {
  ClipboardCheck,
  Home,
  Sparkles,
  ArrowRight,
} from "lucide-react";

export default function DashboardPage() {
  const { t } = useTranslation();
  const { user } = useUser();
  const profile = useMyProfile();
  const matches = useMyMatches();

  const hasProfile = !!profile.data;
  const matchCount = matches.data?.length ?? 0;
  const acceptedCount =
    matches.data?.filter((m) => m.status === "accepted").length ?? 0;

  return (
    <main className="max-w-5xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold">
        {t("dashboard.welcome", { name: user?.firstName ?? "" })}
      </h1>
      <p className="mt-1 text-muted-foreground">{t("dashboard.subtitle")}</p>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-8">
        {/* Profile Status */}
        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-1.5">
              <ClipboardCheck className="size-4" />
              {t("dashboard.profile")}
            </CardDescription>
            <CardTitle className="text-lg">
              {profile.isLoading ? (
                <Skeleton className="h-5 w-32" />
              ) : hasProfile ? (
                t("dashboard.profileComplete")
              ) : (
                t("dashboard.profileIncomplete")
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Button
              asChild
              variant={hasProfile ? "outline" : "default"}
              size="sm"
            >
              <Link href={hasProfile ? "/profile" : "/eligibility"}>
                {hasProfile
                  ? t("dashboard.updateProfile")
                  : t("dashboard.startProfile")}
                <ArrowRight className="size-3.5 ml-1" />
              </Link>
            </Button>
          </CardContent>
        </Card>

        {/* Matches */}
        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-1.5">
              <Sparkles className="size-4" />
              {t("dashboard.matches")}
            </CardDescription>
            <CardTitle className="text-lg">
              {matches.isLoading ? (
                <Skeleton className="h-5 w-20" />
              ) : (
                t("dashboard.matchCount", { count: matchCount })
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Button asChild variant="outline" size="sm">
              <Link href="/matches">
                {t("dashboard.viewMatches")}
                <ArrowRight className="size-3.5 ml-1" />
              </Link>
            </Button>
          </CardContent>
        </Card>

        {/* Listings */}
        <Card>
          <CardHeader className="pb-2">
            <CardDescription className="flex items-center gap-1.5">
              <Home className="size-4" />
              {t("dashboard.listings")}
            </CardDescription>
            <CardTitle className="text-lg">
              {matches.isLoading ? (
                <Skeleton className="h-5 w-24" />
              ) : (
                t("dashboard.acceptedCount", { count: acceptedCount })
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Button asChild variant="outline" size="sm">
              <Link href="/listings">
                {t("dashboard.browseListings")}
                <ArrowRight className="size-3.5 ml-1" />
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Prompt to complete profile if missing */}
      {!profile.isLoading && !hasProfile && (
        <Card className="mt-6 border-primary/30 bg-primary/5">
          <CardContent className="py-6 flex flex-col sm:flex-row items-center gap-4">
            <div className="flex-1">
              <h3 className="font-semibold">{t("dashboard.getStarted")}</h3>
              <p className="text-sm text-muted-foreground mt-1">
                {t("dashboard.getStartedDesc")}
              </p>
            </div>
            <Button asChild>
              <Link href="/eligibility">
                {t("dashboard.startProfile")}
                <ArrowRight className="size-4 ml-1" />
              </Link>
            </Button>
          </CardContent>
        </Card>
      )}
    </main>
  );
}

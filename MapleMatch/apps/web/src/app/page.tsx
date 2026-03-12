"use client";

import Link from "next/link";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";

export default function HomePage() {
  const { t } = useTranslation();

  return (
    <main className="flex flex-col items-center justify-center min-h-[calc(100vh-4rem)] px-4">
      <div className="max-w-3xl text-center space-y-6">
        <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
          {t("home.hero")}
        </h1>
        <p className="text-lg text-muted-foreground sm:text-xl">
          {t("home.subtitle")}
        </p>
        <div className="flex gap-4 justify-center">
          <Button asChild size="lg">
            <Link href="/sign-up">{t("home.cta")}</Link>
          </Button>
          <Button asChild variant="outline" size="lg">
            <Link href="/listings">{t("home.learnMore")}</Link>
          </Button>
        </div>
      </div>
    </main>
  );
}

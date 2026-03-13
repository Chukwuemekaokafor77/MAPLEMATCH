"use client";

import Link from "next/link";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import {
  Sparkles,
  ClipboardCheck,
  Search,
  Bell,
  Globe,
  Accessibility,
  ArrowRight,
  CheckCircle2,
} from "lucide-react";

const FEATURE_ICONS = [Sparkles, ClipboardCheck, Search, Bell, Globe, Accessibility] as const;

export default function HomePage() {
  const { t } = useTranslation();

  const featureKeys = ["ai", "wizard", "filters", "notifications", "bilingual", "accessible"] as const;

  const steps = [
    { num: 1, titleKey: "home.howItWorks.step1Title", descKey: "home.howItWorks.step1Desc" },
    { num: 2, titleKey: "home.howItWorks.step2Title", descKey: "home.howItWorks.step2Desc" },
    { num: 3, titleKey: "home.howItWorks.step3Title", descKey: "home.howItWorks.step3Desc" },
  ];

  return (
    <main>
      {/* ── Hero ── */}
      <section className="relative overflow-hidden">
        <div
          className="absolute inset-0 -z-10"
          style={{
            background:
              "radial-gradient(ellipse 80% 60% at 50% -10%, color-mix(in oklch, var(--color-primary), transparent 82%), transparent 70%)",
          }}
        />
        <div className="mx-auto max-w-5xl px-4 py-24 sm:py-36 text-center">
          <div className="inline-flex items-center gap-2 rounded-full border bg-background/80 px-4 py-1.5 text-sm text-muted-foreground mb-6 backdrop-blur">
            <CheckCircle2 className="size-3.5 text-primary" />
            AI-powered · Bilingual · WCAG compliant
          </div>
          <h1 className="text-4xl font-bold tracking-tight sm:text-6xl lg:text-7xl text-balance">
            {t("home.hero")}
          </h1>
          <p className="mt-6 text-lg text-muted-foreground sm:text-xl max-w-2xl mx-auto text-balance">
            {t("home.subtitle")}
          </p>
          <div className="mt-10 flex flex-col sm:flex-row gap-3 justify-center">
            <Button asChild size="lg" className="text-base h-12 px-8">
              <Link href="/sign-up">
                {t("home.cta")}
                <ArrowRight className="size-4 ml-1" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="text-base h-12 px-8">
              <Link href="/listings">{t("home.learnMore")}</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* ── Stats bar ── */}
      <section className="border-y bg-muted/50">
        <div className="mx-auto max-w-5xl px-4 py-10 grid grid-cols-3 gap-6 text-center">
          {(["listings", "provinces", "free"] as const).map((key) => (
            <div key={key}>
              <p className="text-3xl sm:text-4xl font-bold text-primary">
                {t(`home.stats.${key}`)}
              </p>
              <p className="mt-1 text-sm text-muted-foreground">
                {t(`home.stats.${key}Label`)}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Features ── */}
      <section className="mx-auto max-w-6xl px-4 py-20 sm:py-28">
        <div className="text-center mb-14">
          <h2 className="text-3xl font-bold sm:text-4xl">{t("home.features.title")}</h2>
          <p className="mt-4 text-muted-foreground text-lg max-w-2xl mx-auto">
            {t("home.features.subtitle")}
          </p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {featureKeys.map((key, i) => {
            const Icon = FEATURE_ICONS[i];
            return (
              <Card key={key} className="group hover:shadow-md transition-shadow">
                <CardHeader className="pb-3">
                  <div className="size-10 rounded-lg bg-primary/10 flex items-center justify-center mb-3 group-hover:bg-primary/15 transition-colors">
                    <Icon className="size-5 text-primary" />
                  </div>
                  <CardTitle className="text-base">
                    {t(`home.features.${key}.title`)}
                  </CardTitle>
                  <CardDescription className="leading-relaxed">
                    {t(`home.features.${key}.desc`)}
                  </CardDescription>
                </CardHeader>
              </Card>
            );
          })}
        </div>
      </section>

      {/* ── How it works ── */}
      <section className="bg-muted/50 border-y">
        <div className="mx-auto max-w-5xl px-4 py-20 sm:py-28">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold sm:text-4xl">{t("home.howItWorks.title")}</h2>
            <p className="mt-4 text-muted-foreground text-lg">{t("home.howItWorks.subtitle")}</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-10">
            {steps.map(({ num, titleKey, descKey }) => (
              <div key={num} className="text-center">
                <div className="size-14 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-2xl font-bold mx-auto mb-5 shadow-sm">
                  {num}
                </div>
                <h3 className="font-semibold text-lg mb-2">{t(titleKey)}</h3>
                <p className="text-muted-foreground text-sm leading-relaxed">{t(descKey)}</p>
              </div>
            ))}
          </div>
          {/* connector lines (desktop only) */}
          <div className="hidden md:flex items-center justify-center mt-0 -translate-y-full pointer-events-none select-none" aria-hidden>
          </div>
        </div>
      </section>

      {/* ── Final CTA ── */}
      <section className="bg-primary text-primary-foreground">
        <div className="mx-auto max-w-3xl px-4 py-20 sm:py-28 text-center">
          <h2 className="text-3xl font-bold sm:text-4xl">{t("home.finalCta.title")}</h2>
          <p className="mt-5 text-lg opacity-85 max-w-xl mx-auto">
            {t("home.finalCta.subtitle")}
          </p>
          <Button
            asChild
            size="lg"
            className="mt-10 h-12 px-8 text-base bg-white text-primary hover:bg-white/90 shadow-sm"
          >
            <Link href="/sign-up">
              {t("home.finalCta.button")}
              <ArrowRight className="size-4 ml-1" />
            </Link>
          </Button>
        </div>
      </section>
    </main>
  );
}

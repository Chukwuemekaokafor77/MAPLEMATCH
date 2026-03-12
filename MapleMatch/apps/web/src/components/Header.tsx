"use client";

import Link from "next/link";
import {
  useAuth,
  UserButton,
  SignInButton,
  SignUpButton,
} from "@clerk/clerk-react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import LanguageSwitcher from "@/components/LanguageSwitcher";
import NotificationBell from "@/components/NotificationBell";

export default function Header() {
  const { t } = useTranslation();
  const { isSignedIn, isLoaded } = useAuth();

  return (
    <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur">
      <nav
        className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4"
        aria-label={t("a11y.mainNavigation")}
      >
        <Link href="/" className="text-xl font-bold">
          🍁 {t("app.name")}
        </Link>

        <div className="flex items-center gap-2">
          <LanguageSwitcher />

          {isLoaded && isSignedIn ? (
            <>
              <Button asChild variant="ghost" size="sm">
                <Link href="/dashboard">{t("nav.dashboard")}</Link>
              </Button>
              <Button asChild variant="ghost" size="sm">
                <Link href="/listings">{t("nav.listings")}</Link>
              </Button>
              <Button asChild variant="ghost" size="sm">
                <Link href="/matches">{t("nav.matches")}</Link>
              </Button>
              <NotificationBell />
              <UserButton />
            </>
          ) : isLoaded ? (
            <>
              <Button asChild variant="ghost" size="sm">
                <Link href="/listings">{t("nav.listings")}</Link>
              </Button>
              <SignInButton mode="redirect">
                <Button variant="ghost" size="sm">
                  {t("nav.signIn")}
                </Button>
              </SignInButton>
              <SignUpButton mode="redirect">
                <Button size="sm">{t("nav.signUp")}</Button>
              </SignUpButton>
            </>
          ) : null}
        </div>
      </nav>
    </header>
  );
}

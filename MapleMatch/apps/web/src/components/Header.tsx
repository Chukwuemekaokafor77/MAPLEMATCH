"use client";

import { useState } from "react";
import Link from "next/link";
import {
  useAuth,
  UserButton,
  SignInButton,
  SignUpButton,
} from "@clerk/clerk-react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import LanguageSwitcher from "@/components/LanguageSwitcher";
import NotificationBell from "@/components/NotificationBell";
import { Menu, X } from "lucide-react";

export default function Header() {
  const { t } = useTranslation();
  const { isSignedIn, isLoaded } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);

  const close = () => setMenuOpen(false);

  return (
    <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur">
      <nav
        className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4"
        aria-label={t("a11y.mainNavigation")}
      >
        {/* Brand */}
        <Link href="/" className="text-xl font-bold flex items-center gap-1.5" onClick={close}>
          🍁 {t("app.name")}
        </Link>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-1">
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

        {/* Mobile controls */}
        <div className="flex md:hidden items-center gap-1">
          <LanguageSwitcher />
          {isLoaded && isSignedIn && <NotificationBell />}
          <Button
            variant="ghost"
            size="sm"
            aria-label={menuOpen ? t("a11y.closeMenu") : t("a11y.openMenu")}
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((v) => !v)}
            className="px-2"
          >
            {menuOpen ? <X className="size-5" /> : <Menu className="size-5" />}
          </Button>
        </div>
      </nav>

      {/* Mobile drawer */}
      {menuOpen && (
        <div className="md:hidden border-t bg-background/98 backdrop-blur px-4 py-3 space-y-1">
          {isLoaded && isSignedIn ? (
            <>
              <Button asChild variant="ghost" className="w-full justify-start" onClick={close}>
                <Link href="/dashboard">{t("nav.dashboard")}</Link>
              </Button>
              <Button asChild variant="ghost" className="w-full justify-start" onClick={close}>
                <Link href="/listings">{t("nav.listings")}</Link>
              </Button>
              <Button asChild variant="ghost" className="w-full justify-start" onClick={close}>
                <Link href="/matches">{t("nav.matches")}</Link>
              </Button>
              <Separator className="my-2" />
              <div className="px-1 py-1">
                <UserButton />
              </div>
            </>
          ) : isLoaded ? (
            <>
              <Button asChild variant="ghost" className="w-full justify-start" onClick={close}>
                <Link href="/listings">{t("nav.listings")}</Link>
              </Button>
              <Separator className="my-2" />
              <SignInButton mode="redirect">
                <Button variant="ghost" className="w-full justify-start" onClick={close}>
                  {t("nav.signIn")}
                </Button>
              </SignInButton>
              <SignUpButton mode="redirect">
                <Button className="w-full" onClick={close}>
                  {t("nav.signUp")}
                </Button>
              </SignUpButton>
            </>
          ) : null}
        </div>
      )}
    </header>
  );
}

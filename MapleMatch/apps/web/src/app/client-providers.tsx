"use client";

import { ClerkProvider } from "@clerk/clerk-react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";
import Header from "@/components/Header";
import "@/i18n";

const CLERK_KEY = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

export default function ClientProviders({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { staleTime: 30_000, retry: 1 },
        },
      })
  );

  const content = (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-background text-foreground">
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:p-4 focus:bg-background focus:text-foreground"
        >
          Skip to main content
        </a>
        <Header />
        <div id="main-content">{children}</div>
      </div>
    </QueryClientProvider>
  );

  if (!CLERK_KEY) {
    return content;
  }

  return (
    <ClerkProvider publishableKey={CLERK_KEY}>{content}</ClerkProvider>
  );
}

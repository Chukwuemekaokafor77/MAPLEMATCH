import "@/index.css";
import type { Metadata } from "next";
import { ClerkProvider } from "@clerk/nextjs";
import ClientProviders from "./client-providers";

export const metadata: Metadata = {
  title: "MapleMatch — Affordable Housing in Canada",
  description:
    "AI-powered affordable housing matching platform for Canada",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider>
      <html lang="en" suppressHydrationWarning>
        <body className="antialiased">
          <ClientProviders>{children}</ClientProviders>
        </body>
      </html>
    </ClerkProvider>
  );
}

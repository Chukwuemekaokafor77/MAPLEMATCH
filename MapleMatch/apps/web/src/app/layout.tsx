import "@/index.css";
import type { Metadata } from "next";

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
    <html lang="en" suppressHydrationWarning>
      <body>
        <ClientProviders>{children}</ClientProviders>
      </body>
    </html>
  );
}

import ClientProviders from "./client-providers";

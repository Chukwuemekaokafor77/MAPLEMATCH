"use client";

import { SignIn } from "@clerk/clerk-react";

export default function SignInPage() {
  return (
    <main className="flex items-center justify-center min-h-[calc(100vh-4rem)] px-4">
      <SignIn routing="path" path="/sign-in" />
    </main>
  );
}

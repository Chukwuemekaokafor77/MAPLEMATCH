"use client";

import { SignUp } from "@clerk/nextjs";

export default function SignUpPage() {
  return (
    <main className="flex items-center justify-center min-h-[calc(100vh-4rem)] px-4">
      <SignUp routing="path" path="/sign-up" />
    </main>
  );
}

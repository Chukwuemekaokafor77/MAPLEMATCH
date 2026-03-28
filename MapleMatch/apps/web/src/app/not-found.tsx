import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function NotFound() {
  return (
    <main className="flex flex-col items-center justify-center min-h-[calc(100vh-4rem)] text-center px-4">
      <p className="text-9xl font-black text-primary/10 select-none">404</p>
      <h1 className="text-2xl font-bold mt-2">Page not found</h1>
      <p className="text-muted-foreground mt-2 max-w-sm text-sm">
        The page you&apos;re looking for doesn&apos;t exist or has been moved.
      </p>
      <div className="flex gap-3 mt-6">
        <Button asChild>
          <Link href="/">Go Home</Link>
        </Button>
        <Button asChild variant="outline">
          <Link href="/listings">Browse Listings</Link>
        </Button>
      </div>
    </main>
  );
}

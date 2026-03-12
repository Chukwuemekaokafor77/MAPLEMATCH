import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { I18nextProvider } from "react-i18next";
import i18n from "@/i18n";

// Mock Clerk
vi.mock("@clerk/clerk-react", () => ({
  useAuth: () => ({ isSignedIn: false, isLoaded: true, getToken: vi.fn() }),
  useUser: () => ({ user: null }),
  UserButton: () => <div data-testid="user-button" />,
  SignInButton: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  SignUpButton: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  ClerkProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  SignIn: () => <div data-testid="sign-in" />,
  SignUp: () => <div data-testid="sign-up" />,
}));

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), back: vi.fn() }),
  usePathname: () => "/",
  useSearchParams: () => new URLSearchParams(),
}));

// Mock next/link
vi.mock("next/link", () => ({
  default: ({ children, href, ...props }: { children: React.ReactNode; href: string; [key: string]: unknown }) => (
    <a href={href} {...props}>{children}</a>
  ),
}));

// Mock React Query
vi.mock("@tanstack/react-query", () => ({
  QueryClientProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  QueryClient: vi.fn(),
  useQuery: () => ({ data: undefined, isLoading: false, error: null }),
  useMutation: () => ({ mutate: vi.fn(), isLoading: false }),
  useQueryClient: () => ({ invalidateQueries: vi.fn() }),
}));

function Wrapper({ children }: { children: React.ReactNode }) {
  return (
    <I18nextProvider i18n={i18n}>
      {children}
    </I18nextProvider>
  );
}

beforeEach(() => {
  i18n.changeLanguage("en");
});

// ===== HomePage =====

describe("HomePage", () => {
  it("renders hero text in English", async () => {
    const { default: HomePage } = await import("@/app/page");
    render(<HomePage />, { wrapper: Wrapper });
    expect(screen.getByText("Find Your Affordable Home in Canada")).toBeInTheDocument();
  });

  it("renders CTA buttons", async () => {
    const { default: HomePage } = await import("@/app/page");
    render(<HomePage />, { wrapper: Wrapper });
    expect(screen.getByText("Get Started")).toBeInTheDocument();
    expect(screen.getByText("Learn More")).toBeInTheDocument();
  });
});

// ===== LanguageSwitcher =====

describe("LanguageSwitcher", () => {
  it("shows FR button when language is English", async () => {
    const { default: LanguageSwitcher } = await import("@/components/LanguageSwitcher");
    render(<LanguageSwitcher />, { wrapper: Wrapper });
    expect(screen.getByText("FR")).toBeInTheDocument();
  });

  it("switches language on click", async () => {
    const user = userEvent.setup();
    const { default: LanguageSwitcher } = await import("@/components/LanguageSwitcher");
    render(<LanguageSwitcher />, { wrapper: Wrapper });

    const button = screen.getByText("FR");
    await user.click(button);
    expect(i18n.language).toBe("fr");
  });

  it("has accessible label", async () => {
    const { default: LanguageSwitcher } = await import("@/components/LanguageSwitcher");
    render(<LanguageSwitcher />, { wrapper: Wrapper });
    expect(screen.getByLabelText("Switch language")).toBeInTheDocument();
  });
});

// ===== i18n Parity =====

describe("i18n translations", () => {
  it("has all English keys in French", () => {
    const enKeys = Object.keys(i18n.getResourceBundle("en", "translation"));
    const frKeys = Object.keys(i18n.getResourceBundle("fr", "translation"));
    for (const key of enKeys) {
      expect(frKeys).toContain(key);
    }
  });

  it("has all French keys in English", () => {
    const enKeys = Object.keys(i18n.getResourceBundle("en", "translation"));
    const frKeys = Object.keys(i18n.getResourceBundle("fr", "translation"));
    for (const key of frKeys) {
      expect(enKeys).toContain(key);
    }
  });
});

// ===== API client =====

describe("API client", () => {
  it("exports api object with expected methods", async () => {
    const { api } = await import("@/lib/api");
    expect(api).toBeDefined();
    expect(typeof api.getMe).toBe("function");
    expect(typeof api.getListings).toBe("function");
    expect(typeof api.smartMatch).toBe("function");
    expect(typeof api.getNotifications).toBe("function");
    expect(typeof api.getUnreadCount).toBe("function");
    expect(typeof api.markNotificationsRead).toBe("function");
    expect(typeof api.deleteNotification).toBe("function");
  });

  it("ApiError has correct properties", async () => {
    const { ApiError } = await import("@/lib/api");
    const err = new ApiError(404, "Not Found");
    expect(err.status).toBe(404);
    expect(err.message).toBe("Not Found");
    expect(err.name).toBe("ApiError");
  });
});

// ===== Accessibility =====

describe("Accessibility", () => {
  it("HomePage has main landmark", async () => {
    const { default: HomePage } = await import("@/app/page");
    render(<HomePage />, { wrapper: Wrapper });
    expect(screen.getByRole("main")).toBeInTheDocument();
  });

  it("HomePage heading hierarchy starts at h1", async () => {
    const { default: HomePage } = await import("@/app/page");
    render(<HomePage />, { wrapper: Wrapper });
    const h1 = screen.getByRole("heading", { level: 1 });
    expect(h1).toBeInTheDocument();
  });

  it("Links are keyboard accessible", async () => {
    const { default: HomePage } = await import("@/app/page");
    render(<HomePage />, { wrapper: Wrapper });
    const links = screen.getAllByRole("link");
    expect(links.length).toBeGreaterThan(0);
    for (const link of links) {
      expect(link).toHaveAttribute("href");
    }
  });
});

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { I18nextProvider } from "react-i18next";
import i18n from "@/i18n";

// ─── Controllable auth state ──────────────────────────────────────
const mockAuthState = { isSignedIn: false, isLoaded: true, getToken: vi.fn() };

// ─── Module mocks ─────────────────────────────────────────────────
vi.mock("@clerk/clerk-react", () => ({
  useAuth: () => mockAuthState,
  useUser: () => ({ user: mockAuthState.isSignedIn ? { firstName: "Alex" } : null }),
  UserButton: () => <div data-testid="user-button" />,
  SignInButton: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  SignUpButton: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  ClerkProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  SignIn: () => <div data-testid="sign-in" />,
  SignUp: () => <div data-testid="sign-up" />,
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), back: vi.fn() }),
  usePathname: () => "/",
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("next/link", () => ({
  default: ({
    children,
    href,
    ...props
  }: {
    children: React.ReactNode;
    href: string;
    [key: string]: unknown;
  }) => (
    <a href={href} {...props}>
      {children}
    </a>
  ),
}));

vi.mock("@tanstack/react-query", () => ({
  QueryClientProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  QueryClient: vi.fn(),
  useQuery: () => ({ data: undefined, isLoading: false, isError: false, error: null }),
  useMutation: () => ({
    mutate: vi.fn(),
    mutateAsync: vi.fn().mockResolvedValue([]),
    isPending: false,
    isError: false,
    error: null,
  }),
  useQueryClient: () => ({ invalidateQueries: vi.fn() }),
}));

// ─── Test wrapper ─────────────────────────────────────────────────
function Wrapper({ children }: { children: React.ReactNode }) {
  return <I18nextProvider i18n={i18n}>{children}</I18nextProvider>;
}

beforeEach(() => {
  i18n.changeLanguage("en");
  mockAuthState.isSignedIn = false;
  mockAuthState.isLoaded = true;
});

afterEach(() => {
  mockAuthState.isSignedIn = false;
});

// ══════════════════════════════════════════════════════════════════
// HomePage
// ══════════════════════════════════════════════════════════════════

describe("HomePage", () => {
  it("renders hero heading in English", async () => {
    const { default: HomePage } = await import("@/app/page");
    render(<HomePage />, { wrapper: Wrapper });
    expect(
      screen.getByRole("heading", { level: 1, name: /find your affordable home/i })
    ).toBeInTheDocument();
  });

  it("renders hero heading in French after language switch", async () => {
    i18n.changeLanguage("fr");
    const { default: HomePage } = await import("@/app/page");
    render(<HomePage />, { wrapper: Wrapper });
    expect(
      screen.getByRole("heading", { level: 1, name: /trouvez votre logement/i })
    ).toBeInTheDocument();
  });

  it("renders Get Started Free CTA linking to /sign-up", async () => {
    const { default: HomePage } = await import("@/app/page");
    render(<HomePage />, { wrapper: Wrapper });
    const cta = screen.getByRole("link", { name: /get started free/i });
    expect(cta).toHaveAttribute("href", "/sign-up");
  });

  it("renders Browse Listings CTA linking to /listings", async () => {
    const { default: HomePage } = await import("@/app/page");
    render(<HomePage />, { wrapper: Wrapper });
    const link = screen.getByRole("link", { name: /browse listings/i });
    expect(link).toHaveAttribute("href", "/listings");
  });

  it("renders stats section: listings, provinces, free", async () => {
    const { default: HomePage } = await import("@/app/page");
    render(<HomePage />, { wrapper: Wrapper });
    expect(screen.getByText("10,000+")).toBeInTheDocument();
    expect(screen.getByText("13")).toBeInTheDocument();
    expect(screen.getByText("100% Free")).toBeInTheDocument();
  });

  it("renders stats labels", async () => {
    const { default: HomePage } = await import("@/app/page");
    render(<HomePage />, { wrapper: Wrapper });
    expect(screen.getByText("Available Listings")).toBeInTheDocument();
    expect(screen.getByText("Provinces & Territories")).toBeInTheDocument();
    expect(screen.getByText("For Applicants")).toBeInTheDocument();
  });

  it("renders all 6 feature card titles", async () => {
    const { default: HomePage } = await import("@/app/page");
    render(<HomePage />, { wrapper: Wrapper });
    expect(screen.getByText("AI-Powered Matching")).toBeInTheDocument();
    expect(screen.getByText("Eligibility Wizard")).toBeInTheDocument();
    expect(screen.getByText("Smart Search")).toBeInTheDocument();
    expect(screen.getByText("Instant Alerts")).toBeInTheDocument();
    expect(screen.getByText("Fully Bilingual")).toBeInTheDocument();
    expect(screen.getByText("Accessible by Design")).toBeInTheDocument();
  });

  it("renders How It Works section heading", async () => {
    const { default: HomePage } = await import("@/app/page");
    render(<HomePage />, { wrapper: Wrapper });
    expect(screen.getByText("How It Works")).toBeInTheDocument();
  });

  it("renders all 3 how-it-works step titles", async () => {
    const { default: HomePage } = await import("@/app/page");
    render(<HomePage />, { wrapper: Wrapper });
    expect(screen.getByText("Create Your Profile")).toBeInTheDocument();
    expect(screen.getByText("Get Matched Instantly")).toBeInTheDocument();
    expect(screen.getByText("Apply with Confidence")).toBeInTheDocument();
  });

  it("renders How It Works step numbers 1-3", async () => {
    const { default: HomePage } = await import("@/app/page");
    render(<HomePage />, { wrapper: Wrapper });
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("renders final CTA heading", async () => {
    const { default: HomePage } = await import("@/app/page");
    render(<HomePage />, { wrapper: Wrapper });
    expect(screen.getByText("Ready to Find Your Home?")).toBeInTheDocument();
  });

  it("final CTA sign-up link points to /sign-up", async () => {
    const { default: HomePage } = await import("@/app/page");
    render(<HomePage />, { wrapper: Wrapper });
    const links = screen.getAllByRole("link", { name: /get started/i });
    expect(links.some((l) => l.getAttribute("href") === "/sign-up")).toBe(true);
  });

  it("renders French stats label after language switch", async () => {
    i18n.changeLanguage("fr");
    const { default: HomePage } = await import("@/app/page");
    render(<HomePage />, { wrapper: Wrapper });
    expect(screen.getByText("Pour les candidats")).toBeInTheDocument();
  });

  it("renders French feature titles after language switch", async () => {
    i18n.changeLanguage("fr");
    const { default: HomePage } = await import("@/app/page");
    render(<HomePage />, { wrapper: Wrapper });
    expect(screen.getByText("Jumelage par IA")).toBeInTheDocument();
    expect(screen.getByText("Recherche intelligente")).toBeInTheDocument();
  });
});

// ══════════════════════════════════════════════════════════════════
// Header — signed out
// ══════════════════════════════════════════════════════════════════

describe("Header (signed out)", () => {
  it("renders brand name linking to /", async () => {
    const { default: Header } = await import("@/components/Header");
    render(<Header />, { wrapper: Wrapper });
    const brand = screen.getByRole("link", { name: /maplematch/i });
    expect(brand).toHaveAttribute("href", "/");
  });

  it("shows Sign In and Sign Up when signed out", async () => {
    const { default: Header } = await import("@/components/Header");
    render(<Header />, { wrapper: Wrapper });
    expect(screen.getByText("Sign In")).toBeInTheDocument();
    expect(screen.getByText("Sign Up")).toBeInTheDocument();
  });

  it("does not show Dashboard or My Matches when signed out", async () => {
    const { default: Header } = await import("@/components/Header");
    render(<Header />, { wrapper: Wrapper });
    expect(screen.queryByText("Dashboard")).not.toBeInTheDocument();
    expect(screen.queryByText("My Matches")).not.toBeInTheDocument();
  });

  it("mobile menu button starts with aria-expanded=false", async () => {
    const { default: Header } = await import("@/components/Header");
    render(<Header />, { wrapper: Wrapper });
    const btn = screen.getByRole("button", { name: /open menu/i });
    expect(btn).toHaveAttribute("aria-expanded", "false");
  });

  it("mobile menu opens on click and aria-expanded becomes true", async () => {
    const user = userEvent.setup();
    const { default: Header } = await import("@/components/Header");
    render(<Header />, { wrapper: Wrapper });
    const btn = screen.getByRole("button", { name: /open menu/i });
    await user.click(btn);
    expect(btn).toHaveAttribute("aria-expanded", "true");
  });

  it("mobile menu shows Sign Up in the drawer", async () => {
    const user = userEvent.setup();
    const { default: Header } = await import("@/components/Header");
    render(<Header />, { wrapper: Wrapper });
    await user.click(screen.getByRole("button", { name: /open menu/i }));
    expect(screen.getAllByText("Sign Up").length).toBeGreaterThanOrEqual(1);
  });

  it("mobile menu closes on second click", async () => {
    const user = userEvent.setup();
    const { default: Header } = await import("@/components/Header");
    render(<Header />, { wrapper: Wrapper });
    const btn = screen.getByRole("button", { name: /open menu/i });
    await user.click(btn);
    await user.click(btn);
    expect(btn).toHaveAttribute("aria-expanded", "false");
  });
});

// ══════════════════════════════════════════════════════════════════
// Header — signed in
// ══════════════════════════════════════════════════════════════════

describe("Header (signed in)", () => {
  beforeEach(() => {
    mockAuthState.isSignedIn = true;
  });

  it("shows Dashboard and My Matches links", async () => {
    const { default: Header } = await import("@/components/Header");
    render(<Header />, { wrapper: Wrapper });
    expect(screen.getByRole("link", { name: "Dashboard" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "My Matches" })).toBeInTheDocument();
  });

  it("does not show Sign In or Sign Up when signed in", async () => {
    const { default: Header } = await import("@/components/Header");
    render(<Header />, { wrapper: Wrapper });
    expect(screen.queryByText("Sign In")).not.toBeInTheDocument();
    expect(screen.queryByText("Sign Up")).not.toBeInTheDocument();
  });

  it("renders UserButton when signed in", async () => {
    const { default: Header } = await import("@/components/Header");
    render(<Header />, { wrapper: Wrapper });
    expect(screen.getAllByTestId("user-button").length).toBeGreaterThan(0);
  });

  it("mobile drawer shows Dashboard link when signed in", async () => {
    const user = userEvent.setup();
    const { default: Header } = await import("@/components/Header");
    render(<Header />, { wrapper: Wrapper });
    await user.click(screen.getByRole("button", { name: /open menu/i }));
    expect(screen.getAllByText("Dashboard").length).toBeGreaterThan(0);
  });

  it("mobile drawer shows My Matches link when signed in", async () => {
    const user = userEvent.setup();
    const { default: Header } = await import("@/components/Header");
    render(<Header />, { wrapper: Wrapper });
    await user.click(screen.getByRole("button", { name: /open menu/i }));
    expect(screen.getAllByText("My Matches").length).toBeGreaterThan(0);
  });
});

// ══════════════════════════════════════════════════════════════════
// Header accessibility
// ══════════════════════════════════════════════════════════════════

describe("Header accessibility", () => {
  it("nav element has aria-label for main navigation", async () => {
    const { default: Header } = await import("@/components/Header");
    render(<Header />, { wrapper: Wrapper });
    expect(screen.getByRole("navigation", { name: /main navigation/i })).toBeInTheDocument();
  });
});

// ══════════════════════════════════════════════════════════════════
// LanguageSwitcher
// ══════════════════════════════════════════════════════════════════

describe("LanguageSwitcher", () => {
  it("shows FR when language is English", async () => {
    const { default: LanguageSwitcher } = await import("@/components/LanguageSwitcher");
    render(<LanguageSwitcher />, { wrapper: Wrapper });
    expect(screen.getByText("FR")).toBeInTheDocument();
  });

  it("shows EN when language is French", async () => {
    i18n.changeLanguage("fr");
    const { default: LanguageSwitcher } = await import("@/components/LanguageSwitcher");
    render(<LanguageSwitcher />, { wrapper: Wrapper });
    expect(screen.getByText("EN")).toBeInTheDocument();
  });

  it("switches to French on click", async () => {
    const user = userEvent.setup();
    const { default: LanguageSwitcher } = await import("@/components/LanguageSwitcher");
    render(<LanguageSwitcher />, { wrapper: Wrapper });
    await user.click(screen.getByText("FR"));
    expect(i18n.language).toBe("fr");
  });

  it("switches back to English from French", async () => {
    i18n.changeLanguage("fr");
    const user = userEvent.setup();
    const { default: LanguageSwitcher } = await import("@/components/LanguageSwitcher");
    render(<LanguageSwitcher />, { wrapper: Wrapper });
    await user.click(screen.getByText("EN"));
    expect(i18n.language).toBe("en");
  });

  it("has accessible aria-label", async () => {
    const { default: LanguageSwitcher } = await import("@/components/LanguageSwitcher");
    render(<LanguageSwitcher />, { wrapper: Wrapper });
    expect(screen.getByLabelText("Switch language")).toBeInTheDocument();
  });
});

// ══════════════════════════════════════════════════════════════════
// i18n parity
// ══════════════════════════════════════════════════════════════════

describe("i18n translations", () => {
  function flatKeys(obj: Record<string, unknown>, prefix = ""): string[] {
    return Object.entries(obj).flatMap(([k, v]) => {
      const full = prefix ? `${prefix}.${k}` : k;
      return v !== null && typeof v === "object" && !Array.isArray(v)
        ? flatKeys(v as Record<string, unknown>, full)
        : [full];
    });
  }

  it("top-level keys match between EN and FR", () => {
    const en = Object.keys(i18n.getResourceBundle("en", "translation"));
    const fr = Object.keys(i18n.getResourceBundle("fr", "translation"));
    expect(en.sort()).toEqual(fr.sort());
  });

  it("every deep EN key exists in FR", () => {
    const en = flatKeys(i18n.getResourceBundle("en", "translation"));
    const fr = new Set(flatKeys(i18n.getResourceBundle("fr", "translation")));
    for (const key of en) {
      expect(fr.has(key), `Missing FR key: ${key}`).toBe(true);
    }
  });

  it("every deep FR key exists in EN", () => {
    const fr = flatKeys(i18n.getResourceBundle("fr", "translation"));
    const en = new Set(flatKeys(i18n.getResourceBundle("en", "translation")));
    for (const key of fr) {
      expect(en.has(key), `Missing EN key: ${key}`).toBe(true);
    }
  });

  it("homepage stats keys resolve in both languages", () => {
    const keys = ["listings", "listingsLabel", "provinces", "provincesLabel", "free", "freeLabel"];
    for (const k of keys) {
      expect(i18n.t(`home.stats.${k}`, { lng: "en" })).not.toBe(`home.stats.${k}`);
      expect(i18n.t(`home.stats.${k}`, { lng: "fr" })).not.toBe(`home.stats.${k}`);
    }
  });

  it("homepage feature titles resolve in both languages", () => {
    const keys = ["ai", "wizard", "filters", "notifications", "bilingual", "accessible"];
    for (const k of keys) {
      expect(i18n.t(`home.features.${k}.title`, { lng: "en" })).not.toBe(`home.features.${k}.title`);
      expect(i18n.t(`home.features.${k}.title`, { lng: "fr" })).not.toBe(`home.features.${k}.title`);
    }
  });

  it("howItWorks step keys resolve in both languages", () => {
    const keys = ["title", "subtitle", "step1Title", "step2Title", "step3Title"];
    for (const k of keys) {
      expect(i18n.t(`home.howItWorks.${k}`, { lng: "en" })).not.toBe(`home.howItWorks.${k}`);
      expect(i18n.t(`home.howItWorks.${k}`, { lng: "fr" })).not.toBe(`home.howItWorks.${k}`);
    }
  });

  it("finalCta keys resolve in both languages", () => {
    for (const k of ["title", "subtitle", "button"]) {
      expect(i18n.t(`home.finalCta.${k}`, { lng: "en" })).not.toBe(`home.finalCta.${k}`);
      expect(i18n.t(`home.finalCta.${k}`, { lng: "fr" })).not.toBe(`home.finalCta.${k}`);
    }
  });

  it("French and English hero text differ", () => {
    const en = i18n.t("home.hero", { lng: "en" });
    const fr = i18n.t("home.hero", { lng: "fr" });
    expect(fr).not.toBe(en);
  });

  it("mobile menu a11y keys are correct in both languages", () => {
    expect(i18n.t("a11y.openMenu", { lng: "en" })).toBe("Open menu");
    expect(i18n.t("a11y.closeMenu", { lng: "en" })).toBe("Close menu");
    expect(i18n.t("a11y.openMenu", { lng: "fr" })).toBe("Ouvrir le menu");
    expect(i18n.t("a11y.closeMenu", { lng: "fr" })).toBe("Fermer le menu");
  });
});

// ══════════════════════════════════════════════════════════════════
// API client
// ══════════════════════════════════════════════════════════════════

describe("API client", () => {
  it("exports api with all expected methods", async () => {
    const { api } = await import("@/lib/api");
    const methods = [
      "getMe", "getMyProfile", "createProfile", "updateProfile",
      "getListings", "getListing", "generateMatches", "getMyMatches",
      "updateMatchStatus", "smartMatch", "smartMatchAndSave",
      "checkEligibility", "estimateWaitTime", "getNotifications",
      "getUnreadCount", "markNotificationsRead", "deleteNotification",
    ] as const;
    for (const m of methods) {
      expect(typeof api[m], `api.${m} should be a function`).toBe("function");
    }
  });

  it("ApiError carries name, status, and message", async () => {
    const { ApiError } = await import("@/lib/api");
    const err = new ApiError(422, "Unprocessable Entity");
    expect(err.name).toBe("ApiError");
    expect(err.status).toBe(422);
    expect(err.message).toBe("Unprocessable Entity");
  });

  it("ApiError is instanceof Error", async () => {
    const { ApiError } = await import("@/lib/api");
    expect(new ApiError(500, "Server Error")).toBeInstanceOf(Error);
  });

  it("ApiError with 404 status", async () => {
    const { ApiError } = await import("@/lib/api");
    const err = new ApiError(404, "Not Found");
    expect(err.status).toBe(404);
    expect(err.message).toBe("Not Found");
  });
});

// ══════════════════════════════════════════════════════════════════
// Accessibility
// ══════════════════════════════════════════════════════════════════

describe("Accessibility", () => {
  it("HomePage has a <main> landmark", async () => {
    const { default: HomePage } = await import("@/app/page");
    render(<HomePage />, { wrapper: Wrapper });
    expect(screen.getByRole("main")).toBeInTheDocument();
  });

  it("HomePage heading hierarchy starts at h1", async () => {
    const { default: HomePage } = await import("@/app/page");
    render(<HomePage />, { wrapper: Wrapper });
    expect(screen.getByRole("heading", { level: 1 })).toBeInTheDocument();
  });

  it("HomePage has at least 3 h2 section headings", async () => {
    const { default: HomePage } = await import("@/app/page");
    render(<HomePage />, { wrapper: Wrapper });
    const h2s = screen.getAllByRole("heading", { level: 2 });
    expect(h2s.length).toBeGreaterThanOrEqual(3);
  });

  it("all links in HomePage have an href attribute", async () => {
    const { default: HomePage } = await import("@/app/page");
    render(<HomePage />, { wrapper: Wrapper });
    const links = screen.getAllByRole("link");
    expect(links.length).toBeGreaterThan(0);
    for (const link of links) {
      expect(link).toHaveAttribute("href");
    }
  });

  it("Header nav has aria-label", async () => {
    const { default: Header } = await import("@/components/Header");
    render(<Header />, { wrapper: Wrapper });
    expect(screen.getByRole("navigation", { name: /main navigation/i })).toBeInTheDocument();
  });

  it("ClientProviders renders skip-to-content link targeting #main-content", async () => {
    const { default: ClientProviders } = await import("@/app/client-providers");
    render(<ClientProviders><div /></ClientProviders>, { wrapper: Wrapper });
    const skip = screen.getByText(/skip to main content/i);
    expect(skip).toHaveAttribute("href", "#main-content");
  });
});

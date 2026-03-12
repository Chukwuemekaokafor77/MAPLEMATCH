const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "/api";

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null,
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.detail ?? res.statusText);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

export class ApiError extends Error {
  status: number;

  constructor(
    status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

// === Types ===

export interface EligibilityProfile {
  id: string;
  user_id: string;
  annual_income: number | null;
  household_size: number | null;
  priority_group: string;
  province: string | null;
  city: string | null;
  postal_code: string | null;
  latitude: number | null;
  longitude: number | null;
  max_rent: number | null;
  needs_accessible_unit: boolean;
  consent_given: boolean;
  consent_date: string | null;
  created_at: string;
}

export interface EligibilityProfileCreate {
  annual_income?: number | null;
  household_size?: number | null;
  priority_group?: string;
  province?: string | null;
  city?: string | null;
  postal_code?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  max_rent?: number | null;
  needs_accessible_unit?: boolean;
  consent_given?: boolean;
}

export interface Listing {
  id: string;
  organization_id: string | null;
  title: string;
  description: string;
  address: string;
  city: string;
  province: string;
  postal_code: string;
  latitude: number | null;
  longitude: number | null;
  rent_amount: number;
  is_rgi: boolean;
  bedrooms: number;
  bathrooms: number;
  is_accessible: boolean;
  status: string;
  amenities: string;
  max_income: number | null;
  min_household_size: number | null;
  max_household_size: number | null;
  priority_groups: string;
  estimated_wait_days: number | null;
  created_at: string;
}

export interface MatchRead {
  id: string;
  user_id: string;
  listing_id: string;
  score: number;
  explanation: string;
  status: string;
  created_at: string;
}

export interface MatchFactor {
  name: string;
  score: number;
  weight: number;
  details: string;
}

export interface SmartMatchResult {
  listing_id: string;
  listing_title: string;
  eligible: boolean;
  final_score: number;
  rule_score: number;
  semantic_score: number;
  ml_score: number;
  factors: MatchFactor[];
  explanation: string;
  wait_time_days: number | null;
  wait_time_lower: number | null;
  wait_time_upper: number | null;
  wait_time_confidence: number | null;
  wait_time_factors: string[];
}

export interface WaitTimeResponse {
  listing_id: string;
  listing_title: string;
  estimated_days: number;
  lower_bound_days: number;
  upper_bound_days: number;
  confidence: number;
  factors: string[];
  method: string;
}

export interface Notification {
  id: string;
  user_id: string;
  notification_type: string;
  title: string;
  body: string;
  is_read: boolean;
  related_id: string | null;
  created_at: string;
}

export interface EligibilityCheckResult {
  eligible: boolean;
  score: number;
  reasons: string[];
  listing_id: string;
  listing_title: string;
}

// === API Functions ===

export const api = {
  // Users
  registerUser: (data: Record<string, string>, token?: string | null) =>
    apiFetch("/users/register", { method: "POST", body: JSON.stringify(data) }, token),

  getMe: (token?: string | null) =>
    apiFetch<{ id: string; email: string; first_name: string; last_name: string; role: string }>(
      "/users/me", {}, token,
    ),

  // Eligibility Profile
  getMyProfile: (token?: string | null) =>
    apiFetch<EligibilityProfile>("/users/me/eligibility", {}, token),

  createProfile: (data: EligibilityProfileCreate, token?: string | null) =>
    apiFetch<EligibilityProfile>("/users/me/eligibility", {
      method: "POST",
      body: JSON.stringify(data),
    }, token),

  updateProfile: (data: Partial<EligibilityProfileCreate>, token?: string | null) =>
    apiFetch<EligibilityProfile>("/users/me/eligibility", {
      method: "PUT",
      body: JSON.stringify(data),
    }, token),

  // Listings
  getListings: (params?: URLSearchParams, token?: string | null) =>
    apiFetch<Listing[]>(`/listings/${params ? `?${params}` : ""}`, {}, token),

  getListing: (id: string, token?: string | null) =>
    apiFetch<Listing>(`/listings/${id}`, {}, token),

  // Matching
  generateMatches: (token?: string | null) =>
    apiFetch<MatchRead[]>("/matches/generate", { method: "POST" }, token),

  getMyMatches: (token?: string | null) =>
    apiFetch<MatchRead[]>("/matches", {}, token),

  updateMatchStatus: (id: string, status: string, token?: string | null) =>
    apiFetch<MatchRead>(`/matches/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }, token),

  // AI Smart Matching
  smartMatch: (opts: { use_semantic?: boolean; use_ml?: boolean; limit?: number } = {}, token?: string | null) => {
    const params = new URLSearchParams();
    if (opts.use_semantic !== undefined) params.set("use_semantic", String(opts.use_semantic));
    if (opts.use_ml !== undefined) params.set("use_ml", String(opts.use_ml));
    if (opts.limit !== undefined) params.set("limit", String(opts.limit));
    return apiFetch<SmartMatchResult[]>(`/matches/smart?${params}`, { method: "POST" }, token);
  },

  smartMatchAndSave: (opts: { use_semantic?: boolean; use_ml?: boolean } = {}, token?: string | null) => {
    const params = new URLSearchParams();
    if (opts.use_semantic !== undefined) params.set("use_semantic", String(opts.use_semantic));
    if (opts.use_ml !== undefined) params.set("use_ml", String(opts.use_ml));
    return apiFetch<MatchRead[]>(`/matches/smart/save?${params}`, { method: "POST" }, token);
  },

  // Eligibility Check
  checkEligibility: (listingId: string, token?: string | null) =>
    apiFetch<EligibilityCheckResult>("/eligibility/check", {
      method: "POST",
      body: JSON.stringify({ listing_id: listingId }),
    }, token),

  // Wait Time
  estimateWaitTime: (listingId: string, token?: string | null) =>
    apiFetch<WaitTimeResponse>("/wait-time/estimate", {
      method: "POST",
      body: JSON.stringify({ listing_id: listingId }),
    }, token),

  // Notifications
  getNotifications: (params?: URLSearchParams, token?: string | null) =>
    apiFetch<Notification[]>(`/notifications/${params ? `?${params}` : ""}`, {}, token),

  getUnreadCount: (token?: string | null) =>
    apiFetch<{ unread_count: number }>("/notifications/unread-count", {}, token),

  markNotificationsRead: (notificationIds: string[], token?: string | null) =>
    apiFetch<{ updated: number }>("/notifications/mark-read", {
      method: "PATCH",
      body: JSON.stringify({ notification_ids: notificationIds }),
    }, token),

  deleteNotification: (id: string, token?: string | null) =>
    apiFetch<void>(`/notifications/${id}`, { method: "DELETE" }, token),
};

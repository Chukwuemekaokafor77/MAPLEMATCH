import { useAuth } from "@clerk/nextjs";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, type EligibilityProfileCreate, type DocumentCreate } from "@/lib/api";

function useToken() {
  const { getToken } = useAuth();
  return getToken;
}

// --- Eligibility Profile ---

export function useMyProfile() {
  const getToken = useToken();
  return useQuery({
    queryKey: ["eligibility-profile"],
    queryFn: async () => {
      const token = await getToken();
      return api.getMyProfile(token);
    },
    retry: false,
  });
}

export function useSaveProfile() {
  const getToken = useToken();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: EligibilityProfileCreate) => {
      const token = await getToken();
      return api.createProfile(data, token);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["eligibility-profile"] }),
  });
}

export function useUpdateProfile() {
  const getToken = useToken();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: Partial<EligibilityProfileCreate>) => {
      const token = await getToken();
      return api.updateProfile(data, token);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["eligibility-profile"] }),
  });
}

// --- Listings ---

export function useListings(params?: URLSearchParams) {
  const getToken = useToken();
  return useQuery({
    queryKey: ["listings", params?.toString()],
    queryFn: async () => {
      const token = await getToken();
      return api.getListings(params, token);
    },
  });
}

export function useListing(id: string) {
  const getToken = useToken();
  return useQuery({
    queryKey: ["listing", id],
    queryFn: async () => {
      const token = await getToken();
      return api.getListing(id, token);
    },
    enabled: !!id,
  });
}

// --- Matches ---

export function useMyMatches() {
  const getToken = useToken();
  return useQuery({
    queryKey: ["matches"],
    queryFn: async () => {
      const token = await getToken();
      return api.getMyMatches(token);
    },
  });
}

export function useGenerateMatches() {
  const getToken = useToken();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const token = await getToken();
      return api.generateMatches(token);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["matches"] }),
  });
}

export function useUpdateMatchStatus() {
  const getToken = useToken();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      const token = await getToken();
      return api.updateMatchStatus(id, status, token);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["matches"] }),
  });
}

// --- AI Smart Matching ---

export function useSmartMatch() {
  const getToken = useToken();
  return useMutation({
    mutationFn: async (opts: { use_semantic?: boolean; use_ml?: boolean; limit?: number } = {}) => {
      const token = await getToken();
      return api.smartMatch(opts, token);
    },
  });
}

export function useSmartMatchAndSave() {
  const getToken = useToken();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (opts: { use_semantic?: boolean; use_ml?: boolean } = {}) => {
      const token = await getToken();
      return api.smartMatchAndSave(opts, token);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["matches"] }),
  });
}

// --- Eligibility Check ---

export function useCheckEligibility() {
  const getToken = useToken();
  return useMutation({
    mutationFn: async (listingId: string) => {
      const token = await getToken();
      return api.checkEligibility(listingId, token);
    },
  });
}

// --- Wait Time ---

export function useEstimateWaitTime() {
  const getToken = useToken();
  return useMutation({
    mutationFn: async (listingId: string) => {
      const token = await getToken();
      return api.estimateWaitTime(listingId, token);
    },
  });
}

// --- Current user (with role) ---

export function useMe() {
  const getToken = useToken();
  return useQuery({
    queryKey: ["me"],
    queryFn: async () => {
      const token = await getToken();
      return api.getMe(token);
    },
  });
}

// --- Documents ---

export function useMyDocuments() {
  const getToken = useToken();
  return useQuery({
    queryKey: ["documents"],
    queryFn: async () => {
      const token = await getToken();
      return api.getMyDocuments(token);
    },
  });
}

export function useUploadDocument() {
  const getToken = useToken();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (data: DocumentCreate) => {
      const token = await getToken();
      return api.uploadDocument(data, token);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents"] }),
  });
}

export function useDeleteDocument() {
  const getToken = useToken();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const token = await getToken();
      return api.deleteDocument(id, token);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents"] }),
  });
}

// --- Admin ---

export function usePendingDocuments() {
  const getToken = useToken();
  return useQuery({
    queryKey: ["admin", "pending-documents"],
    queryFn: async () => {
      const token = await getToken();
      return api.getPendingDocuments(token);
    },
  });
}

export function useReviewDocument() {
  const getToken = useToken();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      status,
      notes,
    }: {
      id: string;
      status: string;
      notes?: string;
    }) => {
      const token = await getToken();
      return api.reviewDocument(id, status, notes, token);
    },
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["admin", "pending-documents"] }),
  });
}

export function useTriggerSync() {
  const getToken = useToken();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (opts: { province?: string; city?: string } = {}) => {
      const token = await getToken();
      return api.triggerSync(opts.province, opts.city, token);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sync-logs"] }),
  });
}

export function useSyncLogs() {
  const getToken = useToken();
  return useQuery({
    queryKey: ["sync-logs"],
    queryFn: async () => {
      const token = await getToken();
      return api.getSyncLogs(token);
    },
  });
}

// --- Notifications ---

export function useNotifications(unreadOnly = false) {
  const getToken = useToken();
  const params = new URLSearchParams();
  if (unreadOnly) params.set("unread_only", "true");
  return useQuery({
    queryKey: ["notifications", unreadOnly],
    queryFn: async () => {
      const token = await getToken();
      return api.getNotifications(params, token);
    },
    refetchInterval: 30_000,
  });
}

export function useUnreadCount() {
  const getToken = useToken();
  return useQuery({
    queryKey: ["notifications-unread-count"],
    queryFn: async () => {
      const token = await getToken();
      return api.getUnreadCount(token);
    },
    refetchInterval: 30_000,
  });
}

export function useMarkNotificationsRead() {
  const getToken = useToken();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (ids: string[]) => {
      const token = await getToken();
      return api.markNotificationsRead(ids, token);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
      qc.invalidateQueries({ queryKey: ["notifications-unread-count"] });
    },
  });
}

export function useDeleteNotification() {
  const getToken = useToken();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: string) => {
      const token = await getToken();
      return api.deleteNotification(id, token);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["notifications"] });
      qc.invalidateQueries({ queryKey: ["notifications-unread-count"] });
    },
  });
}

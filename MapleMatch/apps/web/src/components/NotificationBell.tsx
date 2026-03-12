import { useState, useRef, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { useNotifications, useUnreadCount, useMarkNotificationsRead, useDeleteNotification } from "@/hooks/useApi";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

export default function NotificationBell() {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const { data: unread } = useUnreadCount();
  const { data: notifications } = useNotifications();
  const markRead = useMarkNotificationsRead();
  const deleteNotif = useDeleteNotification();

  const count = unread?.unread_count ?? 0;

  // Close on outside click
  useEffect(() => {
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  function handleOpen() {
    setOpen((v) => !v);
    // Mark all visible as read when opening
    if (!open && notifications?.length) {
      const unreadIds = notifications.filter((n) => !n.is_read).map((n) => n.id);
      if (unreadIds.length > 0) markRead.mutate(unreadIds);
    }
  }

  return (
    <div ref={ref} className="relative">
      <Button
        variant="ghost"
        size="sm"
        onClick={handleOpen}
        aria-label={t("notifications.bell", { count })}
        aria-haspopup="true"
        aria-expanded={open}
        className="relative"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
          <path d="M10.3 21a1.94 1.94 0 0 0 3.4 0" />
        </svg>
        {count > 0 && (
          <Badge
            variant="destructive"
            className="absolute -right-1 -top-1 h-5 min-w-5 px-1 text-xs"
          >
            {count > 99 ? "99+" : count}
          </Badge>
        )}
      </Button>

      {open && (
        <div
          role="dialog"
          aria-label={t("notifications.title")}
          className="absolute right-0 top-full mt-2 w-80 max-h-96 overflow-y-auto rounded-lg border bg-background shadow-lg z-50"
        >
          <div className="flex items-center justify-between p-3">
            <h3 className="font-semibold text-sm">{t("notifications.title")}</h3>
          </div>
          <Separator />

          {!notifications?.length ? (
            <p className="p-4 text-sm text-muted-foreground text-center">
              {t("notifications.empty")}
            </p>
          ) : (
            <ul className="divide-y" role="list" aria-label={t("notifications.title")}>
              {notifications.map((n) => (
                <li
                  key={n.id}
                  className={`flex gap-2 p-3 text-sm ${n.is_read ? "opacity-60" : ""}`}
                >
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{n.title}</p>
                    <p className="text-muted-foreground text-xs mt-0.5">{n.body}</p>
                    <time className="text-muted-foreground text-xs mt-1 block" dateTime={n.created_at}>
                      {new Date(n.created_at).toLocaleDateString()}
                    </time>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-6 w-6 p-0 shrink-0"
                    onClick={() => deleteNotif.mutate(n.id)}
                    aria-label={t("notifications.dismiss")}
                  >
                    ×
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}

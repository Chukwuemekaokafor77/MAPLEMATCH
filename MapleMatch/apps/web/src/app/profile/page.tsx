"use client";

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useMyProfile, useUpdateProfile } from "@/hooks/useApi";
import type { EligibilityProfileCreate } from "@/lib/api";
import { CheckCircle } from "lucide-react";

const PROVINCES = [
  "AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU",
  "ON", "PE", "QC", "SK", "YT",
] as const;

const PRIORITY_GROUPS = [
  "none", "newcomer", "senior", "indigenous",
  "veteran", "disability", "fleeing_violence",
] as const;

export default function ProfilePage() {
  const { t } = useTranslation();
  const { data: profile, isLoading } = useMyProfile();
  const updateProfile = useUpdateProfile();
  const [saved, setSaved] = useState(false);
  const [form, setForm] = useState<EligibilityProfileCreate>({
    annual_income: undefined,
    household_size: undefined,
    priority_group: "none",
    province: undefined,
    city: undefined,
    postal_code: undefined,
    max_rent: undefined,
    needs_accessible_unit: false,
    consent_given: false,
  });

  // Pre-populate once profile loads
  useEffect(() => {
    if (!profile) return;
    setForm({
      annual_income: profile.annual_income ?? undefined,
      household_size: profile.household_size ?? undefined,
      priority_group: profile.priority_group ?? "none",
      province: profile.province ?? undefined,
      city: profile.city ?? undefined,
      postal_code: profile.postal_code ?? undefined,
      max_rent: profile.max_rent ?? undefined,
      needs_accessible_unit: profile.needs_accessible_unit ?? false,
      consent_given: profile.consent_given ?? false,
    });
  }, [profile]);

  const update = (patch: Partial<EligibilityProfileCreate>) =>
    setForm((prev) => ({ ...prev, ...patch }));

  const handleSave = async () => {
    setSaved(false);
    await updateProfile.mutateAsync(form);
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  if (isLoading) {
    return (
      <main className="max-w-2xl mx-auto px-4 py-8 space-y-4">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="h-96" />
      </main>
    );
  }

  return (
    <main className="max-w-2xl mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold">{t("profile.title")}</h1>
        <p className="text-muted-foreground mt-1">{t("profile.subtitle")}</p>
      </div>

      <div className="space-y-6">
        {/* Income & Household */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t("profile.income")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="income">{t("wizard.income.annual")}</Label>
              <Input
                id="income"
                type="number"
                min={0}
                step={1000}
                placeholder="35000"
                value={form.annual_income ?? ""}
                onChange={(e) =>
                  update({
                    annual_income: e.target.value
                      ? Number(e.target.value)
                      : undefined,
                  })
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="household">{t("wizard.income.household")}</Label>
              <Input
                id="household"
                type="number"
                min={1}
                max={20}
                placeholder="3"
                value={form.household_size ?? ""}
                onChange={(e) =>
                  update({
                    household_size: e.target.value
                      ? Number(e.target.value)
                      : undefined,
                  })
                }
              />
            </div>
          </CardContent>
        </Card>

        {/* Location */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t("profile.location")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="province">{t("wizard.location.province")}</Label>
              <Select
                value={form.province ?? ""}
                onValueChange={(v) => update({ province: v })}
              >
                <SelectTrigger id="province">
                  <SelectValue placeholder={t("wizard.location.selectProvince")} />
                </SelectTrigger>
                <SelectContent>
                  {PROVINCES.map((p) => (
                    <SelectItem key={p} value={p}>{p}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="city">{t("wizard.location.city")}</Label>
                <Input
                  id="city"
                  placeholder="Toronto"
                  value={form.city ?? ""}
                  onChange={(e) => update({ city: e.target.value || undefined })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="postal">{t("wizard.location.postalCode")}</Label>
                <Input
                  id="postal"
                  placeholder="M5V 2H1"
                  value={form.postal_code ?? ""}
                  onChange={(e) =>
                    update({ postal_code: e.target.value || undefined })
                  }
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Preferences */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{t("profile.preferences")}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="priority">{t("wizard.preferences.priorityGroup")}</Label>
              <Select
                value={form.priority_group ?? "none"}
                onValueChange={(v) => update({ priority_group: v })}
              >
                <SelectTrigger id="priority">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PRIORITY_GROUPS.map((g) => (
                    <SelectItem key={g} value={g}>
                      {t(`wizard.preferences.groups.${g}`)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="maxRent">{t("wizard.preferences.maxRent")}</Label>
              <Input
                id="maxRent"
                type="number"
                min={0}
                step={50}
                placeholder="1500"
                value={form.max_rent ?? ""}
                onChange={(e) =>
                  update({
                    max_rent: e.target.value ? Number(e.target.value) : undefined,
                  })
                }
              />
            </div>
            <div className="flex items-center gap-2">
              <input
                id="accessible"
                type="checkbox"
                checked={form.needs_accessible_unit ?? false}
                onChange={(e) =>
                  update({ needs_accessible_unit: e.target.checked })
                }
                className="size-4 rounded border-input"
              />
              <Label htmlFor="accessible">
                {t("wizard.preferences.accessible")}
              </Label>
            </div>
          </CardContent>
        </Card>

        {/* Save */}
        <div className="flex items-center gap-4">
          <Button
            onClick={handleSave}
            disabled={updateProfile.isPending}
            size="lg"
          >
            {updateProfile.isPending ? t("common.loading") : t("common.save")}
          </Button>
          {saved && (
            <span className="flex items-center gap-1.5 text-sm text-green-600">
              <CheckCircle className="size-4" />
              {t("profile.saved")}
            </span>
          )}
          {updateProfile.isError && (
            <p className="text-sm text-destructive">
              {updateProfile.error.message}
            </p>
          )}
        </div>
      </div>
    </main>
  );
}

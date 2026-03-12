"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
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
import { Progress } from "@/components/ui/progress";
import { useSaveProfile } from "@/hooks/useApi";
import type { EligibilityProfileCreate } from "@/lib/api";

const PROVINCES = [
  "AB",
  "BC",
  "MB",
  "NB",
  "NL",
  "NS",
  "NT",
  "NU",
  "ON",
  "PE",
  "QC",
  "SK",
  "YT",
] as const;

const PRIORITY_GROUPS = [
  "none",
  "newcomer",
  "senior",
  "indigenous",
  "veteran",
  "disability",
  "fleeing_violence",
] as const;

const TOTAL_STEPS = 4;

export default function EligibilityWizardPage() {
  const { t } = useTranslation();
  const router = useRouter();
  const saveProfile = useSaveProfile();
  const [step, setStep] = useState(1);
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

  const update = (patch: Partial<EligibilityProfileCreate>) =>
    setForm((prev) => ({ ...prev, ...patch }));

  const canProceed = (): boolean => {
    switch (step) {
      case 1:
        return (
          (form.annual_income ?? 0) > 0 && (form.household_size ?? 0) > 0
        );
      case 2:
        return !!form.province && !!form.city;
      case 3:
        return true;
      case 4:
        return form.consent_given === true;
      default:
        return false;
    }
  };

  const handleSubmit = async () => {
    try {
      await saveProfile.mutateAsync(form);
      router.push("/matches");
    } catch {
      // error handled by mutation state
    }
  };

  return (
    <main className="max-w-2xl mx-auto px-4 py-8">
      <Card>
        <CardHeader>
          <CardTitle className="text-2xl">{t("wizard.title")}</CardTitle>
          <CardDescription>{t("wizard.subtitle")}</CardDescription>
          <Progress value={(step / TOTAL_STEPS) * 100} className="mt-4" />
          <p className="text-sm text-muted-foreground mt-1">
            {t("wizard.step", { current: step, total: TOTAL_STEPS })}
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          {step === 1 && (
            <StepIncome
              income={form.annual_income}
              householdSize={form.household_size}
              onUpdate={update}
            />
          )}
          {step === 2 && (
            <StepLocation
              province={form.province}
              city={form.city}
              postalCode={form.postal_code}
              onUpdate={update}
            />
          )}
          {step === 3 && (
            <StepPreferences
              priorityGroup={form.priority_group}
              maxRent={form.max_rent}
              needsAccessible={form.needs_accessible_unit}
              onUpdate={update}
            />
          )}
          {step === 4 && (
            <StepConsent consent={form.consent_given} onUpdate={update} />
          )}

          {saveProfile.isError && (
            <p className="text-sm text-destructive" role="alert">
              {saveProfile.error.message}
            </p>
          )}

          <div className="flex justify-between pt-4">
            <Button
              variant="outline"
              onClick={() => setStep((s) => s - 1)}
              disabled={step === 1}
            >
              {t("common.back")}
            </Button>

            {step < TOTAL_STEPS ? (
              <Button
                onClick={() => setStep((s) => s + 1)}
                disabled={!canProceed()}
              >
                {t("common.next")}
              </Button>
            ) : (
              <Button
                onClick={handleSubmit}
                disabled={!canProceed() || saveProfile.isPending}
              >
                {saveProfile.isPending
                  ? t("common.loading")
                  : t("common.save")}
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </main>
  );
}

// --- Step components ---

function StepIncome({
  income,
  householdSize,
  onUpdate,
}: {
  income?: number | null;
  householdSize?: number | null;
  onUpdate: (p: Partial<EligibilityProfileCreate>) => void;
}) {
  const { t } = useTranslation();
  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">{t("wizard.income.title")}</h2>
      <div className="space-y-2">
        <Label htmlFor="income">{t("wizard.income.annual")}</Label>
        <Input
          id="income"
          type="number"
          min={0}
          step={1000}
          placeholder="35000"
          value={income ?? ""}
          onChange={(e) =>
            onUpdate({
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
          value={householdSize ?? ""}
          onChange={(e) =>
            onUpdate({
              household_size: e.target.value
                ? Number(e.target.value)
                : undefined,
            })
          }
        />
      </div>
    </div>
  );
}

function StepLocation({
  province,
  city,
  postalCode,
  onUpdate,
}: {
  province?: string | null;
  city?: string | null;
  postalCode?: string | null;
  onUpdate: (p: Partial<EligibilityProfileCreate>) => void;
}) {
  const { t } = useTranslation();
  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">{t("wizard.location.title")}</h2>
      <div className="space-y-2">
        <Label htmlFor="province">{t("wizard.location.province")}</Label>
        <Select
          value={province ?? ""}
          onValueChange={(v) => onUpdate({ province: v })}
        >
          <SelectTrigger id="province">
            <SelectValue
              placeholder={t("wizard.location.selectProvince")}
            />
          </SelectTrigger>
          <SelectContent>
            {PROVINCES.map((p) => (
              <SelectItem key={p} value={p}>
                {p}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="space-y-2">
        <Label htmlFor="city">{t("wizard.location.city")}</Label>
        <Input
          id="city"
          placeholder="Toronto"
          value={city ?? ""}
          onChange={(e) => onUpdate({ city: e.target.value || undefined })}
        />
      </div>
      <div className="space-y-2">
        <Label htmlFor="postal">{t("wizard.location.postalCode")}</Label>
        <Input
          id="postal"
          placeholder="M5V 2H1"
          value={postalCode ?? ""}
          onChange={(e) =>
            onUpdate({ postal_code: e.target.value || undefined })
          }
        />
      </div>
    </div>
  );
}

function StepPreferences({
  priorityGroup,
  maxRent,
  needsAccessible,
  onUpdate,
}: {
  priorityGroup?: string;
  maxRent?: number | null;
  needsAccessible?: boolean;
  onUpdate: (p: Partial<EligibilityProfileCreate>) => void;
}) {
  const { t } = useTranslation();
  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">
        {t("wizard.preferences.title")}
      </h2>
      <div className="space-y-2">
        <Label htmlFor="priority">
          {t("wizard.preferences.priorityGroup")}
        </Label>
        <Select
          value={priorityGroup ?? "none"}
          onValueChange={(v) => onUpdate({ priority_group: v })}
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
          value={maxRent ?? ""}
          onChange={(e) =>
            onUpdate({
              max_rent: e.target.value ? Number(e.target.value) : undefined,
            })
          }
        />
      </div>
      <div className="flex items-center gap-2 pt-2">
        <input
          id="accessible"
          type="checkbox"
          checked={needsAccessible ?? false}
          onChange={(e) =>
            onUpdate({ needs_accessible_unit: e.target.checked })
          }
          className="size-4 rounded border-input"
        />
        <Label htmlFor="accessible">
          {t("wizard.preferences.accessible")}
        </Label>
      </div>
    </div>
  );
}

function StepConsent({
  consent,
  onUpdate,
}: {
  consent?: boolean;
  onUpdate: (p: Partial<EligibilityProfileCreate>) => void;
}) {
  const { t } = useTranslation();
  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold">{t("wizard.consent.title")}</h2>
      <p className="text-sm text-muted-foreground">
        {t("wizard.consent.description")}
      </p>
      <ul className="ml-4 list-disc text-sm text-muted-foreground space-y-1">
        <li>{t("wizard.consent.point1")}</li>
        <li>{t("wizard.consent.point2")}</li>
        <li>{t("wizard.consent.point3")}</li>
      </ul>
      <div className="flex items-center gap-2 pt-2">
        <input
          id="consent"
          type="checkbox"
          checked={consent ?? false}
          onChange={(e) => onUpdate({ consent_given: e.target.checked })}
          className="size-4 rounded border-input"
        />
        <Label htmlFor="consent">{t("wizard.consent.agree")}</Label>
      </div>
    </div>
  );
}

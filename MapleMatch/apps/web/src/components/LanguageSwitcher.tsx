import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";

export default function LanguageSwitcher() {
  const { i18n, t } = useTranslation();

  const toggleLanguage = () => {
    const next = i18n.language === "en" ? "fr" : "en";
    i18n.changeLanguage(next);
  };

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={toggleLanguage}
      aria-label={t("a11y.languageSwitch")}
    >
      {i18n.language === "en" ? "FR" : "EN"}
    </Button>
  );
}

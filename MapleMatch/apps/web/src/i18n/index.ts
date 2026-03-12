import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "./en.json";
import fr from "./fr.json";

const isBrowser = typeof window !== "undefined";

if (!i18n.isInitialized) {
  i18n.use(initReactI18next).init({
    resources: {
      en: { translation: en },
      fr: { translation: fr },
    },
    lng: isBrowser
      ? (navigator.language?.startsWith("fr") ? "fr" : "en")
      : "en",
    fallbackLng: "en",
    supportedLngs: ["en", "fr"],
    interpolation: {
      escapeValue: false,
    },
  });
}

export default i18n;

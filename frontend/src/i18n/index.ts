import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

// Import translation files
import enTranslations from './locales/en.json';
import arTranslations from './locales/ar.json';
import frTranslations from './locales/fr.json';
import deTranslations from './locales/de.json';
import ruTranslations from './locales/ru.json';
import plTranslations from './locales/pl.json';
import trTranslations from './locales/tr.json';

// Supported languages
export const supportedLanguages = {
  en: 'English',
  ar: 'العربية',
  fr: 'Français', 
  de: 'Deutsch',
  ru: 'Русский',
  pl: 'Polski',
  tr: 'Türkçe'
};

export const supportedLanguageCodes = Object.keys(supportedLanguages);

// i18n configuration
i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    // Translation resources
    resources: {
      en: { translation: enTranslations },
      ar: { translation: arTranslations },
      fr: { translation: frTranslations },
      de: { translation: deTranslations },
      ru: { translation: ruTranslations },
      pl: { translation: plTranslations },
      tr: { translation: trTranslations }
    },
    
    // Default language
    fallbackLng: 'en',
    
    // Language detection options - privacy focused (no persistence)
    detection: {
      // Only detect from URL params and navigator - no localStorage/cookies for privacy
      order: ['querystring', 'navigator'],
      caches: [], // No caching for privacy
      excludeCacheFor: ['cimode'], // Development mode
      lookupQuerystring: 'lang'
    },
    
    // Namespace settings
    defaultNS: 'translation',
    ns: ['translation'],
    
    // Interpolation settings
    interpolation: {
      escapeValue: false // React already does escaping
    },
    
    // React settings
    react: {
      useSuspense: false // Disable suspense for better control
    },
    
    // Development settings
    debug: process.env.NODE_ENV === 'development',
    
    // Return empty string for missing keys in production
    returnEmptyString: process.env.NODE_ENV === 'production',
    
    // Pluralization
    pluralSeparator: '_',
    contextSeparator: '_',
    
    // Optimize performance
    load: 'languageOnly' // Don't load region-specific variations
  });

export default i18n;

// Utility function to get text direction for a language
export const getLanguageDirection = (languageCode: string): 'ltr' | 'rtl' => {
  return languageCode === 'ar' ? 'rtl' : 'ltr';
};

// Utility function to set document direction
export const setDocumentDirection = (languageCode: string) => {
  const direction = getLanguageDirection(languageCode);
  document.documentElement.dir = direction;
  document.documentElement.lang = languageCode;
};

// Helper function to convert flat dot notation to nested object
const convertToNestedObject = (flatObj: Record<string, string>): Record<string, any> => {
  const result: Record<string, any> = {};
  
  for (const [key, value] of Object.entries(flatObj)) {
    const keys = key.split('.');
    let current = result;
    
    for (let i = 0; i < keys.length - 1; i++) {
      const k = keys[i];
      if (!(k in current)) {
        current[k] = {};
      }
      current = current[k];
    }
    
    current[keys[keys.length - 1]] = value;
  }
  
  return result;
};

// Load translations dynamically from API (for admin updates)
export const loadTranslationsFromAPI = async (languageCode: string) => {
  try {
    const response = await fetch(`/api/translations/languages/${languageCode}`);
    if (response.ok) {
      const data = await response.json();
      
      // Convert flat dot notation to nested object structure
      const nestedTranslations = convertToNestedObject(data.translations);
      
      // Merge with existing translations (admin overrides static)
      i18n.addResourceBundle(languageCode, 'translation', nestedTranslations, true, true);
      
      console.log(`✅ Loaded ${Object.keys(data.translations).length} dynamic translations for ${languageCode}`);
      return true;
    }
  } catch (error) {
    console.warn(`Failed to load translations for ${languageCode}:`, error);
  }
  return false;
};

// Initialize with dynamic loading
export const initializeTranslations = async () => {
  const currentLanguage = i18n.language;
  
  // Always load English translations first (admin can edit them)
  await loadTranslationsFromAPI('en');
  
  // Load current language translations if it's not English
  if (currentLanguage && currentLanguage !== 'en') {
    await loadTranslationsFromAPI(currentLanguage);
  }
  
  setDocumentDirection(currentLanguage);
}; 
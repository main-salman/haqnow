import React from 'react';
import { useTranslation } from 'react-i18next';
import { supportedLanguages } from '../i18n';

const ProminentLanguageBar: React.FC = () => {
  const { i18n } = useTranslation();

  const languageFlags = {
    en: '🇺🇸',
    ar: '🇸🇦', 
    fr: '🇫🇷',
    de: '🇩🇪',
    ru: '🇷🇺',
    pl: '🇵🇱',
    tr: '🇹🇷'
  };

  const handleLanguageChange = (languageCode: string) => {
    i18n.changeLanguage(languageCode);
    
    // Set document direction for RTL languages
    if (languageCode === 'ar') {
      document.documentElement.dir = 'rtl';
      document.documentElement.lang = 'ar';
    } else {
      document.documentElement.dir = 'ltr';
      document.documentElement.lang = languageCode;
    }
  };

  return (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-gray-800 dark:to-gray-900 border-b border-gray-200 dark:border-gray-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-center py-2">
          <div className="flex items-center space-x-1 sm:space-x-2">
            <span className="text-xs sm:text-sm text-gray-600 dark:text-gray-300 mr-2 sm:mr-3">
              🌍 Select Language:
            </span>
            
            {Object.entries(supportedLanguages).map(([code, name]) => (
              <button
                key={code}
                onClick={() => handleLanguageChange(code)}
                className={`
                  flex items-center px-2 py-1 sm:px-3 sm:py-1.5 rounded-lg text-sm font-medium
                  transition-all duration-200 hover:scale-105 active:scale-95
                  ${i18n.language === code 
                    ? 'bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 ring-2 ring-blue-300 dark:ring-blue-600' 
                    : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-600 border border-gray-200 dark:border-gray-600'
                  }
                `}
                title={name}
                aria-label={`Switch to ${name}`}
              >
                <span className="text-lg sm:text-xl mr-1 sm:mr-2">
                  {languageFlags[code as keyof typeof languageFlags]}
                </span>
                <span className="hidden sm:inline text-xs font-medium">
                  {code.toUpperCase()}
                </span>
                <span className="sm:hidden text-xs font-medium">
                  {code}
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProminentLanguageBar; 
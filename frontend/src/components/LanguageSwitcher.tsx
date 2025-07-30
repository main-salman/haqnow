import React from 'react';
import { useTranslation } from 'react-i18next';
import { Globe } from 'lucide-react';
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { supportedLanguages, setDocumentDirection, loadTranslationsFromAPI } from '../i18n';

interface LanguageSwitcherProps {
  className?: string;
}

export const LanguageSwitcher: React.FC<LanguageSwitcherProps> = ({ className = "" }) => {
  const { i18n } = useTranslation();

  const handleLanguageChange = async (languageCode: string) => {
    try {
      // Always load fresh translations from API (admin can edit all languages including English)
      await loadTranslationsFromAPI(languageCode);
      
      // Change language
      await i18n.changeLanguage(languageCode);
      
      // Set document direction for RTL languages
      setDocumentDirection(languageCode);
      
    } catch (error) {
      console.warn('Failed to change language:', error);
      // Fallback to changing language without API translations
      await i18n.changeLanguage(languageCode);
      setDocumentDirection(languageCode);
    }
  };

  const currentLanguage = i18n.language || 'en';
  const currentLanguageName = supportedLanguages[currentLanguage as keyof typeof supportedLanguages] || 'English';

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="sm" className={`gap-1 text-xs px-2 py-1 h-7 ${className}`}>
          <Globe className="h-3 w-3" />
          <span className="hidden sm:inline text-xs">{currentLanguageName}</span>
          <span className="sm:hidden text-xs">{currentLanguage.toUpperCase()}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="min-w-[110px]">
        {Object.entries(supportedLanguages).map(([code, name]) => (
          <DropdownMenuItem
            key={code}
            onClick={() => handleLanguageChange(code)}
            className={`cursor-pointer text-xs py-1 ${currentLanguage === code ? 'bg-accent' : ''}`}
          >
            <div className="flex items-center justify-between w-full">
              <span className="text-xs">{name}</span>
              <span className="text-xs text-muted-foreground ml-1">{code.toUpperCase()}</span>
            </div>
            {currentLanguage === code && (
              <span className="ml-1 text-primary text-xs">✓</span>
            )}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}; 
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
      // Load fresh translations from API if not English
      if (languageCode !== 'en') {
        await loadTranslationsFromAPI(languageCode);
      }
      
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
        <Button variant="ghost" size="sm" className={`gap-2 ${className}`}>
          <Globe className="h-4 w-4" />
          <span className="hidden sm:inline">{currentLanguageName}</span>
          <span className="sm:hidden">{currentLanguage.toUpperCase()}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="min-w-[160px]">
        {Object.entries(supportedLanguages).map(([code, name]) => (
          <DropdownMenuItem
            key={code}
            onClick={() => handleLanguageChange(code)}
            className={`cursor-pointer ${currentLanguage === code ? 'bg-accent' : ''}`}
          >
            <div className="flex items-center justify-between w-full">
              <span>{name}</span>
              <span className="text-xs text-muted-foreground ml-2">{code.toUpperCase()}</span>
            </div>
            {currentLanguage === code && (
              <span className="ml-2 text-primary">✓</span>
            )}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}; 
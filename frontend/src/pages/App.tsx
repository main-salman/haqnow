import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";
import CountryDocStatsList from '../components/CountryDocStatsList';
import Version from '../components/Version';
import { LanguageSwitcher } from '../components/LanguageSwitcher';
import ProminentLanguageBar from '../components/ProminentLanguageBar';

export default function App() {
  const [searchTerm, setSearchTerm] = useState(""); // Added state for search term
  const navigate = useNavigate(); // Added navigation hook
  const { t } = useTranslation(); // Added translation hook

  // Added search handler
  const handleSearch = () => {
    if (searchTerm.trim()) {
      navigate(`/search-page?q=${encodeURIComponent(searchTerm.trim())}`);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <ProminentLanguageBar />
      <header className="py-6 px-4 md:px-8 border-b border-border">
        <div className="container mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="h-8 w-8 bg-primary rounded-md flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-sm">F</span>
            </div>
            <h1 className="text-xl md:text-2xl font-bold tracking-tight">
              {t('navigation.brand')}
            </h1>
          </div>
          <div className="flex items-center space-x-4">
            <nav className="hidden md:flex space-x-6">
              <Button variant="ghost" onClick={() => navigate('/search-page')}>
                {t('navigation.search')}
              </Button>
              <Button variant="ghost" onClick={() => navigate('/upload-document-page')}>
                {t('navigation.upload')}
              </Button>
              <Button variant="ghost" onClick={() => navigate('/about')}>
                {t('navigation.about')}
              </Button>
              <Button variant="ghost" onClick={() => navigate('/foi')}>
                {t('navigation.foi')}
              </Button>
              <Button variant="ghost" onClick={() => navigate('/privacy-guaranteed-page')}>
                {t('navigation.privacy')}
              </Button>
              <Button variant="ghost" onClick={() => navigate('/admin-login-page')}>
                {t('navigation.admin')}
              </Button>
            </nav>
            <LanguageSwitcher />
          </div>
        </div>
      </header>

      <main className="flex-grow container mx-auto px-4 py-8 md:py-12">
        <div className="space-y-10 md:space-y-16">
          <section className="text-center space-y-4">
            <h2 className="text-2xl md:text-3xl font-semibold tracking-tight">
              {t('homepage.title')}
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              {t('homepage.subtitle')}
            </p>
          </section>

          <section className="max-w-xl mx-auto">
            <div className="flex w-full items-center space-x-2">
              <Input
                type="search"
                placeholder={t('homepage.searchPlaceholder')}
                className="flex-grow"
                aria-label="Search documents"
                value={searchTerm} // Added value
                onChange={(e) => setSearchTerm(e.target.value)} // Added onChange
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()} // Added onKeyPress for Enter
              />
              <Button type="button" aria-label="Submit search" onClick={handleSearch}> {/* Changed to type="button" and added onClick */}
                <Search className="h-4 w-4 mr-2" />
                {t('homepage.searchButton')}
              </Button>
            </div>
          </section>

          <section className="text-center space-y-4">
            <h3 className="text-xl md:text-2xl font-semibold tracking-tight">
              {t('homepage.mapTitle')}
            </h3>
            <div
              className="bg-muted/40 border border-dashed border-border rounded-lg min-h-[300px] md:min-h-[400px] flex items-center justify-center"
              aria-label="World map placeholder"
            >
              <p className="text-muted-foreground">
                {t('homepage.mapPlaceholder')}
              </p>
            </div>
            {/* MYA-21: Added CountryDocStatsList below map placeholder */}
            <div className="mt-8 md:mt-12">
              <CountryDocStatsList />
            </div>
          </section>
        </div>
      </main>

      <footer className="py-6 px-4 md:px-8 border-t border-border text-center">
        <p className="text-sm text-muted-foreground">
          &copy; {new Date().getFullYear()} {t('navigation.brand')}. {t('homepage.copyright')}
          <Version />
        </p>
      </footer>
    </div>
  );
}

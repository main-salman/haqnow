import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Menu, X } from "lucide-react";
import { LanguageSwitcher } from "./LanguageSwitcher";

export default function Navigation() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const handleMobileNavigation = (path: string) => {
    navigate(path);
    setIsMobileMenuOpen(false); // Close mobile menu after navigation
  };

  return (
    <header className="py-6 px-4 md:px-8 border-b border-border bg-white">
      <div className="container mx-auto">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4 cursor-pointer" onClick={() => navigate('/')}>
            <div className="h-8 w-8 rounded-md flex items-center justify-center">
              <img src="/favicon.svg" alt="HaqNow" className="h-8 w-8" />
            </div>
            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-green-600">
              {t('navigation.brand')}
            </h1>
          </div>
          
          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-4">
            <nav className="flex space-x-6">
              <Button variant="ghost" onClick={() => navigate('/about')}>
                {t('navigation.about')}
              </Button>
              <Button variant="ghost" onClick={() => navigate('/search-page')}>
                {t('navigation.search')}
              </Button>
              <Button variant="ghost" onClick={() => navigate('/upload-document-page')}>
                {t('navigation.upload')}
              </Button>
              <Button variant="ghost" onClick={() => navigate('/foi')}>
                {t('navigation.foi')}
              </Button>
              <Button variant="ghost" onClick={() => navigate('/privacy-guaranteed-page')}>
                {t('navigation.privacy')}
              </Button>
              <Button variant="ghost" onClick={() => navigate('/disclaimer')}>
                {t('navigation.disclaimer')}
              </Button>
              <Button variant="ghost" asChild>
                <a
                  href="https://haqnow.wordpress.com/"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {t('navigation.blog')}
                </a>
              </Button>
              <Button asChild>
                <a
                  href="https://www.nonviolenceinternational.net/dignity_for_palestinians"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {t('navigation.donate')}
                </a>
              </Button>
            </nav>
            <LanguageSwitcher />
          </div>

          {/* Mobile Navigation */}
          <div className="md:hidden flex items-center space-x-2">
            <LanguageSwitcher className="mr-2" />
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              aria-label="Toggle mobile menu"
            >
              {isMobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </Button>
          </div>
        </div>

        {/* Mobile Menu Dropdown */}
        {isMobileMenuOpen && (
          <div className="md:hidden mt-4 py-4 border-t border-border">
            <nav className="flex flex-col space-y-2">
              <Button 
                variant="ghost" 
                className="justify-start" 
                onClick={() => handleMobileNavigation('/about')}
              >
                {t('navigation.about')}
              </Button>
              <Button 
                variant="ghost" 
                className="justify-start" 
                onClick={() => handleMobileNavigation('/search-page')}
              >
                {t('navigation.search')}
              </Button>
              <Button 
                variant="ghost" 
                className="justify-start" 
                onClick={() => handleMobileNavigation('/upload-document-page')}
              >
                {t('navigation.upload')}
              </Button>
              <Button 
                variant="ghost" 
                className="justify-start" 
                onClick={() => handleMobileNavigation('/foi')}
              >
                {t('navigation.foi')}
              </Button>
              <Button 
                variant="ghost"
                className="justify-start" 
                onClick={() => handleMobileNavigation('/privacy-guaranteed-page')}
              >
                {t('navigation.privacy')}
              </Button>
              <Button 
                variant="ghost" 
                className="justify-start" 
                onClick={() => handleMobileNavigation('/disclaimer')}
              >
                {t('navigation.disclaimer')}
              </Button>
                <Button variant="ghost" className="justify-start" asChild>
                  <a
                    href="https://haqnow.wordpress.com/"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {t('navigation.blog')}
                  </a>
                </Button>
                <Button className="justify-start" asChild>
                  <a
                    href="https://www.nonviolenceinternational.net/dignity_for_palestinians"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {t('navigation.donate')}
                  </a>
                </Button>
            </nav>
          </div>
        )}
      </div>
    </header>
  );
}
import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Menu, X, ChevronDown, ExternalLink } from "lucide-react";
import { LanguageSwitcher } from "./LanguageSwitcher";

const DONATE_URL = "https://www.zeffy.com/en-CA/donation-form/haqnow-expose-corruption-worldwide";

export default function Navigation() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isMoreOpen, setIsMoreOpen] = useState(false);
  const moreRef = useRef<HTMLDivElement>(null);

  // Close "More" dropdown on outside click
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (moreRef.current && !moreRef.current.contains(e.target as Node)) {
        setIsMoreOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleMobileNavigation = (path: string) => {
    navigate(path);
    setIsMobileMenuOpen(false);
  };

  // Primary nav items — always visible
  const primaryLinks = [
    { label: t('navigation.home'), path: '/' },
    { label: t('navigation.search'), path: '/search-page' },
    { label: t('navigation.upload'), path: '/upload-document-page' },
  ];

  // Secondary nav items — collapsed into "More" dropdown
  const secondaryLinks = [
    { label: t('navigation.about'), path: '/about' },
    { label: t('navigation.foi'), path: '/foi' },
    { label: t('navigation.privacy'), path: '/privacy-guaranteed-page' },
    { label: t('navigation.disclaimer'), path: '/disclaimer' },
    { label: t('navigation.blog'), path: null, href: 'https://haqnow.wordpress.com/', external: true },
  ];

  return (
    <header className="sticky top-0 z-50 py-4 px-4 md:px-8 border-b border-gray-100 bg-white/95 backdrop-blur-sm shadow-sm">
      <div className="container mx-auto">
        <div className="flex items-center justify-between">

          {/* Logo */}
          <div
            className="flex items-center space-x-3 cursor-pointer group"
            onClick={() => navigate('/')}
          >
            <div className="h-9 w-9 rounded-xl bg-green-50 flex items-center justify-center group-hover:bg-green-100 transition-colors">
              <img src="/favicon.svg" alt="HaqNow" className="h-7 w-7" />
            </div>
            <span className="text-xl md:text-2xl font-bold tracking-tight text-green-600">
              {t('navigation.brand')}
            </span>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-1">
            <nav className="flex items-center space-x-1">
              {primaryLinks.map((link) => (
                <button
                  key={link.path}
                  onClick={() => navigate(link.path)}
                  className="px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  {link.label}
                </button>
              ))}

              {/* "More" dropdown */}
              <div className="relative" ref={moreRef}>
                <button
                  onClick={() => setIsMoreOpen(!isMoreOpen)}
                  className="flex items-center gap-1 px-3 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  {t('navigation.more', 'More')}
                  <ChevronDown className={`h-4 w-4 transition-transform duration-200 ${isMoreOpen ? 'rotate-180' : ''}`} />
                </button>
                {isMoreOpen && (
                  <div className="absolute top-full right-0 mt-1 w-48 bg-white border border-gray-100 rounded-xl shadow-lg py-1 z-50">
                    {secondaryLinks.map((link) =>
                      link.external ? (
                        <a
                          key={link.label}
                          href={link.href!}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-2 px-4 py-2.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50 transition-colors"
                          onClick={() => setIsMoreOpen(false)}
                        >
                          {link.label}
                          <ExternalLink className="h-3 w-3 text-gray-400" />
                        </a>
                      ) : (
                        <button
                          key={link.label}
                          onClick={() => { navigate(link.path!); setIsMoreOpen(false); }}
                          className="w-full text-left px-4 py-2.5 text-sm text-gray-600 hover:text-gray-900 hover:bg-gray-50 transition-colors"
                        >
                          {link.label}
                        </button>
                      )
                    )}
                  </div>
                )}
              </div>
            </nav>

            <div className="flex items-center gap-2 ml-2 pl-2 border-l border-gray-200">
              <LanguageSwitcher />
              <Button
                asChild
                size="sm"
                className="bg-green-600 hover:bg-green-700 rounded-lg px-4 font-medium"
              >
                <a href={DONATE_URL} target="_blank" rel="noopener noreferrer">
                  {t('navigation.donate')}
                </a>
              </Button>
            </div>
          </div>

          {/* Mobile: language + hamburger */}
          <div className="md:hidden flex items-center gap-2">
            <LanguageSwitcher className="mr-1" />
            <button
              onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
              aria-label="Toggle mobile menu"
            >
              {isMobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        {isMobileMenuOpen && (
          <div className="md:hidden mt-3 pt-3 border-t border-gray-100">
            <nav className="flex flex-col gap-1">
              {[...primaryLinks, ...secondaryLinks.filter(l => !l.external)].map((link) => (
                <button
                  key={link.label}
                  onClick={() => handleMobileNavigation(link.path!)}
                  className="text-left px-3 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
                >
                  {link.label}
                </button>
              ))}
              <a
                href="https://haqnow.wordpress.com/"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 px-3 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 rounded-lg transition-colors"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                {t('navigation.blog')}
                <ExternalLink className="h-3.5 w-3.5 text-gray-400" />
              </a>
              <div className="pt-2 border-t border-gray-100 mt-1">
                <Button asChild className="w-full bg-green-600 hover:bg-green-700 rounded-lg">
                  <a href={DONATE_URL} target="_blank" rel="noopener noreferrer">
                    {t('navigation.donate')}
                  </a>
                </Button>
              </div>
            </nav>
          </div>
        )}
      </div>
    </header>
  );
}
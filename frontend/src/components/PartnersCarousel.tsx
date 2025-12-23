import React, { useState, useEffect, useRef } from 'react';
import { Play, Pause, ExternalLink } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface Partner {
  id: number;
  name: string;
  description: string;
  logo_url: string;
  website_url: string;
  category: 'investigative' | 'collaborator';
  categoryTitle: string;
  categoryDescription: string;
}

export default function PartnersCarousel() {
  const { t } = useTranslation();
  const [partners, setPartners] = useState<Partner[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch partners from both APIs
  useEffect(() => {
    fetchAllPartners();
  }, []);

  const fetchAllPartners = async () => {
    try {
      setIsLoading(true);

      // Fetch investigative research partners
      const investigativeResponse = await fetch('/api/collaborators/investigative-research-partners');
      if (!investigativeResponse.ok) {
        throw new Error('Failed to fetch investigative research partners');
      }
      const investigativeData = await investigativeResponse.json();

      // Fetch collaborators
      const collaboratorsResponse = await fetch('/api/collaborators');
      if (!collaboratorsResponse.ok) {
        throw new Error('Failed to fetch collaborators');
      }
      const collaboratorsData = await collaboratorsResponse.json();

      // Combine and format partners
      const combinedPartners: Partner[] = [
        ...investigativeData.collaborators.map((partner: any) => ({
          ...partner,
          category: 'investigative' as const,
          categoryTitle: t('about.investigativeResearchPartnersTitle', 'Investigative Research Partners'),
          categoryDescription: t('about.investigativeResearchPartnersDescription', 'Our research and investigation partners')
        })),
        ...collaboratorsData.collaborators.map((partner: any) => ({
          ...partner,
          category: 'collaborator' as const,
          categoryTitle: t('about.collaboratorsTitle', 'Collaborators and Champions'),
          categoryDescription: t('about.collaboratorsDescription', 'Our trusted partners and supporters')
        }))
      ];

      setPartners(combinedPartners);
      setError(null);
    } catch (err) {
      console.error('Error fetching partners:', err);
      setError('Unable to load partners');
    } finally {
      setIsLoading(false);
    }
  };

  // Auto-scroll functionality
  useEffect(() => {
    if (!isPaused && partners.length > 0) {
      intervalRef.current = setInterval(() => {
        setCurrentIndex((prev) => (prev + 1) % partners.length);
      }, 1000); // 1 second per partner
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isPaused, partners.length]);

  const togglePause = () => {
    setIsPaused(!isPaused);
  };

  const getPartnerOpacity = (index: number) => {
    const diff = Math.abs(index - currentIndex);
    if (diff === 0) return 1; // Current partner fully visible
    if (diff === 1) return 0.3; // Adjacent partners slightly visible
    return 0; // Others invisible
  };

  const getPartnerTransform = (index: number) => {
    const diff = index - currentIndex;
    return `translateX(${diff * 100}%)`;
  };

  if (isLoading) {
    return (
      <section className="mt-12">
        <div className="max-w-6xl mx-auto">
          <div className="bg-white rounded-lg shadow-lg p-8">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500 mx-auto"></div>
              <p className="text-slate-600 mt-2">Loading partners...</p>
            </div>
          </div>
        </div>
      </section>
    );
  }

  if (error || partners.length === 0) {
    return null; // Don't show section if no partners
  }

  const currentPartner = partners[currentIndex];

  return (
    <section className="mt-12">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h2 className="text-2xl md:text-3xl font-semibold tracking-tight text-gray-900 mb-2">
            {currentPartner.categoryTitle}
          </h2>
          <p className="text-gray-700">
            {currentPartner.categoryDescription}
          </p>
        </div>

        {/* Scrolling Carousel Container */}
        <div className="relative bg-white rounded-lg shadow-lg overflow-hidden">
          <div className="relative h-48 md:h-56 flex items-center justify-center">
            {/* Partners */}
            {partners.map((partner, index) => (
              <div
                key={`${partner.category}-${partner.id}`}
                className="absolute inset-0 flex items-center justify-center transition-all duration-1000 ease-in-out"
                style={{
                  opacity: getPartnerOpacity(index),
                  transform: getPartnerTransform(index),
                }}
              >
                <a
                  href={partner.website_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="group flex flex-col items-center justify-center p-6 transition-all duration-200"
                >
                  {/* Logo */}
                  <div className="mb-4 flex items-center justify-center h-20 w-full">
                    <img
                      src={partner.logo_url}
                      alt={partner.name}
                      className="max-h-20 max-w-full object-contain"
                      loading="lazy"
                    />
                  </div>

                  {/* External Link Icon */}
                  <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <ExternalLink className="h-4 w-4 text-indigo-600" />
                  </div>
                </a>
              </div>
            ))}
          </div>

          {/* Pause/Play Button */}
          <button
            onClick={togglePause}
            className="absolute top-4 right-4 bg-white/90 hover:bg-white rounded-full p-2 shadow-lg transition-all duration-200 hover:scale-110 z-10"
            aria-label={isPaused ? "Play carousel" : "Pause carousel"}
          >
            {isPaused ? (
              <Play className="h-4 w-4 text-gray-700" />
            ) : (
              <Pause className="h-4 w-4 text-gray-700" />
            )}
          </button>

          {/* Progress Indicators */}
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex space-x-1">
            {partners.map((_, index) => (
              <div
                key={index}
                className={`w-2 h-2 rounded-full transition-all duration-300 ${
                  index === currentIndex
                    ? 'bg-indigo-600 scale-125'
                    : 'bg-gray-300'
                }`}
              />
            ))}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-4 w-full bg-gray-200 rounded-full h-1">
          <div
            className="bg-indigo-600 h-1 rounded-full transition-all duration-1000 ease-out"
            style={{ width: `${((currentIndex + 1) / partners.length) * 100}%` }}
          />
        </div>
      </div>
    </section>
  );
}

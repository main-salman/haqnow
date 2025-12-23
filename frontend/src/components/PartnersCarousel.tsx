import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import InvestigativeResearchPartnersSection from './InvestigativeResearchPartnersSection';
import CollaboratorsSection from './CollaboratorsSection';

interface CarouselSlide {
  id: string;
  title: string;
  description: string;
  component: React.ReactNode;
}

export default function PartnersCarousel() {
  const { t } = useTranslation();
  const [currentSlide, setCurrentSlide] = useState(0);

  const slides: CarouselSlide[] = [
    {
      id: 'investigative-partners',
      title: t('about.investigativeResearchPartnersTitle', 'Investigative Research Partners'),
      description: t('about.investigativeResearchPartnersDescription', 'Our research and investigation partners'),
      component: <InvestigativeResearchPartnersSection />
    },
    {
      id: 'collaborators',
      title: t('about.collaboratorsTitle', 'Collaborators and Champions'),
      description: t('about.collaboratorsDescription', 'Our trusted partners and supporters'),
      component: <CollaboratorsSection />
    }
  ];

  const nextSlide = () => {
    setCurrentSlide((prev) => (prev + 1) % slides.length);
  };

  const prevSlide = () => {
    setCurrentSlide((prev) => (prev - 1 + slides.length) % slides.length);
  };

  const goToSlide = (index: number) => {
    setCurrentSlide(index);
  };

  // Auto-advance carousel every 8 seconds
  useEffect(() => {
    const timer = setInterval(() => {
      nextSlide();
    }, 8000);

    return () => clearInterval(timer);
  }, []);

  return (
    <section className="mt-12">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h2 className="text-2xl md:text-3xl font-semibold tracking-tight text-gray-900 mb-2">
            {slides[currentSlide].title}
          </h2>
          <p className="text-gray-700">
            {slides[currentSlide].description}
          </p>
        </div>

        {/* Carousel Container */}
        <div className="relative bg-white rounded-lg shadow-lg overflow-hidden">
          {/* Content */}
          <div className="transition-all duration-500 ease-in-out">
            {slides[currentSlide].component}
          </div>

          {/* Navigation Arrows */}
          <button
            onClick={prevSlide}
            className="absolute left-4 top-1/2 -translate-y-1/2 bg-white/90 hover:bg-white rounded-full p-2 shadow-lg transition-all duration-200 hover:scale-110 z-10"
            aria-label="Previous slide"
          >
            <ChevronLeft className="h-5 w-5 text-gray-700" />
          </button>

          <button
            onClick={nextSlide}
            className="absolute right-4 top-1/2 -translate-y-1/2 bg-white/90 hover:bg-white rounded-full p-2 shadow-lg transition-all duration-200 hover:scale-110 z-10"
            aria-label="Next slide"
          >
            <ChevronRight className="h-5 w-5 text-gray-700" />
          </button>

          {/* Dots Indicator */}
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex space-x-2">
            {slides.map((_, index) => (
              <button
                key={index}
                onClick={() => goToSlide(index)}
                className={`w-3 h-3 rounded-full transition-all duration-200 ${
                  index === currentSlide
                    ? 'bg-indigo-600 scale-110'
                    : 'bg-gray-300 hover:bg-gray-400'
                }`}
                aria-label={`Go to slide ${index + 1}`}
              />
            ))}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-4 w-full bg-gray-200 rounded-full h-1">
          <div
            className="bg-indigo-600 h-1 rounded-full transition-all duration-300 ease-out"
            style={{ width: `${((currentSlide + 1) / slides.length) * 100}%` }}
          />
        </div>
      </div>
    </section>
  );
}

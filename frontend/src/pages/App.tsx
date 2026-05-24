import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Search, Upload, Globe, Users, Shield, ArrowRight, FileText, Eye, ChevronRight } from "lucide-react";
import CountryDocStatsList from '../components/CountryDocStatsList';
import InteractiveWorldMap from '../components/InteractiveWorldMap';
import TopViewedDocuments from '../components/TopViewedDocuments';
import RecentlySharedDocuments from '../components/RecentlySharedDocuments';
import CollaboratorsSection from '../components/CollaboratorsSection';
import InvestigativeResearchPartnersSection from '../components/InvestigativeResearchPartnersSection';
import Footer from '../components/Footer';
import Navigation from '../components/Navigation';
import PartnersCarousel from '../components/PartnersCarousel';

interface CountryStats {
  countryCode: string;
  totalDocuments: number;
}

interface StatsResponse {
  countries: Array<{
    country: string;
    doc_count: number;
  }>;
  total_countries: number;
  total_documents: number;
}

interface SiteStats {
  totalDocuments: number | null;
  totalCountries: number | null;
  loading: boolean;
}

export default function App() {
  const [searchTerm, setSearchTerm] = useState("");
  const [mapData, setMapData] = useState<CountryStats[]>([]);
  const [loadingMapData, setLoadingMapData] = useState(true);
  const [siteStats, setSiteStats] = useState<SiteStats>({ totalDocuments: null, totalCountries: null, loading: true });
  const hasFetchedMapData = useRef(false);
  const navigate = useNavigate();
  const { t } = useTranslation();

  const renderHtml = (html: string) => {
    return <span dangerouslySetInnerHTML={{ __html: html }} />;
  };

  const countryCodeMapping: Record<string, string> = {
    'US': 'US', 'United States': 'US', 'Canada': 'CA', 'United Kingdom': 'GB',
    'Germany': 'DE', 'France': 'FR', 'Spain': 'ES', 'Italy': 'IT',
    'Netherlands': 'NL', 'Belgium': 'BE', 'Switzerland': 'CH', 'Austria': 'AT',
    'Sweden': 'SE', 'Norway': 'NO', 'Denmark': 'DK', 'Finland': 'FI',
    'Poland': 'PL', 'Czech Republic': 'CZ', 'Hungary': 'HU', 'Romania': 'RO',
    'Bulgaria': 'BG', 'Greece': 'GR', 'Portugal': 'PT', 'Ireland': 'IE',
    'Croatia': 'HR', 'Slovenia': 'SI', 'Slovakia': 'SK', 'Lithuania': 'LT',
    'Latvia': 'LV', 'Estonia': 'EE', 'Ukraine': 'UA', 'Russia': 'RU',
    'Turkey': 'TR', 'China': 'CN', 'Japan': 'JP', 'South Korea': 'KR',
    'India': 'IN', 'Thailand': 'TH', 'Vietnam': 'VN', 'Malaysia': 'MY',
    'Indonesia': 'ID', 'Philippines': 'PH', 'Singapore': 'SG', 'Australia': 'AU',
    'New Zealand': 'NZ', 'Brazil': 'BR', 'Argentina': 'AR', 'Mexico': 'MX',
    'Colombia': 'CO', 'Peru': 'PE', 'Chile': 'CL', 'Venezuela': 'VE',
    'Ecuador': 'EC', 'Uruguay': 'UY', 'Paraguay': 'PY', 'Bolivia': 'BO',
    'South Africa': 'ZA', 'Nigeria': 'NG', 'Egypt': 'EG', 'Morocco': 'MA',
    'Algeria': 'DZ', 'Tunisia': 'TN', 'Libya': 'LY', 'Sudan': 'SD',
    'Ethiopia': 'ET', 'Kenya': 'KE', 'Tanzania': 'TZ', 'Uganda': 'UG',
    'Ghana': 'GH', 'Ivory Coast': 'CI', 'Senegal': 'SN', 'Mali': 'ML',
    'Afghanistan': 'AF', 'Bangladesh': 'BD', 'Cayman Islands': 'KY',
    'Pakistan': 'PK', 'Iran': 'IR', 'Iraq': 'IQ', 'Syria': 'SY',
    'Lebanon': 'LB', 'Jordan': 'JO', 'Israel': 'IL', 'Palestine': 'PS',
    'Saudi Arabia': 'SA', 'United Arab Emirates': 'AE', 'Qatar': 'QA',
    'Kuwait': 'KW', 'Bahrain': 'BH', 'Oman': 'OM', 'Yemen': 'YE',
    'Sri Lanka': 'LK', 'Myanmar': 'MM', 'Cambodia': 'KH', 'Laos': 'LA',
    'Nepal': 'NP', 'Bhutan': 'BT', 'Maldives': 'MV', 'Mongolia': 'MN',
    'North Korea': 'KP', 'Taiwan': 'TW', 'Hong Kong': 'HK', 'Macau': 'MO',
    'Kazakhstan': 'KZ', 'Uzbekistan': 'UZ', 'Turkmenistan': 'TM',
    'Kyrgyzstan': 'KG', 'Tajikistan': 'TJ', 'Georgia': 'GE', 'Armenia': 'AM',
    'Azerbaijan': 'AZ', 'Belarus': 'BY', 'Moldova': 'MD', 'Serbia': 'RS',
    'Montenegro': 'ME', 'Bosnia and Herzegovina': 'BA', 'North Macedonia': 'MK',
    'Albania': 'AL', 'Kosovo': 'XK', 'Cyprus': 'CY', 'Malta': 'MT',
    'Iceland': 'IS', 'Luxembourg': 'LU', 'Monaco': 'MC', 'San Marino': 'SM',
    'Vatican City': 'VA', 'Andorra': 'AD', 'Liechtenstein': 'LI'
  };

  // Fetch real-time global stats from the dedicated endpoint
  useEffect(() => {
    const fetchGlobalStats = async () => {
      try {
        const response = await fetch('/api/statistics/global-stats');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data = await response.json();
        setSiteStats({
          totalDocuments: data.approved_documents ?? data.total_documents ?? null,
          totalCountries: data.total_countries ?? null,
          loading: false,
        });
      } catch (err) {
        console.error('Error fetching global stats:', err);
        setSiteStats(prev => ({ ...prev, loading: false }));
      }
    };
    fetchGlobalStats();
  }, []);

  useEffect(() => {
    const fetchMapData = async () => {
      const cachedData = localStorage.getItem('haqnow_map_data');
      const cacheTimestamp = localStorage.getItem('haqnow_map_data_timestamp');
      const cacheMaxAge = 5 * 60 * 1000;

      if (cachedData && cacheTimestamp) {
        const age = Date.now() - parseInt(cacheTimestamp);
        if (age < cacheMaxAge) {
          const parsedData = JSON.parse(cachedData);
          setMapData(parsedData);
          setLoadingMapData(false);
          return;
        }
      }

      if (hasFetchedMapData.current) return;
      hasFetchedMapData.current = true;

      try {
        setLoadingMapData(true);
        const response = await fetch('/api/statistics/country-stats');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        const data: StatsResponse = await response.json();

        const mappedData: CountryStats[] = [];
        data.countries.forEach(country => {
          const countryCode = countryCodeMapping[country.country];
          if (countryCode) {
            mappedData.push({ countryCode, totalDocuments: country.doc_count });
          }
        });

        localStorage.setItem('haqnow_map_data', JSON.stringify(mappedData));
        localStorage.setItem('haqnow_map_data_timestamp', Date.now().toString());
        setMapData(mappedData);
      } catch (err) {
        console.error('Error fetching map data:', err);
        setMapData([]);
      } finally {
        setLoadingMapData(false);
      }
    };

    fetchMapData();
  }, []);

  const handleSearch = () => {
    if (searchTerm.trim()) {
      navigate(`/search-page?q=${encodeURIComponent(searchTerm.trim())}`);
    } else {
      navigate('/search-page');
    }
  };

  const handleCountryClick = (countryCode: string) => {
    const countryName = Object.entries(countryCodeMapping).find(([name, code]) => code === countryCode)?.[0];
    if (countryName) {
      navigate(`/search-page?country=${encodeURIComponent(countryName)}`);
    }
  };

  return (
    <div className="min-h-screen bg-white">
      <Navigation />

      {/* ═══════════════════════════════════════════════════════════
          HERO — Unified video + title + CTAs
          ═══════════════════════════════════════════════════════════ */}
      <section className="bg-gradient-to-br from-green-50 via-white to-blue-50 border-b border-gray-100">
        <div className="container mx-auto px-4 py-10 md:py-16">
          <div className="flex flex-col lg:flex-row items-center gap-8 lg:gap-12">

            {/* Video */}
            <div className="w-full lg:w-1/2 flex-shrink-0">
              <div className="relative rounded-2xl overflow-hidden shadow-2xl bg-white/60 backdrop-blur-sm border border-green-100">
                <video
                  id="hero-video"
                  className="w-full h-auto"
                  autoPlay
                  loop
                  muted
                  playsInline
                  style={{ objectFit: 'cover', maxHeight: '380px' }}
                >
                  <source src="/video.mp4" type="video/mp4" />
                </video>
                <div className="absolute bottom-3 right-3 flex gap-2">
                  <button
                    onClick={(e) => {
                      const video = document.getElementById('hero-video') as HTMLVideoElement;
                      if (video) {
                        if (video.paused) { video.play(); e.currentTarget.textContent = '⏸️'; }
                        else { video.pause(); e.currentTarget.textContent = '▶️'; }
                      }
                    }}
                    className="bg-black/40 hover:bg-black/60 text-white p-1.5 rounded-full transition-colors text-sm"
                    aria-label="Toggle play/pause"
                  >⏸️</button>
                  <button
                    onClick={(e) => {
                      const video = document.getElementById('hero-video') as HTMLVideoElement;
                      if (video) { video.muted = !video.muted; e.currentTarget.textContent = video.muted ? '🔇' : '🔊'; }
                    }}
                    className="bg-black/40 hover:bg-black/60 text-white p-1.5 rounded-full transition-colors text-sm"
                    aria-label="Toggle sound"
                  >🔇</button>
                </div>
              </div>
            </div>

            {/* Text + CTAs */}
            <div className="w-full lg:w-1/2 text-center lg:text-left space-y-6">
              <div className="space-y-3">
                <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold tracking-tight text-gray-900 leading-tight">
                  {t('homepage.title')}
                </h1>
                <p className="text-lg text-gray-600 leading-relaxed max-w-xl mx-auto lg:mx-0">
                  {t('homepage.subtitle')}
                </p>
              </div>

              {/* Primary CTAs */}
              <div className="flex flex-col sm:flex-row gap-3 justify-center lg:justify-start">
                <Button
                  size="lg"
                  onClick={() => navigate('/search-page')}
                  className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 text-base font-semibold shadow-lg hover:shadow-xl transition-all duration-200 rounded-xl"
                >
                  <Search className="h-5 w-5 mr-2" />
                  {t('navigation.search')}
                </Button>
                <Button
                  size="lg"
                  onClick={() => navigate('/upload-document-page')}
                  variant="outline"
                  className="border-2 border-green-600 text-green-700 hover:bg-green-600 hover:text-white px-6 py-3 text-base font-semibold transition-all duration-200 rounded-xl"
                >
                  <Upload className="h-5 w-5 mr-2" />
                  {t('navigation.upload')}
                </Button>
              </div>

              {/* Newsletter / feedback links */}
              <div className="text-sm text-gray-500 space-y-1 [&_a]:text-green-600 [&_a]:underline [&_a:hover]:text-green-800">
                <p>{renderHtml(t('homepage.newsletterHtml'))}</p>
                <p>{renderHtml(t('homepage.feedbackHtml'))}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════
          IMPACT STATS STRIP
          ═══════════════════════════════════════════════════════════ */}
      <section className="bg-green-700 text-white py-5">
        <div className="container mx-auto px-4">
          <div className="flex flex-wrap items-center justify-center gap-8 md:gap-16 text-center">
            <div>
              <div className="text-2xl md:text-3xl font-bold">
                {siteStats.loading
                  ? <span className="inline-block w-16 h-8 bg-green-600 rounded animate-pulse" />
                  : siteStats.totalDocuments !== null
                    ? siteStats.totalDocuments.toLocaleString()
                    : '—'}
              </div>
              <div className="text-green-200 text-sm mt-0.5">{t('homepage.statsPublicDocuments', 'Public Documents')}</div>
            </div>
            <div className="hidden md:block w-px h-10 bg-green-500 opacity-50" />
            <div>
              <div className="text-2xl md:text-3xl font-bold">
                {siteStats.loading
                  ? <span className="inline-block w-10 h-8 bg-green-600 rounded animate-pulse" />
                  : siteStats.totalCountries !== null
                    ? siteStats.totalCountries
                    : '—'}
              </div>
              <div className="text-green-200 text-sm mt-0.5">{t('homepage.statsCountries', 'Countries')}</div>
            </div>
            <div className="hidden md:block w-px h-10 bg-green-500 opacity-50" />
            <div>
              <div className="text-2xl md:text-3xl font-bold">100%</div>
              <div className="text-green-200 text-sm mt-0.5">{t('homepage.statsAnonymous', 'Anonymous')}</div>
            </div>
            <div className="hidden md:block w-px h-10 bg-green-500 opacity-50" />
            <div>
              <div className="text-2xl md:text-3xl font-bold">{t('homepage.statsOpen', 'Open')}</div>
              <div className="text-green-200 text-sm mt-0.5">{t('homepage.statsSource', 'Source')}</div>
            </div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════
          QUICK SEARCH (directly accessible)
          ═══════════════════════════════════════════════════════════ */}
      <section className="bg-white py-10 border-b border-gray-100">
        <div className="container mx-auto px-4 max-w-2xl">
          <div className="text-center mb-5">
            <h2 className="text-xl font-semibold text-gray-800">{t('homepage.searchTitle', 'Search Public Records')}</h2>
            <p className="text-gray-500 text-sm mt-1">{t('homepage.searchDescription')}</p>
          </div>
          <div className="flex flex-col sm:flex-row gap-3">
            <Input
              type="search"
              placeholder={t('homepage.searchPlaceholder')}
              className="flex-grow h-12 rounded-xl border-gray-200 shadow-sm text-base"
              aria-label="Search documents"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
            <Button
              type="button"
              aria-label="Submit search"
              onClick={handleSearch}
              className="bg-green-600 hover:bg-green-700 h-12 px-6 rounded-xl text-base font-medium shadow-sm"
            >
              <Search className="h-4 w-4 mr-2" />
              {t('homepage.searchButton')}
            </Button>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════
          HOW IT WORKS — 3 Steps
          ═══════════════════════════════════════════════════════════ */}
      <section className="bg-gray-50 py-12 border-b border-gray-100">
        <div className="container mx-auto px-4 max-w-4xl">
          <h2 className="text-2xl font-semibold text-center text-gray-800 mb-8">{t('homepage.howItWorksTitle', 'How It Works')}</h2>
          <div className="flex flex-col md:flex-row items-center justify-center gap-4 md:gap-0">
            {[
              {
                step: '01',
                stepLabel: t('homepage.step01Label', 'STEP 01'),
                icon: <Search className="h-7 w-7" />,
                title: t('homepage.step01Title', 'Find a Document'),
                desc: t('homepage.step01Desc', 'Search by keyword, country, or organisation')
              },
              {
                step: '02',
                stepLabel: t('homepage.step02Label', 'STEP 02'),
                icon: <Eye className="h-7 w-7" />,
                title: t('homepage.step02Title', 'Read & Explore'),
                desc: t('homepage.step02Desc', 'View AI summaries and ask questions about any document')
              },
              {
                step: '03',
                stepLabel: t('homepage.step03Label', 'STEP 03'),
                icon: <Upload className="h-7 w-7" />,
                title: t('homepage.step03Title', 'Share Evidence'),
                desc: t('homepage.step03Desc', 'Upload anonymously — no account or identity required')
              },
            ].map((item, i) => (
              <React.Fragment key={item.step}>
                <div className="flex flex-col items-center text-center flex-1 px-4">
                  <div className="w-16 h-16 rounded-2xl bg-green-600 text-white flex items-center justify-center mb-3 shadow-md">
                    {item.icon}
                  </div>
                  <div className="text-xs font-bold text-green-600 tracking-widest mb-1">{item.stepLabel}</div>
                  <h3 className="font-semibold text-gray-900 mb-1">{item.title}</h3>
                  <p className="text-sm text-gray-500">{item.desc}</p>
                </div>
                {i < 2 && (
                  <ChevronRight className="hidden md:block h-6 w-6 text-gray-300 flex-shrink-0 mx-2" />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════
          MISSION CARDS — 3 icon cards
          ═══════════════════════════════════════════════════════════ */}
      <section className="bg-white py-14">
        <div className="container mx-auto px-4 max-w-5xl">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                icon: <Globe className="h-8 w-8 text-green-600" />,
                title: t('homepage.missionTitle'),
                desc: t('homepage.missionDescription'),
              },
              {
                icon: <Users className="h-8 w-8 text-green-600" />,
                title: t('homepage.thrivingTitle'),
                desc: t('homepage.thrivingDescription'),
              },
              {
                icon: <Shield className="h-8 w-8 text-green-600" />,
                title: t('homepage.protectedTitle'),
                desc: t('homepage.protectedDescription'),
              },
            ].map((card) => (
              <div
                key={card.title}
                className="bg-gradient-to-b from-green-50 to-white border border-green-100 rounded-2xl p-6 hover:shadow-md hover:border-green-200 transition-all duration-200"
              >
                <div className="w-12 h-12 rounded-xl bg-green-100 flex items-center justify-center mb-4">
                  {card.icon}
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{card.title}</h3>
                <p className="text-sm text-gray-600 leading-relaxed line-clamp-4">{card.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════
          PARTNERS CAROUSEL
          ═══════════════════════════════════════════════════════════ */}
      <section className="bg-gray-50 py-4 border-t border-gray-100">
        <PartnersCarousel />
      </section>

      {/* ═══════════════════════════════════════════════════════════
          WORLD MAP — Elevated, prominent
          ═══════════════════════════════════════════════════════════ */}
      <section className="bg-white py-12 border-t border-gray-100">
        <div className="container mx-auto px-4">
          <div className="text-center mb-6">
            <h2 className="text-2xl md:text-3xl font-semibold text-gray-900">
              {t('homepage.mapTitle')}
            </h2>
            <p className="text-gray-500 mt-1 text-sm">{t('homepage.mapSubtitle', 'Click any country to browse its documents')}</p>
          </div>
          <InteractiveWorldMap data={mapData} onCountryClick={handleCountryClick} />
          <div className="mt-8">
            <CountryDocStatsList />
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════
          TOP VIEWED DOCUMENTS
          ═══════════════════════════════════════════════════════════ */}
      <section className="bg-gray-50 py-4 border-t border-gray-100">
        <TopViewedDocuments />
      </section>

      {/* ═══════════════════════════════════════════════════════════
          RECENTLY SHARED DOCUMENTS
          ═══════════════════════════════════════════════════════════ */}
      <section className="bg-white py-4 border-t border-gray-100">
        <RecentlySharedDocuments />
      </section>

      {/* ═══════════════════════════════════════════════════════════
          UPLOAD CTA — Distinct from search, darker/bolder
          ═══════════════════════════════════════════════════════════ */}
      <section className="bg-green-700 py-14">
        <div className="container mx-auto px-4 text-center">
          <div className="max-w-xl mx-auto space-y-5">
            <div className="w-14 h-14 rounded-2xl bg-white/20 flex items-center justify-center mx-auto">
              <Upload className="h-7 w-7 text-white" />
            </div>
            <h2 className="text-2xl md:text-3xl font-bold text-white">
              {t('homepage.uploadTitle', 'Submit Public Interest Documents')}
            </h2>
            <p className="text-green-100 text-base leading-relaxed">
              {t('homepage.uploadDescription')}
            </p>
            <Button
              size="lg"
              onClick={() => navigate('/upload-document-page')}
              className="bg-white text-green-700 hover:bg-green-50 font-bold px-8 py-4 text-lg rounded-xl shadow-lg hover:shadow-xl transition-all duration-200"
            >
              <Upload className="h-5 w-5 mr-2" />
              {t('navigation.upload')}
              <ArrowRight className="h-5 w-5 ml-2" />
            </Button>
            <p className="text-green-200 text-sm">
              🔒 {t('homepage.uploadAnonymous', 'Upload anonymously and securely')}
            </p>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}

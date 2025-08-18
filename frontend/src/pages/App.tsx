import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Search, Upload } from "lucide-react";
import CountryDocStatsList from '../components/CountryDocStatsList';
import InteractiveWorldMap from '../components/InteractiveWorldMap';
import Version from '../components/Version';
import Navigation from '../components/Navigation';
import ProminentLanguageBar from '../components/ProminentLanguageBar';

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

export default function App() {
  const [searchTerm, setSearchTerm] = useState(""); // Added state for search term
  const [mapData, setMapData] = useState<CountryStats[]>([]);
  const [loadingMapData, setLoadingMapData] = useState(true);
  const hasFetchedMapData = useRef(false); // Track if we've already fetched to prevent duplicates
  const navigate = useNavigate(); // Added navigation hook
  const { t } = useTranslation(); // Added translation hook

  // Country code mapping for converting country names to ISO codes
  const countryCodeMapping: Record<string, string> = {
    'US': 'US',
    'United States': 'US',
    'Canada': 'CA',
    'United Kingdom': 'GB',
    'Germany': 'DE',
    'France': 'FR',
    'Spain': 'ES',
    'Italy': 'IT',
    'Netherlands': 'NL',
    'Belgium': 'BE',
    'Switzerland': 'CH',
    'Austria': 'AT',
    'Sweden': 'SE',
    'Norway': 'NO',
    'Denmark': 'DK',
    'Finland': 'FI',
    'Poland': 'PL',
    'Czech Republic': 'CZ',
    'Hungary': 'HU',
    'Romania': 'RO',
    'Bulgaria': 'BG',
    'Greece': 'GR',
    'Portugal': 'PT',
    'Ireland': 'IE',
    'Croatia': 'HR',
    'Slovenia': 'SI',
    'Slovakia': 'SK',
    'Lithuania': 'LT',
    'Latvia': 'LV',
    'Estonia': 'EE',
    'Ukraine': 'UA',
    'Russia': 'RU',
    'Turkey': 'TR',
    'China': 'CN',
    'Japan': 'JP',
    'South Korea': 'KR',
    'India': 'IN',
    'Thailand': 'TH',
    'Vietnam': 'VN',
    'Malaysia': 'MY',
    'Indonesia': 'ID',
    'Philippines': 'PH',
    'Singapore': 'SG',
    'Australia': 'AU',
    'New Zealand': 'NZ',
    'Brazil': 'BR',
    'Argentina': 'AR',
    'Mexico': 'MX',
    'Colombia': 'CO',
    'Peru': 'PE',
    'Chile': 'CL',
    'Venezuela': 'VE',
    'Ecuador': 'EC',
    'Uruguay': 'UY',
    'Paraguay': 'PY',
    'Bolivia': 'BO',
    'South Africa': 'ZA',
    'Nigeria': 'NG',
    'Egypt': 'EG',
    'Morocco': 'MA',
    'Algeria': 'DZ',
    'Tunisia': 'TN',
    'Libya': 'LY',
    'Sudan': 'SD',
    'Ethiopia': 'ET',
    'Kenya': 'KE',
    'Tanzania': 'TZ',
    'Uganda': 'UG',
    'Ghana': 'GH',
    'Ivory Coast': 'CI',
    'Senegal': 'SN',
    'Mali': 'ML',
    // Additional countries that might be in the database
    'Afghanistan': 'AF',
    'Bangladesh': 'BD',
    'Cayman Islands': 'KY',
    'Pakistan': 'PK',
    'Iran': 'IR',
    'Iraq': 'IQ',
    'Syria': 'SY',
    'Lebanon': 'LB',
    'Jordan': 'JO',
    'Israel': 'IL',
    'Palestine': 'PS',
    'Saudi Arabia': 'SA',
    'United Arab Emirates': 'AE',
    'Qatar': 'QA',
    'Kuwait': 'KW',
    'Bahrain': 'BH',
    'Oman': 'OM',
    'Yemen': 'YE',
    'Sri Lanka': 'LK',
    'Myanmar': 'MM',
    'Cambodia': 'KH',
    'Laos': 'LA',
    'Nepal': 'NP',
    'Bhutan': 'BT',
    'Maldives': 'MV',
    'Mongolia': 'MN',
    'North Korea': 'KP',
    'Taiwan': 'TW',
    'Hong Kong': 'HK',
    'Macau': 'MO',
    'Kazakhstan': 'KZ',
    'Uzbekistan': 'UZ',
    'Turkmenistan': 'TM',
    'Kyrgyzstan': 'KG',
    'Tajikistan': 'TJ',
    'Georgia': 'GE',
    'Armenia': 'AM',
    'Azerbaijan': 'AZ',
    'Belarus': 'BY',
    'Moldova': 'MD',
    'Serbia': 'RS',
    'Montenegro': 'ME',
    'Bosnia and Herzegovina': 'BA',
    'North Macedonia': 'MK',
    'Albania': 'AL',
    'Kosovo': 'XK',
    'Cyprus': 'CY',
    'Malta': 'MT',
    'Iceland': 'IS',
    'Luxembourg': 'LU',
    'Monaco': 'MC',
    'San Marino': 'SM',
    'Vatican City': 'VA',
    'Andorra': 'AD',
    'Liechtenstein': 'LI'
  };

  // Fetch country statistics for the map
  useEffect(() => {
    const fetchMapData = async () => {
      // Check if we have cached data first
              const cachedData = localStorage.getItem('haqnow_map_data');
        const cacheTimestamp = localStorage.getItem('haqnow_map_data_timestamp');
      const cacheMaxAge = 5 * 60 * 1000; // 5 minutes
      
      if (cachedData && cacheTimestamp) {
        const age = Date.now() - parseInt(cacheTimestamp);
        if (age < cacheMaxAge) {
          console.log('🎯 Using cached map data');
          const parsedData = JSON.parse(cachedData);
          setMapData(parsedData);
          setLoadingMapData(false);
          return;
        }
      }
      
      // Prevent duplicate fetches
      if (hasFetchedMapData.current) {
        console.log('🔒 Map data fetch already initiated, skipping duplicate');
        return;
      }
      hasFetchedMapData.current = true;
      
      try {
        setLoadingMapData(true);
        console.log('🚀 Fetching map data...');
        // Fixed API endpoint to match the working endpoint used in CountryDocStatsList
        const response = await fetch('/api/statistics/country-stats');
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data: StatsResponse = await response.json();
        
        console.log('Raw API response data:', data);
        
        // Convert country names to country codes for the map
        const mappedData: CountryStats[] = [];
        const unmappedCountries: string[] = [];
        
        data.countries.forEach(country => {
          const countryCode = countryCodeMapping[country.country];
          if (countryCode) {
            console.log('✅ Mapping country:', country.country, '->', countryCode, 'with', country.doc_count, 'documents');
            mappedData.push({
              countryCode,
              totalDocuments: country.doc_count
            });
          } else {
            console.warn('❌ No mapping found for country:', country.country, 'with', country.doc_count, 'documents');
            unmappedCountries.push(country.country);
          }
        });
        
        if (unmappedCountries.length > 0) {
          console.warn('🚨 Countries without ISO code mappings:', unmappedCountries);
          console.warn('Please add these countries to the countryCodeMapping object in App.tsx');
        }
        
        console.log('Final mapped data for map:', mappedData);
        console.log('Total countries with data:', data.countries.length);
        console.log('Successfully mapped countries:', mappedData.length);
        console.log('Unmapped countries:', unmappedCountries.length);
        
        // Cache the data in localStorage
                  localStorage.setItem('haqnow_map_data', JSON.stringify(mappedData));
          localStorage.setItem('haqnow_map_data_timestamp', Date.now().toString());
        console.log('💾 Map data cached to localStorage');
        
        setMapData(mappedData);
      } catch (err) {
        console.error('Error fetching map data:', err);
        // Set empty data on error - map will still work but show no data
        setMapData([]);
      } finally {
        setLoadingMapData(false);
      }
    };

    fetchMapData();
  }, []);

  // Added search handler
  const handleSearch = () => {
    if (searchTerm.trim()) {
      navigate(`/search-page?q=${encodeURIComponent(searchTerm.trim())}`);
    }
  };

  // Handle country click from map - search by country code/name
  const handleCountryClick = (countryCode: string) => {
    // Find the country name for the clicked code
    const countryName = Object.entries(countryCodeMapping).find(([name, code]) => code === countryCode)?.[0];
    if (countryName) {
      navigate(`/search-page?country=${encodeURIComponent(countryName)}`);
    }
  };



  return (
    <div className="min-h-screen bg-white">
      <ProminentLanguageBar />
      <Navigation />

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
            
            {/* Additional Upload Button */}
            <div className="mt-4 text-center">
              <Button 
                variant="outline" 
                size="lg"
                onClick={() => navigate('/upload-document-page')}
                className="px-8 py-3"
              >
                <Upload className="h-5 w-5 mr-2" />
                {t('navigation.upload')}
              </Button>
            </div>
          </section>

          <section className="space-y-6">
            <div className="text-center">
              <h3 className="text-2xl md:text-3xl font-semibold tracking-tight">
                {t('homepage.mapTitle')}
              </h3>
            </div>
            
            {/* Interactive World Map with real geographic data */}
            <InteractiveWorldMap 
              data={mapData}
              onCountryClick={handleCountryClick}
            />
            
            {/* Original CountryDocStatsList kept for additional functionality */}
            <div className="mt-8 md:mt-12">
              <CountryDocStatsList />
            </div>
          </section>
        </div>
      </main>

      <footer className="border-t border-border bg-muted/10 py-6">
        <div className="container mx-auto px-4 flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            © {new Date().getFullYear()} {t('navigation.brand')}. {t('footer.rights')}
          </p>
          <Version />
        </div>
      </footer>
    </div>
  );
}

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Globe, FileText, TrendingUp } from 'lucide-react';

// Country stats interface
interface CountryStats {
  country: string;
  doc_count: number;
}

interface StatsSummary {
  countries: CountryStats[];
  total_countries: number;
  total_documents: number;
}

// Realistic world map paths (simplified but more traditional shapes)
const WORLD_MAP_PATHS = {
  // North America
  'US': 'M 230 180 L 300 175 L 350 170 L 370 180 L 380 190 L 370 210 L 360 230 L 340 240 L 320 250 L 280 255 L 250 250 L 230 240 L 220 220 L 225 200 Z',
  'CA': 'M 200 120 L 280 115 L 360 110 L 380 120 L 370 140 L 350 150 L 320 155 L 280 160 L 240 165 L 200 160 L 180 140 L 190 130 Z',
  'MX': 'M 200 250 L 280 255 L 300 270 L 290 290 L 270 300 L 240 295 L 210 285 L 200 270 Z',
  
  // South America
  'BR': 'M 330 320 L 380 315 L 420 330 L 430 360 L 425 400 L 410 430 L 380 450 L 350 445 L 330 420 L 325 380 L 330 350 Z',
  'AR': 'M 310 400 L 340 405 L 350 440 L 345 480 L 330 510 L 315 500 L 305 470 L 308 440 Z',
  'PE': 'M 270 350 L 310 355 L 320 380 L 310 410 L 290 405 L 275 385 L 270 365 Z',
  'CO': 'M 280 300 L 320 305 L 325 325 L 315 340 L 295 335 L 280 320 Z',
  
  // Europe
  'GB': 'M 480 160 L 500 155 L 510 170 L 505 185 L 490 180 L 480 170 Z',
  'FR': 'M 480 180 L 520 175 L 530 195 L 520 215 L 500 210 L 485 195 Z',
  'DE': 'M 520 160 L 550 155 L 560 175 L 550 195 L 530 190 L 525 175 Z',
  'ES': 'M 460 200 L 500 205 L 510 225 L 495 240 L 470 235 L 460 220 Z',
  'IT': 'M 520 200 L 540 195 L 550 220 L 545 245 L 530 240 L 525 220 Z',
  'PL': 'M 540 150 L 570 145 L 580 165 L 570 185 L 550 180 L 545 165 Z',
  'RU': 'M 550 100 L 700 95 L 720 110 L 715 140 L 700 160 L 680 170 L 650 175 L 620 170 L 590 165 L 570 155 L 555 135 L 550 115 Z',
  'UA': 'M 550 170 L 590 165 L 610 180 L 600 200 L 580 195 L 560 185 Z',
  'TR': 'M 540 210 L 580 205 L 600 220 L 590 240 L 570 235 L 550 225 Z',
  'NO': 'M 520 100 L 540 95 L 545 125 L 535 140 L 525 135 L 520 115 Z',
  'SE': 'M 540 110 L 560 105 L 565 135 L 555 150 L 545 145 L 540 125 Z',
  
  // Africa
  'EG': 'M 540 250 L 570 245 L 580 270 L 575 290 L 555 285 L 545 270 Z',
  'LY': 'M 520 240 L 560 235 L 570 260 L 555 280 L 535 275 L 525 255 Z',
  'MA': 'M 460 240 L 490 235 L 500 260 L 485 275 L 470 270 L 465 255 Z',
  'NG': 'M 500 310 L 530 305 L 540 325 L 530 345 L 510 340 L 505 325 Z',
  'ZA': 'M 530 420 L 570 415 L 580 440 L 575 465 L 555 460 L 540 445 L 535 430 Z',
  'KE': 'M 580 340 L 610 335 L 620 355 L 610 375 L 590 370 L 585 355 Z',
  'ET': 'M 580 320 L 610 315 L 620 335 L 610 355 L 590 350 L 585 335 Z',
  
  // Asia
  'CN': 'M 700 180 L 780 175 L 800 190 L 795 220 L 780 240 L 760 245 L 730 240 L 710 225 L 705 205 Z',
  'IN': 'M 650 260 L 700 255 L 720 280 L 715 315 L 695 325 L 670 320 L 655 300 L 650 280 Z',
  'JP': 'M 820 200 L 840 195 L 850 220 L 845 245 L 830 240 L 825 220 Z',
  'KR': 'M 780 220 L 800 215 L 805 235 L 795 250 L 785 245 L 780 235 Z',
  'TH': 'M 720 320 L 740 315 L 750 340 L 745 360 L 730 355 L 725 340 Z',
  'VN': 'M 740 300 L 760 295 L 770 320 L 765 345 L 750 340 L 745 320 Z',
  'ID': 'M 720 380 L 780 375 L 800 395 L 790 415 L 760 410 L 730 405 L 725 390 Z',
  'MY': 'M 710 350 L 740 345 L 750 365 L 740 380 L 720 375 L 715 365 Z',
  'PH': 'M 780 340 L 800 335 L 810 355 L 800 375 L 785 370 L 780 355 Z',
  'SA': 'M 580 240 L 620 235 L 635 260 L 625 285 L 600 280 L 585 265 Z',
  'IR': 'M 600 220 L 640 215 L 655 240 L 645 265 L 620 260 L 605 245 Z',
  'IQ': 'M 580 230 L 610 225 L 620 245 L 610 265 L 590 260 L 585 245 Z',
  'AF': 'M 620 240 L 650 235 L 665 255 L 655 275 L 635 270 L 625 255 Z',
  'PK': 'M 635 250 L 665 245 L 675 270 L 665 290 L 645 285 L 640 270 Z',
  
  // Oceania
  'AU': 'M 750 400 L 820 395 L 840 415 L 830 445 L 800 450 L 770 445 L 755 425 Z',
  'NZ': 'M 850 450 L 870 445 L 875 465 L 865 480 L 855 475 L 850 465 Z',
  
  // Additional European countries
  'NL': 'M 510 160 L 530 155 L 535 170 L 525 180 L 515 175 Z',
  'BE': 'M 500 170 L 520 165 L 525 180 L 515 190 L 505 185 Z',
  'CH': 'M 520 185 L 535 180 L 540 195 L 530 205 L 525 200 Z',
  'AT': 'M 540 180 L 560 175 L 565 190 L 555 200 L 545 195 Z',
  'CZ': 'M 540 170 L 560 165 L 565 180 L 555 190 L 545 185 Z',
  'HU': 'M 550 185 L 570 180 L 575 195 L 565 205 L 555 200 Z',
  'RO': 'M 560 190 L 580 185 L 585 205 L 575 220 L 565 215 Z',
  'BG': 'M 560 210 L 580 205 L 585 220 L 575 235 L 565 230 Z',
  'GR': 'M 540 230 L 560 225 L 570 245 L 560 260 L 545 255 Z',
  'PT': 'M 440 210 L 460 205 L 465 230 L 455 245 L 445 240 Z',
};

// Traditional world map component
const WorldMapSVG = ({ stats, onCountryClick, hoveredCountry, setHoveredCountry }: {
  stats: CountryStats[];
  onCountryClick: (country: string) => void;
  hoveredCountry: string | null;
  setHoveredCountry: (country: string | null) => void;
}) => {
  const getCountryIntensity = (country: string) => {
    const countryData = stats.find(s => s.country === country);
    if (!countryData) return 0;
    
    const maxDocs = Math.max(...stats.map(s => s.doc_count));
    return countryData.doc_count / maxDocs;
  };

  const getCountryColor = (country: string) => {
    const intensity = getCountryIntensity(country);
    if (intensity === 0) return 'hsl(145, 10%, 85%)'; // Very light gray-green for no data
    
    // Green color scale matching website theme (from CSS variables)
    const colors = [
      'hsl(145, 30%, 75%)', // Light green (low activity)
      'hsl(145, 40%, 65%)', // Medium-light green
      'hsl(145, 50%, 55%)', // Medium green
      'hsl(145, 60%, 45%)', // Primary green (website theme)
      'hsl(145, 70%, 35%)', // Dark green
      'hsl(145, 75%, 25%)', // Very dark green (high activity)
    ];
    
    const colorIndex = Math.floor(intensity * (colors.length - 1));
    return colors[colorIndex];
  };

  const getStrokeColor = (country: string, isHovered: boolean) => {
    if (isHovered) return 'hsl(145, 63%, 25%)'; // Dark green for hover
    const intensity = getCountryIntensity(country);
    if (intensity === 0) return 'hsl(0, 0%, 75%)'; // Light gray border for no data
    return 'hsl(145, 50%, 40%)'; // Medium green border for data
  };

  return (
    <svg
      viewBox="0 0 900 500"
      className="w-full h-full bg-gradient-to-br from-slate-50 to-blue-50"
      style={{ borderRadius: '0.5rem' }}
    >
      <defs>
        {/* Subtle shadow for hover effect */}
        <filter id="countryHover" x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="2" dy="2" stdDeviation="3" floodColor="hsl(145, 60%, 30%)" floodOpacity="0.3"/>
        </filter>
      </defs>
      
      {/* Ocean/background */}
      <rect 
        width="100%" 
        height="100%" 
        fill="url(#oceanGradient)" 
      />
      
      <defs>
        <linearGradient id="oceanGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="hsl(210, 25%, 97%)" />
          <stop offset="100%" stopColor="hsl(210, 30%, 94%)" />
        </linearGradient>
      </defs>
      
      {/* Country paths */}
      {Object.entries(WORLD_MAP_PATHS).map(([countryCode, path]) => {
        const countryData = stats.find(s => 
          s.country.includes(countryCode) || 
          // Map country name variations
          (countryCode === 'US' && s.country.includes('United States')) ||
          (countryCode === 'GB' && s.country.includes('United Kingdom')) ||
          (countryCode === 'RU' && s.country.includes('Russia')) ||
          (countryCode === 'CN' && s.country.includes('China')) ||
          (countryCode === 'DE' && s.country.includes('Germany')) ||
          (countryCode === 'FR' && s.country.includes('France')) ||
          (countryCode === 'BR' && s.country.includes('Brazil')) ||
          (countryCode === 'IN' && s.country.includes('India')) ||
          (countryCode === 'SA' && s.country.includes('Saudi')) ||
          (countryCode === 'ZA' && s.country.includes('South Africa')) ||
          (countryCode === 'AU' && s.country.includes('Australia')) ||
          (countryCode === 'CA' && s.country.includes('Canada')) ||
          (countryCode === 'JP' && s.country.includes('Japan')) ||
          (countryCode === 'MX' && s.country.includes('Mexico')) ||
          (countryCode === 'IT' && s.country.includes('Italy')) ||
          (countryCode === 'ES' && s.country.includes('Spain')) ||
          (countryCode === 'NL' && s.country.includes('Netherlands')) ||
          (countryCode === 'TR' && s.country.includes('Turkey')) ||
          (countryCode === 'EG' && s.country.includes('Egypt')) ||
          (countryCode === 'NG' && s.country.includes('Nigeria')) ||
          (countryCode === 'AR' && s.country.includes('Argentina'))
        );
        
        const isHovered = hoveredCountry === countryData?.country;
        const hasData = countryData && countryData.doc_count > 0;
        
        return (
          <path
            key={countryCode}
            d={path}
            fill={getCountryColor(countryData?.country || '')}
            stroke={getStrokeColor(countryData?.country || '', isHovered)}
            strokeWidth={isHovered ? 2 : 1}
            opacity={hasData ? 0.9 : 0.6}
            filter={isHovered ? 'url(#countryHover)' : undefined}
            className="transition-all duration-200 cursor-pointer"
            style={{
              transformOrigin: 'center',
            }}
            onMouseEnter={() => setHoveredCountry(countryData?.country || null)}
            onMouseLeave={() => setHoveredCountry(null)}
            onClick={() => countryData && onCountryClick(countryData.country)}
          />
        );
      })}
      
      {/* Data indicators for countries with high activity */}
      {stats.filter(s => s.doc_count > 3).map((country, index) => {
        // Find approximate center of country for indicator
        const centers: {[key: string]: [number, number]} = {
          'United States': [300, 200],
          'Canada': [280, 140],
          'Brazil': [375, 380],
          'United Kingdom': [495, 170],
          'France': [505, 195],
          'Germany': [540, 175],
          'Russia': [625, 140],
          'China': [750, 210],
          'India': [675, 290],
          'Australia': [785, 425],
          'Mexico': [240, 270],
          'Japan': [835, 225],
          'South Africa': [555, 445],
        };
        
        const center = centers[country.country];
        if (!center) return null;
        
        return (
          <g key={`indicator-${index}`}>
            <circle
              cx={center[0]}
              cy={center[1]}
              r="6"
              fill="hsl(145, 70%, 25%)"
              stroke="white"
              strokeWidth="2"
              className="animate-pulse"
              opacity="0.8"
            />
            <text
              x={center[0]}
              y={center[1] + 1}
              textAnchor="middle"
              className="text-xs font-bold fill-white"
              style={{ fontSize: '10px' }}
            >
              {country.doc_count}
            </text>
          </g>
        );
      })}
    </svg>
  );
};

export default function InteractiveWorldMap() {
  const [stats, setStats] = useState<StatsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [hoveredCountry, setHoveredCountry] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchCountryStats();
  }, []);

  const fetchCountryStats = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${window.location.protocol}//${window.location.hostname}:8000/statistics/country-stats`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setStats(data);
    } catch (err) {
      console.error('Error fetching country stats:', err);
      setError('Failed to load map data');
    } finally {
      setLoading(false);
    }
  };

  const handleCountryClick = (country: string) => {
    // Navigate to search page with country filter
    navigate(`/search-page?country=${encodeURIComponent(country)}`);
  };

  if (loading) {
    return (
      <div className="bg-gradient-to-br from-slate-50 to-blue-50 border border-slate-200 rounded-lg min-h-[400px] flex items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <Globe className="h-12 w-12 text-primary animate-spin" />
          <p className="text-slate-600">Loading world map...</p>
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="bg-gradient-to-br from-red-50 to-orange-50 border border-red-200 rounded-lg min-h-[400px] flex items-center justify-center">
        <div className="text-center space-y-2">
          <p className="text-red-600">Map data unavailable</p>
          <button 
            onClick={fetchCountryStats}
            className="text-primary hover:text-primary/80 underline text-sm"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  const topCountries = stats.countries
    .sort((a, b) => b.doc_count - a.doc_count)
    .slice(0, 5);

  return (
    <div className="space-y-6">
      {/* Main Map Container */}
      <Card className="overflow-hidden border-slate-200 shadow-lg">
        <CardHeader className="bg-gradient-to-r from-green-50 to-blue-50 border-b border-slate-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Globe className="h-6 w-6 text-primary" />
              <CardTitle className="text-slate-900">
                Global Document Distribution
              </CardTitle>
            </div>
            <div className="flex items-center space-x-4 text-sm">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded" style={{ backgroundColor: 'hsl(145, 75%, 25%)' }}></div>
                <span className="text-slate-600">High Activity</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded" style={{ backgroundColor: 'hsl(145, 60%, 45%)' }}></div>
                <span className="text-slate-600">Medium Activity</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 rounded" style={{ backgroundColor: 'hsl(145, 10%, 85%)' }}></div>
                <span className="text-slate-600">No Data</span>
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="relative min-h-[400px] lg:min-h-[500px]">
            <WorldMapSVG
              stats={stats.countries}
              onCountryClick={handleCountryClick}
              hoveredCountry={hoveredCountry}
              setHoveredCountry={setHoveredCountry}
            />
            
            {/* Hover tooltip */}
            {hoveredCountry && (
              <div className="absolute top-4 left-4 bg-white border border-slate-300 rounded-lg p-3 shadow-lg z-10">
                <div className="text-primary font-semibold text-sm">
                  {hoveredCountry}
                </div>
                <div className="text-slate-600 text-sm">
                  {stats.countries.find(s => s.country === hoveredCountry)?.doc_count || 0} documents
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  Click to view documents
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="border-slate-200">
          <CardContent className="p-6 text-center">
            <FileText className="h-8 w-8 text-primary mx-auto mb-2" />
            <div className="text-2xl font-bold text-slate-900">
              {stats.total_documents}
            </div>
            <div className="text-sm text-slate-600">Total Documents</div>
          </CardContent>
        </Card>
        
        <Card className="border-slate-200">
          <CardContent className="p-6 text-center">
            <Globe className="h-8 w-8 text-primary mx-auto mb-2" />
            <div className="text-2xl font-bold text-slate-900">
              {stats.total_countries}
            </div>
            <div className="text-sm text-slate-600">Countries</div>
          </CardContent>
        </Card>
        
        <Card className="border-slate-200">
          <CardContent className="p-6 text-center">
            <TrendingUp className="h-8 w-8 text-primary mx-auto mb-2" />
            <div className="text-2xl font-bold text-slate-900">
              {Math.round(stats.total_documents / stats.total_countries)}
            </div>
            <div className="text-sm text-slate-600">Avg per Country</div>
          </CardContent>
        </Card>
      </div>

      {/* Top Countries */}
      <Card className="border-slate-200">
        <CardHeader>
          <CardTitle className="text-slate-900 flex items-center space-x-2">
            <TrendingUp className="h-5 w-5 text-primary" />
            <span>Most Active Countries</span>
          </CardTitle>
          <CardDescription className="text-slate-600">
            Countries with the highest document exposure
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {topCountries.map((country, index) => (
              <div
                key={country.country}
                className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-200 hover:border-primary cursor-pointer transition-all hover:shadow-md"
                onClick={() => handleCountryClick(country.country)}
              >
                <div className="flex items-center space-x-3">
                  <div className="text-primary font-bold text-sm w-6">
                    #{index + 1}
                  </div>
                  <div className="text-slate-900 font-medium">
                    {country.country}
                  </div>
                </div>
                <Badge variant="secondary" className="bg-primary/10 text-primary font-semibold">
                  {country.doc_count} docs
                </Badge>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 
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

// Country code mapping for SVG paths (simplified list of major countries)
const COUNTRY_PATHS = {
  // Major countries with simplified SVG paths
  'US': 'M200,180 L280,180 L280,220 L200,220 Z', // United States (simplified)
  'CN': 'M620,200 L720,200 L720,280 L620,280 Z', // China
  'RU': 'M400,120 L700,120 L700,200 L400,200 Z', // Russia
  'BR': 'M250,300 L350,300 L350,420 L250,420 Z', // Brazil
  'IN': 'M580,260 L650,260 L650,320 L580,320 Z', // India
  'AU': 'M650,380 L750,380 L750,450 L650,450 Z', // Australia
  'CA': 'M150,100 L300,100 L300,180 L150,180 Z', // Canada
  'MX': 'M150,220 L250,220 L250,300 L150,300 Z', // Mexico
  'EG': 'M480,260 L520,260 L520,300 L480,300 Z', // Egypt
  'SA': 'M520,240 L580,240 L580,300 L520,300 Z', // Saudi Arabia
  'TR': 'M480,220 L540,220 L540,260 L480,260 Z', // Turkey
  'IR': 'M540,220 L600,220 L600,280 L540,280 Z', // Iran
  'NG': 'M420,300 L460,300 L460,340 L420,340 Z', // Nigeria
  'ZA': 'M480,380 L520,380 L520,450 L480,450 Z', // South Africa
  'KE': 'M500,320 L540,320 L540,380 L500,380 Z', // Kenya
  'FR': 'M420,180 L460,180 L460,220 L420,220 Z', // France
  'DE': 'M440,160 L480,160 L480,200 L440,200 Z', // Germany
  'GB': 'M400,160 L440,160 L440,200 L400,200 Z', // United Kingdom
  'ES': 'M400,200 L440,200 L440,240 L400,240 Z', // Spain
  'IT': 'M460,200 L480,200 L480,260 L460,260 Z', // Italy
  'PL': 'M460,160 L500,160 L500,200 L460,200 Z', // Poland
  'UA': 'M480,160 L540,160 L540,200 L480,200 Z', // Ukraine
  'JP': 'M720,200 L780,200 L780,280 L720,280 Z', // Japan
  'KR': 'M700,220 L730,220 L730,260 L700,260 Z', // South Korea
  'TH': 'M620,280 L650,280 L650,340 L620,340 Z', // Thailand
  'VN': 'M650,280 L680,280 L680,340 L650,340 Z', // Vietnam
  'ID': 'M620,340 L720,340 L720,400 L620,400 Z', // Indonesia
  'PH': 'M680,300 L720,300 L720,360 L680,360 Z', // Philippines
  'MY': 'M620,320 L670,320 L670,360 L620,360 Z', // Malaysia
};

// Sample world map SVG (simplified version - in real implementation, use proper world map SVG)
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
    if (intensity === 0) return '#1f2937'; // Dark gray for no data
    
    // Corruption heat map colors: from dark red to bright orange/yellow
    const colors = [
      '#7f1d1d', // Dark red (low corruption exposure)
      '#dc2626', // Red
      '#ea580c', // Orange-red
      '#f59e0b', // Orange
      '#fbbf24', // Yellow-orange
      '#fde047', // Yellow (high corruption exposure)
    ];
    
    const colorIndex = Math.floor(intensity * (colors.length - 1));
    return colors[colorIndex];
  };

  return (
    <svg
      viewBox="0 0 800 500"
      className="w-full h-full"
      style={{ background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%)' }}
    >
      {/* Grid pattern for tech aesthetic */}
      <defs>
        <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
          <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#334155" strokeWidth="0.5" opacity="0.3"/>
        </pattern>
        
        {/* Glow effect for active countries */}
        <filter id="glow">
          <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
          <feMerge> 
            <feMergeNode in="coloredBlur"/>
            <feMergeNode in="SourceGraphic"/>
          </feMerge>
        </filter>
      </defs>
      
      {/* Grid background */}
      <rect width="100%" height="100%" fill="url(#grid)" />
      
      {/* Country paths */}
      {Object.entries(COUNTRY_PATHS).map(([countryCode, path]) => {
        const countryData = stats.find(s => s.country.includes(countryCode) || 
          // Map some common country name variations
          (countryCode === 'US' && s.country.includes('United States')) ||
          (countryCode === 'GB' && s.country.includes('United Kingdom')) ||
          (countryCode === 'RU' && s.country.includes('Russia')) ||
          (countryCode === 'CN' && s.country.includes('China')) ||
          (countryCode === 'DE' && s.country.includes('Germany')) ||
          (countryCode === 'FR' && s.country.includes('France')) ||
          (countryCode === 'BR' && s.country.includes('Brazil')) ||
          (countryCode === 'IN' && s.country.includes('India')) ||
          (countryCode === 'SA' && s.country.includes('Saudi')) ||
          (countryCode === 'ZA' && s.country.includes('South Africa'))
        );
        
        const isHovered = hoveredCountry === countryData?.country;
        const hasData = countryData && countryData.doc_count > 0;
        
        return (
          <path
            key={countryCode}
            d={path}
            fill={getCountryColor(countryData?.country || '')}
            stroke={isHovered ? '#fbbf24' : hasData ? '#f59e0b' : '#475569'}
            strokeWidth={isHovered ? 2 : 1}
            opacity={hasData ? 0.8 : 0.4}
            filter={isHovered ? 'url(#glow)' : undefined}
            className="transition-all duration-300 cursor-pointer transform hover:scale-105"
            style={{
              transformOrigin: 'center',
              boxShadow: isHovered ? '0 0 20px rgba(251, 191, 36, 0.6)' : undefined
            }}
            onMouseEnter={() => setHoveredCountry(countryData?.country || null)}
            onMouseLeave={() => setHoveredCountry(null)}
            onClick={() => countryData && onCountryClick(countryData.country)}
          />
        );
      })}
      
      {/* Animated corruption "pulse" effects for high-activity countries */}
      {stats.filter(s => s.doc_count > 5).map((country, index) => {
        const maxDocs = Math.max(...stats.map(s => s.doc_count));
        const intensity = country.doc_count / maxDocs;
        
        return (
          <circle
            key={`pulse-${index}`}
            cx={300 + (index * 80)} // Simplified positioning
            cy={200 + (index * 30)}
            r="8"
            fill="none"
            stroke="#fbbf24"
            strokeWidth="2"
            opacity={intensity}
            className="animate-pulse"
          >
            <animate
              attributeName="r"
              values="8;16;8"
              dur="3s"
              repeatCount="indefinite"
            />
            <animate
              attributeName="opacity"
              values={`${intensity};0.2;${intensity}`}
              dur="3s"
              repeatCount="indefinite"
            />
          </circle>
        );
      })}
      
      {/* Floating data points */}
      {stats.slice(0, 5).map((country, index) => (
        <g key={`point-${index}`}>
          <circle
            cx={200 + (index * 120)}
            cy={150 + Math.sin(index) * 50}
            r="4"
            fill="#fbbf24"
            className="animate-bounce"
            style={{ animationDelay: `${index * 0.5}s` }}
          />
          <text
            x={200 + (index * 120)}
            y={140 + Math.sin(index) * 50}
            textAnchor="middle"
            className="text-xs fill-yellow-300 font-mono"
          >
            {country.doc_count}
          </text>
        </g>
      ))}
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
      <div className="bg-slate-900 border border-slate-700 rounded-lg min-h-[400px] flex items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <Globe className="h-12 w-12 text-yellow-500 animate-spin" />
          <p className="text-slate-300 font-mono">Loading corruption data...</p>
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="bg-slate-900 border border-red-500/30 rounded-lg min-h-[400px] flex items-center justify-center">
        <div className="text-center space-y-2">
          <p className="text-red-400 font-mono">⚠ Map data unavailable</p>
          <button 
            onClick={fetchCountryStats}
            className="text-yellow-500 hover:text-yellow-400 underline font-mono text-sm"
          >
            Retry
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
      <Card className="bg-slate-900 border-slate-700 overflow-hidden">
        <CardHeader className="bg-gradient-to-r from-slate-800 to-slate-900 border-b border-slate-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Globe className="h-6 w-6 text-yellow-500" />
              <CardTitle className="text-slate-100 font-mono">
                Global Corruption Exposure Map
              </CardTitle>
            </div>
            <div className="flex items-center space-x-4 text-sm font-mono">
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-yellow-500 rounded"></div>
                <span className="text-slate-300">High Activity</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-red-600 rounded"></div>
                <span className="text-slate-300">Medium Activity</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-3 h-3 bg-slate-600 rounded"></div>
                <span className="text-slate-300">No Data</span>
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
              <div className="absolute top-4 left-4 bg-slate-800 border border-yellow-500/50 rounded-lg p-3 z-10">
                <div className="text-yellow-400 font-mono text-sm font-semibold">
                  {hoveredCountry}
                </div>
                <div className="text-slate-300 text-sm">
                  {stats.countries.find(s => s.country === hoveredCountry)?.doc_count || 0} documents
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  Click to view documents
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-slate-900/50 border-slate-700">
          <CardContent className="p-6 text-center">
            <FileText className="h-8 w-8 text-yellow-500 mx-auto mb-2" />
            <div className="text-2xl font-bold text-slate-100 font-mono">
              {stats.total_documents}
            </div>
            <div className="text-sm text-slate-400">Total Documents</div>
          </CardContent>
        </Card>
        
        <Card className="bg-slate-900/50 border-slate-700">
          <CardContent className="p-6 text-center">
            <Globe className="h-8 w-8 text-yellow-500 mx-auto mb-2" />
            <div className="text-2xl font-bold text-slate-100 font-mono">
              {stats.total_countries}
            </div>
            <div className="text-sm text-slate-400">Countries</div>
          </CardContent>
        </Card>
        
        <Card className="bg-slate-900/50 border-slate-700">
          <CardContent className="p-6 text-center">
            <TrendingUp className="h-8 w-8 text-yellow-500 mx-auto mb-2" />
            <div className="text-2xl font-bold text-slate-100 font-mono">
              {Math.round(stats.total_documents / stats.total_countries)}
            </div>
            <div className="text-sm text-slate-400">Avg per Country</div>
          </CardContent>
        </Card>
      </div>

      {/* Top Countries */}
      <Card className="bg-slate-900/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-slate-100 font-mono flex items-center space-x-2">
            <TrendingUp className="h-5 w-5 text-yellow-500" />
            <span>Most Active Countries</span>
          </CardTitle>
          <CardDescription className="text-slate-400">
            Countries with the highest corruption document exposure
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {topCountries.map((country, index) => (
              <div
                key={country.country}
                className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg border border-slate-700 hover:border-yellow-500/50 cursor-pointer transition-all"
                onClick={() => handleCountryClick(country.country)}
              >
                <div className="flex items-center space-x-3">
                  <div className="text-yellow-500 font-mono text-sm font-bold w-6">
                    #{index + 1}
                  </div>
                  <div className="text-slate-200 font-medium">
                    {country.country}
                  </div>
                </div>
                <Badge variant="secondary" className="bg-yellow-500/20 text-yellow-400 font-mono">
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
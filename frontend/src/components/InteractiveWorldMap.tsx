import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, CircleMarker, Tooltip } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

// Fix for default markers in react-leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface CountryStats {
  countryCode: string;
  totalDocuments: number;
}

interface InteractiveWorldMapProps {
  data?: CountryStats[];
  onCountryClick?: (countryCode: string) => void;
}

// Country center coordinates for placing circles
const countryCoordinates: Record<string, [number, number]> = {
  'AF': [33.9391, 67.7100], // Afghanistan
  'BD': [23.6850, 90.3563], // Bangladesh
  'KY': [19.3133, -81.2546], // Cayman Islands
  'CA': [56.1304, -106.3468], // Canada
  'US': [37.0902, -95.7129], // United States
  'FR': [46.6034, 1.8883], // France
  'GB': [55.3781, -3.4360], // United Kingdom
  'DE': [51.1657, 10.4515], // Germany
  'IT': [41.8719, 12.5674], // Italy
  'ES': [40.4637, -3.7492], // Spain
  'NL': [52.1326, 5.2913], // Netherlands
  'BE': [50.5039, 4.4699], // Belgium
  'CH': [46.8182, 8.2275], // Switzerland
  'AT': [47.5162, 14.5501], // Austria
  'SE': [60.1282, 18.6435], // Sweden
  'NO': [60.4720, 8.4689], // Norway
  'DK': [56.2639, 9.5018], // Denmark
  'FI': [61.9241, 25.7482], // Finland
  'PL': [51.9194, 19.1451], // Poland
  'CZ': [49.8175, 15.4730], // Czech Republic
  'SK': [48.6690, 19.6990], // Slovakia
  'HU': [47.1625, 19.5033], // Hungary
  'RO': [45.9432, 24.9668], // Romania
  'BG': [42.7339, 25.4858], // Bulgaria
  'GR': [39.0742, 21.8243], // Greece
  'PT': [39.3999, -8.2245], // Portugal
  'IE': [53.1424, -7.6921], // Ireland
  'RU': [61.5240, 105.3188], // Russia
  'CN': [35.8617, 104.1954], // China
  'JP': [36.2048, 138.2529], // Japan
  'KR': [35.9078, 127.7669], // South Korea
  'IN': [20.5937, 78.9629], // India
  'PK': [30.3753, 69.3451], // Pakistan
  'ID': [-0.7893, 113.9213], // Indonesia
  'MY': [4.2105, 101.9758], // Malaysia
  'TH': [15.8700, 100.9925], // Thailand
  'VN': [14.0583, 108.2772], // Vietnam
  'PH': [12.8797, 121.7740], // Philippines
  'SG': [1.3521, 103.8198], // Singapore
  'AU': [-25.2744, 133.7751], // Australia
  'NZ': [-40.9006, 174.8860], // New Zealand
  'ZA': [-30.5595, 22.9375], // South Africa
  'EG': [26.0975, 30.0444], // Egypt
  'NG': [9.0820, 8.6753], // Nigeria
  'KE': [-0.0236, 37.9062], // Kenya
  'MA': [31.7917, -7.0926], // Morocco
  'DZ': [28.0339, 1.6596], // Algeria
  'TN': [33.8869, 9.5375], // Tunisia
  'LY': [26.3351, 17.2283], // Libya
  'BR': [-14.2350, -51.9253], // Brazil
  'MX': [23.6345, -102.5528], // Mexico
  'AR': [-38.4161, -63.6167], // Argentina
  'CL': [-35.6751, -71.5430], // Chile
  'PE': [-9.1900, -75.0152], // Peru
  'CO': [4.5709, -74.2973], // Colombia
  'VE': [6.4238, -66.5897], // Venezuela
  'UY': [-32.5228, -55.7658], // Uruguay
  'PY': [-23.4425, -58.4438], // Paraguay
  'BO': [-16.2902, -63.5887], // Bolivia
  'EC': [-1.8312, -78.1834], // Ecuador
  'GY': [4.8604, -58.9302], // Guyana
  'SR': [3.9193, -56.0278], // Suriname
  'GF': [3.9339, -53.1258], // French Guiana
  'TR': [38.9637, 35.2433], // Turkey
  'IR': [32.4279, 53.6880], // Iran
  'IQ': [33.2232, 43.6793], // Iraq
  'SY': [34.8021, 38.9968], // Syria
  'LB': [33.8547, 35.8623], // Lebanon
  'JO': [30.5852, 36.2384], // Jordan
  'IL': [31.0461, 34.8516], // Israel
  'PS': [31.9522, 35.2332], // Palestine
  'SA': [23.8859, 45.0792], // Saudi Arabia
  'AE': [23.4241, 53.8478], // UAE
  'QA': [25.3548, 51.1839], // Qatar
  'KW': [29.3117, 47.4818], // Kuwait
  'BH': [25.9304, 50.6378], // Bahrain
  'OM': [21.5129, 55.9233], // Oman
  'YE': [15.5527, 48.5164], // Yemen
};

// Calculate circle radius based on document count
const getCircleRadius = (count: number): number => {
  if (count === 0) return 0;
  // Logarithmic scaling for better visual distribution
  // Base radius of 8, with logarithmic scaling
  return Math.max(8, Math.log(count + 1) * 10);
};

// Get circle color based on document count
const getCircleColor = (count: number): string => {
  if (count === 0) return '#e2e8f0'; // slate-300
  if (count >= 50) return '#059669'; // emerald-600
  if (count >= 20) return '#10b981'; // emerald-500
  if (count >= 10) return '#34d399'; // emerald-400
  if (count >= 5) return '#6ee7b7'; // emerald-300
  return '#a7f3d0'; // emerald-200
};

const InteractiveWorldMap: React.FC<InteractiveWorldMapProps> = ({
  data = [],
  onCountryClick
}) => {
  const [loading, setLoading] = useState(false); // No loading needed for circles

  // Create a map of country codes to document counts for quick lookup
  const dataMap = data.reduce((acc, item) => {
    acc[item.countryCode] = item.totalDocuments;
    return acc;
  }, {} as Record<string, number>);

  console.log('InteractiveWorldMap received data:', data);
  console.log('Generated dataMap:', dataMap);

  // Create circle markers for countries with data
  const renderCircleMarkers = () => {
    return Object.keys(dataMap).map(countryCode => {
      const documentCount = dataMap[countryCode];
      const coordinates = countryCoordinates[countryCode];
      
      if (!coordinates || documentCount === 0) {
        return null;
      }

      const radius = getCircleRadius(documentCount);
      const color = getCircleColor(documentCount);
      
      return (
        <CircleMarker
          key={countryCode}
          center={coordinates}
          radius={radius}
          color="#ffffff"
          weight={2}
          fillColor={color}
          fillOpacity={0.7}
          eventHandlers={{
            click: () => {
              console.log(`Clicked on ${countryCode} with ${documentCount} documents`);
              if (onCountryClick) {
                onCountryClick(countryCode);
              }
            },
            mouseover: (e) => {
              const layer = e.target;
              layer.setStyle({
                fillOpacity: 0.9,
                weight: 3
              });
            },
            mouseout: (e) => {
              const layer = e.target;
              layer.setStyle({
                fillOpacity: 0.7,
                weight: 2
              });
            }
          }}
        >
          <Tooltip>
            <div className="text-center">
              <div className="font-semibold text-slate-800">
                {getCountryName(countryCode)}
              </div>
              <div className="text-sm text-slate-600">
                {documentCount} {documentCount === 1 ? 'document' : 'documents'}
              </div>
              <div className="text-xs text-slate-500 mt-1">
                Click to explore
              </div>
            </div>
          </Tooltip>
        </CircleMarker>
      );
    }).filter(Boolean);
  };

  // Helper function to get country name from code
  const getCountryName = (code: string): string => {
    const countryNames: Record<string, string> = {
      'AF': 'Afghanistan',
      'BD': 'Bangladesh', 
      'KY': 'Cayman Islands',
      'CA': 'Canada',
      'US': 'United States',
      'FR': 'France',
      'GB': 'United Kingdom',
      'DE': 'Germany',
      'IT': 'Italy',
      'ES': 'Spain',
      'NL': 'Netherlands',
      'BE': 'Belgium',
      'CH': 'Switzerland',
      'AT': 'Austria',
      'SE': 'Sweden',
      'NO': 'Norway',
      'DK': 'Denmark',
      'FI': 'Finland',
      'PL': 'Poland',
      'CZ': 'Czech Republic',
      'SK': 'Slovakia',
      'HU': 'Hungary',
      'RO': 'Romania',
      'BG': 'Bulgaria',
      'GR': 'Greece',
      'PT': 'Portugal',
      'IE': 'Ireland',
      'RU': 'Russia',
      'CN': 'China',
      'JP': 'Japan',
      'KR': 'South Korea',
      'IN': 'India',
      'PK': 'Pakistan',
      'ID': 'Indonesia',
      'MY': 'Malaysia',
      'TH': 'Thailand',
      'VN': 'Vietnam',
      'PH': 'Philippines',
      'SG': 'Singapore',
      'AU': 'Australia',
      'NZ': 'New Zealand',
      'ZA': 'South Africa',
      'EG': 'Egypt',
      'NG': 'Nigeria',
      'KE': 'Kenya',
      'MA': 'Morocco',
      'DZ': 'Algeria',
      'TN': 'Tunisia',
      'LY': 'Libya',
      'BR': 'Brazil',
      'MX': 'Mexico',
      'AR': 'Argentina',
      'CL': 'Chile',
      'PE': 'Peru',
      'CO': 'Colombia',
      'VE': 'Venezuela',
      'UY': 'Uruguay',
      'PY': 'Paraguay',
      'BO': 'Bolivia',
      'EC': 'Ecuador',
      'GY': 'Guyana',
      'SR': 'Suriname',
      'GF': 'French Guiana',
      'TR': 'Turkey',
      'IR': 'Iran',
      'IQ': 'Iraq',
      'SY': 'Syria',
      'LB': 'Lebanon',
      'JO': 'Jordan',
      'IL': 'Israel',
      'PS': 'Palestine',
      'SA': 'Saudi Arabia',
      'AE': 'UAE',
      'QA': 'Qatar',
      'KW': 'Kuwait',
      'BH': 'Bahrain',
      'OM': 'Oman',
      'YE': 'Yemen'
    };
    return countryNames[code] || code;
  };

  // No external data loading needed - using circle markers with built-in coordinates

  if (loading) {
    return (
      <div className="w-full h-[500px] bg-gradient-to-br from-slate-50 to-blue-50 rounded-lg flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500 mx-auto mb-4"></div>
          <p className="text-slate-600">Loading world map...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-[500px] rounded-lg overflow-hidden shadow-lg relative">
      <MapContainer
        center={[20, 0]}
        zoom={2}
        style={{ height: '100%', width: '100%' }}
        worldCopyJump={true}
        maxBounds={[[-90, -180], [90, 180]]}
        maxBoundsViscosity={1.0}
      >
        {/* Map tiles */}
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          noWrap={true}
        />
        
        {/* Circle markers for countries with documents */}
        {renderCircleMarkers()}
      </MapContainer>
      
      {/* Legend for circle sizes */}
      <div className="absolute bottom-4 left-4 bg-white/90 backdrop-blur-sm rounded-lg p-3 shadow-lg z-[1000]">
        <h4 className="font-semibold text-sm mb-2 text-slate-700">Documents by Country</h4>
        <div className="space-y-2 text-xs">
          <div className="flex items-center">
            <div className="w-6 h-6 mr-2 rounded-full border-2 border-white" style={{ 
              backgroundColor: getCircleColor(50),
              transform: 'scale(1.2)'
            }}></div>
            <span>50+ docs</span>
          </div>
          <div className="flex items-center">
            <div className="w-5 h-5 mr-2 rounded-full border-2 border-white" style={{ 
              backgroundColor: getCircleColor(20)
            }}></div>
            <span>20-49 docs</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 mr-2 rounded-full border-2 border-white" style={{ 
              backgroundColor: getCircleColor(10)
            }}></div>
            <span>10-19 docs</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 mr-2 rounded-full border-2 border-white" style={{ 
              backgroundColor: getCircleColor(5)
            }}></div>
            <span>5-9 docs</span>
          </div>
          <div className="flex items-center">
            <div className="w-3 h-3 mr-2 rounded-full border-2 border-white" style={{ 
              backgroundColor: getCircleColor(1)
            }}></div>
            <span>1-4 docs</span>
          </div>
          <div className="text-xs text-slate-500 mt-2">
            Circle size = document count
          </div>
        </div>
      </div>
    </div>
  );
};

export default InteractiveWorldMap; 
import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, GeoJSON, Tooltip } from 'react-leaflet';
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

const InteractiveWorldMap: React.FC<InteractiveWorldMapProps> = ({
  data = [],
  onCountryClick
}) => {
  const [countryData, setCountryData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // Create a map of country codes to document counts for quick lookup
  const dataMap = data.reduce((acc, item) => {
    acc[item.countryCode] = item.totalDocuments;
    return acc;
  }, {} as Record<string, number>);

  console.log('InteractiveWorldMap received data:', data);
  console.log('Generated dataMap:', dataMap);

  // Load country boundaries data
  useEffect(() => {
    const loadCountryData = async () => {
      try {
        // Try multiple public GeoJSON sources for world countries
        const sources = [
          'https://raw.githubusercontent.com/hjalmar/world.geo.json/master/countries.geo.json',
          'https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson',
          'https://raw.githubusercontent.com/AshKyd/geojson-regions/master/countries/50m/all.geojson'
        ];
        
        let geoData = null;
        for (const source of sources) {
          try {
            const response = await fetch(source);
            if (response.ok) {
              geoData = await response.json();
              console.log('Successfully loaded country data from:', source);
              break;
            }
          } catch (error) {
            console.warn('Failed to load from source:', source, error);
            continue;
          }
        }
        
        if (geoData) {
          setCountryData(geoData);
        } else {
          console.warn('All external sources failed, using fallback data');
          setCountryData(createFallbackCountryData());
        }
      } catch (error) {
        console.error('Failed to load country data:', error);
        setCountryData(createFallbackCountryData());
      } finally {
        setLoading(false);
      }
    };

    loadCountryData();
  }, []);

  // Create fallback country data if external source fails
  const createFallbackCountryData = () => ({
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        properties: { ISO_A2: "US", NAME: "United States" },
        geometry: {
          type: "Polygon",
          coordinates: [[[-125, 50], [-125, 25], [-65, 25], [-65, 50], [-125, 50]]]
        }
      },
      {
        type: "Feature", 
        properties: { ISO_A2: "CA", NAME: "Canada" },
        geometry: {
          type: "Polygon",
          coordinates: [[[-140, 70], [-140, 50], [-60, 50], [-60, 70], [-140, 70]]]
        }
      },
      {
        type: "Feature",
        properties: { ISO_A2: "GB", NAME: "United Kingdom" },
        geometry: {
          type: "Polygon",
          coordinates: [[[-8, 60], [-8, 50], [2, 50], [2, 60], [-8, 60]]]
        }
      },
      {
        type: "Feature",
        properties: { ISO_A2: "DE", NAME: "Germany" },
        geometry: {
          type: "Polygon",
          coordinates: [[[5, 55], [5, 47], [15, 47], [15, 55], [5, 55]]]
        }
      },
      {
        type: "Feature",
        properties: { ISO_A2: "FR", NAME: "France" },
        geometry: {
          type: "Polygon",
          coordinates: [[[-5, 51], [-5, 42], [8, 42], [8, 51], [-5, 51]]]
        }
      },
      {
        type: "Feature",
        properties: { ISO_A2: "CN", NAME: "China" },
        geometry: {
          type: "Polygon",
          coordinates: [[[73, 53], [73, 18], [135, 18], [135, 53], [73, 53]]]
        }
      },
      {
        type: "Feature",
        properties: { ISO_A2: "RU", NAME: "Russia" },
        geometry: {
          type: "Polygon",
          coordinates: [[[19, 77], [19, 41], [180, 41], [180, 77], [19, 77]]]
        }
      },
      {
        type: "Feature",
        properties: { ISO_A2: "BR", NAME: "Brazil" },
        geometry: {
          type: "Polygon",
          coordinates: [[[-74, 5], [-74, -34], [-34, -34], [-34, 5], [-74, 5]]]
        }
      },
      {
        type: "Feature",
        properties: { ISO_A2: "AF", NAME: "Afghanistan" },
        geometry: {
          type: "Polygon",
          coordinates: [[[60, 30], [60, 20], [75, 20], [75, 30], [60, 30]]]
        }
      },
      {
        type: "Feature",
        properties: { ISO_A2: "BD", NAME: "Bangladesh" },
        geometry: {
          type: "Polygon",
          coordinates: [[[88, 22], [88, 20], [92, 20], [92, 22], [88, 22]]]
        }
      },
      {
        type: "Feature",
        properties: { ISO_A2: "KY", NAME: "Cayman Islands" },
        geometry: {
          type: "Polygon",
          coordinates: [[[-80, 19], [-80, 18], [-79, 18], [-79, 19], [-80, 19]]]
        }
      }
    ]
  });

  // Get color for country based on document count
  const getCountryColor = (countryCode: string) => {
    const count = dataMap[countryCode] || 0;
    if (count === 0) return '#e2e8f0'; // Light gray for no data
    
    // Green color scale matching website theme
    if (count >= 50) return 'hsl(145, 60%, 35%)'; // Dark green
    if (count >= 20) return 'hsl(145, 60%, 45%)'; // Medium green  
    if (count >= 10) return 'hsl(145, 60%, 55%)'; // Light green
    if (count >= 5) return 'hsl(145, 60%, 65%)';  // Very light green
    return 'hsl(145, 40%, 75%)'; // Minimal green for 1-4 docs
  };

  // Style function for GeoJSON countries
  const countryStyle = (feature: any) => {
    // Try different possible property names for country code
    const countryCode = feature.properties.ISO_A2 || 
                       feature.properties.ADM0_A3 || 
                       feature.properties.iso_a2 ||
                       feature.properties.ISO2 ||
                       feature.properties.code ||
                       feature.properties.id;
    
    const fillColor = getCountryColor(countryCode);
    
    return {
      fillColor,
      weight: 1,
      opacity: 0.8,
      color: '#6b7280',
      fillOpacity: 0.7,
    };
  };

  // Handle country interactions
  const onEachCountry = (feature: any, layer: any) => {
    // Get country name first for better matching
    const countryName = feature.properties.NAME || 
                       feature.properties.NAME_EN ||
                       feature.properties.name ||
                       feature.properties.admin ||
                       feature.properties.ADMIN ||
                       feature.properties.NAME_LONG ||
                       feature.properties.SOVEREIGN ||
                       feature.properties.sovereignt ||
                       feature.properties.NAME_SORT ||
                       feature.properties.name_en;

    // Try different possible property names for country code - expanded list
    let countryCode = feature.properties.ISO_A2 || 
                     feature.properties.ADM0_A3 || 
                     feature.properties.iso_a2 ||
                     feature.properties.ISO2 ||
                     feature.properties.code ||
                     feature.properties.id ||
                     feature.properties.iso ||
                     feature.properties.ISO ||
                     feature.properties.country_code ||
                     feature.properties.COUNTRY_CODE ||
                     feature.properties.alpha_2 ||
                     feature.properties.ALPHA_2 ||
                     feature.properties.A2 ||
                     feature.properties.iso2 ||
                     feature.properties.ADM0_A2 ||
                     feature.properties.ISO_A3 ||
                     feature.properties.ADM0_ISO ||
                     feature.properties.SU_A3;

    // Always check name-based matching first for our key countries
    if (countryName) {
      const lowerName = countryName.toLowerCase();
      if (lowerName.includes('afghanistan') || lowerName.includes('afghan')) {
        countryCode = 'AF';
      } else if (lowerName.includes('bangladesh') || lowerName.includes('bangla')) {
        countryCode = 'BD';
      } else if (lowerName.includes('cayman')) {
        countryCode = 'KY';
      } else if (lowerName.includes('united states') || lowerName === 'usa' || lowerName === 'us' || 
                 lowerName.includes('america') || lowerName === 'united states of america') {
        countryCode = 'US';
      } else if (lowerName.includes('canada') || lowerName === 'can') {
        countryCode = 'CA';
      }
    }

    // Normalize existing country code to uppercase and handle 3-letter codes
    if (countryCode && !['AF', 'BD', 'KY', 'US', 'CA'].includes(countryCode)) {
      countryCode = countryCode.toString().toUpperCase();
      
      // Convert 3-letter codes to 2-letter codes for common countries
      const iso3ToIso2 = {
        'AFG': 'AF', // Afghanistan
        'BGD': 'BD', // Bangladesh  
        'CYM': 'KY', // Cayman Islands
        'USA': 'US', // United States
        'CAN': 'CA'  // Canada
      };
      
      if (iso3ToIso2[countryCode]) {
        countryCode = iso3ToIso2[countryCode];
      }
    }

    // Alternative: try to match by exact country name if no code found or code doesn't match our data
    if (!countryCode || !dataMap[countryCode]) {
      if (countryName) {
        const nameToCode = {
          'Afghanistan': 'AF',
          'Bangladesh': 'BD', 
          'Cayman Islands': 'KY',
          'Cayman Is.': 'KY',
          'United States': 'US',
          'United States of America': 'US',
          'USA': 'US',
          'Canada': 'CA',
          // Add more variations
          'Islamic Republic of Afghanistan': 'AF',
          'Afghanistan, Islamic Republic of': 'AF',
          'People\'s Republic of Bangladesh': 'BD',
          'Bangladesh, People\'s Republic of': 'BD',
          'Cayman': 'KY'
        };
        
        const matchedCode = nameToCode[countryName];
        if (matchedCode) {
          countryCode = matchedCode;
        }
      }
    }
                       
    const documentCount = dataMap[countryCode] || 0;

    // Enhanced debugging for ALL countries that should have data
    const expectedCountries = ['AF', 'BD', 'KY', 'US', 'CA']; // All countries we know should have data
    const isExpectedCountry = expectedCountries.includes(countryCode) || 
                             countryName?.toLowerCase().includes('afghanistan') ||
                             countryName?.toLowerCase().includes('bangladesh') ||
                             countryName?.toLowerCase().includes('cayman') ||
                             countryName?.toLowerCase().includes('united states') ||
                             countryName?.toLowerCase().includes('america') ||
                             countryName?.toLowerCase().includes('canada');

    // Also check if this country matches any of our expected data
    const hasExpectedData = Object.keys(dataMap).some(code => dataMap[code] > 0);
    
    if (isExpectedCountry || documentCount > 0 || 
        (hasExpectedData && (countryName?.toLowerCase().includes('afghan') ||
                            countryName?.toLowerCase().includes('bangla') ||
                            countryName?.toLowerCase().includes('cayman') ||
                            countryName?.toLowerCase().includes('united states') ||
                            countryName?.toLowerCase().includes('america') ||
                            countryName?.toLowerCase().includes('canada')))) {
      console.log('🔍 DETAILED COUNTRY ANALYSIS:', {
        countryName,
        extractedCountryCode: countryCode,
        documentCount,
        expectedInDataMap: dataMap[countryCode],
        allAvailableProperties: feature.properties,
        matchedFromDataMap: Object.keys(dataMap).includes(countryCode),
        dataMapKeys: Object.keys(dataMap),
        dataMapEntries: Object.entries(dataMap),
        // Show all property values, not just keys
        propertyValues: Object.entries(feature.properties).map(([key, value]) => `${key}: ${value}`).join(', ')
      });
    }

    // Log ALL target countries to find our data
    if (countryName && (countryName.toLowerCase().includes('afghan') || 
                       countryName.toLowerCase().includes('bangla') || 
                       countryName.toLowerCase().includes('cayman') ||
                       countryName.toLowerCase().includes('united states') ||
                       countryName.toLowerCase().includes('america') ||
                       countryName.toLowerCase().includes('canada'))) {
      console.log('🎯 FOUND TARGET COUNTRY:', {
        originalName: countryName,
        extractedCode: countryCode,
        allProperties: feature.properties,
        documentCount,
        shouldHaveData: 'YES - This should show 1 document!',
        isInDataMap: Object.keys(dataMap).includes(countryCode),
        dataMapHasThisCode: dataMap[countryCode] !== undefined,
        dataMapValue: dataMap[countryCode]
      });
    }

    // Enhanced debugging for data integration - only log relevant countries
    const isRelevantCountry = documentCount > 0 || 
                             countryName?.toLowerCase().includes('afghan') ||
                             countryName?.toLowerCase().includes('bangla') ||
                             countryName?.toLowerCase().includes('cayman') ||
                             expectedCountries.includes(countryCode);

    if (isRelevantCountry) {
      console.log('Processing country:', {
        countryCode,
        countryName,
        documentCount,
        availableProperties: Object.keys(feature.properties),
        allProperties: feature.properties
      });
    }
    
    if (documentCount > 0) {
      console.log('✅ Country with data found:', {
        countryCode,
        countryName,
        documentCount
      });
    } else if (countryCode && isRelevantCountry) {
      console.log('ℹ️ Relevant country with no documents:', {
        countryCode,
        countryName,
        documentCount: 0
      });
    } else if (!countryCode && isRelevantCountry) {
      console.warn('⚠️ Relevant country with no valid code:', {
        countryName,
        availableProperties: Object.keys(feature.properties)
      });
    }

    // Add hover effects
    layer.on({
      mouseover: (e: any) => {
        const layer = e.target;
        layer.setStyle({
          weight: 2,
          color: 'hsl(145, 60%, 30%)',
          fillOpacity: 0.9,
        });
      },
      mouseout: (e: any) => {
        const layer = e.target;
        layer.setStyle(countryStyle(feature));
      },
      click: () => {
        if (onCountryClick && countryCode) {
          onCountryClick(countryCode);
        }
      }
    });

    // Bind tooltip with country info
    layer.bindTooltip(
      `<div style="text-align: center;">
        <strong>${countryName}</strong><br/>
        ${documentCount} document${documentCount !== 1 ? 's' : ''}
      </div>`,
      {
        permanent: false,
        sticky: true,
        className: 'country-tooltip'
      }
    );
  };

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
    <div className="w-full h-[500px] rounded-lg overflow-hidden shadow-lg">
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
        
        {/* Country boundaries with data */}
        {countryData && (
          <GeoJSON
            data={countryData}
            style={countryStyle}
            onEachFeature={onEachCountry}
          />
        )}
      </MapContainer>
      
      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-white/90 backdrop-blur-sm rounded-lg p-3 shadow-lg z-[1000]">
        <h4 className="font-semibold text-sm mb-2 text-slate-700">Documents</h4>
        <div className="space-y-1 text-xs">
          <div className="flex items-center">
            <div className="w-4 h-3 mr-2 rounded" style={{ backgroundColor: 'hsl(145, 60%, 35%)' }}></div>
            <span>50+ docs</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-3 mr-2 rounded" style={{ backgroundColor: 'hsl(145, 60%, 45%)' }}></div>
            <span>20-49 docs</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-3 mr-2 rounded" style={{ backgroundColor: 'hsl(145, 60%, 55%)' }}></div>
            <span>10-19 docs</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-3 mr-2 rounded" style={{ backgroundColor: 'hsl(145, 60%, 65%)' }}></div>
            <span>5-9 docs</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-3 mr-2 rounded" style={{ backgroundColor: 'hsl(145, 40%, 75%)' }}></div>
            <span>1-4 docs</span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-3 mr-2 rounded bg-slate-300"></div>
            <span>No data</span>
          </div>
        </div>
      </div>
      
      {/* Custom styles for tooltips */}
      <style jsx global>{`
        .country-tooltip {
          background: rgba(255, 255, 255, 0.95) !important;
          border: 1px solid hsl(145, 60%, 50%) !important;
          border-radius: 6px !important;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
          font-size: 12px !important;
          padding: 6px 8px !important;
        }
        .country-tooltip::before {
          border-top-color: hsl(145, 60%, 50%) !important;
        }
      `}</style>
    </div>
  );
};

export default InteractiveWorldMap; 
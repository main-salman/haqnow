import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { AlertCircle, Loader2, ChevronDown } from 'lucide-react';

// Remove brain import and use direct API call
// import brain from 'brain';

// Updated type definitions to match backend API
interface CountryStat {
  country: string;
  doc_count: number;
}

interface CountryStatsResponse {
  countries: CountryStat[];
  total_countries: number;
  total_documents: number;
}

export interface Props {}

const CountryDocStatsList: React.FC<Props> = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<CountryStat[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCountry, setSelectedCountry] = useState<string>("");

  useEffect(() => {
    const fetchStats = async () => {
      setIsLoading(true);
      setError(null);
      try {
        // Make direct API call to statistics endpoint
        const response = await fetch('/api/statistics/country-stats');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data: CountryStatsResponse = await response.json();
        // Use the 'countries' field from the API response
        setStats(data.countries);
      } catch (err) {
        console.error("Error fetching country stats:", err);
        let errorMessage = "Failed to load document statistics.";
        if (err instanceof Error) {
          errorMessage = err.message;
        }
        setError(errorMessage);
      } finally {
        setIsLoading(false);
      }
    };

    fetchStats();
  }, []);

  const handleCountrySelect = (countryName: string) => {
    setSelectedCountry(countryName);
    navigate(`/search-page?country=${encodeURIComponent(countryName)}`);
  };

  const getSelectedCountryStats = () => {
    if (!selectedCountry) return null;
    return stats.find(stat => stat.country === selectedCountry);
  };

  if (isLoading) {
    return (
      <Card className="w-full shadow-lg">
        <CardHeader>
          <CardTitle className="text-xl font-semibold font-serif">Top Countries by Documents</CardTitle>
        </CardHeader>
        <CardContent className="flex justify-center items-center min-h-[200px]">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="ml-2 text-muted-foreground">Loading statistics...</p>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="w-full shadow-lg">
        <CardHeader>
          <CardTitle className="text-xl font-semibold font-serif">Top Countries by Documents</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center min-h-[200px] text-destructive">
          <AlertCircle className="h-8 w-8 mb-2" />
          <p className="font-semibold">Error loading statistics</p>
          <p className="text-sm">{error}</p>
        </CardContent>
      </Card>
    );
  }

  if (stats.length === 0) {
    return (
      <Card className="w-full shadow-lg">
        <CardHeader>
          <CardTitle className="text-xl font-semibold font-serif">Documents by Country</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">No document statistics available at the moment.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full shadow-lg">
      <CardHeader>
        <CardTitle className="text-xl font-semibold font-serif">Documents by Country</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium text-foreground">Select a Country:</label>
            <Select value={selectedCountry} onValueChange={handleCountrySelect}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Choose a country to view documents..." />
              </SelectTrigger>
              <SelectContent>
                {stats.map((stat) => (
                  <SelectItem key={stat.country} value={stat.country}>
                    <div className="flex justify-between items-center w-full">
                      <span>{stat.country}</span>
                      <span className="ml-4 font-semibold text-primary">({stat.doc_count} docs)</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {selectedCountry && getSelectedCountryStats() && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="font-semibold text-gray-900">{selectedCountry}</h3>
                  <p className="text-sm text-gray-600">Click below to view all documents</p>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-primary">{getSelectedCountryStats()?.doc_count}</div>
                  <div className="text-xs text-gray-500">documents</div>
                </div>
              </div>
              <Button 
                className="w-full mt-3" 
                onClick={() => navigate(`/search-page?country=${encodeURIComponent(selectedCountry)}`)}
              >
                View {selectedCountry} Documents →
              </Button>
            </div>
          )}

          <div className="text-xs text-gray-500 text-center">
            Total countries with documents: {stats.length}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default CountryDocStatsList;

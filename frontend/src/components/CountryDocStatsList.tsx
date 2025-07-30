import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertCircle, Loader2 } from 'lucide-react';

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

  const handleCountryClick = (countryName: string) => {
    navigate(`/search-page?country=${encodeURIComponent(countryName)}`);
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
        <CardTitle className="text-xl font-semibold font-serif">Top Countries by Documents</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {stats.map((stat) => (
            <div 
              key={stat.country} 
              onClick={() => handleCountryClick(stat.country)}
              className="flex justify-between items-center p-3 rounded-md hover:bg-muted/50 cursor-pointer transition-colors border border-transparent hover:border-primary/30"
            >
              <span className="font-medium text-foreground text-lg">{stat.country}</span>
              <span className="text-lg font-semibold text-primary">{stat.doc_count}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default CountryDocStatsList;

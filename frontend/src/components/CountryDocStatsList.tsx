import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
// import { List, ListItem } from "@/components/ui/list"; // Removed unused import
import { Button } from "@/components/ui/button"; // Kept for potential future use, though not used in current list item action
import { AlertCircle, Loader2 } from 'lucide-react';

import brain from 'brain';
import type { CountryStat, CountryStatsResponse } from 'types'; // Using 'types' which re-exports from brain/data-contracts

// Mock data - REMOVE THIS LATER
// const mockCountryStats: CountryStat[] = [
//   { country: "United States", doc_count: 178 },
//   { country: "Canada", doc_count: 120 },
//   { country: "United Kingdom", doc_count: 95 },
//   { country: "Germany", doc_count: 60 },
//   { country: "Australia", doc_count: 45 },
//   { country: "France", doc_count: 30 },
// ];

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
        const response = await brain.get_docs_by_country();
        // Assuming brain client directly returns the parsed JSON data (CountryStatsResponse)
        // If it returns a HttpResponse, you might need: const data: CountryStatsResponse = await response.json();
        // Based on current setup, brain client methods return HttpResponse, so .json() is needed.
        const data: CountryStatsResponse = await response.json();
        setStats(data.stats);
      } catch (err) {
        console.error("Error fetching country stats:", err);
        let errorMessage = "Failed to load document statistics.";
        if (err instanceof Error) {
          errorMessage = err.message;
        }
        // Consider more specific error messages based on err type if possible
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
              <span className="font-medium text-foreground text-base">{stat.country}</span>
              <span className="text-lg font-semibold text-primary">{stat.doc_count}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default CountryDocStatsList;

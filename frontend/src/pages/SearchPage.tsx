import React, { useState, useEffect, useCallback } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Loader2,
  Search as SearchIcon,
  AlertCircle,
  ArrowLeft,
  FileText,
} from "lucide-react";
import { toast } from "sonner";

// Define the document result interface
interface SearchDocumentResult {
  id: number;
  title?: string;
  country?: string;
  state?: string;
  file_path?: string;
  file_url?: string;
  generated_tags?: string[];
  ocr_text?: string;
  description?: string;
  created_at?: string;
}

export default function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const [tagsInput, setTagsInput] = useState(searchParams.get("tags") || "");
  const [searchResults, setSearchResults] = useState<SearchDocumentResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchAttempted, setSearchAttempted] = useState(false);
  const [downloadingDocId, setDownloadingDocId] = useState<number | null>(null);

  const handleDocumentClick = useCallback(async (documentId: number) => {
    setDownloadingDocId(documentId);
    
    try {
      // Direct download - the server now streams the file directly
      const downloadUrl = `/api/search/download/${documentId}`;
      
      // Create a temporary link element and click it to trigger download
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      
      // Add the link to the document, click it, and remove it
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      toast.success("Document download started");
    } catch (err: any) {
      let errorMsg = "Failed to download document.";
      if (err.message) {
        errorMsg = err.message;
      }
      toast.error(`Document download failed: ${errorMsg}`);
    } finally {
      setDownloadingDocId(null);
    }
  }, []);

  const performSearch = useCallback(
    async (tagsToSearch: string, countryFilter?: string | null) => {
      if (!tagsToSearch.trim()) {
        setSearchResults([]);
        setError(null);
        if (searchAttempted) {
          setError(null);
        }
        return;
      }

      setIsLoading(true);
      setError(null);
      setSearchAttempted(true);
      
      // Update URL params
      const newParams: Record<string, string> = { q: tagsToSearch };
      if (countryFilter) {
        newParams.country = countryFilter;
      }
      setSearchParams(newParams);

      try {
        console.log(`[SearchPage] Searching for tags: ${tagsToSearch}, country: ${countryFilter || 'none'}`);
        
        // Use the new backend search API
        const searchUrl = new URL('/api/search/search', window.location.origin);
        searchUrl.searchParams.append('q', tagsToSearch);
        searchUrl.searchParams.append('per_page', '50');
        
        // Add country filter if provided
        if (countryFilter) {
          searchUrl.searchParams.append('country', countryFilter);
        }
        
        const response = await fetch(searchUrl.toString(), {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        console.log("[SearchPage] Search results:", data);

        if (data && data.documents) {
          setSearchResults(data.documents);
        } else {
          setSearchResults([]);
        }
      } catch (err: any) {
        console.error("[SearchPage] Search error:", err);
        let errorMsg = "An error occurred while searching.";
        if (err.message) {
          errorMsg = err.message;
        }
        setError(errorMsg);
        setSearchResults([]);
        toast.error(`Search failed: ${errorMsg}`);
      } finally {
        setIsLoading(false);
      }
    },
    [setSearchParams, searchAttempted],
  );

  useEffect(() => {
    const initialTags = searchParams.get("tags") || searchParams.get("q");
    const initialCountry = searchParams.get("country");
    
    if (initialTags) {
      setTagsInput(initialTags);
      performSearch(initialTags, initialCountry);
    } else if (initialCountry) {
      // If only country is provided, search for that country
      setTagsInput(initialCountry);
      performSearch(initialCountry, initialCountry);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Run only on initial mount to get tags from URL

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setTagsInput(e.target.value);
    if (!e.target.value.trim()) {
      // If input is cleared
      setSearchAttempted(false); // Reset search attempted
      setSearchResults([]);
      setError(null);
      setSearchParams({}); // Optionally clear URL params
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    performSearch(tagsInput);
  };

  return (
    <div className="container mx-auto p-4 md:p-8 max-w-4xl">
      <Button variant="outline" onClick={() => navigate("/")} className="mb-6">
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to Home
      </Button>

      <h1 className="text-3xl font-bold mb-2 font-serif text-center">
        Search Documents by Tags
      </h1>
      <p className="text-muted-foreground mb-8 text-center">
        Enter comma-separated tags to find relevant documents.
      </p>

      <form onSubmit={handleSubmit} className="flex items-center space-x-2 mb-8">
        <Input
          type="text"
          placeholder="e.g., report, budget, environment"
          value={tagsInput}
          onChange={handleInputChange}
          className="flex-grow text-base p-3"
        />
        <Button type="submit" size="lg" disabled={isLoading}>
          {isLoading ? (
            <Loader2 className="mr-2 h-5 w-5 animate-spin" />
          ) : (
            <SearchIcon className="mr-2 h-5 w-5" />
          )}
          Search
        </Button>
      </form>

      {isLoading && (
        <div className="flex justify-center items-center py-10">
          <Loader2 className="h-12 w-12 animate-spin text-primary" />
          <p className="ml-3 text-lg">Searching...</p>
        </div>
      )}

      {!isLoading && error && (
        <Card className="bg-destructive/10 border-destructive">
          <CardHeader>
            <CardTitle className="flex items-center text-destructive">
              <AlertCircle className="mr-2 h-5 w-5" /> Search Error
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p>{error}</p>
          </CardContent>
        </Card>
      )}

      {!isLoading &&
        !error &&
        searchAttempted &&
        searchResults.length === 0 && (
          <div className="text-center text-muted-foreground py-12">
            <FileText className="h-16 w-16 mx-auto mb-4 text-gray-400" />
            <p className="text-xl font-semibold">No Documents Found</p>
            <p>
              No documents matched the tags: "{tagsInput}". Try different or
              broader tags.
            </p>
          </div>
        )}

      {!isLoading && !error && searchResults.length > 0 && (
        <div className="space-y-6">
          <h2 className="text-2xl font-semibold">
            Found {searchResults.length} document
            {searchResults.length === 1 ? "" : "s"}
          </h2>
          {searchResults.map((doc) => (
            <Card
              key={doc.id}
              className="hover:shadow-lg transition-shadow duration-200 ease-in-out"
            >
              <CardHeader>
                <CardTitle className="text-xl font-serif">
                  {doc.id ? (
                    <button
                      onClick={() => handleDocumentClick(doc.id)}
                      className="text-primary hover:underline text-left flex items-center gap-2"
                      disabled={downloadingDocId === doc.id}
                    >
                      {downloadingDocId === doc.id && (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      )}
                      {doc.title || "Untitled Document"}
                    </button>
                  ) : (
                    doc.title || "Untitled Document"
                  )}
                </CardTitle>
                <CardDescription>
                  Country: {doc.country || "N/A"}
                </CardDescription>
              </CardHeader>
              <CardContent>
                {doc.description && (
                  <div className="mb-4">
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {doc.description}
                    </p>
                  </div>
                )}
                {doc.generated_tags && doc.generated_tags.length > 0 && (
                  <div className="mb-3">
                    <h4 className="text-sm font-medium mb-1 text-muted-foreground">
                      Tags:
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {doc.generated_tags.map((tag, index) => (
                        <Badge
                          key={index}
                          variant="secondary"
                          className="text-xs"
                        >
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
                {!doc.generated_tags ||
                  (doc.generated_tags.length === 0 && (
                    <p className="text-sm text-muted-foreground">
                      No tags available for this document.
                    </p>
                  ))}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

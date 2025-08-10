import React, { useState, useEffect, useCallback } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Loader2,
  Search as SearchIcon,
  AlertCircle,
  ArrowLeft,
  FileText,
  Brain,
} from "lucide-react";
import { toast } from "sonner";
import Navigation from "@/components/Navigation";
// Removed global AI Q&A per design change

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
  document_language?: string;  // Language of the original document
  has_arabic_text?: boolean;   // Whether Arabic text is available for download
  has_english_translation?: boolean;  // Whether English translation is available for download
}

export default function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState("search");

  const [tagsInput, setTagsInput] = useState(searchParams.get("tags") || "");
  const [searchResults, setSearchResults] = useState<SearchDocumentResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchAttempted, setSearchAttempted] = useState(false);
  const [downloadingDocId, setDownloadingDocId] = useState<number | null>(null);

  // Extract initial country filter from URL
  const countryFilter = searchParams.get("country");

  const handleDocumentClick = async (docId: number, format: "original" | "english" | string) => {
    try {
      setDownloadingDocId(docId);
      
      // Different endpoints based on format
      let endpoint;
      if (format === "original") {
        endpoint = `/api/search/download/${docId}`;
      } else if (format === "english") {
        endpoint = `/api/search/download/${docId}?language=english`;
      } else {
        // For specific language downloads
        endpoint = `/api/search/download/${docId}?language=${format}`;
      }
      
      const response = await fetch(endpoint);
      
      if (!response.ok) {
        try {
          const data = await response.json();
          if (response.status === 429 && data?.detail) {
            toast.error(data.detail);
          } else if (data?.detail) {
            toast.error(`Failed to download: ${data.detail}`);
          } else {
            toast.error(`Failed to download: ${response.statusText}`);
          }
        } catch (_) {
          toast.error(`Failed to download: ${response.statusText}`);
        }
        return;
      }
      
      // Get the filename from response headers or create a default one
      const contentDisposition = response.headers.get('content-disposition');
      let filename = `document_${docId}`;
      
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="(.+)"/);
        if (filenameMatch) {
          filename = filenameMatch[1];
        }
      } else {
        // Add appropriate extension based on format
        if (format === "original") {
          filename += ".pdf";
        } else {
          filename += ".txt";
        }
      }
      
      // Create blob and download
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      toast.success(`Downloaded: ${filename}`);
    } catch (error) {
      console.error('Download failed:', error);
      toast.error('Failed to download document');
    } finally {
      setDownloadingDocId(null);
    }
  };

  const performSearch = useCallback(
    async (tagsToSearch: string, specificCountry?: string | null) => {
      const finalCountryFilter = specificCountry !== undefined ? specificCountry : countryFilter;
      
      // Allow empty searches when there's a country filter
      if (!tagsToSearch.trim() && !finalCountryFilter) {
        if (searchAttempted) {
          toast.error(t('search.enterTags'));
        }
        return;
      }

      setIsLoading(true);
      setError(null);
      setSearchAttempted(true);
      
      // Update URL params
      const newParams: Record<string, string> = {};
      if (tagsToSearch.trim()) {
        newParams.q = tagsToSearch;
      }
      if (finalCountryFilter) {
        newParams.country = finalCountryFilter;
      }
      setSearchParams(newParams);

      try {
        console.log(`[SearchPage] Searching for tags: ${tagsToSearch}, country: ${finalCountryFilter || 'none'}`);
        
        // Use the new backend search API
        const searchUrl = new URL('/api/search/search', window.location.origin);
        searchUrl.searchParams.append('q', tagsToSearch || ''); // Allow empty queries for country-only searches
        searchUrl.searchParams.append('per_page', '50');
        
        // Add country filter if provided
        if (finalCountryFilter) {
          searchUrl.searchParams.append('country', finalCountryFilter);
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
        console.log('[SearchPage] Search results:', data);

        if (data.documents && Array.isArray(data.documents)) {
          setSearchResults(data.documents);
          if (data.documents.length === 0) {
            toast.info(t('search.noResults'));
          } else {
            toast.success(`${data.documents.length} ${t('search.resultsFound')}`);
          }
        } else {
          console.error('[SearchPage] Unexpected response format:', data);
          setError('Unexpected response format from server');
        }
      } catch (err) {
        console.error('[SearchPage] Search error:', err);
        setError(err instanceof Error ? err.message : 'An error occurred while searching');
        toast.error(t('search.error'));
      } finally {
        setIsLoading(false);
      }
    },
    [setSearchParams, searchAttempted, countryFilter, t],
  );

  useEffect(() => {
    const initialTags = searchParams.get("tags") || searchParams.get("q");
    const initialCountry = searchParams.get("country");
    
    if (initialTags) {
      setTagsInput(initialTags);
      performSearch(initialTags, initialCountry);
    } else if (initialCountry) {
      // If only country is provided, show all documents from that country
      setTagsInput(""); // Clear the search input
      performSearch("", initialCountry); // Empty query with country filter
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
    <div className="min-h-screen bg-white">
      <Navigation />
      <div className="container mx-auto p-4 md:p-8 max-w-4xl">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Search
          </h1>
          <div className="w-24 h-1 bg-green-600 mx-auto mb-6"></div>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Find corruption documents using keyword search. For AI questions, open a document and use the AI button on its page.
          </p>
        </div>

        {/* Search Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-1">
            <TabsTrigger value="search" className="flex items-center space-x-2">
              <SearchIcon className="w-4 h-4" />
              <span>Document Search</span>
            </TabsTrigger>
          </TabsList>

          {/* Traditional Search Tab */}
          <TabsContent value="search" className="space-y-6 mt-6">
            {/* Search Input */}
            <Card className="w-full shadow-lg">
              <CardHeader className="text-center">
                <CardTitle className="text-2xl font-serif">
                  Document Search
                </CardTitle>
                <CardDescription>
                  Enter keywords or tags to find relevant documents
                </CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <label htmlFor="tags" className="text-sm font-medium">
                      Search Keywords
                    </label>
                    <Input
                      id="tags"
                      type="text"
                      placeholder="Enter keywords like: corruption, bribery, fraud, contracts..."
                      value={tagsInput}
                      onChange={handleInputChange}
                      className="text-base"
                    />
                    <p className="text-xs text-muted-foreground">
                      Search for documents by entering relevant keywords, country names, or corruption types
                    </p>
                  </div>
                  <Button type="submit" className="w-full" disabled={isLoading}>
                    {isLoading ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        {t('search.searching')}
                      </>
                    ) : (
                      <>
                        <SearchIcon className="h-4 w-4 mr-2" />
                        {t('search.searchButton')}
                      </>
                    )}
                  </Button>
                </form>
              </CardContent>
            </Card>

            {/* Error Display */}
            {error && (
              <Card className="border-destructive">
                <CardContent className="pt-6">
                  <div className="flex items-center space-x-2 text-destructive">
                    <AlertCircle className="h-5 w-5" />
                    <span>{error}</span>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* No Results Message */}
            {!isLoading && !error && searchAttempted && 
              searchResults.length === 0 && (
                <div className="text-center text-muted-foreground py-12">
                  <FileText className="h-16 w-16 mx-auto mb-4 text-gray-400" />
                  <p className="text-xl font-semibold">{t('search.noResults')}</p>
                  <p>
                    {t('search.tryDifferent')}
                  </p>
                </div>
              )}

            {/* Search Results */}
            {!isLoading && !error && searchResults.length > 0 && (
              <div className="space-y-6">
                <h2 className="text-2xl font-semibold">
                  {searchResults.length} {t('search.resultsFound')}
                </h2>
                {searchResults.map((doc) => (
                  <Card
                    key={doc.id}
                    className="hover:shadow-lg transition-shadow duration-200 ease-in-out"
                  >
                    <CardHeader>
                      <CardTitle className="text-xl font-serif">
                        {doc.title || "Untitled Document"}
                      </CardTitle>
                      <CardDescription>
                        {t('search.country')}: {doc.country || "N/A"}
                        {doc.document_language && doc.document_language !== 'english' && (
                          <Badge variant="outline" className="ml-2">
                            {doc.document_language === 'arabic' ? 'العربية' : doc.document_language}
                          </Badge>
                        )}
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
                      
                      {/* Download Options */}
                      <div className="mb-4">
                        <h4 className="text-sm font-medium mb-2 text-muted-foreground">
                          Download Options:
                        </h4>
                        <div className="flex flex-wrap gap-2">
                          {/* Original File Download */}
                          <Button
                            onClick={() => handleDocumentClick(doc.id, "original")}
                            disabled={downloadingDocId === doc.id}
                            size="sm"
                            variant="default"
                            className="flex items-center gap-2"
                          >
                            {downloadingDocId === doc.id && (
                              <Loader2 className="h-3 w-3 animate-spin" />
                            )}
                            <FileText className="h-3 w-3" />
                            Original PDF
                          </Button>
                          
                          {/* English Translation Download (for multilingual documents) */}
                          {doc.document_language !== 'english' && doc.has_english_translation && (
                            <Button
                              onClick={() => handleDocumentClick(doc.id, "english")}
                              disabled={downloadingDocId === doc.id}
                              size="sm"
                              variant="outline"
                              className="flex items-center gap-2"
                            >
                              {downloadingDocId === doc.id && (
                                <Loader2 className="h-3 w-3 animate-spin" />
                              )}
                              <FileText className="h-3 w-3" />
                              English Translation
                            </Button>
                          )}
                          
                          {/* Original Language Text Download (for multilingual documents) */}
                          {doc.document_language !== 'english' && doc.has_english_translation && (
                            <Button
                              onClick={() => handleDocumentClick(doc.id, doc.document_language.toLowerCase())}
                              disabled={downloadingDocId === doc.id}
                              size="sm"
                              variant="outline"
                              className="flex items-center gap-2"
                            >
                              {downloadingDocId === doc.id && (
                                <Loader2 className="h-3 w-3 animate-spin" />
                              )}
                              <FileText className="h-3 w-3" />
                              {doc.document_language.charAt(0).toUpperCase() + doc.document_language.slice(1)} Text
                            </Button>
                          )}

                          {/* Ask AI about this document */}
                          <Button asChild size="sm" variant="outline" className="flex items-center gap-2">
                            <Link to={`/document-detail-page?id=${doc.id}`}>
                              <Brain className="h-3 w-3" />
                              Ask Questions About this Document
                            </Link>
                          </Button>
                          
                          {/* Info message for multilingual documents without translation */}
                          {doc.document_language !== 'english' && !doc.has_english_translation && (
                            <div className="text-sm text-muted-foreground italic">
                              English translation processing... (may take a few minutes for new uploads)
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {doc.generated_tags && doc.generated_tags.length > 0 && (
                        <div className="mb-3">
                          <h4 className="text-sm font-medium mb-1 text-muted-foreground">
                            {t('search.tags')}:
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
          </TabsContent>

          {/* AI Q&A Tab removed */}
        </Tabs>
      </div>
    </div>
  );
}
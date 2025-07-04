import React, { useState, useEffect, useCallback } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";
import brain from "brain";
import { SearchDocumentResult } from "brain/data-contracts"; // Adjust path if needed, or from types.ts
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

export default function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const [tagsInput, setTagsInput] = useState(searchParams.get("tags") || "");
  const [searchResults, setSearchResults] = useState<SearchDocumentResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchAttempted, setSearchAttempted] = useState(false);

  const performSearch = useCallback(
    async (tagsToSearch: string) => {
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
      setSearchParams({ tags: tagsToSearch }); // Update URL

      try {
        console.log(`[SearchPage] Searching for tags: ${tagsToSearch}`);
        const response = await brain.search_documents_by_tags({
          tags: tagsToSearch,
        });
        const data = await response.json(); // if brain methods return HttpResponse

        if (data && data.results) {
          setSearchResults(data.results);
        } else {
          setSearchResults([]);
        }
        console.log("[SearchPage] Search results:", data);
      } catch (err: any) {
        console.error("[SearchPage] Search error:", err);
        let errorMsg = "An error occurred while searching.";
        if (err?.data?.detail) {
          errorMsg =
            typeof err.data.detail === "string"
              ? err.data.detail
              : JSON.stringify(err.data.detail);
        } else if (err?.response?.data?.detail) {
          errorMsg =
            typeof err.response.data.detail === "string"
              ? err.response.data.detail
              : JSON.stringify(err.response.data.detail);
        } else if (err.message) {
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
    const initialTags = searchParams.get("tags");
    if (initialTags) {
      setTagsInput(initialTags);
      performSearch(initialTags);
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
                  {doc.file_path ? (
                    <a
                      href={doc.file_path}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline"
                    >
                      {doc.title || "Untitled Document"}
                    </a>
                  ) : (
                    doc.title || "Untitled Document"
                  )}
                </CardTitle>
                <CardDescription>
                  Country: {doc.country || "N/A"}
                </CardDescription>
              </CardHeader>
              <CardContent>
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

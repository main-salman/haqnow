import React, { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Download, Tag, PlusCircle, ArrowLeft, Brain, Loader2, FileText } from "lucide-react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { AlertCircle } from "lucide-react";

interface ApiDocument {
  id: number;
  title: string;
  description?: string;
  country: string;
  state?: string;
  file_url: string;
  original_filename: string;
  created_at?: string;
  generated_tags?: string[];
  document_language?: string;
  has_english_translation?: boolean;
}

interface DocumentTag {
  id: string;
  name: string;
}

export default function DocumentDetailPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const documentId = useMemo(() => Number(searchParams.get("id")), [searchParams]);
  const [doc, setDoc] = useState<ApiDocument | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newTag, setNewTag] = useState("");
  const [downloadingDocId, setDownloadingDocId] = useState<number | null>(null);

  // AI Q&A state
  const [isAIOpen, setIsAIOpen] = useState(false);
  const [aiQuestion, setAiQuestion] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const [aiAnswer, setAiAnswer] = useState<string | null>(null);
  const [aiConfidence, setAiConfidence] = useState<number | null>(null);

  const handleAddTag = () => {
    // Placeholder: real implementation would call backend to add a tag
    console.log("Add tag requested:", newTag);
    setNewTag("");
  };

  useEffect(() => {
    const fetchDoc = async () => {
      if (!documentId || Number.isNaN(documentId)) {
        setError("Invalid document ID");
        setLoading(false);
        return;
      }
      try {
        setLoading(true);
        setError(null);
        const resp = await fetch(`/api/search/document/${documentId}`);
        if (!resp.ok) {
          if (resp.status === 404) {
            setError("Document not found or has been deleted.");
          } else {
            setError(`Failed to load document (HTTP ${resp.status})`);
          }
          setLoading(false);
          return;
        }
        const data: ApiDocument = await resp.json();
        setDoc(data);
      } catch (e) {
        setError("Network error while loading document.");
      } finally {
        setLoading(false);
      }
    };
    fetchDoc();
  }, [documentId]);

  const handleDocumentClick = async (
    docId: number,
    format: "original" | "english" | string
  ) => {
    try {
      setDownloadingDocId(docId);
      let endpoint: string;
      if (format === "original") {
        endpoint = `/api/search/download/${docId}`;
      } else if (format === "english") {
        endpoint = `/api/search/download/${docId}?language=english`;
      } else {
        endpoint = `/api/search/download/${docId}?language=${format}`;
      }

      // Trigger a browser navigation so it follows redirects and avoids CORS
      const anchor = window.document.createElement("a");
      anchor.href = endpoint;
      anchor.rel = "noopener";
      window.document.body.appendChild(anchor);
      anchor.click();
      window.document.body.removeChild(anchor);
    } finally {
      setDownloadingDocId(null);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground p-4 md:p-8">
      <div className="container mx-auto max-w-5xl space-y-8">
        <div>
          <Button
            variant="outline"
            onClick={() => navigate(-1)} // Or navigate to a specific listing page
            className="mb-6"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Search
          </Button>
        </div>

        {loading && (
          <section className="bg-card p-6 rounded-lg shadow">
            <p>Loading document...</p>
          </section>
        )}

        {error && (
          <section className="bg-card p-6 rounded-lg shadow border border-red-200">
            <div className="flex items-center text-red-600 space-x-2">
              <AlertCircle className="h-5 w-5" />
              <span>{error}</span>
            </div>
            <div className="mt-4">
              <Button variant="outline" onClick={() => navigate(-1)}>
                Back to Search
              </Button>
            </div>
          </section>
        )}

        {!loading && !error && doc && (
        <>
        {/* Document Metadata Section */}
        <section className="bg-card p-6 rounded-lg shadow">
          <h1 className="text-3xl font-bold mb-2 text-primary font-serif">
            {doc.title}
          </h1>
          <div className="flex flex-wrap gap-x-4 gap-y-2 text-sm text-muted-foreground mb-4">
            <span>Country: {doc.country}</span>
            {doc.state && (
              <span>State/Province: {doc.state}</span>
            )}
            {doc.created_at && (
              <span>Uploaded: {new Date(doc.created_at).toLocaleDateString()}</span>
            )}
          </div>
          <p className="text-foreground/80 mb-6 leading-relaxed">
            {doc.description}
          </p>
          <div className="flex flex-wrap gap-3">
            <Button asChild>
              <a href={doc.file_url} download target="_blank" rel="noopener noreferrer">
                <Download className="mr-2 h-4 w-4" />
                Download PDF
              </a>
            </Button>

            {/* AI Q&A Button */}
            <Dialog open={isAIOpen} onOpenChange={setIsAIOpen}>
              <DialogTrigger asChild>
                <Button variant="secondary">
                  <Brain className="mr-2 h-4 w-4" />
                  Ask AI about this document
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[700px]">
                <DialogHeader>
                  <DialogTitle>Ask AI about this document</DialogTitle>
                  <DialogDescription>
                    Your question will be answered using only the content of this document.
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-4">
                  <Textarea
                    placeholder="Ask a question about this document..."
                    value={aiQuestion}
                    onChange={(e) => setAiQuestion(e.target.value)}
                    rows={3}
                    maxLength={1000}
                    className="resize-none"
                  />
                  {aiError && (
                    <div className="text-sm text-red-600">{aiError}</div>
                  )}
                  {aiAnswer && (
                    <div className="rounded border p-3 bg-muted/30">
                      <div className="text-sm text-muted-foreground mb-1">
                        Confidence: {aiConfidence !== null ? Math.round(aiConfidence * 100) + '%' : '—'}
                      </div>
                      <div className="whitespace-pre-wrap leading-relaxed">{aiAnswer}</div>
                    </div>
                  )}
                </div>
                <DialogFooter>
                  <Button
                    variant="default"
                    onClick={async () => {
                      if (!doc) return;
                      if (!aiQuestion.trim()) {
                        setAiError("Please enter a question.");
                        return;
                      }
                      setAiError(null);
                      setAiAnswer(null);
                      setAiLoading(true);
                      try {
                         const resp = await fetch('/api/rag/document-question', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                           body: JSON.stringify({ question: aiQuestion.trim(), document_id: doc.id }),
                        });
                        if (!resp.ok) {
                          const data = await resp.json().catch(() => ({}));
                          throw new Error(data?.detail || 'Failed to get AI answer');
                        }
                        const data = await resp.json();
                        setAiAnswer(data.answer || '');
                        setAiConfidence(typeof data.confidence === 'number' ? data.confidence : null);
                      } catch (e: any) {
                        setAiError(e?.message || 'An error occurred');
                      } finally {
                        setAiLoading(false);
                      }
                    }}
                    disabled={aiLoading || !aiQuestion.trim()}
                  >
                    {aiLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Processing...
                      </>
                    ) : (
                      'Ask'
                    )}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </section>

        {/* Download Options Section (consistent with SearchPage) */}
        <section className="bg-card p-6 rounded-lg shadow">
          <h3 className="text-xl font-semibold mb-3 font-serif">Download Options:</h3>
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
              {doc.document_language !== "english" && doc.has_english_translation && (
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
              {doc.document_language !== "english" && doc.has_english_translation && (
              <Button
                onClick={() => handleDocumentClick(doc.id, (doc.document_language || '').toLowerCase())}
                disabled={downloadingDocId === doc.id}
                size="sm"
                variant="outline"
                className="flex items-center gap-2"
              >
                {downloadingDocId === doc.id && (
                  <Loader2 className="h-3 w-3 animate-spin" />
                )}
                <FileText className="h-3 w-3" />
                {doc.document_language ? (doc.document_language.charAt(0).toUpperCase() + doc.document_language.slice(1)) : 'Original'} Text
              </Button>
            )}
          </div>

          {/* Info message for multilingual documents without translation */}
            {doc.document_language !== "english" && !doc.has_english_translation && (
            <div className="text-sm text-muted-foreground italic mt-2">
              English translation processing... (may take a few minutes for new uploads)
            </div>
          )}
        </section>

        {/* PDF Preview Section */}
        <section className="bg-card p-6 rounded-lg shadow">
          <h2 className="text-2xl font-semibold mb-4 font-serif">Document Preview</h2>
          <div className="aspect-[8.5/11] border border-border rounded overflow-hidden">
            <iframe
              src={doc.file_url}
              title={doc.title}
              width="100%"
              height="100%"
              className="w-full h-full"
              // sandbox="allow-scripts allow-same-origin" // Consider security implications
            />
          </div>
        </section>

        {/* Tags Section */}
        <section className="bg-card p-6 rounded-lg shadow">
          <h2 className="text-2xl font-semibold mb-4 font-serif">Tags</h2>
            <div className="flex flex-wrap gap-2 mb-4">
            {(doc.generated_tags || []).map((tag, index) => (
              <Badge key={index} variant="secondary" className="text-sm">
                {tag}
              </Badge>
            ))}
          </div>
          <div className="flex items-center space-x-2">
            <Input
              type="text"
              value={newTag}
              onChange={(e) => setNewTag(e.target.value)}
              placeholder="Add a new tag"
              className="flex-grow"
              aria-label="Add new tag"
            />
            <Button onClick={handleAddTag} variant="outline">
              <PlusCircle className="mr-2 h-4 w-4" />
              Add Tag
            </Button>
          </div>
        </section>
        </>
        )}
      </div>
    </div>
  );
}

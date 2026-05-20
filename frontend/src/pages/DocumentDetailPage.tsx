import React, { useEffect, useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { Download, Tag, PlusCircle, ArrowLeft, Brain, Loader2, FileText, MessageSquare, ExternalLink, X, Send, Trash2, Sparkles } from "lucide-react";
import { useNavigate, useSearchParams, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { AlertCircle } from "lucide-react";
import DocumentComments from "@/components/DocumentComments";
import DocumentAnnotations from "@/components/DocumentAnnotations";

interface ApiDocument {
  id: number;
  title: string;
  description?: string;
  ai_summary?: string;  // AI-generated summary from Groq
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
  const params = useParams();
  const { t } = useTranslation();
  
  // Support both URL parameter (/document/16) and query string (?id=16)
  const documentId = useMemo(() => {
    const paramId = params.id;
    const queryId = searchParams.get("id");
    return Number(paramId || queryId);
  }, [params.id, searchParams]);
  const [doc, setDoc] = useState<ApiDocument | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newTag, setNewTag] = useState("");
  const [downloadingDocId, setDownloadingDocId] = useState<number | null>(null);

  // AI Q&A Drawer state
  interface ChatMessage {
    question: string;
    answer: string;
    confidence: number | null;
    timestamp: Date;
  }

  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [aiQuestion, setAiQuestion] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);

  const handleAddTag = () => {
    // Placeholder: real implementation would call backend to add a tag
    console.log("Add tag requested:", newTag);
    setNewTag("");
  };

  const handleAskAI = async (questionOverride?: string) => {
    if (!doc) return;
    const query = (questionOverride || aiQuestion).trim();
    if (!query) {
      setAiError(t("aiQna.pleaseEnterQuestion", "Please enter a question."));
      return;
    }
    setAiError(null);
    setAiLoading(true);
    try {
      const resp = await fetch('/api/rag/document-question', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: query, document_id: doc.id }),
      });
      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        throw new Error(data?.detail || t("aiQna.errorMessage", "An error occurred. Please try again."));
      }
      const data = await resp.json();
      const answer = data.answer || '';
      const confidence = typeof data.confidence === 'number' ? data.confidence : null;

      // Add to conversation thread
      setChatHistory((prev) => [
        ...prev,
        {
          question: query,
          answer,
          confidence,
          timestamp: new Date(),
        },
      ]);
      
      // Reset input only if user typed it
      if (!questionOverride) {
        setAiQuestion("");
      }
    } catch (e: any) {
      setAiError(e?.message || t("aiQna.errorMessage", "An error occurred. Please try again."));
    } finally {
      setAiLoading(false);
    }
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

          {/* ✨ Sticky AI Banner */}
          <button
            onClick={() => {
              setIsDrawerOpen(true);
              setAiQuestion("");
              setAiError(null);
            }}
            className="w-full my-4 group relative overflow-hidden rounded-xl px-5 py-3.5 flex items-center justify-between gap-3 bg-gradient-to-r from-violet-600 via-indigo-600 to-blue-600 hover:from-violet-500 hover:via-indigo-500 hover:to-blue-500 text-white shadow-md hover:shadow-lg transition-all duration-300 hover:-translate-y-0.5 active:translate-y-0 focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:ring-offset-2"
          >
            {/* Animated shimmer overlay */}
            <span className="pointer-events-none absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-700 ease-in-out bg-gradient-to-r from-transparent via-white/10 to-transparent" />

            <span className="flex items-center gap-3">
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white/20 group-hover:bg-white/30 transition-colors">
                <Brain className="h-4 w-4" />
              </span>
              <span className="flex flex-col items-start">
                <span className="text-sm font-semibold leading-tight">
                  {t("aiQna.floatingButtonTooltip", "Ask AI about this document")}
                </span>
                <span className="text-xs text-white/75 leading-tight">
                  {t("aiQna.bannerSubtitle", "Get instant answers · Powered by Thaura.AI")}
                </span>
              </span>
            </span>

            <span className="flex items-center gap-2 shrink-0">
              <span className="hidden sm:flex gap-1.5 items-center">
                {[
                  t("aiQna.suggestedQ1", "Summarize"),
                  t("aiQna.suggestedQ2", "Key names"),
                  t("aiQna.suggestedQ3", "Red flags"),
                ].map((label, i) => (
                  <span
                    key={i}
                    className="text-[10px] bg-white/15 hover:bg-white/25 rounded-full px-2 py-0.5 font-medium whitespace-nowrap transition-colors"
                  >
                    {label}
                  </span>
                ))}
              </span>
              <Sparkles className="h-4 w-4 opacity-75 group-hover:opacity-100 group-hover:rotate-12 transition-all duration-300" />
            </span>
          </button>

          {doc.ai_summary && (
            <div className="mb-6 p-4 bg-blue-50 border-l-4 border-l-blue-600 rounded-lg">
              <p className="text-sm font-semibold text-blue-900 mb-2 flex items-center gap-2">
                <Brain className="h-4 w-4" />
                AI-Generated Summary
              </p>
              <p className="text-blue-800 leading-relaxed">
                {doc.ai_summary}
              </p>
            </div>
          )}
          
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

            {/* Discuss Anonymously Button */}
            <Button 
              variant="outline"
              onClick={() => {
                // Scroll to comments section
                const commentsSection = document.getElementById('comments-section');
                if (commentsSection) {
                  commentsSection.scrollIntoView({ behavior: 'smooth' });
                }
              }}
            >
              <MessageSquare className="mr-2 h-4 w-4" />
              Discuss anonymously
            </Button>

            {/* Discuss on Reddit Button */}
            <Button 
              variant="outline"
              asChild
            >
              <a 
                href="https://www.reddit.com/r/haqnow/" 
                target="_blank" 
                rel="noopener noreferrer"
              >
                <ExternalLink className="mr-2 h-4 w-4" />
                Discuss on Reddit
              </a>
            </Button>
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

        {/* PDF Preview Section with Annotations */}
        <section className="bg-card p-6 rounded-lg shadow">
          <h2 className="text-2xl font-semibold mb-4 font-serif">Document Preview</h2>
          <DocumentAnnotations documentId={doc.id} pdfUrl={doc.file_url} />
        </section>

        {/* Comments Section */}
        <section className="bg-card p-6 rounded-lg shadow">
          <DocumentComments documentId={doc.id} />
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
        
        {/* Floating AI Button */}
        <button
          onClick={() => setIsDrawerOpen(true)}
          className={`fixed bottom-6 right-6 z-40 flex items-center justify-center p-4 bg-primary text-primary-foreground rounded-full shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-110 active:scale-95 group focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 hover:bg-primary/95 ${
            isDrawerOpen ? "scale-0 opacity-0" : "scale-100 opacity-100"
          }`}
          title={t("aiQna.floatingButtonTooltip", "Ask AI about this document")}
        >
          <Brain className="h-6 w-6 group-hover:animate-pulse" />
          <span className="max-w-0 overflow-hidden group-hover:max-w-xs transition-all duration-500 ease-in-out whitespace-nowrap font-medium text-sm ml-0 group-hover:ml-2">
            {t("aiQna.floatingButtonTooltip", "Ask AI about this document")}
          </span>
        </button>

        {/* Slide-out Drawer Panel */}
        <div
          className={`fixed inset-0 z-50 overflow-hidden transition-all duration-300 ${
            isDrawerOpen ? "visible" : "invisible"
          }`}
          role="dialog"
          aria-modal="true"
        >
          {/* Backdrop Overlay */}
          <div
            className={`absolute inset-0 bg-black/40 backdrop-blur-sm transition-opacity duration-300 ${
              isDrawerOpen ? "opacity-100" : "opacity-0"
            }`}
            onClick={() => setIsDrawerOpen(false)}
          />

          {/* Drawer Content Container */}
          <div
            className={`absolute inset-y-0 right-0 max-w-full flex transition-transform duration-300 ease-out transform ${
              isDrawerOpen ? "translate-x-0" : "translate-x-full"
            }`}
          >
            <div className="w-screen max-w-md bg-card border-l border-border flex flex-col h-full shadow-2xl relative">
              {/* Header */}
              <div className="px-6 py-5 border-b border-border bg-gradient-to-r from-primary/5 to-secondary/5 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-primary/10 text-primary rounded-lg flex items-center justify-center">
                    <Brain className="h-5 w-5 animate-pulse" />
                  </div>
                  <div>
                    <h2 className="text-lg font-bold text-foreground font-serif">
                      {t("aiQna.assistantTitle", "AI Document Companion")}
                    </h2>
                    <p className="text-xs text-muted-foreground">
                      {t("aiQna.assistantSubtitle", "Ask questions about this document.")}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setIsDrawerOpen(false)}
                  className="p-1.5 rounded-full text-muted-foreground hover:bg-muted transition-colors focus:outline-none focus:ring-1 focus:ring-border"
                  aria-label="Close panel"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {/* Chat Thread */}
              <div className="flex-grow overflow-y-auto px-6 py-6 space-y-6 flex flex-col">
                {chatHistory.length === 0 ? (
                  /* Welcome Panel */
                  <div className="flex-1 flex flex-col items-center justify-center text-center space-y-6 max-w-xs mx-auto my-auto">
                    <div className="w-16 h-16 bg-primary/10 text-primary rounded-full flex items-center justify-center animate-pulse">
                      <Sparkles className="h-8 w-8" />
                    </div>
                    <div className="space-y-2">
                      <h3 className="font-semibold text-foreground text-base">
                        {t("aiQna.assistantTitle", "AI Document Companion")}
                      </h3>
                      <p className="text-xs text-muted-foreground leading-relaxed">
                        {t("aiQna.assistantSubtitle", "Ask questions about the content of this document. Answers are derived solely from the text to prevent hallucinations.")}
                      </p>
                    </div>
                    
                    {/* Suggested Questions */}
                    <div className="w-full space-y-3 pt-4 border-t border-border">
                      <h4 className="text-[10px] font-semibold text-muted-foreground tracking-wider uppercase">
                        {t("aiQna.suggestedTitle", "Suggested Questions")}
                      </h4>
                      <div className="flex flex-col gap-2">
                        {[
                          t("aiQna.suggestedQ1", "Summarize key findings"),
                          t("aiQna.suggestedQ2", "List key names, dates & organizations"),
                          t("aiQna.suggestedQ3", "Identify potential red flags")
                        ].map((suggested, index) => (
                          <button
                            key={index}
                            onClick={() => handleAskAI(suggested)}
                            disabled={aiLoading}
                            className="w-full text-left px-4 py-2.5 bg-muted/40 hover:bg-muted text-xs text-foreground/80 hover:text-foreground rounded-lg border border-border transition-all duration-200 hover:-translate-y-0.5 active:translate-y-0 focus:outline-none focus:ring-2 focus:ring-primary/30"
                          >
                            💡 {suggested}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  /* Message Bubbles */
                  <div className="flex flex-col space-y-4">
                    {/* Clear Button */}
                    <div className="flex justify-end pb-2">
                      <button
                        onClick={() => setChatHistory([])}
                        className="text-xs text-muted-foreground hover:text-destructive flex items-center gap-1 transition-colors px-2 py-1 rounded hover:bg-muted"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                        {t("aiQna.clearHistory", "Clear Chat")}
                      </button>
                    </div>
                    
                    {chatHistory.map((chat, idx) => (
                      <React.Fragment key={idx}>
                        {/* User Bubble */}
                        <div className="bg-primary text-primary-foreground rounded-2xl rounded-tr-none px-4 py-2.5 max-w-[85%] self-end shadow-sm">
                          <p className="text-sm leading-relaxed whitespace-pre-wrap">{chat.question}</p>
                        </div>
                        
                        {/* AI Bubble */}
                        <div className="bg-muted rounded-2xl rounded-tl-none px-4 py-3.5 max-w-[90%] self-start shadow-sm border border-border flex flex-col space-y-2">
                          <div className="flex items-center space-x-1.5 text-primary text-xs font-semibold">
                            <Brain className="h-3.5 w-3.5" />
                            <span>{t("aiQna.answerTitle", "AI Answer")}</span>
                          </div>
                          <p className="text-sm leading-relaxed text-foreground whitespace-pre-wrap">{chat.answer}</p>
                          <div className="flex items-center justify-between border-t border-border/40 pt-2 mt-1 text-[10px] text-muted-foreground">
                            <span>Thaura.AI</span>
                            <span>
                              {t("aiQna.confidenceLabel", "Confidence")}: {chat.confidence !== null ? Math.round(chat.confidence * 100) + '%' : '—'}
                            </span>
                          </div>
                        </div>
                      </React.Fragment>
                    ))}
                  </div>
                )}

                {/* AI Thinking Animation */}
                {aiLoading && (
                  <div className="flex flex-col space-y-2 max-w-[90%] self-start animate-fade-in">
                    <div className="flex items-center space-x-2 text-xs text-muted-foreground animate-pulse">
                      <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />
                      <span>{t("aiQna.processing", "Processing...")}</span>
                    </div>
                    <div className="bg-muted/50 rounded-2xl rounded-tl-none p-4 w-full space-y-2 animate-pulse border border-border/50">
                      <div className="h-3 bg-muted-foreground/15 rounded w-5/6"></div>
                      <div className="h-3 bg-muted-foreground/15 rounded w-full"></div>
                      <div className="h-3 bg-muted-foreground/15 rounded w-2/3"></div>
                    </div>
                  </div>
                )}

                {/* Error Banner */}
                {aiError && (
                  <div className="p-3 bg-destructive/15 text-destructive border border-destructive/20 rounded-lg text-sm flex items-center space-x-2">
                    <AlertCircle className="h-4 w-4 shrink-0" />
                    <span>{aiError}</span>
                  </div>
                )}
              </div>

              {/* Floating suggested chips if chat history has messages */}
              {chatHistory.length > 0 && !aiLoading && (
                <div className="px-6 py-2 border-t border-border bg-muted/10 overflow-x-auto flex space-x-2 scrollbar-none shrink-0">
                  {[
                    t("aiQna.suggestedQ1", "Summarize findings"),
                    t("aiQna.suggestedQ2", "List names & dates"),
                    t("aiQna.suggestedQ3", "Red flags")
                  ].map((suggested, index) => (
                    <button
                      key={index}
                      onClick={() => handleAskAI(suggested)}
                      className="whitespace-nowrap px-3 py-1 bg-background hover:bg-muted text-xs text-foreground/75 hover:text-foreground rounded-full border border-border transition-colors focus:outline-none"
                    >
                      💡 {suggested}
                    </button>
                  ))}
                </div>
              )}

              {/* Input Area Footer */}
              <div className="p-4 border-t border-border bg-background">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    if (!aiLoading && aiQuestion.trim()) {
                      handleAskAI();
                    }
                  }}
                  className="flex items-center space-x-2"
                >
                  <Textarea
                    placeholder={t("aiQna.inputPlaceholder", "Ask a question about this document...")}
                    value={aiQuestion}
                    onChange={(e) => setAiQuestion(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        if (!aiLoading && aiQuestion.trim()) {
                          handleAskAI();
                        }
                      }
                    }}
                    rows={1}
                    maxLength={1000}
                    className="resize-none min-h-[40px] max-h-[120px] rounded-lg py-2 flex-grow border-border focus-visible:ring-primary"
                  />
                  <Button
                    type="submit"
                    size="icon"
                    disabled={aiLoading || !aiQuestion.trim()}
                    className="h-10 w-10 shrink-0 bg-primary hover:bg-primary/90 text-primary-foreground transition-all duration-200 hover:scale-105 active:scale-95"
                    aria-label="Send question"
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                </form>
                <div className="mt-2 text-center text-[10px] text-muted-foreground flex justify-between px-1">
                  <span>{t("aiQna.inputHelp", "Press Enter to submit")}</span>
                  <span>
                    Powered by{' '}
                    <a
                      href="https://thaura.ai/"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline font-semibold"
                    >
                      Thaura.AI
                    </a>
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

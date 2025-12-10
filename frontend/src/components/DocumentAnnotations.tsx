import React, { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Highlighter, X, Loader2, Trash2, ChevronLeft, ChevronRight, ExternalLink } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import * as pdfjsLib from 'pdfjs-dist';

interface Annotation {
  id: number;
  document_id: number;
  page_number: number;
  x: number;
  y: number;
  width: number;
  height: number;
  highlighted_text: string | null;
  annotation_note: string | null;
  created_at: string;
}

interface DocumentAnnotationsProps {
  documentId: number;
  pdfUrl: string;
}

// Configure PDF.js worker - use CDN for reliability
// Using version 4.10.38 which matches the installed pdfjs-dist version
pdfjsLib.GlobalWorkerOptions.workerSrc = `https://cdnjs.cloudflare.com/ajax/libs/pdf.js/4.10.38/pdf.worker.min.mjs`;

export default function DocumentAnnotations({ documentId, pdfUrl }: DocumentAnnotationsProps) {
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSelecting, setIsSelecting] = useState(false);
  const [selectedText, setSelectedText] = useState("");
  const [selectedRect, setSelectedRect] = useState<DOMRect | null>(null);
  const [showNoteDialog, setShowNoteDialog] = useState(false);
  const [noteText, setNoteText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [pdfDoc, setPdfDoc] = useState<any>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [pdfLoading, setPdfLoading] = useState(true);
  const [pdfError, setPdfError] = useState<string | null>(null);
  const [useIframeFallback, setUseIframeFallback] = useState(false);
  const pdfContainerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    fetchAnnotations();
    // Reset PDF state when URL changes
    setPdfDoc(null);
    setPdfError(null);
    setPdfLoading(true);
    setUseIframeFallback(false);
    loadPDF();
  }, [documentId, pdfUrl]);

  const loadPDF = async () => {
    try {
      setPdfLoading(true);
      setPdfError(null);
      setUseIframeFallback(false);
      
      // Check if PDF URL is from S3/Exoscale (known CORS issues)
      // Skip PDF.js for S3 URLs and use iframe directly
      const isS3Url = pdfUrl.includes('sos-ch-dk-2.exo.io') || 
                      pdfUrl.includes('s3.amazonaws.com') ||
                      pdfUrl.includes('.exo.io');
      
      if (isS3Url) {
        // S3 URLs don't support CORS for PDF.js, use iframe directly
        console.log('S3 URL detected, using iframe fallback directly');
        setPdfDoc(null);
        setUseIframeFallback(true);
        setPdfLoading(false);
        return;
      }
      
      // Set a timeout for PDF.js loading (8 seconds)
      const timeoutPromise = new Promise((_, reject) => 
        setTimeout(() => reject(new Error('PDF.js loading timeout')), 8000)
      );
      
      // Try loading PDF with PDF.js first
      const loadingTask = pdfjsLib.getDocument({
        url: pdfUrl,
        withCredentials: false,
        httpHeaders: {},
        verbosity: 0, // Suppress console warnings
      });
      
      // Race between loading and timeout
      const pdf = await Promise.race([loadingTask.promise, timeoutPromise]) as any;
      setPdfDoc(pdf);
      setTotalPages(pdf.numPages);
      setCurrentPage(1);
    } catch (err: any) {
      console.error('Error loading PDF with PDF.js:', err);
      // If PDF.js fails due to CORS, timeout, or other issues, use iframe fallback
      setPdfError(null);
      setPdfDoc(null);
      setUseIframeFallback(true); // Explicitly set fallback flag
    } finally {
      setPdfLoading(false);
    }
  };

  const renderPage = async (pageNum: number) => {
    if (!pdfDoc || !canvasRef.current) return;

    try {
      const page = await pdfDoc.getPage(pageNum);
      const canvas = canvasRef.current;
      const context = canvas.getContext('2d');
      
      if (!context) return;

      const viewport = page.getViewport({ scale: 1.5 });
      canvas.height = viewport.height;
      canvas.width = viewport.width;

      const renderContext = {
        canvasContext: context,
        viewport: viewport,
      };

      await page.render(renderContext).promise;
    } catch (err: any) {
      console.error('Error rendering PDF page:', err);
      setPdfError('Failed to render PDF page');
    }
  };

  useEffect(() => {
    if (pdfDoc && currentPage) {
      renderPage(currentPage);
    }
  }, [pdfDoc, currentPage]);

  const fetchAnnotations = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/comments/documents/${documentId}/annotations`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch annotations');
      }
      
      const data = await response.json();
      setAnnotations(data);
      setError(null);
    } catch (err: any) {
      console.error('Error fetching annotations:', err);
      setError(err.message || 'Failed to load annotations');
    } finally {
      setLoading(false);
    }
  };

  const handleTextSelection = (e?: MouseEvent) => {
    // Get selection from the main window
    const selection = window.getSelection();
    
    if (!selection || selection.rangeCount === 0) {
      if (isSelecting) {
        // User might have selected text in PDF and copied it
        // Show instructions to paste the text
        return;
      }
      return;
    }

    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    const containerRect = pdfContainerRef.current?.getBoundingClientRect();
    
    if (!containerRect) return;

    // Check if selection is within PDF container
    if (
      rect.left >= containerRect.left &&
      rect.right <= containerRect.right &&
      rect.top >= containerRect.top &&
      rect.bottom <= containerRect.bottom
    ) {
      const text = selection.toString().trim();
      if (text.length > 0) {
        setSelectedText(text);
        setSelectedRect(rect);
        setIsSelecting(true);
      }
    }
  };

  // Listen for paste events when in selection mode (for iframe workaround)
  useEffect(() => {
    if (!isSelecting) return;

    const handlePaste = async (e: ClipboardEvent) => {
      e.preventDefault();
      const pastedText = e.clipboardData?.getData('text') || '';
      if (pastedText.trim().length > 0) {
        setSelectedText(pastedText.trim());
        // Estimate position (center of PDF container)
        if (pdfContainerRef.current) {
          const containerRect = pdfContainerRef.current.getBoundingClientRect();
          const estimatedRect = new DOMRect(
            containerRect.left + containerRect.width * 0.3,
            containerRect.top + containerRect.height * 0.4,
            containerRect.width * 0.4,
            20 // Estimated height
          );
          setSelectedRect(estimatedRect);
        }
      }
    };

    window.addEventListener('paste', handlePaste);
    return () => window.removeEventListener('paste', handlePaste);
  }, [isSelecting]);

  const handleCreateAnnotation = async () => {
    if (!selectedText || selectedText.trim().length === 0) {
      setError('Please select or paste some text to highlight');
      return;
    }

    if (!pdfContainerRef.current) {
      setError('PDF container not found');
      return;
    }

    const containerRect = pdfContainerRef.current.getBoundingClientRect();
    
    // Calculate relative coordinates (0-1 scale)
    // If selectedRect is not available (pasted text), use estimated position
    let x, y, width, height;
    if (selectedRect) {
      x = (selectedRect.left - containerRect.left) / containerRect.width;
      y = (selectedRect.top - containerRect.top) / containerRect.height;
      width = selectedRect.width / containerRect.width;
      height = selectedRect.height / containerRect.height;
    } else {
      // Use estimated position for pasted text (center-left area)
      x = 0.1;
      y = 0.4;
      width = 0.6;
      height = 0.05;
    }

    // For now, assume page 1 (in a real implementation, you'd track the current page)
    // TODO: Track current PDF page number
    const pageNumber = 1;

    try {
      setSubmitting(true);
      setError(null);
      
      const response = await fetch(`/api/comments/documents/${documentId}/annotations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          page_number: pageNumber,
          x: x,
          y: y,
          width: width,
          height: height,
          highlighted_text: selectedText,
          annotation_note: noteText.trim() || null
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to create annotation');
      }

      // Clear selection
      window.getSelection()?.removeAllRanges();
      setSelectedText("");
      setSelectedRect(null);
      setIsSelecting(false);
      setNoteText("");
      setShowNoteDialog(false);

      // Refresh annotations
      await fetchAnnotations();
    } catch (err: any) {
      console.error('Error creating annotation:', err);
      setError(err.message || 'Failed to create annotation');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteAnnotation = async (annotationId: number) => {
    if (!confirm("Are you sure you want to delete this annotation?")) {
      return;
    }

    try {
      setDeletingId(annotationId);
      const response = await fetch(`/api/comments/annotations/${annotationId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete annotation');
      }

      await fetchAnnotations();
    } catch (err: any) {
      console.error('Error deleting annotation:', err);
      setError(err.message || 'Failed to delete annotation');
    } finally {
      setDeletingId(null);
    }
  };

  useEffect(() => {
    if (isSelecting && selectedText) {
      setShowNoteDialog(true);
    }
  }, [isSelecting, selectedText]);

  // Render annotation overlays
  const renderAnnotationOverlays = () => {
    if (!pdfContainerRef.current) return null;

    const containerRect = pdfContainerRef.current.getBoundingClientRect();
    
    return annotations.map((annotation) => {
      const x = annotation.x * containerRect.width;
      const y = annotation.y * containerRect.height;
      const width = annotation.width * containerRect.width;
      const height = annotation.height * containerRect.height;

      return (
        <div
          key={annotation.id}
          className="absolute border-2 border-yellow-400 bg-yellow-400/20 cursor-pointer group"
          style={{
            left: `${x}px`,
            top: `${y}px`,
            width: `${width}px`,
            height: `${height}px`,
            pointerEvents: 'auto',
          }}
          title={annotation.annotation_note || annotation.highlighted_text || 'Annotation'}
          onClick={() => {
            if (annotation.annotation_note) {
              alert(`Note: ${annotation.annotation_note}`);
            }
          }}
        >
          <div className="absolute -top-6 right-0 opacity-0 group-hover:opacity-100 transition-opacity">
            <Button
              variant="destructive"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                handleDeleteAnnotation(annotation.id);
              }}
              disabled={deletingId === annotation.id}
              className="h-6 px-2"
            >
              {deletingId === annotation.id ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : (
                <Trash2 className="h-3 w-3" />
              )}
            </Button>
          </div>
        </div>
      );
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <Highlighter className="h-5 w-5" />
          Annotations ({annotations.length})
        </h3>
        <Button
          variant="outline"
          size="sm"
          onClick={() => {
            // Enable text selection mode
            setIsSelecting(true);
          }}
        >
          <Highlighter className="mr-2 h-4 w-4" />
          Highlight Text
        </Button>
      </div>

      {error && (
        <div className="bg-destructive/10 text-destructive p-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {isSelecting && (
        <div className="bg-blue-50 border border-blue-200 p-3 rounded-lg text-sm space-y-2">
          <p className="text-blue-800 font-medium">
            Selection Mode Active
          </p>
          {selectedText ? (
            <div>
              <p className="text-blue-800">
                Selected text: "{selectedText}"
              </p>
              <Button
                size="sm"
                className="mt-2"
                onClick={() => {
                  if (selectedText && selectedRect) {
                    handleCreateAnnotation();
                  } else {
                    setShowNoteDialog(true);
                  }
                }}
              >
                Create Highlight
              </Button>
            </div>
          ) : (
            <div className="space-y-2">
              <p className="text-blue-800">
                Select text in the PDF above, or copy text from the PDF and paste it here:
              </p>
              <Textarea
                placeholder="Paste selected text here..."
                value={selectedText}
                onChange={(e) => {
                  const text = e.target.value.trim();
                  setSelectedText(text);
                  if (text.length > 0 && pdfContainerRef.current) {
                    // Estimate position for pasted text
                    const containerRect = pdfContainerRef.current.getBoundingClientRect();
                    const estimatedRect = new DOMRect(
                      containerRect.left + containerRect.width * 0.3,
                      containerRect.top + containerRect.height * 0.4,
                      containerRect.width * 0.4,
                      20
                    );
                    setSelectedRect(estimatedRect);
                  }
                }}
                rows={2}
                className="bg-white"
              />
              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={() => {
                    if (selectedText && selectedRect) {
                      setShowNoteDialog(true);
                    }
                  }}
                  disabled={!selectedText}
                >
                  Add Note & Create
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setIsSelecting(false);
                    setSelectedText("");
                    setSelectedRect(null);
                    window.getSelection()?.removeAllRanges();
                  }}
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* PDF Container with annotations */}
      <div className="space-y-4">
        {pdfLoading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground mr-2" />
            <span className="text-muted-foreground">Loading PDF...</span>
          </div>
        )}

        {pdfDoc && !pdfError && (
          <>
            {/* PDF Navigation Controls */}
            <div className="flex items-center justify-between bg-muted/50 p-2 rounded-lg">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  if (currentPage > 1) {
                    setCurrentPage(currentPage - 1);
                  }
                }}
                disabled={currentPage <= 1}
              >
                <ChevronLeft className="h-4 w-4 mr-1" />
                Previous
              </Button>
              
              <span className="text-sm text-muted-foreground">
                Page {currentPage} of {totalPages}
              </span>
              
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  if (currentPage < totalPages) {
                    setCurrentPage(currentPage + 1);
                  }
                }}
                disabled={currentPage >= totalPages}
              >
                Next
                <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </div>

            {/* PDF Canvas Container */}
            <div
              ref={pdfContainerRef}
              className="relative border rounded-lg overflow-auto bg-gray-100"
              style={{ maxHeight: '800px' }}
              onMouseUp={handleTextSelection}
            >
              <div className="flex justify-center p-4">
                <canvas
                  ref={canvasRef}
                  className="shadow-lg"
                  style={{ maxWidth: '100%', height: 'auto' }}
                />
              </div>
              {renderAnnotationOverlays()}
            </div>
          </>
        )}

        {/* Fallback to iframe if PDF.js fails or times out */}
        {(!pdfDoc || useIframeFallback) && !pdfLoading && (
          <div
            ref={pdfContainerRef}
            className="relative w-full"
            onMouseUp={handleTextSelection}
          >
            <div className="border rounded-lg overflow-hidden bg-gray-50" style={{ minHeight: '600px' }}>
              <iframe
                src={pdfUrl}
                title="PDF Viewer"
                width="100%"
                height="600px"
                className="w-full"
                style={{ border: 'none', display: 'block' }}
                allow="fullscreen"
              />
            </div>
            {renderAnnotationOverlays()}
            <div className="mt-2 text-xs text-muted-foreground text-center">
              <a href={pdfUrl} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline inline-flex items-center gap-1">
                <ExternalLink className="h-3 w-3" />
                Open PDF in new tab
              </a>
            </div>
          </div>
        )}
      </div>

      {/* Annotation list */}
      {annotations.length > 0 && (
        <div className="space-y-2">
          <h4 className="font-medium">All Annotations:</h4>
          {annotations.map((annotation) => (
            <div
              key={annotation.id}
              className="bg-muted/30 rounded-lg p-3 flex items-start justify-between"
            >
              <div className="flex-1">
                {annotation.highlighted_text && (
                  <p className="text-sm font-medium mb-1">
                    "{annotation.highlighted_text}"
                  </p>
                )}
                {annotation.annotation_note && (
                  <p className="text-sm text-muted-foreground">
                    {annotation.annotation_note}
                  </p>
                )}
                <p className="text-xs text-muted-foreground mt-1">
                  Page {annotation.page_number}
                </p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleDeleteAnnotation(annotation.id)}
                disabled={deletingId === annotation.id}
              >
                {deletingId === annotation.id ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4" />
                )}
              </Button>
            </div>
          ))}
        </div>
      )}

      {/* Note dialog */}
      <Dialog open={showNoteDialog} onOpenChange={setShowNoteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Annotation Note</DialogTitle>
            <DialogDescription>
              Selected text: "{selectedText}"
            </DialogDescription>
          </DialogHeader>
          <Textarea
            placeholder="Add a note about this highlight (optional)..."
            value={noteText}
            onChange={(e) => setNoteText(e.target.value)}
            rows={3}
            maxLength={1000}
          />
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowNoteDialog(false);
                setIsSelecting(false);
                setSelectedText("");
                setSelectedRect(null);
                setNoteText("");
                window.getSelection()?.removeAllRanges();
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreateAnnotation}
              disabled={submitting}
            >
              {submitting ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                'Create Annotation'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}


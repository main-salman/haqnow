import React, { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Highlighter, X, Loader2, Trash2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

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
  const pdfContainerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchAnnotations();
  }, [documentId]);

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
    // Try to get selection from the main window first
    let selection = window.getSelection();
    let range: Range | null = null;
    
    // If no selection in main window, try to get it from the iframe
    if (!selection || selection.rangeCount === 0) {
      // Check if we can access iframe content (only works if same-origin)
      const iframe = pdfContainerRef.current?.querySelector('iframe');
      if (iframe && iframe.contentWindow) {
        try {
          const iframeSelection = iframe.contentWindow.getSelection();
          if (iframeSelection && iframeSelection.rangeCount > 0) {
            selection = iframeSelection;
            range = iframeSelection.getRangeAt(0);
          }
        } catch (err) {
          // Cross-origin restriction - can't access iframe content
          console.log('Cannot access iframe selection (cross-origin restriction)');
        }
      }
    } else {
      range = selection.getRangeAt(0);
    }

    if (!selection || !range || selection.rangeCount === 0) {
      // If no selection found, check if user has copied text to clipboard
      if (isSelecting) {
        // User might have selected text in PDF and copied it
        // Show instructions to paste the text
        return;
      }
      return;
    }

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
      <div
        ref={pdfContainerRef}
        className="relative"
        onMouseUp={handleTextSelection}
      >
        <iframe
          src={pdfUrl}
          title="PDF Viewer"
          width="100%"
          height="600px"
          className="border rounded"
          style={{ pointerEvents: isSelecting ? 'auto' : 'auto' }}
        />
        {renderAnnotationOverlays()}
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


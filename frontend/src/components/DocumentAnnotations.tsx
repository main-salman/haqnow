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

  const handleTextSelection = () => {
    const selection = window.getSelection();
    if (!selection || selection.rangeCount === 0) {
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

  const handleCreateAnnotation = async () => {
    if (!selectedRect || !pdfContainerRef.current) {
      return;
    }

    const containerRect = pdfContainerRef.current.getBoundingClientRect();
    
    // Calculate relative coordinates (0-1 scale)
    const x = (selectedRect.left - containerRect.left) / containerRect.width;
    const y = (selectedRect.top - containerRect.top) / containerRect.height;
    const width = selectedRect.width / containerRect.width;
    const height = selectedRect.height / containerRect.height;

    // For now, assume page 1 (in a real implementation, you'd track the current page)
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
        <div className="bg-blue-50 border border-blue-200 p-3 rounded-lg text-sm">
          <p className="text-blue-800">
            Select text in the PDF above to create a highlight. Selected: "{selectedText}"
          </p>
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


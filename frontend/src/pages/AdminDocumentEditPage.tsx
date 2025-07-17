import React, { useEffect, useState, useCallback } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
// Remove Supabase import - we don't use it anymore
// import { supabase } from "../utils/supabaseClient";
import { Document } from "../types";
// Remove brain import - we'll use direct fetch instead
// import brain from "brain";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle, Info, Loader2, ArrowLeft, Save, X, CheckCircle2, XCircle } from "lucide-react";
import { toast } from "sonner";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

interface AdminDocumentDetails extends Document {
  description?: string | null;
  state_province?: string | null;
  admin_level?: string | null;
  file_path?: string | null; 
  ocr_text?: string | null;
  generated_tags?: string[] | null;
}

export default function AdminDocumentEditPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const documentId = searchParams.get("id");

  const [document, setDocument] = useState<AdminDocumentDetails | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Editable fields state
  const [editedTitle, setEditedTitle] = useState("");
  const [editedDescription, setEditedDescription] = useState("");
  const [editedCountry, setEditedCountry] = useState("");
  const [editedStateProvince, setEditedStateProvince] = useState("");
  const [editedAdminLevel, setEditedAdminLevel] = useState("");
  const [editedTags, setEditedTags] = useState<string[]>([]);
  const [newTagInput, setNewTagInput] = useState("");
  
  const [isSaving, setIsSaving] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [isRejecting, setIsRejecting] = useState(false);

  const fetchDocumentDetails = useCallback(async () => {
    if (!documentId) {
      setError("No document ID provided in the URL.");
      setIsLoading(false);
      setDocument(null);
      return;
    }
    setIsLoading(true);
    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) {
        throw new Error('No authentication token found. Please log in again.');
      }

      const response = await fetch(`/api/document-processing/document/${documentId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (data) {
        const documentData: AdminDocumentDetails = {
          id: data.id.toString(),
          title: data.title || "",
          description: data.description,
          country: data.country || "",
          stateProvince: data.state,
          uploadDate: data.created_at,
          pdfUrl: data.file_url || data.file_path || "", 
          tags: data.generated_tags || [],
          state_province: data.state,
          admin_level: data.admin_level,
          file_path: data.file_path,
          ocr_text: data.ocr_text,
          generated_tags: data.generated_tags,
          status: data.status
        };
        
        setDocument(documentData);
        setEditedTitle(data.title || "");
        setEditedDescription(data.description || "");
        setEditedCountry(data.country || "");
        setEditedStateProvince(data.state || "");
        setEditedAdminLevel(data.admin_level || "");

        let parsedTags: string[] = [];
        if (data.generated_tags) {
          try {
            parsedTags = Array.isArray(data.generated_tags) ? data.generated_tags : JSON.parse(data.generated_tags);
          } catch (parseError) {
            console.warn("Failed to parse generated_tags:", parseError);
            parsedTags = [];
          }
        }
        setEditedTags(parsedTags);
        
        setError(null);
      } else {
        setError("Document not found.");
        setDocument(null);
      }
    } catch (err) {
      console.error("Error fetching document details:", err);
      setError(`Failed to fetch document: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setDocument(null);
    } finally {
      setIsLoading(false);
    }
  }, [documentId]);

  useEffect(() => {
    fetchDocumentDetails();
  }, [fetchDocumentDetails]);

  // Refactored core logic for saving main fields and tags
  const saveCoreChanges = async (suppressToast = false): Promise<boolean> => {
    console.log("[AdminDocEdit] saveCoreChanges called. SuppressToast:", suppressToast);
    if (!documentId || !document) {
      if (!suppressToast) toast.error("Cannot save: Document data is missing or ID is invalid.");
      return false;
    }

    try {
      const updates = {
        title: editedTitle,
        description: editedDescription,
        country: editedCountry,
        state_province: editedStateProvince,
        admin_level: editedAdminLevel,
        generated_tags: editedTags,
        updated_at: new Date().toISOString(),
      };
      const token = localStorage.getItem('jwt_token');
      if (!token) {
        throw new Error('No authentication token found. Please log in again.');
      }

      console.log("[AdminDocEdit] Attempting to save core changes with updates:", updates, "for docId:", documentId);
      const response = await fetch(`/api/document-processing/update-document/${documentId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(updates),
      });

      console.log("[AdminDocEdit] Backend saveCoreChanges response:", response);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      console.log("[AdminDocEdit] Save result:", result);

      if (!suppressToast) {
        await fetchDocumentDetails(); 
      }
      return true;
    } catch (err: any) {
      console.error("[AdminDocEdit] Catch block error during core save:", err);
      if (!suppressToast) toast.error(err.message || "An unexpected error occurred while saving changes.");
      return false;
    }
  };

  const handleSaveChanges = async () => {
    if (isSaving || isApproving || isRejecting) return; // Prevent multiple operations
    setIsSaving(true);
    const success = await saveCoreChanges();
    if (success) {
      toast.success("Changes saved successfully!");
    }
    setIsSaving(false);
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setEditedTags(editedTags.filter(tag => tag !== tagToRemove));
  };

  const handleAddNewTag = () => {
    const newTag = newTagInput.trim();
    if (newTag === "") {
      toast.info("Tag cannot be empty.");
      return;
    }
    if (editedTags.some(tag => tag.toLowerCase() === newTag.toLowerCase())) {
      toast.info("Tag already exists.");
      setNewTagInput("");
      return;
    }
    setEditedTags([...editedTags, newTag]);
    setNewTagInput("");
  };

  const handleNewTagInputKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      handleAddNewTag();
    }
  };

  const handleApprove = async () => {
    console.log("[AdminDocEdit] handleApprove called");
    if (!documentId || !document || isApproving || isRejecting || document.status === 'approved') return;
    
    setIsApproving(true);
    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) {
        throw new Error('No authentication token found. Please log in again.');
      }

      console.log(`[AdminDocEdit] Attempting to approve docId: ${documentId}`);
      const response = await fetch(`/api/document-processing/approve-document/${documentId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      console.log("[AdminDocEdit] Backend approve response:", response);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      console.log("[AdminDocEdit] Approve result:", result);
      
      toast.success("Document approved and published!");
      
      // Refresh document details
      fetchDocumentDetails();
      
    } catch (approveError: any) {
      console.error("[AdminDocEdit] Error during approve:", approveError);
      toast.error(`Failed to approve document: ${approveError.message}`);
    } finally {
      setIsApproving(false);
    }
  };

  const handleReject = async () => {
    console.log("[AdminDocEdit] handleReject called");
    if (!documentId || !document || isApproving || isRejecting || document.status === 'rejected') return;
    
    setIsRejecting(true);
    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) {
        throw new Error('No authentication token found. Please log in again.');
      }

      console.log(`[AdminDocEdit] Attempting to reject docId: ${documentId}`);
      const response = await fetch(`/api/document-processing/reject-document/${documentId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      console.log("[AdminDocEdit] Backend reject response:", response);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      console.log("[AdminDocEdit] Reject result:", result);
      
      toast.success("Document rejected successfully!");
      
      // Refresh document details
      fetchDocumentDetails();
      
    } catch (rejectError: any) {
      console.error("[AdminDocEdit] Error during reject:", rejectError);
      toast.error(`Failed to reject document: ${rejectError.message}`);
    } finally {
      setIsRejecting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <Loader2 className="h-12 w-12 animate-spin text-primary" />
        <p className="ml-3 text-lg">Loading document details...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto p-4">
         <Button variant="outline" size="sm" onClick={() => navigate("/admin-pending-documents-page")} className="mb-6 w-fit">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Pending Documents
        </Button>
        <Alert variant="destructive" className="mt-4">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="container mx-auto p-4">
        <Button variant="outline" size="sm" onClick={() => navigate("/admin-pending-documents-page")} className="mb-6 w-fit">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Pending Documents
        </Button>
        <Alert variant="default" className="mt-4">
          <Info className="h-4 w-4" />
          <AlertTitle>Not Found or No ID</AlertTitle>
          <AlertDescription>The requested document could not be found or no ID was provided.</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 font-sans">
      <div className="flex justify-between items-center mb-6">
        <Button variant="outline" size="sm" onClick={() => navigate("/admin-pending-documents-page")} className="w-fit">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Pending Documents
        </Button>
        <Button onClick={handleSaveChanges} disabled={isSaving || isApproving || isRejecting} className="w-fit">
          {isSaving ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Save className="mr-2 h-4 w-4" />
          )}
          Save Changes
        </Button>
      </div>

      <Card className="max-w-4xl mx-auto shadow-lg">
        <CardHeader>
          <Label htmlFor="title" className="text-sm font-medium text-muted-foreground">Document Title</Label>
          <Input 
            id="title"
            value={editedTitle}
            onChange={(e) => setEditedTitle(e.target.value)}
            placeholder="Document Title"
            className="text-2xl font-serif h-auto p-1 mt-1 border-gray-300 focus-visible:ring-primary focus-visible:ring-offset-0 break-words"
          />
          <CardDescription className="mt-2">Document ID: {document.id}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-6">
            <div className="space-y-1">
              <Label htmlFor="status" className="text-sm font-medium text-muted-foreground">Status</Label>
              <Badge variant={document.status === 'pending' ? 'secondary' : document.status === 'approved' ? 'default' : 'outline'}
                     className="text-base px-3 py-1">
                {document.status?.toUpperCase() || "N/A"}
              </Badge>
            </div>
            <div className="space-y-1">
              <Label htmlFor="fileName" className="text-sm font-medium text-muted-foreground">File Name</Label>
              <p id="fileName" className="text-base ">{document.file_name || "N/A"}</p>
              {document.file_path && (
                <button
                  onClick={() => {
                    try {
                      // Direct download - the server now streams the file directly
                      const downloadUrl = `/api/search/download/${document.id}`;
                      
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
                    } catch (error) {
                      console.error('Download error:', error);
                      toast.error('Failed to download document');
                    }
                  }}
                  className="text-sm text-primary hover:underline block mt-1 bg-none border-none p-0"
                >
                  View/Download PDF
                </button>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-6 pt-4 border-t">
            <div className="space-y-1">
              <Label htmlFor="uploaderName" className="text-sm font-medium text-muted-foreground">Uploader Name</Label>
              <Input id="uploaderName" readOnly value={document.uploader_name || "Not provided"} className="bg-muted/40 text-base"/>
            </div>
            <div className="space-y-1">
              <Label htmlFor="uploaderEmail" className="text-sm font-medium text-muted-foreground">Uploader Email</Label>
              <Input id="uploaderEmail" readOnly value={document.uploader_email || "Not provided"} className="bg-muted/40 text-base"/>
            </div>
          </div>
          
          <div className="pt-4 border-t space-y-4">
            <h3 className="text-lg font-medium text-gray-900">Editable Information</h3>
            <div className="space-y-1">
                <Label htmlFor="descriptionEdit" className="text-sm font-medium text-muted-foreground">Description</Label>
                <Textarea 
                    id="descriptionEdit" 
                    value={editedDescription}
                    onChange={(e) => setEditedDescription(e.target.value)}
                    placeholder="Enter document description."
                    className="min-h-[120px] text-base mt-1 border-gray-300 focus-visible:ring-primary"
                />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-x-8 gap-y-6">
                <div className="space-y-1">
                    <Label htmlFor="countryEdit" className="text-sm font-medium text-muted-foreground">Country</Label>
                    <Input 
                        id="countryEdit" 
                        value={editedCountry}
                        onChange={(e) => setEditedCountry(e.target.value)}
                        placeholder="Enter country"
                        className="text-base mt-1 border-gray-300 focus-visible:ring-primary"
                    />
                </div>
                <div className="space-y-1">
                    <Label htmlFor="stateProvinceEdit" className="text-sm font-medium text-muted-foreground">State/Province</Label>
                    <Input 
                        id="stateProvinceEdit" 
                        value={editedStateProvince}
                        onChange={(e) => setEditedStateProvince(e.target.value)}
                        placeholder="Enter state or province"
                        className="text-base mt-1 border-gray-300 focus-visible:ring-primary"
                    />
                </div>
                <div className="space-y-1">
                    <Label htmlFor="adminLevelEdit" className="text-sm font-medium text-muted-foreground">Admin Level</Label>
                    <Input 
                        id="adminLevelEdit" 
                        value={editedAdminLevel}
                        onChange={(e) => setEditedAdminLevel(e.target.value)}
                        placeholder="Enter admin level (e.g., Federal, State)"
                        className="text-base mt-1 border-gray-300 focus-visible:ring-primary"
                    />
                </div>
            </div>
          </div>
          
          <div className="pt-4 border-t space-y-2">
            <Label className="text-sm font-medium text-muted-foreground">Manage Tags</Label>
            <div className="flex flex-wrap gap-2 pt-1">
              {editedTags.length > 0 ? (
                editedTags.map((tag, index) => (
                  <Badge key={index} variant="secondary" className="text-base px-2 py-1 flex items-center">
                    {tag}
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      className="h-4 w-4 ml-1 p-0 hover:bg-destructive/20"
                      onClick={() => handleRemoveTag(tag)}
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </Badge>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">No tags currently. Add some below.</p>
              )}
            </div>
            <div className="flex items-center gap-2 pt-2">
              <Input 
                type="text"
                value={newTagInput}
                onChange={(e) => setNewTagInput(e.target.value)}
                onKeyDown={handleNewTagInputKeyDown}
                placeholder="Add a new tag"
                className="flex-grow text-base border-gray-300 focus-visible:ring-primary"
              />
              <Button onClick={handleAddNewTag} variant="outline" size="sm">Add Tag</Button>
            </div>
          </div>

          <div className="pt-4 border-t space-y-1">
            <Label htmlFor="ocrText" className="text-sm font-medium text-muted-foreground">OCR Extracted Text</Label>
            <Textarea id="ocrText" readOnly value={document.ocr_text || "No OCR text available or not yet processed."} className="bg-muted/40 min-h-[150px] max-h-[300px] resize-y text-base"/>
          </div>

          <div className="pt-4 border-t space-y-1">
            <Label htmlFor="createdAt" className="text-sm font-medium text-muted-foreground">Submitted On</Label>
            <p id="createdAt" className="text-base ">
              {document.created_at ? new Date(document.created_at).toLocaleString() : "N/A"}
            </p>
          </div>
          
          <div className="pt-6 mt-6 border-t flex flex-col md:flex-row justify-end space-y-3 md:space-y-0 md:space-x-3">
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button 
                  variant="outline" // Using outline, specific destructive styling via className
                  className="w-full md:w-auto border-red-500 text-red-600 hover:bg-red-50 hover:text-red-700 disabled:border-muted-foreground/50 disabled:bg-transparent disabled:text-muted-foreground/50"
                  disabled={isApproving || isRejecting || document.status === 'rejected'}
                >
                  {isRejecting ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <XCircle className="mr-2 h-4 w-4" />}
                  Reject Document
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Confirm Rejection</AlertDialogTitle>
                  <AlertDialogDescription>
                    Are you sure you want to reject this document? This will mark it as unsuitable for publishing and it will not appear on the public archive. Any pending edits will also be saved.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction onClick={handleReject} className="bg-red-600 hover:bg-red-700">Confirm Reject</AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>

            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button 
                  className="w-full md:w-auto bg-green-600 hover:bg-green-700 text-white disabled:bg-green-600/50"
                  disabled={isApproving || isRejecting || document.status === 'approved'}
                >
                  {isApproving ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <CheckCircle2 className="mr-2 h-4 w-4" />}
                  Approve & Publish
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Confirm Approval & Publish</AlertDialogTitle>
                  <AlertDialogDescription>
                    Are you sure you want to approve and publish this document? This will make it publicly visible in the archive. Any pending edits will also be saved.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction onClick={handleApprove} className="bg-green-600 hover:bg-green-700">Confirm Approve</AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>

        </CardContent>
      </Card>
    </div>
  );
}

import React, { useEffect, useState, useCallback } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { supabase } from "../utils/supabaseClient";
import { Document } from "../types";
import brain from "brain";
import { ProcessDocumentRequest } from "brain/data-contracts";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle, Info, Loader2, ArrowLeft, Save, X, CheckCircle2, XCircle } from "lucide-react"; // Added Save, X, CheckCircle2, XCircle
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
  const documentId = searchParams.get("id");
  const navigate = useNavigate(); 

  const [document, setDocument] = useState<AdminDocumentDetails | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);

  // States for editable fields
  const [editedTitle, setEditedTitle] = useState("");
  const [editedDescription, setEditedDescription] = useState("");
  const [editedCountry, setEditedCountry] = useState("");
  const [editedStateProvince, setEditedStateProvince] = useState("");
  const [editedAdminLevel, setEditedAdminLevel] = useState("");
  const [editedTags, setEditedTags] = useState<string[]>([]);
  const [newTagInput, setNewTagInput] = useState("");

  // States for approve/reject actions
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
      const { data, error: dbError } = await supabase
        .from("documents")
        .select(
          "id, title, description, country, state_province, admin_level, file_path, file_name, status, ocr_text, generated_tags, uploader_name, uploader_email, created_at, updated_at"
        )
        .eq("id", documentId)
        .single();

      if (dbError) {
        setError(`Failed to fetch document: ${dbError.message}`);
        setDocument(null);
      } else if (data) {
        setDocument(data as AdminDocumentDetails);
        setEditedTitle(data.title || "");
        setEditedDescription(data.description || "");
        setEditedCountry(data.country || "");
        setEditedStateProvince(data.state_province || "");
        setEditedAdminLevel(data.admin_level || "");

        let parsedTags: string[] = [];
        if (typeof data.generated_tags === 'string') {
          try {
            const tags = JSON.parse(data.generated_tags);
            if (Array.isArray(tags)) {
              parsedTags = tags.map(String); // Ensure all elements are strings
            } else {
              console.warn("[AdminDocEdit] generated_tags from DB (string) did not parse to an array, defaulting to []. Value:", data.generated_tags);
            }
          } catch (e) {
            console.error("[AdminDocEdit] Error parsing generated_tags string from DB, defaulting to []. Value:", data.generated_tags, "Error:", e);
          }
        } else if (Array.isArray(data.generated_tags)) {
          parsedTags = data.generated_tags.map(String); // Ensure all elements are strings
        } else if (data.generated_tags === null || data.generated_tags === undefined) {
          // Default to empty array if null/undefined
          parsedTags = [];
        } else {
          console.warn("[AdminDocEdit] generated_tags from DB is neither string, array, null, nor undefined, defaulting to []. Value:", data.generated_tags);
        }
        setEditedTags(parsedTags);
        setError(null);
      } else {
        setError("Document not found.");
        setDocument(null);
      }
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred.");
      setDocument(null);
    } finally {
      setIsLoading(false);
    }
  }, [documentId]);

  useEffect(() => {
    if (documentId) {
      fetchDocumentDetails();
    } else {
      setError("No document ID provided.");
      setDocument(null);
      setIsLoading(false);
    }
  }, [documentId, fetchDocumentDetails]);

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
      console.log("[AdminDocEdit] Attempting to save core changes with updates:", updates, "for docId:", documentId);
      const { data, error: saveError } = await supabase
        .from("documents")
        .update(updates)
        .eq("id", documentId)
        .select();

      console.log("[AdminDocEdit] Supabase saveCoreChanges response data:", data);
      console.log("[AdminDocEdit] Supabase saveCoreChanges response error:", saveError); 

      if (saveError) {
        if (!suppressToast) toast.error(`Failed to save changes: ${saveError.message}`);
        return false;
      }
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
    console.log("[AdminDocEdit] Calling saveCoreChanges before status update to 'approved'");
    const changesSaved = await saveCoreChanges(true); 
    if (!changesSaved) {
      toast.error("Failed to save pending changes before approving. Please try saving again.");
      setIsApproving(false);
      return;
    }
    try {
      console.log(`[AdminDocEdit] Attempting to update status to 'approved' for docId: ${documentId}`);
      const { data, error: approveError } = await supabase
        .from("documents")
        .update({ status: "approved", updated_at: new Date().toISOString() })
        .eq("id", documentId)
        .select();

      console.log("[AdminDocEdit] Supabase approve response data:", data);
      console.log("[AdminDocEdit] Supabase approve response error:", approveError); 

      if (approveError) {
        toast.error(`Failed to approve document: ${approveError.message}`);
      } else {
        toast.success("Document approved and published!");
        // --- BEGIN ADDITION ---
        if (data && data.length > 0 && data[0].id && data[0].file_path) {
          const approvedDocId = data[0].id;
          const approvedDocPdfUrl = data[0].file_path;
          
          toast.info("Initiating document processing (OCR, tagging)...", { id: `processing-${approvedDocId}` });
          try {
            console.log(`[AdminDocEdit] Calling brain.process_document for docId: ${approvedDocId}, pdf_url: ${approvedDocPdfUrl}`);
            // Explicitly type the request body
            const requestBody: ProcessDocumentRequest = {
              document_id: approvedDocId,
              pdf_url: approvedDocPdfUrl,
            };
            const processResponse = await brain.process_document(requestBody);

            console.log("[AdminDocEdit] brain.process_document successful:", processResponse);
            // Assuming processResponse.data contains the actual response from the endpoint
             // We can update the local document state if needed, or just rely on fetchDocumentDetails for now.
            toast.success("Document processing initiated successfully.", { id: `processing-${approvedDocId}` });

          } catch (processError: any) {
            console.error("[AdminDocEdit] Error calling brain.process_document:", processError);
            let PErrorMsg = "Failed to initiate document processing.";
            // Errors from brain HTTP client often have a 'data' property with the actual API error response
            if (processError?.data?.detail) { 
              PErrorMsg = typeof processError.data.detail === 'string' ? processError.data.detail : JSON.stringify(processError.data.detail);
            } else if (processError?.response?.data?.detail) { // Sometimes it's nested further
                 PErrorMsg = typeof processError.response.data.detail === 'string' ? processError.response.data.detail : JSON.stringify(processError.response.data.detail);
            } else if (processError.message) {
              PErrorMsg = processError.message;
            }
            toast.error(`Processing Error: ${PErrorMsg}`, { id: `processing-${approvedDocId}`, duration: 10000 });
          }
        } else {
          console.warn("[AdminDocEdit] Could not initiate processing: document ID or file_path missing after approval response.", data);
          toast.warning("Could not automatically initiate document processing: missing document details in approval response.");
        }
        // --- END ADDITION ---
        await fetchDocumentDetails(); 
      }
    } catch (err: any) {
      console.error("[AdminDocEdit] Catch block error during approve status update:", err);
      toast.error(`An error occurred: ${err.message}`);
    } finally {
      setIsApproving(false);
    }
  };

  const handleReject = async () => {
    console.log("[AdminDocEdit] handleReject called");
    if (!documentId || !document || isApproving || isRejecting || document.status === 'rejected') return;
    setIsRejecting(true);
    console.log("[AdminDocEdit] Calling saveCoreChanges before status update to 'rejected'");
    const changesSaved = await saveCoreChanges(true); 
    if (!changesSaved) {
      toast.error("Failed to save pending changes before rejecting. Please try saving again.");
      setIsRejecting(false);
      return;
    }
    try {
      console.log(`[AdminDocEdit] Attempting to update status to 'rejected' for docId: ${documentId}`);
      const { data, error: rejectError } = await supabase
        .from("documents")
        .update({ status: "rejected", updated_at: new Date().toISOString() })
        .eq("id", documentId)
        .select();

      console.log("[AdminDocEdit] Supabase reject response data:", data);
      console.log("[AdminDocEdit] Supabase reject response error:", rejectError);

      if (rejectError) {
        toast.error(`Failed to reject document: ${rejectError.message}`);
      } else {
        toast.success("Document rejected.");
        await fetchDocumentDetails();
      }
    } catch (err: any) {
      console.error("[AdminDocEdit] Catch block error during reject status update:", err);
      toast.error(`An error occurred: ${err.message}`);
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
                <a href={document.file_path} target="_blank" rel="noopener noreferrer" className="text-sm text-primary hover:underline block mt-1">
                  View/Download PDF
                </a>
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

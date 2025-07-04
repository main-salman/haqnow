import React, { useState, useEffect } from "react"; // Added useEffect
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Eye, CheckCircle, XCircle, Filter, Search as SearchIcon, Loader2, FileText } from "lucide-react"; // Added Loader2 and FileText
import { Link } from "react-router-dom";
import { supabase } from "utils/supabaseClient"; // Use supabaseClient
import { toast } from "sonner";
import brain from "brain"; // Added import
import { ProcessDocumentRequest } from "brain/data-contracts"; // Added import
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

// Define the structure of a document fetched from Supabase
interface DocumentData {
  id: string;
  title: string | null;
  country: string | null;
  uploader_name: string | null;
  uploader_email: string | null;
  file_name: string | null; // Fallback if uploader info is missing
  file_path: string | null; // Added this for process_document call
  created_at: string; // Supabase typically returns ISO string for timestamps
  status: string;
  // Add other fields if needed, like state_province, etc.
}

// Mock data for countries filter - can be replaced with dynamic data later
const mockCountries = [
  { id: "all", name: "All Countries" },
  { id: "us", name: "United States" },
  { id: "ca", name: "Canada" },
  { id: "gb", name: "United Kingdom" },
  // Add other countries that are expected or fetch dynamically
];

export default function AdminPendingDocumentsPage() {
  const [documents, setDocuments] = useState<DocumentData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCountry, setSelectedCountry] = useState("all");
  const [updatingDocId, setUpdatingDocId] = useState<string | null>(null); // For loading state on specific row buttons

  useEffect(() => {
    const fetchPendingDocuments = async () => {
      setIsLoading(true);
      setError(null);
      console.log("[AdminPendingDocs] fetchPendingDocuments called. Querying Supabase..."); // New log
      try {
        const { data, error: supaError } = await supabase
          .from("documents")
          .select("id, title, country, uploader_name, uploader_email, file_name, file_path, created_at, status") // Added file_path
          .eq("status", "pending") // Fetch documents with 'pending' status
          .order("created_at", { ascending: false });

        console.log("[AdminPendingDocs] Supabase response received."); // New log
        console.log("[AdminPendingDocs] Supabase data:", data); // New log
        console.log("[AdminPendingDocs] Supabase error:", supaError); // New log

        if (supaError) {
          console.error("Error fetching pending documents:", supaError);
          throw new Error(supaError.message);
        }
        console.log(`[AdminPendingDocs] ${data?.length || 0} documents fetched from Supabase with status 'pending'.`); // New log
        setDocuments(data || []);
      } catch (err) {
        console.error("[AdminPendingDocs] Caught error in fetchPendingDocuments:", err); // Modified log
        let message = "Failed to fetch documents. Please try again.";
        if (err instanceof Error) {
          message = err.message;
        }
        setError(message);
        setDocuments([]); // Clear documents on error
      } finally {
        setIsLoading(false);
        console.log("[AdminPendingDocs] fetchPendingDocuments finished. isLoading set to false."); // New log
      }
    };

    console.log("[AdminPendingDocs] useEffect triggered. Fetching documents..."); // New log
    fetchPendingDocuments();
  }, []); // Empty dependency array means this runs once on mount

  // Function to refresh documents - can be called after actions
  const fetchPendingDocuments = async () => {
    setIsLoading(true);
    setError(null);
    console.log("[AdminPendingDocs] fetchPendingDocuments called. Querying Supabase...");
    try {
      const { data, error: supaError } = await supabase
        .from("documents")
        .select("id, title, country, uploader_name, uploader_email, file_name, file_path, created_at, status") // Added file_path
        .eq("status", "pending")
        .order("created_at", { ascending: false });

      console.log("[AdminPendingDocs] Supabase response received.");
      console.log("[AdminPendingDocs] Supabase data:", data);
      console.log("[AdminPendingDocs] Supabase error:", supaError);

      if (supaError) {
        console.error("Error fetching pending documents:", supaError);
        throw new Error(supaError.message);
      }
      console.log(`[AdminPendingDocs] ${data?.length || 0} documents fetched from Supabase with status 'pending'.`);
      setDocuments(data || []);
    } catch (err) {
      console.error("[AdminPendingDocs] Caught error in fetchPendingDocuments:", err);
      let message = "Failed to fetch documents. Please try again.";
      if (err instanceof Error) {
        message = err.message;
      }
      setError(message);
      setDocuments([]);
    } finally {
      setIsLoading(false);
      console.log("[AdminPendingDocs] fetchPendingDocuments finished. isLoading set to false.");
    }
  };

  useEffect(() => {
    console.log("[AdminPendingDocs] useEffect triggered. Fetching documents...");
    fetchPendingDocuments();
  }, []);

  const handleApprove = async (docId: string) => {
    console.log(`[AdminPendingDocs] handleApprove called for docId: ${docId}`);
    setUpdatingDocId(docId);
    try {
      console.log(`[AdminPendingDocs] Attempting to update status to 'approved' for docId: ${docId}`);
      const { data, error } = await supabase
        .from("documents")
        .update({ status: "approved", updated_at: new Date().toISOString() })
        .eq("id", docId)
        .select(); // Add select to get the updated row back

      console.log("[AdminPendingDocs] Supabase approve response data:", data);
      console.log("[AdminPendingDocs] Supabase approve response error:", error);

      if (error) {
        toast.error(`Failed to approve document: ${error.message}`);
      } else {
        toast.success("Document approved successfully!");
        // --- BEGIN ADDITION ---
        if (data && data.length > 0 && data[0].id && data[0].file_path) {
          const approvedDocId = data[0].id;
          const approvedDocPdfUrl = data[0].file_path;

          toast.info(`Initiating processing for ${data[0].title || 'document'}...`, { id: `processing-${approvedDocId}` });
          try {
            console.log(`[AdminPendingDocs] Calling brain.process_document for docId: ${approvedDocId}, pdf_url: ${approvedDocPdfUrl}`);
            const requestBody: ProcessDocumentRequest = {
              document_id: approvedDocId,
              pdf_url: approvedDocPdfUrl,
            };
            await brain.process_document(requestBody);
            toast.success(`Processing initiated for ${data[0].title || 'document'}.`, { id: `processing-${approvedDocId}` });
          } catch (processError: any) {
            console.error("[AdminPendingDocs] Error calling brain.process_document:", processError);
            let PErrorMsg = "Failed to initiate document processing.";
             if (processError?.data?.detail) { 
              PErrorMsg = typeof processError.data.detail === 'string' ? processError.data.detail : JSON.stringify(processError.data.detail);
            } else if (processError?.response?.data?.detail) { 
                 PErrorMsg = typeof processError.response.data.detail === 'string' ? processError.response.data.detail : JSON.stringify(processError.response.data.detail);
            } else if (processError.message) {
              PErrorMsg = processError.message;
            }
            toast.error(`Processing Error: ${PErrorMsg}`, { id: `processing-${approvedDocId}`, duration: 10000 });
          }
        } else {
          console.warn("[AdminPendingDocs] Could not initiate processing: document ID or file_path missing after approval.", data);
          toast.warning("Could not automatically initiate processing: missing document details.");
        }
        // --- END ADDITION ---
        fetchPendingDocuments(); // Refetch to update the list
      }
    } catch (err: any) {
      console.error("[AdminPendingDocs] Catch block error during approve:", err);
      toast.error(`An error occurred: ${err.message}`);
    } finally {
      setUpdatingDocId(null);
    }
  };

  const handleReject = async (docId: string) => {
    console.log(`[AdminPendingDocs] handleReject called for docId: ${docId}`);
    setUpdatingDocId(docId);
    try {
      console.log(`[AdminPendingDocs] Attempting to update status to 'rejected' for docId: ${docId}`);
      const { data, error } = await supabase
        .from("documents")
        .update({ status: "rejected", updated_at: new Date().toISOString() })
        .eq("id", docId)
        .select(); // Add select to get the updated row back

      console.log("[AdminPendingDocs] Supabase reject response data:", data);
      console.log("[AdminPendingDocs] Supabase reject response error:", error);

      if (error) {
        toast.error(`Failed to reject document: ${error.message}`);
      } else {
        toast.success("Document rejected successfully!");
        fetchPendingDocuments(); // Refetch to update the list
      }
    } catch (err: any) {
      console.error("[AdminPendingDocs] Catch block error during reject:", err);
      toast.error(`An error occurred: ${err.message}`);
    } finally {
      setUpdatingDocId(null);
    }
  };

  // Client-side filtering (can be moved to server-side for large datasets)
  const filteredDocuments = documents.filter(doc => {
    const searchLower = searchTerm.toLowerCase();
    const matchesSearch = 
      (doc.title?.toLowerCase().includes(searchLower)) ||
      (doc.uploader_name?.toLowerCase().includes(searchLower)) ||
      (doc.uploader_email?.toLowerCase().includes(searchLower)) ||
      (doc.file_name?.toLowerCase().includes(searchLower));
    
    const countryLower = doc.country?.toLowerCase().replace(/\s+/g, "") || "";
    const matchesCountry = selectedCountry === "all" || countryLower === selectedCountry.toLowerCase().replace(/\s+/g, "");
    
    return matchesSearch && matchesCountry;
  });

  const getSubmitterDisplay = (doc: DocumentData) => {
    return doc.uploader_name || doc.uploader_email || doc.file_name || "N/A";
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="ml-2 text-muted-foreground">Loading pending documents...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-destructive">
        <XCircle className="h-8 w-8 mb-2" />
        <p className="font-semibold">Error loading documents</p>
        <p className="text-sm">{error}</p>
        <Button variant="outline" onClick={() => window.location.reload()} className="mt-4">
          Try Again
        </Button>
      </div>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-2xl font-serif">Pending Document Review</CardTitle>
        <CardDescription>Review, approve, or reject submitted documents.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Filters */}
        <div className="flex flex-col md:flex-row gap-4 items-center p-4 border rounded-lg bg-muted/50">
          <div className="flex-grow flex items-center space-x-2 w-full md:w-auto">
            <SearchIcon className="text-muted-foreground"/>
            <Input 
              placeholder="Search by title, submitter, filename..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="flex-grow"
            />
          </div>
          <div className="flex items-center space-x-2 w-full md:w-auto">
            <Filter className="text-muted-foreground"/>
            <Select value={selectedCountry} onValueChange={setSelectedCountry}>
              <SelectTrigger className="min-w-[180px]">
                <SelectValue placeholder="Filter by Country" />
              </SelectTrigger>
              <SelectContent>
                {mockCountries.map(country => (
                  <SelectItem key={country.id} value={country.id}>{country.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Documents Table */}
        {filteredDocuments.length === 0 && !isLoading ? (
            <div className="text-center text-muted-foreground py-12">
                 <FileText className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                <p className="text-lg font-semibold">No Pending Documents</p>
                <p>There are currently no documents awaiting review, or none match your filters.</p>
            </div>
        ) : (
          <div className="border rounded-lg overflow-hidden">
            <Table>
              <TableHeader className="bg-muted/50">
                <TableRow>
                  <TableHead className="w-[35%]">Title</TableHead>
                  <TableHead>Country</TableHead>
                  <TableHead>Submitter</TableHead>
                  <TableHead>Uploaded Date</TableHead>
                  <TableHead className="text-center w-[20%]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredDocuments.map((doc) => (
                  <TableRow key={doc.id}>
                    <TableCell className="font-medium">{doc.title || "N/A"}</TableCell>
                    <TableCell>{doc.country || "N/A"}</TableCell>
                    <TableCell>{getSubmitterDisplay(doc)}</TableCell>
                    <TableCell>{new Date(doc.created_at).toLocaleDateString()}</TableCell>
                    <TableCell className="text-center space-x-1">
                      <Button asChild variant="outline" size="sm" className="px-2 py-1 h-auto">
                        <Link to={`/admin-document-edit-page?id=${doc.id}`}> 
                          <Eye className="h-4 w-4 mr-1" /> View
                        </Link>
                      </Button>

                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            className="text-green-600 hover:text-green-700 hover:bg-green-50 px-2 py-1 h-auto disabled:text-muted-foreground"
                            disabled={updatingDocId === doc.id}
                          >
                            {updatingDocId === doc.id ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <CheckCircle className="h-4 w-4 mr-1" />}
                            Approve
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>Confirm Approval</AlertDialogTitle>
                            <AlertDialogDescription>
                              Are you sure you want to approve the document "{doc.title || 'Untitled Document'}"? This will make it publicly visible.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction onClick={() => handleApprove(doc.id)} className="bg-green-600 hover:bg-green-700">Confirm Approve</AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>

                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            className="text-red-600 hover:text-red-700 hover:bg-red-50 px-2 py-1 h-auto disabled:text-muted-foreground"
                            disabled={updatingDocId === doc.id}
                          >
                            {updatingDocId === doc.id ? <Loader2 className="h-4 w-4 mr-1 animate-spin" /> : <XCircle className="h-4 w-4 mr-1" />}
                            Reject
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>Confirm Rejection</AlertDialogTitle>
                            <AlertDialogDescription>
                              Are you sure you want to reject the document "{doc.title || 'Untitled Document'}"? This will mark it as not suitable for publishing.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction onClick={() => handleReject(doc.id)} className="bg-red-600 hover:bg-red-700">Confirm Reject</AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

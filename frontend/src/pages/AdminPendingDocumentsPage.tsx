import React, { useState, useEffect } from "react"; // Added useEffect
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Eye, CheckCircle, XCircle, Filter, Search as SearchIcon, Loader2, FileText, AlertTriangle } from "lucide-react"; // Added Loader2 and FileText
import { Link } from "react-router-dom";
// Remove Supabase import - we don't use it anymore
// import { supabase } from "utils/supabaseClient";
import { toast } from "sonner";
// Remove brain import - we'll use direct fetch instead
// import brain from "brain";
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

// Define the structure of a document from the backend API
interface DocumentData {
  id: number;
  title: string | null;
  country: string | null;
  state: string | null;
  original_filename: string | null;
  file_path: string | null;
  created_at: string;
  status: string;
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
  const [updatingDocId, setUpdatingDocId] = useState<number | null>(null); // For loading state on specific row buttons
  const [failedJobs, setFailedJobs] = useState<any[]>([]);
  const [isLoadingFailedJobs, setIsLoadingFailedJobs] = useState(false);

  // Function to fetch pending documents from backend API
  const fetchPendingDocuments = async () => {
    setIsLoading(true);
    setError(null);
    console.log("[AdminPendingDocs] fetchPendingDocuments called. Querying backend API...");
    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) {
        throw new Error('No authentication token found. Please log in again.');
      }

      const response = await fetch('/api/document-processing/documents?status=pending', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      console.log("[AdminPendingDocs] Backend API response received.");

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log("[AdminPendingDocs] Backend API data:", data);

      setDocuments(data.documents || []);
      console.log(`[AdminPendingDocs] ${data.documents?.length || 0} documents fetched from backend with status 'pending'.`);
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
    fetchFailedJobs();
  }, []);

  const fetchFailedJobs = async () => {
    setIsLoadingFailedJobs(true);
    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) {
        return;
      }

      const response = await fetch('/api/document-processing/failed-jobs?limit=50', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setFailedJobs(data.failed_jobs || []);
      }
    } catch (err) {
      console.error("[AdminPendingDocs] Error fetching failed jobs:", err);
    } finally {
      setIsLoadingFailedJobs(false);
    }
  };

  const handleApprove = async (docId: number) => {
    console.log(`[AdminPendingDocs] handleApprove called for docId: ${docId}`);
    setUpdatingDocId(docId);
    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) {
        throw new Error('No authentication token found. Please log in again.');
      }

      console.log(`[AdminPendingDocs] Attempting to approve docId: ${docId}`);
      const response = await fetch(`/api/document-processing/approve-document/${docId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      console.log("[AdminPendingDocs] Backend approve response:", response);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      console.log("[AdminPendingDocs] Approve result:", result);
      
      toast.success("Document approved successfully!");
      
      // Refresh the document list
      fetchPendingDocuments();
      
    } catch (err: any) {
      console.error("[AdminPendingDocs] Catch block error during approve:", err);
      toast.error(`Failed to approve document: ${err.message}`);
    } finally {
      setUpdatingDocId(null);
    }
  };

  const handleReject = async (docId: number) => {
    console.log(`[AdminPendingDocs] handleReject called for docId: ${docId}`);
    setUpdatingDocId(docId);
    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) {
        throw new Error('No authentication token found. Please log in again.');
      }

      console.log(`[AdminPendingDocs] Attempting to reject docId: ${docId}`);
      const response = await fetch(`/api/document-processing/reject-document/${docId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      console.log("[AdminPendingDocs] Backend reject response:", response);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      console.log("[AdminPendingDocs] Reject result:", result);
      
      toast.success("Document rejected successfully!");
      
      // Refresh the document list
      fetchPendingDocuments();
      
    } catch (err: any) {
      console.error("[AdminPendingDocs] Catch block error during reject:", err);
      toast.error(`Failed to reject document: ${err.message}`);
    } finally {
      setUpdatingDocId(null);
    }
  };

  // Client-side filtering (can be moved to server-side for large datasets)
  const filteredDocuments = documents.filter(doc => {
    const searchLower = searchTerm.toLowerCase();
    const matchesSearch = 
      (doc.title?.toLowerCase().includes(searchLower)) ||
      (doc.original_filename?.toLowerCase().includes(searchLower));
    
    const countryLower = doc.country?.toLowerCase().replace(/\s+/g, "") || "";
    const matchesCountry = selectedCountry === "all" || countryLower === selectedCountry.toLowerCase().replace(/\s+/g, "");
    
    return matchesSearch && matchesCountry;
  });

  const getSubmitterDisplay = (doc: DocumentData) => {
    return "Anonymous";
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
    <div className="space-y-6">
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-2xl font-serif">Pending Document Review</CardTitle>
            <CardDescription>Review, approve, or reject submitted documents.</CardDescription>
          </div>
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => {
              console.log("[AdminPendingDocs] Manual refresh triggered");
              fetchPendingDocuments();
            }}
            className="flex items-center gap-2"
          >
            <Loader2 className="h-4 w-4" />
            Refresh
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Filters */}
        <div className="flex flex-col md:flex-row gap-4 items-center p-4 border rounded-lg bg-muted/50">
          <div className="flex-grow flex items-center space-x-2 w-full md:w-auto">
            <SearchIcon className="text-muted-foreground"/>
            <Input 
              placeholder="Search by title, filename..." 
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

    {/* Failed Jobs Section */}
    {failedJobs.length > 0 && (
      <Card className="mt-6 border-orange-200">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-orange-600" />
              <div>
                <CardTitle className="text-xl font-serif text-orange-900">Failed Processing Jobs</CardTitle>
                <CardDescription>Documents that failed to process automatically</CardDescription>
              </div>
            </div>
            <Button 
              variant="outline" 
              size="sm"
              onClick={fetchFailedJobs}
              className="flex items-center gap-2"
            >
              <Loader2 className="h-4 w-4" />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="border rounded-lg overflow-hidden">
            <Table>
              <TableHeader className="bg-orange-50">
                <TableRow>
                  <TableHead>Document</TableHead>
                  <TableHead>Error</TableHead>
                  <TableHead>Failed At</TableHead>
                  <TableHead>Retries</TableHead>
                  <TableHead className="text-center">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {failedJobs.map((job) => (
                  <TableRow key={job.id}>
                    <TableCell>
                      {job.document ? (
                        <div>
                          <div className="font-medium">{job.document.title || 'Untitled'}</div>
                          <div className="text-sm text-muted-foreground">
                            {job.document.country} {job.document.state ? `- ${job.document.state}` : ''}
                          </div>
                        </div>
                      ) : (
                        <span className="text-muted-foreground">Document ID: {job.document_id}</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="max-w-md truncate text-sm text-red-600" title={job.error_message}>
                        {job.error_message || 'Unknown error'}
                      </div>
                    </TableCell>
                    <TableCell>
                      {job.failed_at ? new Date(job.failed_at).toLocaleString() : 'N/A'}
                    </TableCell>
                    <TableCell>
                      {job.retry_count} / {job.max_retries}
                    </TableCell>
                    <TableCell className="text-center">
                      {job.document && (
                        <Button asChild variant="outline" size="sm">
                          <Link to={`/admin-document-edit-page?id=${job.document_id}`}>
                            <Eye className="h-4 w-4 mr-1" /> View
                          </Link>
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    )}
    </div>
  );
}

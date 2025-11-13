import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Eye, Trash2, Loader2, AlertCircle, ArrowLeft, FileText } from "lucide-react";
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
import { toast } from "sonner";

// Document data interface
interface DocumentData {
  id: number;
  title: string | null;
  country: string | null;
  state: string | null;
  description: string | null;
  file_path: string | null;
  file_url: string | null;
  original_filename: string | null;
  file_size: number | null;
  content_type: string | null;
  status: string;
  created_at: string;
  updated_at: string;
  processed_at: string | null;
  approved_at: string | null;
  approved_by: string | null;
  ocr_text: string | null;
  generated_tags: string[] | null;
  view_count?: number;
  hidden_from_top_viewed?: boolean;
}

// Mock data for countries filter - can be replaced with dynamic data later
const mockCountries = [
  { id: "all", name: "All Countries" },
  { id: "us", name: "United States" },
  { id: "ca", name: "Canada" },
  { id: "gb", name: "United Kingdom" },
  // Add other countries that are expected or fetch dynamically
];

export default function AdminApprovedDocumentsPage() {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<DocumentData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCountry, setSelectedCountry] = useState("all");
  const [deletingDocId, setDeletingDocId] = useState<number | null>(null);

  // Function to fetch approved documents from backend API
  const fetchApprovedDocuments = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) {
        console.error('No authentication token found');
        navigate("/admin-login-page");
        return;
      }

      const response = await fetch('/api/document-processing/documents?status=approved', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          console.error('Authentication failed');
          navigate("/admin-login-page");
          return;
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log("[AdminApprovedDocumentsPage] Approved documents:", data);

      if (data && data.documents) {
        setDocuments(data.documents);
      } else {
        setDocuments([]);
      }
    } catch (err: any) {
      console.error("[AdminApprovedDocumentsPage] Error fetching documents:", err);
      let errorMessage = "Failed to load approved documents.";
      if (err.message) {
        errorMessage = err.message;
      }
      setError(errorMessage);
      toast.error(`Failed to load documents: ${errorMessage}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Function to delete a document
  const deleteDocument = async (documentId: number) => {
    setDeletingDocId(documentId);
    
    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) {
        console.error('No authentication token found');
        navigate("/admin-login-page");
        return;
      }

      const response = await fetch(`/api/document-processing/delete-document/${documentId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          console.error('Authentication failed');
          navigate("/admin-login-page");
          return;
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      console.log("[AdminApprovedDocumentsPage] Document deleted:", data);

      // Remove document from local state
      setDocuments(prev => prev.filter(doc => doc.id !== documentId));
      
      toast.success(`Document deleted successfully`);
    } catch (err: any) {
      console.error("[AdminApprovedDocumentsPage] Error deleting document:", err);
      let errorMessage = "Failed to delete document.";
      if (err.message) {
        errorMessage = err.message;
      }
      setError(errorMessage);
      toast.error(`Failed to delete document: ${errorMessage}`);
    } finally {
      setDeletingDocId(null);
    }
  };

  // Fetch documents on component mount
  useEffect(() => {
    fetchApprovedDocuments();
  }, []);

  // Filter documents based on search term and country
  const filteredDocuments = documents.filter((doc) => {
    const matchesSearch = 
      !searchTerm ||
      (doc.title && doc.title.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (doc.country && doc.country.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (doc.description && doc.description.toLowerCase().includes(searchTerm.toLowerCase()));
    
    const matchesCountry = 
      selectedCountry === "all" || 
      doc.country === selectedCountry;
    
    return matchesSearch && matchesCountry;
  });

  // Helper function to get submitter display
  const getSubmitterDisplay = (doc: DocumentData) => {
    return "Anonymous";
  };

  // Helper function to format file size
  const formatFileSize = (bytes: number | null) => {
    if (!bytes) return "N/A";
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button asChild variant="outline" size="sm">
            <Link to="/admin-dashboard-page">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Dashboard
            </Link>
          </Button>
          <div>
            <h1 className="text-3xl font-bold font-serif">Approved Documents</h1>
            <p className="text-muted-foreground">Manage documents that are live on the platform</p>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardHeader>
          <CardTitle>Filter and Search</CardTitle>
          <CardDescription>Find specific approved documents</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <Input
                placeholder="Search by title, country, or description..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full"
              />
            </div>
            <div className="w-full md:w-48">
              <Select value={selectedCountry} onValueChange={setSelectedCountry}>
                <SelectTrigger>
                  <SelectValue placeholder="Filter by country" />
                </SelectTrigger>
                <SelectContent>
                  {mockCountries.map((country) => (
                    <SelectItem key={country.id} value={country.id}>
                      {country.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Documents Table */}
      <Card>
        <CardHeader>
          <CardTitle>Approved Documents ({filteredDocuments.length})</CardTitle>
          <CardDescription>
            Documents that are currently live and searchable on the platform
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center items-center py-12">
              <Loader2 className="h-8 w-8 animate-spin" />
              <span className="ml-2">Loading approved documents...</span>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center py-12 text-destructive">
              <AlertCircle className="h-12 w-12 mb-4" />
              <p className="text-lg font-semibold">Error Loading Documents</p>
              <p className="text-sm">{error}</p>
              <Button onClick={fetchApprovedDocuments} className="mt-4">
                Try Again
              </Button>
            </div>
          ) : filteredDocuments.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="h-16 w-16 mx-auto mb-4 text-gray-400" />
              <p className="text-xl font-semibold">No Approved Documents Found</p>
              <p className="text-muted-foreground">
                {documents.length === 0 
                  ? "No documents have been approved yet."
                  : "No documents match your current search criteria."}
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Title</TableHead>
                    <TableHead>Country</TableHead>
                    <TableHead>Submitter</TableHead>
                    <TableHead>Approved Date</TableHead>
                    <TableHead>Approved By</TableHead>
                    <TableHead>File Size</TableHead>
                    <TableHead className="text-center">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredDocuments.map((doc) => (
                    <TableRow key={doc.id}>
                      <TableCell className="font-medium">{doc.title || "N/A"}</TableCell>
                      <TableCell>{doc.country || "N/A"}</TableCell>
                      <TableCell>{getSubmitterDisplay(doc)}</TableCell>
                      <TableCell>{doc.approved_at ? new Date(doc.approved_at).toLocaleDateString() : "N/A"}</TableCell>
                      <TableCell>{doc.approved_by || "N/A"}</TableCell>
                      <TableCell>{formatFileSize(doc.file_size)}</TableCell>
                      <TableCell className="text-center space-x-1">
                        <Button asChild variant="outline" size="sm" className="px-2 py-1 h-auto">
                          <Link to={`/admin-document-edit-page?id=${doc.id}`}> 
                            <Eye className="h-4 w-4 mr-1" /> View
                          </Link>
                        </Button>
                        <AlertDialog>
                          <AlertDialogTrigger asChild>
                            <Button 
                              variant="destructive" 
                              size="sm" 
                              className="px-2 py-1 h-auto"
                              disabled={deletingDocId === doc.id}
                            >
                              {deletingDocId === doc.id ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                              ) : (
                                <>
                                  <Trash2 className="h-4 w-4 mr-1" /> Delete
                                </>
                              )}
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>Delete Document</AlertDialogTitle>
                              <AlertDialogDescription>
                                Are you sure you want to permanently delete "{doc.title || 'this document'}"? 
                                This action cannot be undone and will remove the document from the platform and delete its file.
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>Cancel</AlertDialogCancel>
                              <AlertDialogAction 
                                onClick={() => deleteDocument(doc.id)}
                                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                              >
                                Delete Permanently
                              </AlertDialogAction>
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
    </div>
  );
} 
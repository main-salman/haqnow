import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Eye, EyeOff, Loader2, AlertCircle, ArrowLeft, TrendingUp } from "lucide-react";
import { toast } from "sonner";

interface TopViewedDocument {
  id: number;
  title: string;
  country: string;
  state: string;
  view_count: number;
  hidden_from_top_viewed?: boolean;
  created_at: string;
}

export default function AdminTopViewedPage() {
  const [documents, setDocuments] = useState<TopViewedDocument[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [togglingId, setTogglingId] = useState<number | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchTopViewedDocuments();
  }, []);

  const fetchTopViewedDocuments = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) {
        navigate("/admin-login-page");
        return;
      }

      // Fetch top viewed including hidden ones for admin view
      const response = await fetch('/api/search/top-viewed?limit=50', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          navigate("/admin-login-page");
          return;
        }
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      
      // Fetch full document details to get hidden status
      const docsWithStatus = await Promise.all(
        (data.documents || []).map(async (doc: any) => {
          try {
            const detailResponse = await fetch(`/api/document-processing/document/${doc.id}`, {
              headers: { 'Authorization': `Bearer ${token}` },
            });
            if (detailResponse.ok) {
              const fullDoc = await detailResponse.json();
              return { ...doc, hidden_from_top_viewed: fullDoc.hidden_from_top_viewed || false };
            }
          } catch (e) {
            console.error(`Error fetching details for doc ${doc.id}:`, e);
          }
          return { ...doc, hidden_from_top_viewed: false };
        })
      );

      setDocuments(docsWithStatus);
    } catch (err: any) {
      console.error('Error fetching top viewed documents:', err);
      setError(err.message || 'Failed to load documents');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleTopViewed = async (documentId: number) => {
    setTogglingId(documentId);

    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) {
        navigate("/admin-login-page");
        return;
      }

      const response = await fetch(`/api/admin-management/documents/${documentId}/toggle-top-viewed`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to toggle visibility');
      }

      const result = await response.json();
      
      // Update local state
      setDocuments(docs =>
        docs.map(doc =>
          doc.id === documentId
            ? { ...doc, hidden_from_top_viewed: result.hidden_from_top_viewed }
            : doc
        )
      );

      toast.success(result.message || 'Visibility updated');
    } catch (err: any) {
      console.error('Error toggling top viewed:', err);
      toast.error('Failed to update visibility');
    } finally {
      setTogglingId(null);
    }
  };

  return (
    <div className="container mx-auto py-6 space-y-6">
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
            <h1 className="text-3xl font-bold font-serif flex items-center gap-2">
              <TrendingUp className="h-8 w-8" />
              Top Viewed Documents
            </h1>
            <p className="text-muted-foreground">Manage which documents appear in the "Most Viewed" section</p>
          </div>
        </div>
      </div>

      {/* Documents Table */}
      <Card>
        <CardHeader>
          <CardTitle>Most Viewed Documents</CardTitle>
          <CardDescription>
            Hide or unhide documents from the public "Top Viewed" list on the homepage
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center items-center py-12">
              <Loader2 className="h-8 w-8 animate-spin" />
              <span className="ml-2">Loading documents...</span>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center py-12 text-destructive">
              <AlertCircle className="h-12 w-12 mb-4" />
              <p className="text-lg font-semibold">Error Loading Documents</p>
              <p className="text-sm">{error}</p>
              <Button onClick={fetchTopViewedDocuments} className="mt-4">
                Try Again
              </Button>
            </div>
          ) : documents.length === 0 ? (
            <div className="text-center py-12">
              <TrendingUp className="h-16 w-16 mx-auto mb-4 text-gray-400" />
              <p className="text-xl font-semibold">No Viewed Documents Yet</p>
              <p className="text-muted-foreground">
                Documents will appear here once users start viewing them
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-12">#</TableHead>
                    <TableHead>Title</TableHead>
                    <TableHead>Country</TableHead>
                    <TableHead className="text-center">Views</TableHead>
                    <TableHead className="text-center">Visibility</TableHead>
                    <TableHead className="text-center">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {documents.map((doc, index) => (
                    <TableRow key={doc.id} className={doc.hidden_from_top_viewed ? 'opacity-50' : ''}>
                      <TableCell className="font-semibold text-emerald-600">{index + 1}</TableCell>
                      <TableCell className="font-medium max-w-md truncate">{doc.title}</TableCell>
                      <TableCell>{doc.country}{doc.state && `, ${doc.state}`}</TableCell>
                      <TableCell className="text-center">
                        <span className="inline-flex items-center gap-1 font-semibold">
                          <Eye className="h-4 w-4" />
                          {doc.view_count.toLocaleString()}
                        </span>
                      </TableCell>
                      <TableCell className="text-center">
                        {doc.hidden_from_top_viewed ? (
                          <span className="inline-flex items-center gap-1 text-amber-600">
                            <EyeOff className="h-4 w-4" />
                            Hidden
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-emerald-600">
                            <Eye className="h-4 w-4" />
                            Visible
                          </span>
                        )}
                      </TableCell>
                      <TableCell className="text-center">
                        <Button
                          variant={doc.hidden_from_top_viewed ? "default" : "outline"}
                          size="sm"
                          onClick={() => toggleTopViewed(doc.id)}
                          disabled={togglingId === doc.id}
                        >
                          {togglingId === doc.id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : doc.hidden_from_top_viewed ? (
                            <>
                              <Eye className="h-4 w-4 mr-1" />
                              Show
                            </>
                          ) : (
                            <>
                              <EyeOff className="h-4 w-4 mr-1" />
                              Hide
                            </>
                          )}
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <TrendingUp className="h-5 w-5 text-blue-600 mt-0.5" />
            <div>
              <h3 className="font-semibold text-blue-900 mb-1">About Top Viewed Documents</h3>
              <ul className="text-sm text-blue-800 space-y-1">
                <li>• View counts increment when users open document details or download files</li>
                <li>• Rate limited to once per hour per session to prevent spam</li>
                <li>• Hidden documents still accumulate views but won't appear on the homepage</li>
                <li>• Top 10 visible documents are shown on the main page below the world map</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}


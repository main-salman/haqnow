import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { MessageSquare, CheckCircle, XCircle, Loader2, Flag, Trash2 } from "lucide-react";
import { toast } from "sonner";

interface Comment {
  id: number;
  document_id: number;
  parent_comment_id: number | null;
  comment_text: string;
  status: string;
  flag_count: number;
  created_at: string;
  reply_count: number;
}

export default function AdminCommentModerationPage() {
  const [comments, setComments] = useState<Comment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [moderatingId, setModeratingId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [showAll, setShowAll] = useState(true);

  const fetchComments = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) {
        throw new Error('No authentication token found. Please log in again.');
      }

      const endpoint = showAll 
        ? '/api/comments/admin/comments/all'
        : '/api/comments/admin/comments/pending';

      const response = await fetch(endpoint, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setComments(data || []);
    } catch (error: any) {
      console.error('Error fetching comments:', error);
      toast.error(`Failed to fetch comments: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchComments();
  }, [showAll]);

  const handleModerate = async (commentId: number, action: 'approve' | 'reject') => {
    setModeratingId(commentId);
    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) {
        throw new Error('No authentication token found. Please log in again.');
      }

      const response = await fetch(`/api/comments/admin/comments/${commentId}/moderate?action=${action}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      toast.success(`Comment ${action}d successfully!`);
      await fetchComments();
    } catch (error: any) {
      console.error(`Error ${action}ing comment:`, error);
      toast.error(`Failed to ${action} comment: ${error.message}`);
    } finally {
      setModeratingId(null);
    }
  };

  const handleDelete = async (commentId: number) => {
    if (!confirm('Are you sure you want to permanently delete this comment? This action cannot be undone.')) {
      return;
    }

    setDeletingId(commentId);
    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) {
        throw new Error('No authentication token found. Please log in again.');
      }

      const response = await fetch(`/api/comments/admin/comments/${commentId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch (e) {
          const errorText = await response.text().catch(() => '');
          console.error('Delete error response:', {
            status: response.status,
            statusText: response.statusText,
            errorText,
            url: response.url
          });
        }
        throw new Error(errorMessage);
      }

      const result = await response.json().catch(() => ({}));
      console.log('Comment deleted successfully:', result);

      // Remove comment from local state immediately for better UX
      setComments(prevComments => prevComments.filter(c => c.id !== commentId));
      
      toast.success('Comment deleted successfully!');
      
      // Refresh from server to ensure consistency
      await fetchComments();
    } catch (error: any) {
      console.error('Error deleting comment:', error);
      toast.error(`Failed to delete comment: ${error.message}`);
      // Refresh to get current state
      await fetchComments();
    } finally {
      setDeletingId(null);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const getStatusBadge = (status: string, flagCount: number) => {
    if (status === 'flagged') {
      return <Badge variant="destructive">Flagged ({flagCount} flags)</Badge>;
    }
    if (status === 'approved') {
      return <Badge variant="default">Approved</Badge>;
    }
    if (status === 'rejected') {
      return <Badge variant="secondary">Rejected</Badge>;
    }
    return <Badge variant="secondary">Pending</Badge>;
  };

  // Group comments by document_id
  const commentsByDocument = comments.reduce((acc, comment) => {
    const docId = comment.document_id;
    if (!acc[docId]) {
      acc[docId] = [];
    }
    acc[docId].push(comment);
    return acc;
  }, {} as Record<number, Comment[]>);

  return (
    <div className="min-h-screen flex bg-muted/40">
      <aside className="w-64 bg-background border-r border-border p-6 flex flex-col justify-between shadow-lg">
        <div>
          <div className="mb-8 text-center">
            <a href="/admin-dashboard-page" className="text-2xl font-bold text-primary font-serif">
              Admin Panel
            </a>
            <p className="text-sm text-muted-foreground">Dig Out the Dirt</p>
          </div>
        </div>
      </aside>

      <main className="flex-1 p-6 md:p-10 overflow-auto">
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <MessageSquare className="h-6 w-6" />
                  Comment Management
                </CardTitle>
                <CardDescription>
                  Manage all comments. Comments are grouped by document.
                </CardDescription>
              </div>
              <div className="flex gap-2">
                <Button
                  variant={showAll ? "default" : "outline"}
                  size="sm"
                  onClick={() => setShowAll(true)}
                >
                  All Comments
                </Button>
                <Button
                  variant={!showAll ? "default" : "outline"}
                  size="sm"
                  onClick={() => setShowAll(false)}
                >
                  Pending Only
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : comments.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <MessageSquare className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>No comments found.</p>
              </div>
            ) : (
              <div className="space-y-6">
                {Object.entries(commentsByDocument).map(([docId, docComments]) => (
                  <div key={docId} className="space-y-4">
                    <div className="flex items-center gap-2 pb-2 border-b">
                      <h3 className="text-lg font-semibold">Document #{docId}</h3>
                      <Badge variant="outline">{docComments.length} comment{docComments.length !== 1 ? 's' : ''}</Badge>
                      <Button
                        variant="outline"
                        size="sm"
                        asChild
                        className="ml-auto"
                      >
                        <a href={`/document/${docId}`} target="_blank" rel="noopener noreferrer">
                          View Document
                        </a>
                      </Button>
                    </div>
                    {docComments.map((comment) => (
                      <Card key={comment.id} className="border-l-4 border-l-blue-500">
                        <CardContent className="pt-6">
                          <div className="flex items-start justify-between mb-4">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                {getStatusBadge(comment.status, comment.flag_count)}
                                <span className="text-sm text-muted-foreground">
                                  Comment #{comment.id.toString(36).slice(-4).toUpperCase()}
                                </span>
                                {comment.flag_count > 0 && (
                                  <div className="flex items-center gap-1 text-sm text-destructive">
                                    <Flag className="h-3 w-3" />
                                    {comment.flag_count} {comment.flag_count === 1 ? 'flag' : 'flags'}
                                  </div>
                                )}
                                {comment.parent_comment_id && (
                                  <span className="text-sm text-muted-foreground">
                                    (Reply to #{comment.parent_comment_id})
                                  </span>
                                )}
                              </div>
                              <p className="text-sm text-muted-foreground mb-3">
                                {formatDate(comment.created_at)}
                              </p>
                            </div>
                          </div>
                          
                          <div className="bg-muted/50 rounded-lg p-4 mb-4">
                            <p className="whitespace-pre-wrap text-sm">{comment.comment_text}</p>
                          </div>

                          <div className="flex gap-2">
                            {comment.status !== 'approved' && (
                              <Button
                                variant="default"
                                size="sm"
                                onClick={() => handleModerate(comment.id, 'approve')}
                                disabled={moderatingId === comment.id}
                              >
                                {moderatingId === comment.id ? (
                                  <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Processing...
                                  </>
                                ) : (
                                  <>
                                    <CheckCircle className="mr-2 h-4 w-4" />
                                    Approve
                                  </>
                                )}
                              </Button>
                            )}
                            {comment.status === 'pending' && (
                              <Button
                                variant="destructive"
                                size="sm"
                                onClick={() => handleModerate(comment.id, 'reject')}
                                disabled={moderatingId === comment.id}
                              >
                                {moderatingId === comment.id ? (
                                  <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Processing...
                                  </>
                                ) : (
                                  <>
                                    <XCircle className="mr-2 h-4 w-4" />
                                    Reject
                                  </>
                                )}
                              </Button>
                            )}
                            <Button
                              variant="destructive"
                              size="sm"
                              onClick={() => handleDelete(comment.id)}
                              disabled={deletingId === comment.id}
                            >
                              {deletingId === comment.id ? (
                                <>
                                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                  Deleting...
                                </>
                              ) : (
                                <>
                                  <Trash2 className="mr-2 h-4 w-4" />
                                  Delete
                                </>
                              )}
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}


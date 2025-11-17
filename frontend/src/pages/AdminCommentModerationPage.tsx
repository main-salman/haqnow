import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { MessageSquare, CheckCircle, XCircle, Loader2, Flag } from "lucide-react";
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

  const fetchPendingComments = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) {
        throw new Error('No authentication token found. Please log in again.');
      }

      const response = await fetch('/api/comments/admin/comments/pending', {
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
      console.error('Error fetching pending comments:', error);
      toast.error(`Failed to fetch comments: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPendingComments();
  }, []);

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
      await fetchPendingComments();
    } catch (error: any) {
      console.error(`Error ${action}ing comment:`, error);
      toast.error(`Failed to ${action} comment: ${error.message}`);
    } finally {
      setModeratingId(null);
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
    return <Badge variant="secondary">Pending</Badge>;
  };

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
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-6 w-6" />
              Comment Moderation Queue
            </CardTitle>
            <CardDescription>
              Review and moderate pending comments. Comments with 3+ flags are automatically hidden.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : comments.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <MessageSquare className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>No pending comments to moderate. All clear!</p>
              </div>
            ) : (
              <div className="space-y-4">
                {comments.map((comment) => (
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
                          </div>
                          <p className="text-sm mb-2">
                            <strong>Document ID:</strong> {comment.document_id}
                            {comment.parent_comment_id && (
                              <span className="text-muted-foreground ml-2">
                                (Reply to comment #{comment.parent_comment_id})
                              </span>
                            )}
                          </p>
                          <p className="text-sm text-muted-foreground mb-3">
                            {formatDate(comment.created_at)}
                          </p>
                        </div>
                      </div>
                      
                      <div className="bg-muted/50 rounded-lg p-4 mb-4">
                        <p className="whitespace-pre-wrap text-sm">{comment.comment_text}</p>
                      </div>

                      <div className="flex gap-2">
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
                        <Button
                          variant="outline"
                          size="sm"
                          asChild
                        >
                          <a href={`/document/${comment.document_id}`} target="_blank" rel="noopener noreferrer">
                            View Document
                          </a>
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}


import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { MessageSquare, Reply, Trash2, Flag, Loader2, ArrowUpDown } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface Comment {
  id: number;
  document_id: number;
  parent_comment_id: number | null;
  comment_text: string;
  status: string;
  flag_count: number;
  created_at: string;
  reply_count: number;
  replies?: Comment[];
}

interface DocumentCommentsProps {
  documentId: number;
}

export default function DocumentComments({ documentId }: DocumentCommentsProps) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newComment, setNewComment] = useState("");
  const [replyingTo, setReplyingTo] = useState<number | null>(null);
  const [replyText, setReplyText] = useState("");
  const [sortOrder, setSortOrder] = useState("most_replies");
  const [submitting, setSubmitting] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  useEffect(() => {
    fetchComments();
  }, [documentId, sortOrder]);

  const fetchComments = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`/api/comments/documents/${documentId}/comments?sort_order=${sortOrder}`, {
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'same-origin',
      });
      
      if (!response.ok) {
        const errorText = await response.text().catch(() => 'Unknown error');
        console.error('Failed to fetch comments:', {
          status: response.status,
          statusText: response.statusText,
          errorText,
          url: response.url
        });
        throw new Error(`Failed to fetch comments: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      setComments(data);
      setError(null);
    } catch (err: any) {
      console.error('Error fetching comments:', err);
      setError(err.message || 'Failed to load comments. Please try refreshing the page.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitComment = async (parentId: number | null = null) => {
    const text = parentId ? replyText : newComment;
    
    if (!text.trim() || text.length < 10) {
      setError("Comment must be at least 10 characters");
      return;
    }
    
    if (text.length > 5000) {
      setError("Comment must be less than 5000 characters");
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      
      const response = await fetch(`/api/comments/documents/${documentId}/comments`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
        },
        credentials: 'same-origin',
        body: JSON.stringify({
          comment_text: text,
          parent_comment_id: parentId
        }),
      });

      if (!response.ok) {
        let errorMessage = 'Failed to submit comment';
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch (e) {
          const errorText = await response.text().catch(() => '');
          console.error('Error response:', {
            status: response.status,
            statusText: response.statusText,
            errorText,
            url: response.url
          });
          errorMessage = `Failed to submit comment: ${response.status} ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }

      const result = await response.json();
      console.log('Comment submitted successfully:', result);

      // Clear form
      if (parentId) {
        setReplyText("");
        setReplyingTo(null);
      } else {
        setNewComment("");
      }

      // Add new comment to local state immediately for better UX
      if (result && result.id) {
        setComments(prevComments => {
          // If it's a reply, add it to the parent's replies
          if (parentId) {
            return prevComments.map(comment => {
              if (comment.id === parentId) {
                return {
                  ...comment,
                  replies: [...(comment.replies || []), result],
                  reply_count: (comment.reply_count || 0) + 1
                };
              }
              // Check if it's a reply to a reply
              if (comment.replies) {
                const updatedReplies = comment.replies.map(reply => {
                  if (reply.id === parentId) {
                    return {
                      ...reply,
                      replies: [...(reply.replies || []), result],
                      reply_count: (reply.reply_count || 0) + 1
                    };
                  }
                  return reply;
                });
                if (updatedReplies.some(r => r.id === result.parent_comment_id)) {
                  return { ...comment, replies: updatedReplies };
                }
              }
              return comment;
            });
          }
          // If it's a top-level comment, add it to the beginning
          return [result, ...prevComments];
        });
      }

      // Refresh comments from server to ensure consistency
      await fetchComments();
    } catch (err: any) {
      console.error('Error submitting comment:', err);
      setError(err.message || 'Failed to submit comment. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteComment = async (commentId: number) => {
    if (!confirm("Are you sure you want to delete this comment?")) {
      return;
    }

    // Prevent double-deletion
    if (deletingId === commentId) {
      return;
    }

    setDeletingId(commentId);
    
    // Helper function to remove comment from nested structure
    const removeCommentFromState = (commentsList: Comment[]): Comment[] => {
      return commentsList
        .filter(c => c.id !== commentId) // Remove the comment itself
        .map(comment => {
          // Remove from replies if it's a reply
          if (comment.replies && comment.replies.length > 0) {
            return {
              ...comment,
              replies: removeCommentFromState(comment.replies),
              reply_count: Math.max(0, (comment.reply_count || 0) - (comment.replies.some(r => r.id === commentId) ? 1 : 0))
            };
          }
          return comment;
        });
    };

    // Optimistically remove from UI immediately
    setComments(prevComments => removeCommentFromState(prevComments));

    try {
      const response = await fetch(`/api/comments/comments/${commentId}`, {
        method: 'DELETE',
        credentials: 'same-origin',
      });

      if (!response.ok) {
        // If 404, comment was already deleted - that's fine
        if (response.status === 404) {
          console.log(`Comment ${commentId} was already deleted`);
          // Already removed from UI, just refresh to ensure consistency
          await fetchComments();
          return;
        }
        
        let errorMessage = 'Failed to delete comment';
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch (e) {
          const errorText = await response.text().catch(() => '');
          console.error('Delete error response:', {
            status: response.status,
            statusText: response.statusText,
            errorText
          });
          errorMessage = `Failed to delete comment: ${response.status} ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }

      const result = await response.json().catch(() => ({}));
      console.log('Comment deleted successfully:', result);

      // Refresh from server to ensure consistency
      await fetchComments();
    } catch (err: any) {
      console.error('Error deleting comment:', err);
      
      // If it's a 404, comment was already deleted - refresh to sync
      if (err.message && err.message.includes('404')) {
        await fetchComments();
      } else {
        setError(err.message || 'Failed to delete comment');
        // Refresh to get current state
        await fetchComments();
      }
    } finally {
      setDeletingId(null);
    }
  };

  const handleFlagComment = async (commentId: number) => {
    try {
      const response = await fetch(`/api/comments/comments/${commentId}/flag`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Failed to flag comment');
      }

      alert("Comment flagged for moderation. Thank you for your report.");
      await fetchComments();
    } catch (err: any) {
      console.error('Error flagging comment:', err);
      setError(err.message || 'Failed to flag comment');
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "just now";
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    return date.toLocaleDateString();
  };

  const renderComment = (comment: Comment, depth: number = 0) => {
    const isDeleting = deletingId === comment.id;
    const isReplying = replyingTo === comment.id;

    return (
      <div key={comment.id} className={`${depth > 0 ? 'ml-8 mt-4 border-l-2 border-muted pl-4' : ''}`}>
        <div className="bg-muted/30 rounded-lg p-4 mb-3">
          <div className="flex items-start justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-muted-foreground">
                Anonymous User #{comment.id.toString(36).slice(-4).toUpperCase()}
              </span>
              <span className="text-xs text-muted-foreground">
                {formatDate(comment.created_at)}
              </span>
            </div>
            <div className="flex items-center gap-2">
              {comment.reply_count > 0 && (
                <span className="text-xs text-muted-foreground">
                  {comment.reply_count} {comment.reply_count === 1 ? 'reply' : 'replies'}
                </span>
              )}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setReplyingTo(isReplying ? null : comment.id)}
                className="h-7 px-2"
              >
                <Reply className="h-3 w-3 mr-1" />
                Reply
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleFlagComment(comment.id)}
                className="h-7 px-2"
              >
                <Flag className="h-3 w-3" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleDeleteComment(comment.id)}
                disabled={isDeleting}
                className="h-7 px-2 text-destructive"
              >
                {isDeleting ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <Trash2 className="h-3 w-3" />
                )}
              </Button>
            </div>
          </div>
          <p className="text-sm whitespace-pre-wrap">{comment.comment_text}</p>
        </div>

        {/* Reply form */}
        {isReplying && (
          <div className="mb-4 ml-4">
            <Textarea
              placeholder="Write a reply..."
              value={replyText}
              onChange={(e) => setReplyText(e.target.value)}
              rows={3}
              maxLength={5000}
              className="mb-2"
            />
            <div className="flex gap-2">
              <Button
                size="sm"
                onClick={() => handleSubmitComment(comment.id)}
                disabled={submitting || replyText.length < 10}
              >
                {submitting ? (
                  <>
                    <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  'Submit Reply'
                )}
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setReplyingTo(null);
                  setReplyText("");
                }}
              >
                Cancel
              </Button>
            </div>
          </div>
        )}

        {/* Render replies */}
        {comment.replies && comment.replies.length > 0 && (
          <div className="mt-2">
            {comment.replies.map((reply) => renderComment(reply, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div id="comments-section" className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-semibold flex items-center gap-2">
          <MessageSquare className="h-5 w-5" />
          Discussion ({comments.length} {comments.length === 1 ? 'comment' : 'comments'})
        </h3>
        <div className="flex items-center gap-2">
          <Select value={sortOrder} onValueChange={setSortOrder}>
            <SelectTrigger className="w-[180px]">
              <ArrowUpDown className="h-4 w-4 mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="most_replies">Most Replies</SelectItem>
              <SelectItem value="newest">Newest First</SelectItem>
              <SelectItem value="oldest">Oldest First</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {error && (
        <div className="bg-destructive/10 text-destructive p-3 rounded-lg text-sm">
          {error}
        </div>
      )}

      {/* New comment form */}
      <div className="bg-card border rounded-lg p-4">
        <Textarea
          placeholder="Share your thoughts about this document... (minimum 10 characters)"
          value={newComment}
          onChange={(e) => {
            setNewComment(e.target.value);
            setError(null);
          }}
          rows={4}
          maxLength={5000}
          className="mb-3"
        />
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">
            {newComment.length}/5000 characters
          </span>
          <Button
            onClick={() => handleSubmitComment()}
            disabled={submitting || newComment.length < 10}
          >
            {submitting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Submitting...
              </>
            ) : (
              <>
                <MessageSquare className="mr-2 h-4 w-4" />
                Post Comment
              </>
            )}
          </Button>
        </div>
      </div>

      {/* Comments list */}
      {comments.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          <MessageSquare className="h-12 w-12 mx-auto mb-3 opacity-50" />
          <p>No comments yet. Be the first to discuss this document!</p>
        </div>
      ) : (
        <div className="space-y-4">
          {comments.map((comment) => renderComment(comment))}
        </div>
      )}
    </div>
  );
}


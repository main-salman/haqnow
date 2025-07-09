import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { PlusCircle, Trash2, ShieldBan, Loader2 } from "lucide-react";
import { toast } from "sonner";

interface BannedTag {
  id: number;
  tag: string;
  reason?: string;
  banned_by: string;
  banned_at: string;
}

export default function AdminBannedTagsPage() {
  const [bannedTags, setBannedTags] = useState<BannedTag[]>([]);
  const [newTag, setNewTag] = useState("");
  const [newReason, setNewReason] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isAdding, setIsAdding] = useState(false);
  const [removingTagId, setRemovingTagId] = useState<number | null>(null);

  // Fetch banned tags from API
  const fetchBannedTags = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) {
        throw new Error('No authentication token found. Please log in again.');
      }

      const response = await fetch('/api/search/banned-tags', {
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
      setBannedTags(data.banned_tags || []);
    } catch (error: any) {
      console.error('Error fetching banned tags:', error);
      toast.error(`Failed to fetch banned tags: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchBannedTags();
  }, []);

  const handleAddBannedTag = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newTag.trim() === "") {
      toast.error("Tag cannot be empty.");
      return;
    }

    // Check if tag already exists (case-insensitive)
    if (bannedTags.some(tag => tag.tag.toLowerCase() === newTag.trim().toLowerCase())) {
      toast.error(`Tag "${newTag.trim()}" is already banned.`);
      setNewTag("");
      return;
    }

    setIsAdding(true);
    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) {
        throw new Error('No authentication token found. Please log in again.');
      }

      // Use URL search params to match backend expectations
      const banUrl = new URL('/api/search/ban-tag', window.location.origin);
      banUrl.searchParams.append('tag', newTag.trim());
      if (newReason.trim()) {
        banUrl.searchParams.append('reason', newReason.trim());
      }

      const response = await fetch(banUrl.toString(), {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      toast.success(`Tag "${newTag.trim()}" banned successfully!`);
      setNewTag("");
      setNewReason("");
      
      // Refresh the list
      fetchBannedTags();
    } catch (error: any) {
      console.error('Error banning tag:', error);
      toast.error(`Failed to ban tag: ${error.message}`);
    } finally {
      setIsAdding(false);
    }
  };

  const handleRemoveBannedTag = async (tagId: number) => {
    const tagToRemove = bannedTags.find(tag => tag.id === tagId);
    if (!tagToRemove) return;

    if (!confirm(`Are you sure you want to unban the tag "${tagToRemove.tag}"?`)) {
      return;
    }

    setRemovingTagId(tagId);
    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) {
        throw new Error('No authentication token found. Please log in again.');
      }

      const response = await fetch(`/api/search/unban-tag/${tagId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      toast.success(`Tag "${tagToRemove.tag}" unbanned successfully!`);
      
      // Refresh the list
      fetchBannedTags();
    } catch (error: any) {
      console.error('Error unbanning tag:', error);
      toast.error(`Failed to unban tag: ${error.message}`);
    } finally {
      setRemovingTagId(null);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <p className="ml-2 text-muted-foreground">Loading banned tags...</p>
      </div>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-2xl font-serif flex items-center">
                <ShieldBan className="mr-3 h-6 w-6 text-destructive" /> Manage Banned Tags
            </CardTitle>
            <CardDescription>
              Add or remove tags that should be prevented from being used or displayed on the platform.
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        <form onSubmit={handleAddBannedTag} className="space-y-4 pb-4 border-b">
          <div className="flex items-center space-x-2">
            <Input
              type="text"
              placeholder="Enter a tag to ban..."
              value={newTag}
              onChange={(e) => setNewTag(e.target.value)}
              className="flex-grow"
              aria-label="New tag to ban"
              disabled={isAdding}
            />
            <Button type="submit" disabled={isAdding}>
              {isAdding ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <PlusCircle className="mr-2 h-4 w-4" />}
              Ban Tag
            </Button>
          </div>
          <Input
            type="text"
            placeholder="Reason for banning (optional)..."
            value={newReason}
            onChange={(e) => setNewReason(e.target.value)}
            className="w-full"
            aria-label="Reason for banning"
            disabled={isAdding}
          />
        </form>

        {bannedTags.length > 0 ? (
          <div className="border rounded-lg overflow-hidden">
            <Table>
              <TableHeader className="bg-muted/50">
                <TableRow>
                  <TableHead className="w-[40%]">Tag Name</TableHead>
                  <TableHead className="w-[30%]">Reason</TableHead>
                  <TableHead>Date Banned</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {bannedTags.map((tag) => (
                  <TableRow key={tag.id}>
                    <TableCell className="font-medium">{tag.tag}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {tag.reason || "No reason provided"}
                    </TableCell>
                    <TableCell>{new Date(tag.banned_at).toLocaleDateString()}</TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-destructive hover:text-destructive-foreground hover:bg-destructive/90"
                        onClick={() => handleRemoveBannedTag(tag.id)}
                        aria-label={`Unban tag ${tag.tag}`}
                        disabled={removingTagId === tag.id}
                      >
                        {removingTagId === tag.id ? (
                          <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                        ) : (
                          <Trash2 className="h-4 w-4 mr-1" />
                        )}
                        Unban
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        ) : (
          <p className="text-center text-muted-foreground py-6">
            No tags are currently banned.
          </p>
        )}
      </CardContent>
    </Card>
  );
}

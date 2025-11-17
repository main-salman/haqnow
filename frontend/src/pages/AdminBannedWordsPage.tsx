import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { PlusCircle, Trash2, ShieldBan, Loader2 } from "lucide-react";
import { toast } from "sonner";

interface BannedWord {
  id: number;
  word: string;
  reason?: string;
  banned_by: string;
  created_at: string;
}

export default function AdminBannedWordsPage() {
  const [bannedWords, setBannedWords] = useState<BannedWord[]>([]);
  const [newWord, setNewWord] = useState("");
  const [newReason, setNewReason] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isAdding, setIsAdding] = useState(false);
  const [removingWordId, setRemovingWordId] = useState<number | null>(null);

  const fetchBannedWords = async () => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) {
        throw new Error('No authentication token found. Please log in again.');
      }

      const response = await fetch('/api/comments/admin/banned-words', {
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
      setBannedWords(data || []);
    } catch (error: any) {
      console.error('Error fetching banned words:', error);
      toast.error(`Failed to fetch banned words: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchBannedWords();
  }, []);

  const handleAddBannedWord = async (e: React.FormEvent) => {
    e.preventDefault();
    if (newWord.trim() === "") {
      toast.error("Word cannot be empty.");
      return;
    }

    // Check if word already exists (case-insensitive)
    if (bannedWords.some(word => word.word.toLowerCase() === newWord.trim().toLowerCase())) {
      toast.error(`Word "${newWord.trim()}" is already banned.`);
      setNewWord("");
      return;
    }

    setIsAdding(true);
    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) {
        throw new Error('No authentication token found. Please log in again.');
      }

      const banUrl = new URL('/api/comments/admin/banned-words', window.location.origin);
      banUrl.searchParams.append('word', newWord.trim());
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

      toast.success(`Word "${newWord.trim()}" banned successfully!`);
      setNewWord("");
      setNewReason("");
      await fetchBannedWords();
    } catch (error: any) {
      console.error('Error adding banned word:', error);
      toast.error(`Failed to ban word: ${error.message}`);
    } finally {
      setIsAdding(false);
    }
  };

  const handleRemoveBannedWord = async (wordId: number) => {
    if (!confirm("Are you sure you want to remove this banned word?")) {
      return;
    }

    setRemovingWordId(wordId);
    try {
      const token = localStorage.getItem('jwt_token');
      if (!token) {
        throw new Error('No authentication token found. Please log in again.');
      }

      const response = await fetch(`/api/comments/admin/banned-words/${wordId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      toast.success("Banned word removed successfully!");
      await fetchBannedWords();
    } catch (error: any) {
      console.error('Error removing banned word:', error);
      toast.error(`Failed to remove banned word: ${error.message}`);
    } finally {
      setRemovingWordId(null);
    }
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
              <ShieldBan className="h-6 w-6" />
              Manage Banned Words
            </CardTitle>
            <CardDescription>
              Add or remove words/phrases that will be automatically filtered from comments and annotations.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {/* Add Banned Word Form */}
            <form onSubmit={handleAddBannedWord} className="mb-6 p-4 bg-muted/50 rounded-lg">
              <div className="flex gap-4 items-end">
                <div className="flex-1">
                  <label htmlFor="newWord" className="text-sm font-medium mb-2 block">
                    Word or Phrase
                  </label>
                  <Input
                    id="newWord"
                    type="text"
                    value={newWord}
                    onChange={(e) => setNewWord(e.target.value)}
                    placeholder="Enter word or phrase to ban"
                    className="mb-2"
                  />
                </div>
                <div className="flex-1">
                  <label htmlFor="newReason" className="text-sm font-medium mb-2 block">
                    Reason (optional)
                  </label>
                  <Input
                    id="newReason"
                    type="text"
                    value={newReason}
                    onChange={(e) => setNewReason(e.target.value)}
                    placeholder="Reason for banning"
                  />
                </div>
                <Button type="submit" disabled={isAdding || newWord.trim() === ""}>
                  {isAdding ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Adding...
                    </>
                  ) : (
                    <>
                      <PlusCircle className="mr-2 h-4 w-4" />
                      Add Banned Word
                    </>
                  )}
                </Button>
              </div>
            </form>

            {/* Banned Words Table */}
            {isLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : bannedWords.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <ShieldBan className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>No banned words yet. Add words to filter spam and inappropriate content.</p>
              </div>
            ) : (
              <div className="border rounded-lg overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Word/Phrase</TableHead>
                      <TableHead>Reason</TableHead>
                      <TableHead>Banned By</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {bannedWords.map((word) => (
                      <TableRow key={word.id}>
                        <TableCell className="font-medium">{word.word}</TableCell>
                        <TableCell className="text-muted-foreground">
                          {word.reason || "—"}
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {word.banned_by}
                        </TableCell>
                        <TableCell className="text-muted-foreground">
                          {new Date(word.created_at).toLocaleDateString()}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRemoveBannedWord(word.id)}
                            disabled={removingWordId === word.id}
                            className="text-destructive hover:text-destructive"
                          >
                            {removingWordId === word.id ? (
                              <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                              <Trash2 className="h-4 w-4" />
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
      </main>
    </div>
  );
}


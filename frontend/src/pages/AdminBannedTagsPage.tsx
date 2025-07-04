import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { PlusCircle, Trash2, ShieldBan } from "lucide-react";

// Mock data - replace with API calls later
const initialBannedTags = [
  { id: "tag1", name: "spam", dateAdded: "2024-01-01" },
  { id: "tag2", name: "irrelevant", dateAdded: "2024-01-15" },
  { id: "tag3", name: "offensive-content", dateAdded: "2024-02-01" },
  { id: "tag4", name: "misinformation", dateAdded: "2024-02-20" },
];

export default function AdminBannedTagsPage() {
  const [bannedTags, setBannedTags] = useState(initialBannedTags);
  const [newTag, setNewTag] = useState("");

  const handleAddBannedTag = (e: React.FormEvent) => {
    e.preventDefault();
    if (newTag.trim() === "") return;
    // Check if tag already exists (case-insensitive for robustness)
    if (bannedTags.some(tag => tag.name.toLowerCase() === newTag.trim().toLowerCase())) {
      alert(`Tag "${newTag.trim()}" is already banned.`);
      setNewTag("");
      return;
    }

    const newBannedTag = {
      id: `tag${Date.now()}`,
      name: newTag.trim(),
      dateAdded: new Date().toISOString().split('T')[0],
    };
    setBannedTags([...bannedTags, newBannedTag]);
    setNewTag("");
    console.log(`Tag "${newBannedTag.name}" banned (mock).`);
    // In a real app, save to DB
  };

  const handleRemoveBannedTag = (tagId: string) => {
    const tagToRemove = bannedTags.find(tag => tag.id === tagId);
    if(tagToRemove && confirm(`Are you sure you want to unban the tag "${tagToRemove.name}"?`)){
      setBannedTags(bannedTags.filter((tag) => tag.id !== tagId));
      console.log(`Tag ID "${tagId}" unbanned (mock).`);
      // In a real app, remove from DB
    }
  };

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
        <form onSubmit={handleAddBannedTag} className="flex items-center space-x-2 pb-4 border-b">
          <Input
            type="text"
            placeholder="Enter a tag to ban..."
            value={newTag}
            onChange={(e) => setNewTag(e.target.value)}
            className="flex-grow"
            aria-label="New tag to ban"
          />
          <Button type="submit">
            <PlusCircle className="mr-2 h-4 w-4" /> Ban Tag
          </Button>
        </form>

        {bannedTags.length > 0 ? (
          <div className="border rounded-lg overflow-hidden">
            <Table>
              <TableHeader className="bg-muted/50">
                <TableRow>
                  <TableHead className="w-[60%]">Tag Name</TableHead>
                  <TableHead>Date Banned</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {bannedTags.map((tag) => (
                  <TableRow key={tag.id}>
                    <TableCell className="font-medium">{tag.name}</TableCell>
                    <TableCell>{new Date(tag.dateAdded).toLocaleDateString()}</TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-destructive hover:text-destructive-foreground hover:bg-destructive/90"
                        onClick={() => handleRemoveBannedTag(tag.id)}
                        aria-label={`Unban tag ${tag.name}`}
                      >
                        <Trash2 className="h-4 w-4 mr-1" /> Unban
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

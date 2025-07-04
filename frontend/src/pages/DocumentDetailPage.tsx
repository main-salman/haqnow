import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Download, Tag, PlusCircle, ArrowLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";

// Mock data for the document - replace with actual data fetching later
const mockDocument = {
  id: "doc123",
  title: "FOIA Request Results: UFO Sightings Q4 2023",
  description:
    "This document contains a summary of UFO sighting reports collected by the National UFO Reporting Center in the fourth quarter of 2023, released under a Freedom of Information Act request. It includes dates, locations, and brief descriptions of each reported incident.",
  country: "United States",
  stateProvince: "Federal",
  uploadDate: "2024-01-15",
  pdfUrl: "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf", // Placeholder PDF
  tags: ["UFO", "Q4 2023", "Sightings", "Federal", "NUFORC"],
};

interface DocumentTag {
  id: string;
  name: string;
}

export default function DocumentDetailPage() {
  const navigate = useNavigate();
  const [document, setDocument] = useState(mockDocument);
  const [newTag, setNewTag] = useState("");

  const handleAddTag = () => {
    if (newTag.trim() !== "" && !document.tags.includes(newTag.trim())) {
      // In a real app, this would call an API to add the tag
      setDocument((prevDoc) => ({
        ...prevDoc,
        tags: [...prevDoc.tags, newTag.trim()],
      }));
      setNewTag("");
      console.log(`Tag "${newTag.trim()}" added (mock).`);
    } else {
      console.log("Tag already exists or is empty.");
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground p-4 md:p-8">
      <div className="container mx-auto max-w-5xl space-y-8">
        <div>
          <Button
            variant="outline"
            onClick={() => navigate(-1)} // Or navigate to a specific listing page
            className="mb-6"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Search
          </Button>
        </div>

        {/* Document Metadata Section */}
        <section className="bg-card p-6 rounded-lg shadow">
          <h1 className="text-3xl font-bold mb-2 text-primary font-serif">
            {document.title}
          </h1>
          <div className="flex flex-wrap gap-x-4 gap-y-2 text-sm text-muted-foreground mb-4">
            <span>Country: {document.country}</span>
            {document.stateProvince && (
              <span>State/Province: {document.stateProvince}</span>
            )}
            <span>Uploaded: {new Date(document.uploadDate).toLocaleDateString()}</span>
          </div>
          <p className="text-foreground/80 mb-6 leading-relaxed">
            {document.description}
          </p>
          <Button asChild>
            <a href={document.pdfUrl} download target="_blank" rel="noopener noreferrer">
              <Download className="mr-2 h-4 w-4" />
              Download PDF
            </a>
          </Button>
        </section>

        {/* PDF Preview Section */}
        <section className="bg-card p-6 rounded-lg shadow">
          <h2 className="text-2xl font-semibold mb-4 font-serif">Document Preview</h2>
          <div className="aspect-[8.5/11] border border-border rounded overflow-hidden">
            <iframe
              src={document.pdfUrl}
              title={document.title}
              width="100%"
              height="100%"
              className="w-full h-full"
              // sandbox="allow-scripts allow-same-origin" // Consider security implications
            />
          </div>
        </section>

        {/* Tags Section */}
        <section className="bg-card p-6 rounded-lg shadow">
          <h2 className="text-2xl font-semibold mb-4 font-serif">Tags</h2>
          <div className="flex flex-wrap gap-2 mb-4">
            {document.tags.map((tag, index) => (
              <Badge key={index} variant="secondary" className="text-sm">
                {tag}
              </Badge>
            ))}
          </div>
          <div className="flex items-center space-x-2">
            <Input
              type="text"
              value={newTag}
              onChange={(e) => setNewTag(e.target.value)}
              placeholder="Add a new tag"
              className="flex-grow"
              aria-label="Add new tag"
            />
            <Button onClick={handleAddTag} variant="outline">
              <PlusCircle className="mr-2 h-4 w-4" />
              Add Tag
            </Button>
          </div>
        </section>
      </div>
    </div>
  );
}

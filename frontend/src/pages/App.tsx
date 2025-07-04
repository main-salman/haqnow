import React, { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Search } from "lucide-react";
import { useNavigate, Link } from "react-router-dom"; // Added Link
import CountryDocStatsList from "components/CountryDocStatsList"; // MYA-21: Import new component

export default function App() {
  const navigate = useNavigate(); // Added for navigation
  const [searchTerm, setSearchTerm] = useState(""); // Added for search input

  const handleSearch = () => {
    if (searchTerm.trim() !== "") {
      navigate(`/search-page?tags=${encodeURIComponent(searchTerm.trim())}`);
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-background text-foreground">
      <header className="py-6 px-4 md:px-8 border-b border-border">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-3xl font-bold text-primary">Dig Out the Dirt</h1>
          <nav className="space-x-4">
            <Button variant="ghost" asChild>
              <Link to="/upload-document-page">Upload Document</Link>
            </Button>
            <Button variant="outline" asChild>
              <Link to="/admin-login-page">Admin Login</Link>
            </Button>
          </nav>
        </div>
      </header>

      <main className="flex-grow container mx-auto px-4 py-8 md:py-12">
        <div className="space-y-10 md:space-y-16">
          <section className="text-center space-y-4">
            <h2 className="text-2xl md:text-3xl font-semibold tracking-tight">
              Access Freedom of Information Documents Worldwide
            </h2>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              FOIArchive is a platform dedicated to collecting, organizing, and
              providing access to Freedom of Information (FOI/FOIA) documents
              from around the globe. Explore, search, and contribute to a
              growing repository of public knowledge.
            </p>
          </section>

          <section className="max-w-xl mx-auto">
            <div className="flex w-full items-center space-x-2">
              <Input
                type="search"
                placeholder="Search documents by keyword, country, tag..."
                className="flex-grow"
                aria-label="Search documents"
                value={searchTerm} // Added value
                onChange={(e) => setSearchTerm(e.target.value)} // Added onChange
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()} // Added onKeyPress for Enter
              />
              <Button type="button" aria-label="Submit search" onClick={handleSearch}> {/* Changed to type="button" and added onClick */}
                <Search className="h-4 w-4 mr-2" />
                Search
              </Button>
            </div>
          </section>

          <section className="text-center space-y-4">
            <h3 className="text-xl md:text-2xl font-semibold tracking-tight">
              Global Document Distribution
            </h3>
            <div
              className="bg-muted/40 border border-dashed border-border rounded-lg min-h-[300px] md:min-h-[400px] flex items-center justify-center"
              aria-label="World map placeholder"
            >
              <p className="text-muted-foreground">
                Interactive World Map Coming Soon
              </p>
            </div>
            {/* MYA-21: Added CountryDocStatsList below map placeholder */}
            <div className="mt-8 md:mt-12">
              <CountryDocStatsList />
            </div>
          </section>
        </div>
      </main>

      <footer className="py-6 px-4 md:px-8 border-t border-border text-center">
        <p className="text-sm text-muted-foreground">
          &copy; {new Date().getFullYear()} FOIArchive. All rights reserved.
        </p>
      </footer>
    </div>
  );
}

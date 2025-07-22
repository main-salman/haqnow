import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { 
  ArrowLeft, 
  Save, 
  RefreshCw, 
  Languages, 
  Copy, 
  Check,
  AlertCircle,
  Loader2,
  Download,
  Upload
} from "lucide-react";
import { toast } from "sonner";
import { supportedLanguages } from "../i18n";

interface Translation {
  id: number;
  key: string;
  language: string;
  value: string;
  section: string;
  updated_by: string;
  created_at: string;
  updated_at: string;
}

const sections = [
  'navigation',
  'homepage', 
  'search',
  'upload',
  'privacy',
  'disclaimer',
  'general'
];

export default function AdminTranslationsPage() {
  const navigate = useNavigate();
  const { t, i18n } = useTranslation();
  
  const [translations, setTranslations] = useState<Translation[]>([]);
  const [selectedLanguage, setSelectedLanguage] = useState<string>('en');
  const [selectedSection, setSelectedSection] = useState<string>('navigation');
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [editedTranslations, setEditedTranslations] = useState<Record<string, string>>({});
  const [searchTerm, setSearchTerm] = useState('');

  // Fetch translations
  const fetchTranslations = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/translations/admin/all', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('🔍 Fetched translations:', data.length);
        console.log('🔍 Disclaimer translations:', data.filter(t => t.section === 'disclaimer').length);
        setTranslations(data);
      } else {
        toast.error('Failed to fetch translations');
      }
    } catch (error) {
      toast.error('Error fetching translations');
      console.error('Translation fetch error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Bulk update translations for a section
  const saveTranslations = async () => {
    if (Object.keys(editedTranslations).length === 0) {
      toast.info('No changes to save');
      return;
    }

    setIsSaving(true);
    try {
      const response = await fetch(`/api/translations/admin/bulk-update/${selectedLanguage}/${selectedSection}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
        },
        body: JSON.stringify({
          translations: editedTranslations
        })
      });

      if (response.ok) {
        const result = await response.json();
        toast.success(`Saved ${result.updated + result.created} translations`);
        setEditedTranslations({});
        fetchTranslations();
        
        // Refresh translations in the app
        if (selectedLanguage === i18n.language) {
          window.location.reload();
        }
      } else {
        toast.error('Failed to save translations');
      }
    } catch (error) {
      toast.error('Error saving translations');
      console.error('Translation save error:', error);
    } finally {
      setIsSaving(false);
    }
  };

  // Export translations as JSON
  const exportTranslations = () => {
    const filtered = translations.filter(t => 
      t.language === selectedLanguage && 
      (selectedSection === 'all' || t.section === selectedSection)
    );
    
    const exportData = filtered.reduce((acc, t) => {
      if (!acc[t.section]) acc[t.section] = {};
      acc[t.section][t.key] = t.value;
      return acc;
    }, {} as Record<string, Record<string, string>>);

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `translations-${selectedLanguage}-${selectedSection}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    toast.success('Translations exported');
  };

  // Copy section as JSON for easy editing
  const copyAsJSON = () => {
    const filtered = translations.filter(t => 
      t.language === selectedLanguage && t.section === selectedSection
    );
    
    const jsonData = filtered.reduce((acc, t) => {
      acc[t.key] = editedTranslations[t.key] || t.value;
      return acc;
    }, {} as Record<string, string>);

    navigator.clipboard.writeText(JSON.stringify(jsonData, null, 2))
      .then(() => toast.success('Copied to clipboard'))
      .catch(() => toast.error('Failed to copy'));
  };

  // Handle manual key editing
  const handleTranslationChange = (key: string, value: string) => {
    setEditedTranslations(prev => ({
      ...prev,
      [key]: value
    }));
  };

  // Reset edited translations
  const resetChanges = () => {
    setEditedTranslations({});
    toast.info('Changes reset');
  };

  useEffect(() => {
    fetchTranslations();
  }, []);

  // Filter translations based on current selection and search
  const filteredTranslations = translations.filter(t => {
    const matchesLanguage = t.language === selectedLanguage;
    const matchesSection = selectedSection === 'all' || t.section === selectedSection;
    const matchesSearch = !searchTerm || 
      t.key.toLowerCase().includes(searchTerm.toLowerCase()) || 
      t.value.toLowerCase().includes(searchTerm.toLowerCase());
    
    return matchesLanguage && matchesSection && matchesSearch;
  });

  // Debug logging for disclaimer section
  if (selectedSection === 'disclaimer' && selectedLanguage === 'en') {
    console.log('🔍 Filtering disclaimer translations:');
    console.log('  - Total translations loaded:', translations.length);
    console.log('  - Selected language:', selectedLanguage);
    console.log('  - Selected section:', selectedSection);
    console.log('  - Search term:', searchTerm);
    console.log('  - Filtered results:', filteredTranslations.length);
    console.log('  - Disclaimer translations available:', translations.filter(t => t.section === 'disclaimer' && t.language === 'en').length);
  }

  const hasChanges = Object.keys(editedTranslations).length > 0;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="py-6 px-4 md:px-8 border-b border-border">
        <div className="container mx-auto">
          <Button variant="outline" onClick={() => navigate("/admin-dashboard-page")} className="mb-4">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Admin Dashboard
          </Button>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold font-serif flex items-center space-x-2">
                <Languages className="h-8 w-8" />
                <span>Translation Management</span>
              </h1>
              <p className="text-muted-foreground mt-2">
                Manage website translations across all supported languages
              </p>
            </div>
            <div className="flex items-center space-x-2">
              {hasChanges && (
                <Badge variant="secondary" className="animate-pulse">
                  {Object.keys(editedTranslations).length} unsaved changes
                </Badge>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Controls */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Translation Controls</CardTitle>
            <CardDescription>
              Select language and section to manage translations
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Language</label>
                <Select value={selectedLanguage} onValueChange={setSelectedLanguage}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(supportedLanguages).map(([code, name]) => (
                      <SelectItem key={code} value={code}>
                        {name} ({code.toUpperCase()})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Section</label>
                <Select value={selectedSection} onValueChange={setSelectedSection}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Sections</SelectItem>
                    {sections.map(section => (
                      <SelectItem key={section} value={section}>
                        {section.charAt(0).toUpperCase() + section.slice(1)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Search</label>
                <Input
                  placeholder="Search keys or values..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Actions</label>
                <div className="flex space-x-2">
                  <Button variant="outline" size="sm" onClick={fetchTranslations} disabled={isLoading}>
                    <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                  </Button>
                  <Button variant="outline" size="sm" onClick={exportTranslations}>
                    <Download className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Button onClick={saveTranslations} disabled={!hasChanges || isSaving}>
                {isSaving ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Save className="mr-2 h-4 w-4" />
                )}
                Save Changes
              </Button>
              <Button variant="outline" onClick={resetChanges} disabled={!hasChanges}>
                Reset Changes
              </Button>
              <Button variant="outline" onClick={copyAsJSON}>
                <Copy className="mr-2 h-4 w-4" />
                Copy as JSON
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Translation Editor */}
        <Card className="h-auto">
          <CardHeader>
            <CardTitle>
              Translations for {supportedLanguages[selectedLanguage as keyof typeof supportedLanguages]} 
              {selectedSection !== 'all' && ` - ${selectedSection.charAt(0).toUpperCase() + selectedSection.slice(1)}`}
            </CardTitle>
            <CardDescription>
              Click on any value to edit inline, or copy the JSON structure to edit externally
            </CardDescription>
          </CardHeader>
          <CardContent className="h-auto max-h-none overflow-visible">
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin" />
                <span className="ml-2">Loading translations...</span>
              </div>
            ) : filteredTranslations.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <Languages className="h-16 w-16 mx-auto mb-4 opacity-50" />
                <p className="text-lg font-semibold">No translations found</p>
                <p>Try adjusting your filters or create new translations</p>
              </div>
            ) : (
              <div className="space-y-4 max-h-none overflow-visible">
                {(() => {
                  console.log(`🔍 Rendering ${filteredTranslations.length} translation elements`);
                  return filteredTranslations.map((translation) => (
                  <div key={translation.id} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <Badge variant="outline">{translation.section}</Badge>
                        <code className="text-sm bg-muted px-2 py-1 rounded">
                          {translation.key}
                        </code>
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Updated: {new Date(translation.updated_at).toLocaleDateString()}
                      </div>
                    </div>
                    <Textarea
                      value={editedTranslations[translation.key] ?? translation.value}
                      onChange={(e) => handleTranslationChange(translation.key, e.target.value)}
                      className={`min-h-[60px] ${
                        editedTranslations[translation.key] ? 'border-yellow-500 bg-yellow-50 dark:bg-yellow-950/20' : ''
                      }`}
                      placeholder="Enter translation..."
                    />
                    {editedTranslations[translation.key] && (
                      <div className="mt-2 flex items-center space-x-2 text-sm text-yellow-700 dark:text-yellow-300">
                        <AlertCircle className="h-4 w-4" />
                        <span>Modified</span>
                      </div>
                    )}
                  </div>
                  ));
                })()}
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
} 
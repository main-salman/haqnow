import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '@/components/ui/card';
import { Clock, FileText } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface RecentDocument {
  id: number;
  title: string;
  country: string;
  state: string;
  approved_at: string;
  created_at: string;
}

export default function RecentlySharedDocuments() {
  const [documents, setDocuments] = useState<RecentDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { t } = useTranslation();

  useEffect(() => {
    fetchRecentlySharedDocuments();
  }, []);

  const fetchRecentlySharedDocuments = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/search/recently-shared?limit=10');
      
      if (!response.ok) {
        throw new Error('Failed to fetch recently shared documents');
      }

      const data = await response.json();
      setDocuments(data.documents || []);
      setError(null);
    } catch (err) {
      console.error('Error fetching recently shared documents:', err);
      setError('Unable to load recently shared documents');
    } finally {
      setLoading(false);
    }
  };

  const handleDocumentClick = (documentId: number) => {
    navigate(`/document/${documentId}`);
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffTime = Math.abs(now.getTime() - date.getTime());
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      
      if (diffDays === 0) {
        return 'Today';
      } else if (diffDays === 1) {
        return 'Yesterday';
      } else if (diffDays < 7) {
        return `${diffDays} days ago`;
      } else if (diffDays < 30) {
        const weeks = Math.floor(diffDays / 7);
        return `${weeks} ${weeks === 1 ? 'week' : 'weeks'} ago`;
      } else {
        return date.toLocaleDateString();
      }
    } catch (e) {
      return dateString;
    }
  };

  if (loading) {
    return (
      <div className="w-full py-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
          <p className="text-slate-600 mt-2">Loading recently shared documents...</p>
        </div>
      </div>
    );
  }

  if (error || documents.length === 0) {
    return null; // Don't show section if no documents or error
  }

  return (
    <div className="w-full py-8 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="mb-6">
          <h2 className="text-2xl md:text-3xl font-semibold tracking-tight text-center mb-2">
            {t('homepage.recentlySharedTitle', 'Recently Shared Documents')}
          </h2>
          <p className="text-slate-600 text-center">
            {t('homepage.recentlySharedDescription', 'Latest corruption documents added to the platform')}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {documents.map((doc, index) => (
            <Card
              key={doc.id}
              className="p-4 hover:shadow-lg transition-shadow cursor-pointer border-l-4 border-l-blue-500"
              onClick={() => handleDocumentClick(doc.id)}
            >
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-semibold">
                  {index + 1}
                </div>
                
                <div className="flex-grow min-w-0">
                  <h3 className="font-semibold text-slate-900 mb-1 line-clamp-2">
                    {doc.title}
                  </h3>
                  
                  <div className="flex flex-wrap items-center gap-3 text-sm text-slate-600">
                    <span className="flex items-center gap-1">
                      <FileText className="h-4 w-4" />
                      {doc.country}
                      {doc.state && `, ${doc.state}`}
                    </span>
                    
                    <span className="flex items-center gap-1 text-blue-600 font-medium">
                      <Clock className="h-4 w-4" />
                      {formatDate(doc.approved_at || doc.created_at)}
                    </span>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}




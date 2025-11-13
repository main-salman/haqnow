import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from './ui/card';
import { Eye, FileText } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface TopViewedDocument {
  id: number;
  title: string;
  country: string;
  state: string;
  view_count: number;
  created_at: string;
}

export default function TopViewedDocuments() {
  const [documents, setDocuments] = useState<TopViewedDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
  const { t } = useTranslation();

  useEffect(() => {
    fetchTopViewedDocuments();
  }, []);

  const fetchTopViewedDocuments = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/search/top-viewed?limit=10');
      
      if (!response.ok) {
        throw new Error('Failed to fetch top viewed documents');
      }

      const data = await response.json();
      setDocuments(data.documents || []);
      setError(null);
    } catch (err) {
      console.error('Error fetching top viewed documents:', err);
      setError('Unable to load top viewed documents');
    } finally {
      setLoading(false);
    }
  };

  const handleDocumentClick = (documentId: number) => {
    navigate(`/document/${documentId}`);
  };

  if (loading) {
    return (
      <div className="w-full py-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500 mx-auto"></div>
          <p className="text-slate-600 mt-2">Loading top viewed documents...</p>
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
            {t('homepage.topViewedTitle', 'Most Viewed Documents')}
          </h2>
          <p className="text-slate-600 text-center">
            {t('homepage.topViewedDescription', 'Discover the most accessed corruption documents')}
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {documents.map((doc, index) => (
            <Card
              key={doc.id}
              className="p-4 hover:shadow-lg transition-shadow cursor-pointer border-l-4 border-l-emerald-500"
              onClick={() => handleDocumentClick(doc.id)}
            >
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-700 font-semibold">
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
                    
                    <span className="flex items-center gap-1 text-emerald-600 font-medium">
                      <Eye className="h-4 w-4" />
                      {doc.view_count.toLocaleString()} {t('homepage.views', 'views')}
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


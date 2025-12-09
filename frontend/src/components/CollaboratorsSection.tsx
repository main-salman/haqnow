import { useEffect, useState } from 'react';
import { ExternalLink } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface Collaborator {
  id: number;
  name: string;
  description: string;
  logo_url: string;
  website_url: string;
  priority: number;
}

export default function CollaboratorsSection() {
  const [collaborators, setCollaborators] = useState<Collaborator[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { t } = useTranslation();

  useEffect(() => {
    fetchCollaborators();
  }, []);

  const fetchCollaborators = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/collaborators');
      
      if (!response.ok) {
        throw new Error('Failed to fetch collaborators');
      }

      const data = await response.json();
      setCollaborators(data.collaborators || []);
      setError(null);
    } catch (err) {
      console.error('Error fetching collaborators:', err);
      setError('Unable to load collaborators');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="w-full py-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500 mx-auto"></div>
          <p className="text-slate-600 mt-2">Loading collaborators...</p>
        </div>
      </div>
    );
  }

  if (error || collaborators.length === 0) {
    return null; // Don't show section if no collaborators or error
  }

  return (
    <div className="w-full py-8 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
          {collaborators.map((collaborator) => (
            <a
              key={collaborator.id}
              href={collaborator.website_url}
              target="_blank"
              rel="noopener noreferrer"
              className="group relative flex flex-col items-center justify-center p-6 bg-white rounded-lg shadow-md hover:shadow-lg transition-all duration-200 border border-gray-200 hover:border-indigo-300"
            >
              {/* Logo */}
              <div className="mb-4 flex items-center justify-center h-20 w-full">
                <img
                  src={collaborator.logo_url}
                  alt={collaborator.name}
                  className="max-h-20 max-w-full object-contain"
                  loading="lazy"
                />
              </div>
              
              {/* Description Tooltip on Hover */}
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-64 p-3 bg-gray-900 text-white text-sm rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none z-10 shadow-xl">
                <p className="text-center">{collaborator.description}</p>
                <div className="absolute top-full left-1/2 transform -translate-x-1/2 -mt-1">
                  <div className="border-4 border-transparent border-t-gray-900"></div>
                </div>
              </div>
              
              {/* External Link Icon */}
              <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <ExternalLink className="h-4 w-4 text-indigo-600" />
              </div>
            </a>
          ))}
        </div>
      </div>
    </div>
  );
}


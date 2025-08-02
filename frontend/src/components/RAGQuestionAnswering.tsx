import React, { useState } from 'react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { AlertCircle, MessageCircle, FileText, ThumbsUp, ThumbsDown, Loader2, Brain, ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface RAGSource {
  document_id: number;
  document_title: string;
  country: string;
  chunk_preview: string;
}

interface RAGResponse {
  question: string;
  answer: string;
  confidence: number;
  sources: RAGSource[];
  response_time_ms: number;
  query_id: number;
}

const RAGQuestionAnswering: React.FC = () => {
  const navigate = useNavigate();
  const [question, setQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [response, setResponse] = useState<RAGResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);

  const handleSubmitQuestion = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!question.trim()) {
      return;
    }

    setIsLoading(true);
    setError(null);
    setResponse(null);
    setFeedbackSubmitted(false);

    try {
      const response = await fetch('/api/rag/question', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: question.trim(),
          language: 'en'
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get answer');
      }

      const data: RAGResponse = await response.json();
      setResponse(data);
    } catch (err) {
      setError('An error occurred while processing your question. Please try again.');
      console.error('RAG query error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFeedback = async (feedback: 'helpful' | 'not_helpful') => {
    if (!response) return;

    try {
      await fetch('/api/rag/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query_id: response.query_id,
          feedback: feedback
        }),
      });
      setFeedbackSubmitted(true);
    } catch (err) {
      console.error('Failed to submit feedback:', err);
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'bg-green-100 text-green-800';
    if (confidence >= 0.6) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 0.8) return 'High Confidence';
    if (confidence >= 0.6) return 'Medium Confidence';
    return 'Low Confidence';
  };

  return (
    <div className="space-y-6">
      {/* Question Input */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Brain className="w-5 h-5 text-blue-600" />
            <span>Ask AI about the Documents</span>
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            Ask questions in natural language about corruption documents and get AI-powered answers with sources.
          </p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmitQuestion} className="space-y-4">
            <div>
              <Textarea
                placeholder="Ask a question about corruption documents... (e.g., 'What corruption cases have been reported in Brazil?' or 'What are the main types of government fraud mentioned?')"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                rows={3}
                maxLength={1000}
                className="resize-none"
              />
              <div className="text-xs text-muted-foreground text-right mt-1">
                {question.length}/1000 characters
              </div>
            </div>
            <Button 
              type="submit" 
              disabled={isLoading || !question.trim()}
              className="w-full"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Processing Question...
                </>
              ) : (
                <>
                  <MessageCircle className="w-4 h-4 mr-2" />
                  Ask Question
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Card className="border-red-200">
          <CardContent className="pt-6">
            <div className="flex items-center space-x-2 text-red-600">
              <AlertCircle className="w-5 h-5" />
              <span>{error}</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Answer Display */}
      {response && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">AI Answer</CardTitle>
              <div className="flex items-center space-x-2">
                <Badge className={getConfidenceColor(response.confidence)}>
                  {getConfidenceLabel(response.confidence)} ({Math.round(response.confidence * 100)}%)
                </Badge>
                <Badge variant="outline">
                  {response.response_time_ms}ms
                </Badge>
              </div>
            </div>
            <p className="text-sm text-muted-foreground font-medium">
              Question: "{response.question}"
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Answer Text */}
            <div className="prose prose-sm max-w-none">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
                  {response.answer}
                </p>
              </div>
            </div>

            <Separator />

            {/* Sources */}
            {response.sources.length > 0 && (
              <div className="space-y-3">
                <h4 className="text-sm font-semibold flex items-center space-x-2">
                  <FileText className="w-4 h-4" />
                  <span>Sources ({response.sources.length} documents)</span>
                </h4>
                <div className="grid gap-3">
                  {response.sources.map((source, index) => (
                    <div 
                      key={index} 
                      className="border border-gray-200 rounded-lg p-3 hover:border-blue-300 transition-colors cursor-pointer"
                      onClick={() => navigate(`/document-detail-page?id=${source.document_id}`)}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <h5 className="font-medium text-sm text-blue-600 hover:text-blue-800">
                            {source.document_title}
                          </h5>
                          <p className="text-xs text-gray-500 mb-2">
                            Country: {source.country}
                          </p>
                          <p className="text-xs text-gray-600 leading-relaxed">
                            {source.chunk_preview}
                          </p>
                        </div>
                        <ExternalLink className="w-4 h-4 text-gray-400 ml-2 flex-shrink-0" />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <Separator />

            {/* Feedback */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">
                Was this answer helpful?
              </span>
              {!feedbackSubmitted ? (
                <div className="flex space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleFeedback('helpful')}
                    className="flex items-center space-x-1"
                  >
                    <ThumbsUp className="w-4 h-4" />
                    <span>Yes</span>
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleFeedback('not_helpful')}
                    className="flex items-center space-x-1"
                  >
                    <ThumbsDown className="w-4 h-4" />
                    <span>No</span>
                  </Button>
                </div>
              ) : (
                <Badge variant="outline" className="text-green-600">
                  Thank you for your feedback!
                </Badge>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Help Text */}
      <Card className="bg-gray-50">
        <CardContent className="pt-6">
          <div className="space-y-2">
            <h4 className="text-sm font-semibold">Tips for better results:</h4>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• Be specific in your questions (e.g., mention countries, types of corruption, specific topics)</li>
              <li>• Ask about content that might be in the documents (corruption cases, government issues, transparency)</li>
              <li>• Use natural language - ask questions as you would to a human researcher</li>
              <li>• Check the confidence score - higher confidence means more reliable answers</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default RAGQuestionAnswering;
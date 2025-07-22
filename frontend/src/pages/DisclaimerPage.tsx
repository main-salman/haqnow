import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { AlertDialog, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog";
import { AlertTriangle, Shield, Eye, Globe, ArrowLeft, Plus, Edit, Trash2, HelpCircle } from 'lucide-react';

interface FAQ {
  question: string;
  answer: string;
  id: string;
}

const DisclaimerPage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [isAdmin, setIsAdmin] = useState(false);
  const [showAddFAQ, setShowAddFAQ] = useState(false);
  const [editingFAQ, setEditingFAQ] = useState<FAQ | null>(null);
  const [newQuestion, setNewQuestion] = useState('');
  const [newAnswer, setNewAnswer] = useState('');
  const [customFAQs, setCustomFAQs] = useState<FAQ[]>([]);

  // Check if user is admin
  useEffect(() => {
    const token = localStorage.getItem('jwt_token');
    setIsAdmin(!!token);
  }, []);

  // Default FAQs from translations
  const defaultFAQs = [
    { id: 'faq1', question: t('disclaimer.faqQ1'), answer: t('disclaimer.faqA1') },
    { id: 'faq2', question: t('disclaimer.faqQ2'), answer: t('disclaimer.faqA2') },
    { id: 'faq3', question: t('disclaimer.faqQ3'), answer: t('disclaimer.faqA3') },
    { id: 'faq4', question: t('disclaimer.faqQ4'), answer: t('disclaimer.faqA4') },
    { id: 'faq5', question: t('disclaimer.faqQ5'), answer: t('disclaimer.faqA5') },
    { id: 'faq6', question: t('disclaimer.faqQ6'), answer: t('disclaimer.faqA6') },
    { id: 'faq7', question: t('disclaimer.faqQ7'), answer: t('disclaimer.faqA7') },
    { id: 'faq8', question: t('disclaimer.faqQ8'), answer: t('disclaimer.faqA8') }
  ];

  // Load custom FAQs from translations API
  const loadCustomFAQs = async () => {
    try {
      const response = await fetch('/api/translations/sections/disclaimer');
      if (response.ok) {
        const data = await response.json();
        const faqs: FAQ[] = [];
        
        // Extract custom FAQ entries
        Object.keys(data.translations).forEach(key => {
          if (key.startsWith('customFaqQ_')) {
            const faqId = key.replace('customFaqQ_', '');
            const answerKey = `customFaqA_${faqId}`;
            if (data.translations[answerKey]) {
              faqs.push({
                id: faqId,
                question: data.translations[key],
                answer: data.translations[answerKey]
              });
            }
          }
        });
        
        setCustomFAQs(faqs);
      }
    } catch (error) {
      console.error('Error loading custom FAQs:', error);
    }
  };

  useEffect(() => {
    loadCustomFAQs();
  }, []);

  // Save FAQ via translations API
  const saveFAQ = async () => {
    if (!newQuestion.trim() || !newAnswer.trim()) {
      alert('Please fill in both question and answer');
      return;
    }

    try {
      const faqId = editingFAQ?.id || Date.now().toString();
      const token = localStorage.getItem('jwt_token');
      
      // Create translation entries for question and answer
      const translations = {
        [`customFaqQ_${faqId}`]: newQuestion,
        [`customFaqA_${faqId}`]: newAnswer
      };

      const response = await fetch('/api/translations/admin/bulk-update/en/disclaimer', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ translations })
      });

      if (response.ok) {
        await loadCustomFAQs();
        setShowAddFAQ(false);
        setEditingFAQ(null);
        setNewQuestion('');
        setNewAnswer('');
        alert(editingFAQ ? 'FAQ updated successfully!' : 'FAQ added successfully!');
      } else {
        alert('Failed to save FAQ');
      }
    } catch (error) {
      console.error('Error saving FAQ:', error);
      alert('Error saving FAQ');
    }
  };

  // Delete FAQ
  const deleteFAQ = async (faqId: string) => {
    if (!confirm('Are you sure you want to delete this FAQ?')) return;

    try {
      const token = localStorage.getItem('jwt_token');
      
      // Delete both question and answer translations
      await fetch(`/api/translations/admin/delete/customFaqQ_${faqId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      await fetch(`/api/translations/admin/delete/customFaqA_${faqId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      await loadCustomFAQs();
      alert('FAQ deleted successfully!');
    } catch (error) {
      console.error('Error deleting FAQ:', error);
      alert('Error deleting FAQ');
    }
  };

  // Start editing FAQ
  const startEditFAQ = (faq: FAQ) => {
    setEditingFAQ(faq);
    setNewQuestion(faq.question);
    setNewAnswer(faq.answer);
    setShowAddFAQ(true);
  };

  const allFAQs = [...defaultFAQs, ...customFAQs];

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50 py-8">
      <div className="container mx-auto px-4 max-w-4xl">
        {/* Back Button */}
        <Button 
          variant="ghost" 
          onClick={() => navigate('/')}
          className="mb-6 hover:bg-red-100"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          {t('disclaimer.backToHome')}
        </Button>

        {/* Main Warning Card */}
        <Card className="border-red-200 shadow-lg mb-8">
          <CardHeader className="bg-gradient-to-r from-red-500 to-orange-500 text-white">
            <CardTitle className="text-2xl font-bold flex items-center">
              <AlertTriangle className="h-8 w-8 mr-3" />
              {t('disclaimer.securityWarningTitle')}
            </CardTitle>
          </CardHeader>
          <CardContent className="p-8">
            <div className="prose prose-lg max-w-none">
              {/* Corporate Warning */}
              <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-8">
                <h3 className="text-xl font-bold text-red-800 mb-4 flex items-center">
                  <Shield className="h-6 w-6 mr-2" />
                  {t('disclaimer.corporateWarningTitle')}
                </h3>
                <p className="text-red-700 font-medium mb-4">
                  <strong>{t('disclaimer.corporateWarningText')}</strong>
                </p>
                <p className="text-red-600 mb-4">
                  {t('disclaimer.corporateWarningDescription')}
                </p>
                <ul className="list-disc list-inside text-red-600 space-y-2 ml-4">
                  <li>{t('disclaimer.corporateWarningItem1')}</li>
                  <li>{t('disclaimer.corporateWarningItem2')}</li>
                  <li>{t('disclaimer.corporateWarningItem3')}</li>
                  <li>{t('disclaimer.corporateWarningItem4')}</li>
                </ul>
              </div>

              {/* Country Warning */}
              <div className="bg-orange-50 border border-orange-200 rounded-lg p-6 mb-8">
                <h3 className="text-xl font-bold text-orange-800 mb-4 flex items-center">
                  <Globe className="h-6 w-6 mr-2" />
                  {t('disclaimer.countryWarningTitle')}
                </h3>
                <p className="text-orange-700 font-medium mb-4">
                  {t('disclaimer.countryWarningText')}
                </p>
                <div className="bg-orange-100 border border-orange-300 rounded-md p-4 mb-4">
                  <h4 className="font-semibold text-orange-800 mb-2">{t('disclaimer.countryWarningSubtitle')}</h4>
                  <ul className="list-disc list-inside text-orange-700 space-y-1 ml-4">
                    <li>{t('disclaimer.countryWarningItem1')}</li>
                    <li>{t('disclaimer.countryWarningItem2')}</li>
                    <li>{t('disclaimer.countryWarningItem3')}</li>
                    <li>{t('disclaimer.countryWarningItem4')}</li>
                  </ul>
                </div>
              </div>

              {/* Best Practices */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
                <h3 className="text-xl font-bold text-blue-800 mb-4 flex items-center">
                  <Eye className="h-6 w-6 mr-2" />
                  {t('disclaimer.bestPracticesTitle')}
                </h3>
                <ul className="list-disc list-inside text-blue-700 space-y-2 ml-4">
                  <li>{t('disclaimer.bestPracticesItem1')}</li>
                  <li>{t('disclaimer.bestPracticesItem2')}</li>
                  <li>{t('disclaimer.bestPracticesItem3')}</li>
                  <li>{t('disclaimer.bestPracticesItem4')}</li>
                  <li>{t('disclaimer.bestPracticesItem5')}</li>
                </ul>
              </div>

              {/* Privacy Commitment */}
              <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                <h3 className="text-xl font-bold text-green-800 mb-4">{t('disclaimer.privacyCommitmentTitle')}</h3>
                <p className="text-green-700 mb-4">
                  {t('disclaimer.privacyCommitmentText')}
                </p>
                <ul className="list-disc list-inside text-green-700 space-y-1 ml-4">
                  <li>{t('disclaimer.privacyCommitmentItem1')}</li>
                  <li>{t('disclaimer.privacyCommitmentItem2')}</li>
                  <li>{t('disclaimer.privacyCommitmentItem3')}</li>
                  <li>{t('disclaimer.privacyCommitmentItem4')}</li>
                </ul>
                <p className="text-green-600 mt-4 font-medium">
                  {t('disclaimer.privacyCommitmentNote')}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* FAQ Section */}
        <Card className="border-blue-200 shadow-lg mb-8">
          <CardHeader className="bg-gradient-to-r from-blue-500 to-indigo-500 text-white">
            <div className="flex items-center justify-between">
              <CardTitle className="text-2xl font-bold flex items-center">
                <HelpCircle className="h-8 w-8 mr-3" />
                {t('disclaimer.faqTitle')}
              </CardTitle>
              {isAdmin && (
                <Button 
                  variant="secondary" 
                  size="sm"
                  onClick={() => {
                    setEditingFAQ(null);
                    setNewQuestion('');
                    setNewAnswer('');
                    setShowAddFAQ(true);
                  }}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  {t('disclaimer.addQuestionButton')}
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="p-6">
            <div className="space-y-6">
              {allFAQs.map((faq, index) => (
                <div key={faq.id} className="border-b border-gray-200 pb-6 last:border-b-0">
                  <div className="flex items-start justify-between mb-3">
                    <h4 className="text-lg font-semibold text-gray-900 flex-1">
                      Q{index + 1}: {faq.question}
                    </h4>
                    {isAdmin && faq.id.startsWith('custom') && (
                      <div className="flex items-center space-x-2 ml-4">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => startEditFAQ(faq)}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => deleteFAQ(faq.id)}
                          className="text-red-600 hover:text-red-700"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    )}
                  </div>
                  <p className="text-gray-700 leading-relaxed">{faq.answer}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Add/Edit FAQ Dialog */}
        <AlertDialog open={showAddFAQ} onOpenChange={setShowAddFAQ}>
          <AlertDialogContent className="max-w-2xl">
            <AlertDialogHeader>
              <AlertDialogTitle>
                {editingFAQ ? t('disclaimer.editQuestionButton') : t('disclaimer.addQuestionButton')}
              </AlertDialogTitle>
              <AlertDialogDescription>
                {editingFAQ ? 'Edit the FAQ question and answer' : 'Add a new frequently asked question'}
              </AlertDialogDescription>
            </AlertDialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <label className="text-sm font-medium mb-2 block">{t('disclaimer.questionLabel')}</label>
                <Input
                  value={newQuestion}
                  onChange={(e) => setNewQuestion(e.target.value)}
                  placeholder="Enter the question..."
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">{t('disclaimer.answerLabel')}</label>
                <Textarea
                  value={newAnswer}
                  onChange={(e) => setNewAnswer(e.target.value)}
                  placeholder="Enter the answer..."
                  rows={6}
                />
              </div>
            </div>
            <AlertDialogFooter>
              <Button variant="outline" onClick={() => setShowAddFAQ(false)}>
                {t('disclaimer.cancelButton')}
              </Button>
              <Button onClick={saveFAQ}>
                {t('disclaimer.saveQuestionButton')}
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button 
            onClick={() => navigate('/privacy-guaranteed-page')}
            variant="outline"
            className="border-blue-300 text-blue-700 hover:bg-blue-50"
          >
            {t('disclaimer.learnMoreButton')}
          </Button>
          <Button 
            onClick={() => navigate('/')}
            className="bg-green-600 hover:bg-green-700 text-white"
          >
            {t('disclaimer.continueButton')}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default DisclaimerPage; 
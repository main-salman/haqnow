import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertTriangle, Shield, Eye, Globe, ArrowLeft, HelpCircle } from 'lucide-react';
import Navigation from "@/components/Navigation";

interface FAQ {
  question: string;
  answer: string;
  id: string;
}

const DisclaimerPage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [customFAQs, setCustomFAQs] = useState<FAQ[]>([]);

  // Helper function to convert URLs in text to clickable links
  const renderTextWithLinks = (text: string) => {
    const urlRegex = /(https?:\/\/[^\s]+)/g;
    const parts = text.split(urlRegex);
    
    return parts.map((part, index) => {
      if (part.match(urlRegex)) {
        return (
          <a
            key={index}
            href={part}
            target="_blank"
            rel="noopener noreferrer"
            className="text-green-600 hover:text-green-800 underline"
          >
            {part}
          </a>
        );
      }
      return part;
    });
  };

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
      const response = await fetch('/api/translations/languages/en');
      if (response.ok) {
        const data = await response.json();
        const faqs: FAQ[] = [];
        
        // Check if translations exist and access them correctly
        const translations = data.translations || {};
        console.log('🔍 Loading custom FAQs, found translations:', Object.keys(translations));
        
        // Extract custom FAQ entries from disclaimer section
        Object.keys(translations).forEach(key => {
          if (key.startsWith('customFaqQ_')) {
            const faqId = key.replace('customFaqQ_', '');
            const answerKey = `customFaqA_${faqId}`;
            console.log(`🔍 Found FAQ question: ${key}, looking for answer: ${answerKey}`);
            
            if (translations[answerKey]) {
              faqs.push({
                id: `custom_${faqId}`,
                question: translations[key],
                answer: translations[answerKey]
              });
              console.log(`✅ Added custom FAQ: ${translations[key]}`);
            } else {
              console.log(`❌ No answer found for: ${answerKey}`);
            }
          }
        });
        
        console.log(`📝 Loaded ${faqs.length} custom FAQs:`, faqs);
        setCustomFAQs(faqs);
      } else {
        console.error('Failed to fetch translations:', response.status);
      }
    } catch (error) {
      console.error('Error loading custom FAQs:', error);
    }
  };

  useEffect(() => {
    loadCustomFAQs();
  }, []);



  const allFAQs = [...defaultFAQs, ...customFAQs];

  return (
    <div className="min-h-screen bg-white">
      <Navigation />
      <div className="py-8">
        <div className="container mx-auto px-4 max-w-4xl">
        {/* Main Warning Card */}
        <Card className="border-green-200 shadow-lg mb-8">
          <CardHeader className="bg-gradient-to-r from-green-500 to-green-600 text-white">
            <CardTitle className="text-2xl font-bold flex items-center">
              <AlertTriangle className="h-8 w-8 mr-3" />
              {t('disclaimer.securityWarningTitle')}
            </CardTitle>
          </CardHeader>
          <CardContent className="p-8">
            <div className="prose prose-lg max-w-none">
              {/* Corporate Warning */}
              <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-8">
                <h3 className="text-xl font-bold text-green-800 mb-4 flex items-center">
                  <Shield className="h-6 w-6 mr-2" />
                  {t('disclaimer.corporateWarningTitle')}
                </h3>
                <p className="text-green-700 font-medium mb-4">
                  <strong>{t('disclaimer.corporateWarningText')}</strong>
                </p>
                <p className="text-green-600 mb-4">
                  {t('disclaimer.corporateWarningDescription')}
                </p>
                <ul className="list-disc list-inside text-green-600 space-y-2 ml-4">
                  <li>{t('disclaimer.corporateWarningItem1')}</li>
                  <li>{t('disclaimer.corporateWarningItem2')}</li>
                  <li>{t('disclaimer.corporateWarningItem3')}</li>
                  <li>{t('disclaimer.corporateWarningItem4')}</li>
                </ul>
              </div>

              {/* Country Warning */}
              <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-8">
                <h3 className="text-xl font-bold text-green-800 mb-4 flex items-center">
                  <Globe className="h-6 w-6 mr-2" />
                  {t('disclaimer.countryWarningTitle')}
                </h3>
                <p className="text-green-700 font-medium mb-4">
                  {t('disclaimer.countryWarningText')}
                </p>
                <div className="bg-green-100 border border-green-300 rounded-md p-4 mb-4">
                  <h4 className="font-semibold text-green-800 mb-2">{t('disclaimer.countryWarningSubtitle')}</h4>
                  <ul className="list-disc list-inside text-green-700 space-y-1 ml-4">
                    <li>{t('disclaimer.countryWarningItem1')}</li>
                    <li>{t('disclaimer.countryWarningItem2')}</li>
                    <li>{t('disclaimer.countryWarningItem3')}</li>
                    <li>{t('disclaimer.countryWarningItem4')}</li>
                  </ul>
                </div>
              </div>

              {/* Best Practices */}
              <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-8">
                <h3 className="text-xl font-bold text-green-800 mb-4 flex items-center">
                  <Eye className="h-6 w-6 mr-2" />
                  {t('disclaimer.bestPracticesTitle')}
                </h3>
                <ul className="list-disc list-inside text-green-700 space-y-2 ml-4">
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
        <Card className="border-green-200 shadow-lg mb-8">
          <CardHeader className="bg-gradient-to-r from-green-500 to-green-600 text-white">
            <CardTitle className="text-2xl font-bold flex items-center">
              <HelpCircle className="h-8 w-8 mr-3" />
              {t('disclaimer.faqTitle')}
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <div className="space-y-6">
              {allFAQs.map((faq, index) => (
                <div key={faq.id} className="border-b border-gray-200 pb-6 last:border-b-0">
                  <h4 className="text-lg font-semibold text-gray-900 mb-3">
                    Q{index + 1}: {faq.question}
                  </h4>
                  <p className="text-gray-700 leading-relaxed">{renderTextWithLinks(faq.answer)}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>



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
    </div>
  );
};

export default DisclaimerPage; 
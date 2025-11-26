import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertTriangle, Shield, Eye, Globe, ArrowLeft, HelpCircle, FileText } from 'lucide-react';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
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

  // Helper function to render moderation content with line breaks
  const renderModerationContent = (content: string) => {
    return content.split('\n').map((line, index) => {
      // Check if line starts with bullet or number
      if (line.trim().startsWith('•') || /^\d+\./.test(line.trim())) {
        return <div key={index} className="mb-2 ml-4">{line}</div>;
      }
      // Check if line is a sub-bullet
      if (line.trim().startsWith('-')) {
        return <div key={index} className="mb-1 ml-8 text-sm">{line}</div>;
      }
      // Regular paragraph
      if (line.trim()) {
        return <p key={index} className="mb-4">{line}</p>;
      }
      return <br key={index} />;
    });
  };

  return (
    <div className="min-h-screen bg-white">
      <Navigation />
      <div className="py-12">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Table of Contents */}
        <Card className="border-green-200 shadow-lg mb-8">
          <CardHeader className="bg-gradient-to-r from-green-500 to-green-600 text-white">
            <CardTitle className="text-2xl font-bold">
              {t('disclaimer.tableOfContentsTitle')}
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6">
            <ul className="space-y-2">
              <li>
                <a 
                  href="#moderation-policies" 
                  className="text-green-600 hover:text-green-800 underline flex items-center"
                  onClick={(e) => {
                    e.preventDefault();
                    document.getElementById('moderation-policies')?.scrollIntoView({ behavior: 'smooth' });
                  }}
                >
                  <FileText className="h-4 w-4 mr-2" />
                  {t('disclaimer.moderationSectionTitle')}
                </a>
              </li>
              <li>
                <a 
                  href="#disclaimers" 
                  className="text-green-600 hover:text-green-800 underline flex items-center"
                  onClick={(e) => {
                    e.preventDefault();
                    document.getElementById('disclaimers')?.scrollIntoView({ behavior: 'smooth' });
                  }}
                >
                  <Shield className="h-4 w-4 mr-2" />
                  {t('disclaimer.disclaimerSectionTitle')}
                </a>
              </li>
              <li>
                <a 
                  href="#faq" 
                  className="text-green-600 hover:text-green-800 underline flex items-center"
                  onClick={(e) => {
                    e.preventDefault();
                    document.getElementById('faq')?.scrollIntoView({ behavior: 'smooth' });
                  }}
                >
                  <HelpCircle className="h-4 w-4 mr-2" />
                  {t('disclaimer.faqSectionTitle')}
                </a>
              </li>
            </ul>
          </CardContent>
        </Card>

        {/* Accordion Container */}
        <Card className="border-green-200 shadow-lg mb-8">
          <CardContent className="p-0">
            <Accordion type="multiple" className="w-full" defaultValue={[]}>
              {/* Moderation Policies Section */}
              <AccordionItem value="moderation" id="moderation-policies">
                <AccordionTrigger className="px-6 py-4 text-xl font-semibold">
                  <div className="flex items-center">
                    <FileText className="h-6 w-6 mr-3" />
                    {t('disclaimer.moderationSectionTitle')}
                  </div>
                </AccordionTrigger>
                <AccordionContent className="px-6 pb-6">
                  <div className="prose prose-lg max-w-none">
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">{t('moderation.title')}</h2>
                    
                    <div className="mb-6">
                      <h3 className="text-xl font-bold text-gray-900 mb-3">{t('moderation.section1Title')}</h3>
                      <div className="text-gray-700 whitespace-pre-line">
                        {renderModerationContent(t('moderation.section1Content'))}
                      </div>
                    </div>

                    <div className="mb-6">
                      <h3 className="text-xl font-bold text-gray-900 mb-3">{t('moderation.section2Title')}</h3>
                      <div className="text-gray-700 whitespace-pre-line">
                        {renderModerationContent(t('moderation.section2Content'))}
                      </div>
                    </div>

                    <div className="mb-6">
                      <h3 className="text-xl font-bold text-gray-900 mb-3">{t('moderation.section3Title')}</h3>
                      <div className="text-gray-700 whitespace-pre-line">
                        {renderModerationContent(t('moderation.section3Content'))}
                      </div>
                    </div>

                    <div className="mb-6">
                      <h3 className="text-xl font-bold text-gray-900 mb-3">{t('moderation.section4Title')}</h3>
                      <div className="text-gray-700 whitespace-pre-line">
                        {renderModerationContent(t('moderation.section4Content'))}
                      </div>
                    </div>

                    <div className="mb-6">
                      <h3 className="text-xl font-bold text-gray-900 mb-3">{t('moderation.section5Title')}</h3>
                      <div className="text-gray-700 whitespace-pre-line">
                        {renderModerationContent(t('moderation.section5Content'))}
                      </div>
                    </div>

                    <div className="mb-6">
                      <h3 className="text-xl font-bold text-gray-900 mb-3">{t('moderation.section6Title')}</h3>
                      <div className="text-gray-700 whitespace-pre-line">
                        {renderModerationContent(t('moderation.section6Content'))}
                      </div>
                    </div>

                    <div className="mb-6">
                      <h3 className="text-xl font-bold text-gray-900 mb-3">{t('moderation.section7Title')}</h3>
                      <div className="text-gray-700 whitespace-pre-line">
                        {renderModerationContent(t('moderation.section7Content'))}
                      </div>
                    </div>
                  </div>
                </AccordionContent>
              </AccordionItem>

              {/* Disclaimer Section */}
              <AccordionItem value="disclaimer" id="disclaimers">
                <AccordionTrigger className="px-6 py-4 text-xl font-semibold">
                  <div className="flex items-center">
                    <Shield className="h-6 w-6 mr-3" />
                    {t('disclaimer.disclaimerSectionTitle')}
                  </div>
                </AccordionTrigger>
                <AccordionContent className="px-6 pb-6">
                  <div className="prose prose-lg max-w-none">
                    {/* Corporate Warning */}
                    <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-8">
                      <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
                        <Shield className="h-6 w-6 mr-2" />
                        {t('disclaimer.corporateWarningTitle')}
                      </h3>
                      <p className="text-gray-700 font-medium mb-4">
                        <strong>{t('disclaimer.corporateWarningText')}</strong>
                      </p>
                      <p className="text-gray-600 mb-4">
                        {t('disclaimer.corporateWarningDescription')}
                      </p>
                      <ul className="list-disc list-inside text-gray-600 space-y-2 ml-4">
                        <li>{t('disclaimer.corporateWarningItem1')}</li>
                        <li>{t('disclaimer.corporateWarningItem2')}</li>
                        <li>{t('disclaimer.corporateWarningItem3')}</li>
                        <li>{t('disclaimer.corporateWarningItem4')}</li>
                      </ul>
                    </div>

                    {/* Country Warning */}
                    <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-8">
                      <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
                        <Globe className="h-6 w-6 mr-2" />
                        {t('disclaimer.countryWarningTitle')}
                      </h3>
                      <p className="text-gray-700 font-medium mb-4">
                        {t('disclaimer.countryWarningText')}
                      </p>
                      <div className="bg-green-100 border border-green-300 rounded-md p-4 mb-4">
                        <h4 className="font-semibold text-gray-900 mb-2">{t('disclaimer.countryWarningSubtitle')}</h4>
                        <ul className="list-disc list-inside text-gray-700 space-y-1 ml-4">
                          <li>{t('disclaimer.countryWarningItem1')}</li>
                          <li>{t('disclaimer.countryWarningItem2')}</li>
                          <li>{t('disclaimer.countryWarningItem3')}</li>
                          <li>{t('disclaimer.countryWarningItem4')}</li>
                        </ul>
                      </div>
                    </div>

                    {/* Best Practices */}
                    <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-8">
                      <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center">
                        <Eye className="h-6 w-6 mr-2" />
                        {t('disclaimer.bestPracticesTitle')}
                      </h3>
                      <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
                        <li>{t('disclaimer.bestPracticesItem1')}</li>
                        <li>{t('disclaimer.bestPracticesItem2')}</li>
                        <li>{t('disclaimer.bestPracticesItem3')}</li>
                        <li>{t('disclaimer.bestPracticesItem4')}</li>
                        <li>{t('disclaimer.bestPracticesItem5')}</li>
                        <li>{t('upload.phoneUploadTip')}</li>
                      </ul>
                    </div>

                    {/* Privacy Commitment */}
                    <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                      <h3 className="text-xl font-bold text-gray-900 mb-4">{t('disclaimer.privacyCommitmentTitle')}</h3>
                      <p className="text-gray-700 mb-4">
                        {t('disclaimer.privacyCommitmentText')}
                      </p>
                      <ul className="list-disc list-inside text-gray-700 space-y-1 ml-4">
                        <li>{t('disclaimer.privacyCommitmentItem1')}</li>
                        <li>{t('disclaimer.privacyCommitmentItem2')}</li>
                        <li>{t('disclaimer.privacyCommitmentItem3')}</li>
                        <li>{t('disclaimer.privacyCommitmentItem4')}</li>
                      </ul>
                      <p className="text-gray-600 mt-4 font-medium">
                        {t('disclaimer.privacyCommitmentNote')}
                      </p>
                    </div>
                  </div>
                </AccordionContent>
              </AccordionItem>

              {/* FAQ Section */}
              <AccordionItem value="faq" id="faq">
                <AccordionTrigger className="px-6 py-4 text-xl font-semibold">
                  <div className="flex items-center">
                    <HelpCircle className="h-6 w-6 mr-3" />
                    {t('disclaimer.faqSectionTitle')}
                  </div>
                </AccordionTrigger>
                <AccordionContent className="px-6 pb-6">
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
                </AccordionContent>
              </AccordionItem>
            </Accordion>
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
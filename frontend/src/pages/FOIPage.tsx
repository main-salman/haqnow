import React from 'react';
import { useTranslation, Trans } from 'react-i18next';
import { FileText, ExternalLink, Search, Globe, Shield, Book, ArrowLeft } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import Navigation from "@/components/Navigation";

const FOIPage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();

  const foiCountries = [
    {
      country: "Australia",
      law: "Freedom of Information Act 1982",
      portal: "https://www.oaic.gov.au/freedom-of-information",
      agency: "Office of the Australian Information Commissioner",
      flag: "🇦🇺"
    },
    {
      country: "Brazil",
      law: "Lei de Acesso à Informação",
      portal: "https://www.gov.br/acessoainformacao/pt-br",
      agency: "Governo Federal",
      flag: "🇧🇷"
    },
    {
      country: "Canada",
      law: "Access to Information Act",
      portal: "https://www.canada.ca/en/treasury-board-secretariat/services/access-information-privacy.html",
      agency: "Treasury Board of Canada",
      flag: "🇨🇦"
    },
    {
      country: "European Union",
      law: "Regulation 1049/2001",
      portal: "https://www.asktheeu.org/",
      agency: "AskTheEU.org",
      flag: "🇪🇺"
    },
    {
      country: "France",
      law: "Commission d'accès aux documents administratifs (CADA)",
      portal: "https://www.cada.fr/",
      agency: "CADA",
      flag: "🇫🇷"
    },
    {
      country: "Germany",
      law: "Informationsfreiheitsgesetz (IFG)",
      portal: "https://fragdenstaat.de/",
      agency: "FragDenStaat",
      flag: "🇩🇪"
    },
    {
      country: "India",
      law: "Right to Information Act 2005",
      portal: "https://rtionline.gov.in/",
      agency: "RTI Online",
      flag: "🇮🇳"
    },
    {
      country: "Japan",
      law: "Act on Access to Information",
      portal: "https://www.soumu.go.jp/main_sosiki/gyoukan/kanri/jyohokokai/index.html",
      agency: "Ministry of Internal Affairs and Communications",
      flag: "🇯🇵"
    },
    {
      country: "Mexico",
      law: "Ley Federal de Transparencia",
      portal: "https://www.plataformadetransparencia.org.mx/",
      agency: "Plataforma Nacional de Transparencia",
      flag: "🇲🇽"
    },
    {
      country: "South Africa",
      law: "Promotion of Access to Information Act",
      portal: "https://www.sahrc.org.za/",
      agency: "South African Human Rights Commission",
      flag: "🇿🇦"
    },
    {
      country: "United Kingdom", 
      law: "Freedom of Information Act 2000",
      portal: "https://www.gov.uk/make-a-freedom-of-information-request",
      agency: "GOV.UK",
      flag: "🇬🇧"
    },
    {
      country: "United States",
      law: "Freedom of Information Act (FOIA)",
      portal: "https://www.foia.gov/",
      agency: "FOIA.gov",
      flag: "🇺🇸"
    }
  ];

  return (
    <div className="min-h-screen bg-white">
      <Navigation />
      <div className="py-12">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Freedom of Information Laws
          </h1>
          <div className="w-24 h-1 bg-green-600 mx-auto mb-6"></div>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            {t('foi.subtitle')}
          </p>
        </div>

        {/* Introduction */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <div className="flex items-center mb-6">
            <Book className="w-8 h-8 text-green-600 mr-3" />
            <h2 className="text-2xl font-bold text-gray-900">{t('foi.whatIs')}</h2>
          </div>
          
          <div className="prose prose-lg text-gray-700 space-y-4 mb-6">
            <p>
              {t('foi.whatIsDesc1')}
            </p>
            
            <p>
              {t('foi.whatIsDesc2')}
            </p>
            
            <p className="font-medium text-green-700">
              {t('foi.proTip')}
            </p>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              <strong>{t('foi.source')}</strong> {t('foi.sourceText')}{' '}
              <a 
                href="https://en.wikipedia.org/wiki/Freedom_of_information_laws_by_country"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 underline"
              >
                {t('foi.wikipediaLink')}
              </a>
              {' '}{t('foi.sourceEnd')}
            </p>
          </div>
        </div>

        {/* Best Practices */}
        <div className="bg-green-50 border border-green-200 rounded-lg shadow-lg p-8 mb-8">
          <div className="flex items-center mb-6">
            <Shield className="w-8 h-8 text-green-600 mr-3" />
            <h2 className="text-2xl font-bold text-gray-900">Best Practices for FOI Requests</h2>
          </div>
          
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold text-gray-900 mb-3">📝 Before Submitting</h3>
              <ul className="space-y-2 text-gray-700">
                <li>• Be specific about what information you want</li>
                <li>• Research which agency likely holds the information</li>
                <li>• Check if the information is already public</li>
                <li>• Use precise language and avoid broad requests</li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-semibold text-gray-900 mb-3">⏰ During Process</h3>
              <ul className="space-y-2 text-gray-700">
                <li>• Keep records of all communications</li>
                <li>• Follow up if deadlines are missed</li>
                <li>• Be prepared to appeal decisions</li>
                <li>• Consider narrowing requests if they're too broad</li>
              </ul>
            </div>
          </div>
          
          <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">
              <strong>💡 Pro Tip:</strong> FOI requests work best when combined with platforms like HaqNow for sharing obtained documents with journalists and researchers worldwide.
            </p>
          </div>
        </div>

        {/* How to Use FOI */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <div className="flex items-center mb-6">
            <Search className="w-8 h-8 text-green-600 mr-3" />
            <h2 className="text-2xl font-bold text-gray-900">{t('foi.howTo')}</h2>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="bg-green-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-green-600">1</span>
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">{t('foi.step1')}</h3>
              <p className="text-gray-600 text-sm">{t('foi.step1Desc')}</p>
            </div>
            
            <div className="text-center">
              <div className="bg-green-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-green-600">2</span>
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">{t('foi.step2')}</h3>
              <p className="text-gray-600 text-sm">{t('foi.step2Desc')}</p>
            </div>
            
            <div className="text-center">
              <div className="bg-green-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-green-600">3</span>
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">{t('foi.step3')}</h3>
              <p className="text-gray-600 text-sm">{t('foi.step3Desc')}</p>
            </div>
            
            <div className="text-center">
              <div className="bg-green-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-green-600">4</span>
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">{t('foi.step4')}</h3>
              <p className="text-gray-600 text-sm">{t('foi.step4Desc')}</p>
            </div>
          </div>
        </div>

        {/* Country-specific FOI Resources */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <div className="flex items-center mb-6">
            <Globe className="w-8 h-8 text-green-600 mr-3" />
            <h2 className="text-2xl font-bold text-gray-900">{t('foi.countries')}</h2>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {foiCountries.map((country, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-6 hover:border-green-300 hover:shadow-md transition-all">
                <div className="flex items-center mb-4">
                  <span className="text-3xl mr-3">{country.flag}</span>
                  <div>
                    <h3 className="font-semibold text-gray-900 text-lg">{country.country}</h3>
                    <p className="text-sm text-gray-600">{country.law}</p>
                  </div>
                </div>
                
                <div className="mb-4">
                  <p className="text-sm text-gray-600 mb-2">
                    <strong>{t('foi.agency')}</strong> {country.agency}
                  </p>
                </div>
                
                <a 
                  href={country.portal}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center text-green-600 hover:text-green-800 font-medium text-sm"
                >
                  <ExternalLink className="w-4 h-4 mr-2" />
                  {t('foi.submitRequest')}
                </a>
              </div>
            ))}
          </div>
        </div>

        {/* Best Practices */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <div className="flex items-center mb-6">
            <Shield className="w-8 h-8 text-green-600 mr-3" />
            <h2 className="text-2xl font-bold text-gray-900">{t('foi.bestPractices')}</h2>
          </div>
          
          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <h3 className="font-semibold text-gray-900 mb-4">{t('foi.dos')}</h3>
              <ul className="space-y-2 text-gray-700">
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">•</span>
                  {t('foi.do1')}
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">•</span>
                  {t('foi.do2')}
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">•</span>
                  {t('foi.do3')}
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">•</span>
                  {t('foi.do4')}
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">•</span>
                  {t('foi.do5')}
                </li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-semibold text-gray-900 mb-4">{t('foi.donts')}</h3>
              <ul className="space-y-2 text-gray-700">
                <li className="flex items-start">
                  <span className="text-red-600 mr-2">•</span>
                  {t('foi.dont1')}
                </li>
                <li className="flex items-start">
                  <span className="text-red-600 mr-2">•</span>
                  {t('foi.dont2')}
                </li>
                <li className="flex items-start">
                  <span className="text-red-600 mr-2">•</span>
                  {t('foi.dont3')}
                </li>
                <li className="flex items-start">
                  <span className="text-red-600 mr-2">•</span>
                  {t('foi.dont4')}
                </li>
                <li className="flex items-start">
                  <span className="text-red-600 mr-2">•</span>
                  {t('foi.dont5')}
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Connection to HaqNow */}
        <div className="bg-gradient-to-r from-green-600 to-blue-600 rounded-lg shadow-lg p-8 text-white">
          <div className="text-center">
            <FileText className="w-16 h-16 mx-auto mb-4 text-white" />
            <h2 className="text-2xl font-bold mb-4">{t('foi.connection')}</h2>
            <p className="text-lg mb-6 text-green-100">
              {t('foi.connectionDesc')}
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <a 
                href="/upload-document-page" 
                className="bg-white text-green-600 px-6 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
              >
                {t('foi.uploadDocuments')}
              </a>
              <a 
                href="/search-page" 
                className="bg-green-500 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-400 transition-colors"
              >
                {t('foi.searchExisting')}
              </a>
            </div>
          </div>
        </div>
        </div>
      </div>
      
      {/* Footer */}
      <footer className="border-t border-border bg-muted/10 py-6 mt-8">
        <div className="container mx-auto px-4 flex flex-col items-center justify-center space-y-2">
          <p className="text-sm text-muted-foreground text-center">
            {t('footer.copyright')}
          </p>
          <p className="text-sm text-muted-foreground text-center">
            {t('footer.privacyPromise')}
          </p>
          <p className="text-sm text-muted-foreground text-center">
            <Trans
              i18nKey="footer.poweredBy"
              components={{
                link: (
                  <a
                    className="text-indigo-600 hover:text-indigo-800 underline"
                    href="https://thaura.ai/home"
                    target="_blank"
                    rel="noopener noreferrer"
                  />
                ),
              }}
            />
          </p>
        </div>
      </footer>
    </div>
  );
};

export default FOIPage; 
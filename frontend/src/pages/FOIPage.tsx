import React from 'react';
import { useTranslation } from 'react-i18next';
import { FileText, ExternalLink, Search, Globe, Shield, Book, ArrowLeft } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";

const FOIPage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();

  const foiCountries = [
    {
      country: "United States",
      law: "Freedom of Information Act (FOIA)",
      portal: "https://www.foia.gov/",
      agency: "FOIA.gov",
      flag: "🇺🇸"
    },
    {
      country: "United Kingdom", 
      law: "Freedom of Information Act 2000",
      portal: "https://www.gov.uk/make-a-freedom-of-information-request",
      agency: "GOV.UK",
      flag: "🇬🇧"
    },
    {
      country: "Canada",
      law: "Access to Information Act",
      portal: "https://www.canada.ca/en/treasury-board-secretariat/services/access-information-privacy.html",
      agency: "Treasury Board of Canada",
      flag: "🇨🇦"
    },
    {
      country: "Australia",
      law: "Freedom of Information Act 1982",
      portal: "https://www.oaic.gov.au/freedom-of-information",
      agency: "Office of the Australian Information Commissioner",
      flag: "🇦🇺"
    },
    {
      country: "Germany",
      law: "Informationsfreiheitsgesetz (IFG)",
      portal: "https://fragdenstaat.de/",
      agency: "FragDenStaat",
      flag: "🇩🇪"
    },
    {
      country: "France",
      law: "Commission d'accès aux documents administratifs (CADA)",
      portal: "https://www.cada.fr/",
      agency: "CADA",
      flag: "🇫🇷"
    },
    {
      country: "European Union",
      law: "Regulation 1049/2001",
      portal: "https://www.asktheeu.org/",
      agency: "AskTheEU.org",
      flag: "🇪🇺"
    },
    {
      country: "India",
      law: "Right to Information Act 2005",
      portal: "https://rtionline.gov.in/",
      agency: "RTI Online",
      flag: "🇮🇳"
    },
    {
      country: "Brazil",
      law: "Lei de Acesso à Informação",
      portal: "https://www.gov.br/acessoainformacao/pt-br",
      agency: "Governo Federal",
      flag: "🇧🇷"
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
      country: "Japan",
      law: "Act on Access to Information",
      portal: "https://www.soumu.go.jp/main_sosiki/gyoukan/kanri/jyohokokai/index.html",
      agency: "Ministry of Internal Affairs and Communications",
      flag: "🇯🇵"
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-100 py-12">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Back Button */}
        <Button variant="outline" onClick={() => navigate("/")} className="mb-6">
          <ArrowLeft className="mr-2 h-4 w-4" />
          {t('navigation.backToHome', 'Back to Home')}
        </Button>
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            {t('navigation.foi')} - Freedom of Information Laws
          </h1>
          <div className="w-24 h-1 bg-green-600 mx-auto mb-6"></div>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Your guide to accessing government information and promoting transparency worldwide
          </p>
        </div>

        {/* Introduction */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <div className="flex items-center mb-6">
            <Book className="w-8 h-8 text-green-600 mr-3" />
            <h2 className="text-2xl font-bold text-gray-900">What is Freedom of Information?</h2>
          </div>
          
          <div className="prose prose-lg text-gray-700 space-y-4 mb-6">
            <p>
              Freedom of Information (FOI) laws give citizens the right to access government documents, 
              records, and data. These laws are fundamental tools for democracy, transparency, and 
              accountability. They allow journalists, researchers, activists, and ordinary citizens 
              to uncover government activities, expose corruption, and hold public officials accountable.
            </p>
            
            <p>
              FOI laws typically cover government agencies, departments, and public institutions. 
              They require these bodies to respond to information requests within specified timeframes, 
              though certain exemptions may apply for national security, personal privacy, or 
              commercial confidentiality reasons.
            </p>
            
            <p className="font-medium text-green-700">
              💡 Pro Tip: FOI requests are powerful tools for uncovering corruption, government 
              misconduct, and holding power accountable. Combined with platforms like HaqNow.com, 
              they create a comprehensive approach to transparency and anti-corruption work.
            </p>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              <strong>Source:</strong> This information is based on{' '}
              <a 
                href="https://en.wikipedia.org/wiki/Freedom_of_information_laws_by_country"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 underline"
              >
                Wikipedia's comprehensive article on Freedom of Information laws by country
              </a>
              {' '}and various government sources.
            </p>
          </div>
        </div>

        {/* How to Use FOI */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <div className="flex items-center mb-6">
            <Search className="w-8 h-8 text-green-600 mr-3" />
            <h2 className="text-2xl font-bold text-gray-900">How to Submit FOI Requests</h2>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="bg-green-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-green-600">1</span>
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Identify Agency</h3>
              <p className="text-gray-600 text-sm">Determine which government body holds the information you need</p>
            </div>
            
            <div className="text-center">
              <div className="bg-green-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-green-600">2</span>
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Be Specific</h3>
              <p className="text-gray-600 text-sm">Make your request clear, specific, and focused to get better results</p>
            </div>
            
            <div className="text-center">
              <div className="bg-green-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-green-600">3</span>
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Submit Request</h3>
              <p className="text-gray-600 text-sm">Use official portals or contact agencies directly through proper channels</p>
            </div>
            
            <div className="text-center">
              <div className="bg-green-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl font-bold text-green-600">4</span>
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">Follow Up</h3>
              <p className="text-gray-600 text-sm">Track your request and appeal if necessary to ensure compliance</p>
            </div>
          </div>
        </div>

        {/* Country-specific FOI Resources */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <div className="flex items-center mb-6">
            <Globe className="w-8 h-8 text-green-600 mr-3" />
            <h2 className="text-2xl font-bold text-gray-900">FOI Laws and Portals by Country</h2>
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
                    <strong>Agency:</strong> {country.agency}
                  </p>
                </div>
                
                <a 
                  href={country.portal}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center text-green-600 hover:text-green-800 font-medium text-sm"
                >
                  <ExternalLink className="w-4 h-4 mr-2" />
                  Submit FOI Request
                </a>
              </div>
            ))}
          </div>
        </div>

        {/* Best Practices */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <div className="flex items-center mb-6">
            <Shield className="w-8 h-8 text-green-600 mr-3" />
            <h2 className="text-2xl font-bold text-gray-900">FOI Best Practices</h2>
          </div>
          
          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <h3 className="font-semibold text-gray-900 mb-4">✅ Do's</h3>
              <ul className="space-y-2 text-gray-700">
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">•</span>
                  Be specific about dates, departments, and document types
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">•</span>
                  Request information, not opinions or analysis
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">•</span>
                  Keep records of all correspondence
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">•</span>
                  Be patient but persistent with follow-ups
                </li>
                <li className="flex items-start">
                  <span className="text-green-600 mr-2">•</span>
                  Consider appealing rejections when appropriate
                </li>
              </ul>
            </div>
            
            <div>
              <h3 className="font-semibold text-gray-900 mb-4">❌ Don'ts</h3>
              <ul className="space-y-2 text-gray-700">
                <li className="flex items-start">
                  <span className="text-red-600 mr-2">•</span>
                  Make overly broad or fishing expedition requests
                </li>
                <li className="flex items-start">
                  <span className="text-red-600 mr-2">•</span>
                  Request information that clearly falls under exemptions
                </li>
                <li className="flex items-start">
                  <span className="text-red-600 mr-2">•</span>
                  Use FOI for personal disputes or harassment
                </li>
                <li className="flex items-start">
                  <span className="text-red-600 mr-2">•</span>
                  Expect immediate responses - processing takes time
                </li>
                <li className="flex items-start">
                  <span className="text-red-600 mr-2">•</span>
                  Give up after initial rejection without considering appeals
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Connection to HaqNow.com */}
        <div className="bg-gradient-to-r from-green-600 to-blue-600 rounded-lg shadow-lg p-8 text-white">
          <div className="text-center">
            <FileText className="w-16 h-16 mx-auto mb-4 text-white" />
            <h2 className="text-2xl font-bold mb-4">FOI + HaqNow.com: Powerful Transparency Tools</h2>
            <p className="text-lg mb-6 text-green-100">
              When FOI requests uncover corruption, HaqNow.com provides a secure platform to share 
              those documents with the world. Together, they create a comprehensive approach to 
              fighting corruption and promoting transparency.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <a 
                href="/upload" 
                className="bg-white text-green-600 px-6 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
              >
                Upload FOI Documents
              </a>
              <a 
                href="/search" 
                className="bg-green-500 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-400 transition-colors"
              >
                Search Existing Documents
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FOIPage; 
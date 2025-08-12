import React from "react";
import { Button } from "@/components/ui/button";
import { ArrowLeft, ExternalLink, Globe, Users, Shield, List } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import Navigation from "@/components/Navigation";

export default function AboutPage() {
  const navigate = useNavigate();
  const { t } = useTranslation();

  return (
    <div className="min-h-screen bg-white">
      <Navigation />
      <div className="p-4 md:p-8">
        <div className="container mx-auto max-w-4xl space-y-8">
          {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            {t('navigation.about')}
          </h1>
          <div className="w-24 h-1 bg-indigo-600 mx-auto"></div>
        </div>

        {/* Table of Contents */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg shadow-lg p-6 mb-8">
          <div className="flex items-center mb-4">
            <List className="w-6 h-6 text-blue-600 mr-3" />
            <h2 className="text-xl font-bold text-gray-900">Table of Contents</h2>
          </div>
          <nav className="space-y-2">
            <a href="#founder" className="block text-blue-600 hover:text-blue-800 hover:underline transition-colors">
              • Meet the Founder
            </a>
            <a href="#mission" className="block text-blue-600 hover:text-blue-800 hover:underline transition-colors">
              • Mission & Values
            </a>
            <a href="#projects" className="block text-blue-600 hover:text-blue-800 hover:underline transition-colors">
              • Connected Projects & Links
            </a>
            <a href="#mission-statement" className="block text-blue-600 hover:text-blue-800 hover:underline transition-colors">
              • Mission Statement
            </a>
            <a href="#technical" className="block text-blue-600 hover:text-blue-800 hover:underline transition-colors">
              • Platform Features & Technical Details
            </a>
            <a href="#funding" className="block text-blue-600 hover:text-blue-800 hover:underline transition-colors">
              • {t('about.fundingTitle')}
            </a>
            <a href="#hosting" className="block text-blue-600 hover:text-blue-800 hover:underline transition-colors">
              • {t('about.hostingTitle')}
            </a>
          </nav>
        </div>

        {/* Founder Section */}
        <div id="founder" className="bg-white text-gray-800 rounded-lg shadow-lg p-8 mb-8">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              {t('about.founder')}
            </h2>
            <div className="flex justify-center mb-6">
              <a 
                href="https://www.linkedin.com/in/salmannaqvi/" 
                target="_blank" 
                rel="noopener noreferrer"
                className="inline-flex items-center text-indigo-600 hover:text-indigo-800 font-medium"
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                {t('about.linkedinConnect')}
              </a>
            </div>
            <blockquote className="text-lg italic text-gray-700 mb-6">
              "{t('about.quote')}"
            </blockquote>
          </div>

          {/* Mission Alignment */}
          <div id="mission" className="grid md:grid-cols-3 gap-6 mb-8">
            <div className="text-center">
              <Globe className="w-12 h-12 text-indigo-600 mx-auto mb-3" />
              <h3 className="font-semibold text-gray-900 mb-2">{t('about.globalTransparency')}</h3>
              <p className="text-gray-600 text-sm">{t('about.globalTransparencyDesc')}</p>
            </div>
            <div className="text-center">
              <Users className="w-12 h-12 text-indigo-600 mx-auto mb-3" />
              <h3 className="font-semibold text-gray-900 mb-2">{t('about.humanRights')}</h3>
              <p className="text-gray-600 text-sm">{t('about.humanRightsDesc')}</p>
            </div>
            <div className="text-center">
              <Shield className="w-12 h-12 text-indigo-600 mx-auto mb-3" />
              <h3 className="font-semibold text-gray-900 mb-2">{t('about.antiCorruption')}</h3>
              <p className="text-gray-600 text-sm">{t('about.antiCorruptionDesc')}</p>
            </div>
          </div>

          {/* Connected Projects */}
          <div id="projects" className="border-t pt-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">{t('about.connectedProjects')}</h3>
            <div className="grid md:grid-cols-2 gap-4">
              <a 
                href="https://www.ministryofwoke.com" 
                target="_blank" 
                rel="noopener noreferrer"
                className="p-4 border border-gray-200 rounded-lg hover:border-indigo-300 hover:shadow-md transition-all"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-semibold text-gray-900">{t('about.ministryOfWoke')}</h4>
                    <p className="text-gray-600 text-sm">{t('about.ministryOfWokeDesc')}</p>
                  </div>
                  <ExternalLink className="w-4 h-4 text-gray-400" />
                </div>
              </a>
              
              <a 
                href="https://www.salmannaqvi.com" 
                target="_blank" 
                rel="noopener noreferrer"
                className="p-4 border border-gray-200 rounded-lg hover:border-indigo-300 hover:shadow-md transition-all"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-semibold text-gray-900">{t('about.salmanNaqvi')}</h4>
                    <p className="text-gray-600 text-sm">{t('about.salmanNaqviDesc')}</p>
                  </div>
                  <ExternalLink className="w-4 h-4 text-gray-400" />
                </div>
              </a>
              
              <a 
                href="https://www.acetheinterview.com" 
                target="_blank" 
                rel="noopener noreferrer"
                className="p-4 border border-gray-200 rounded-lg hover:border-indigo-300 hover:shadow-md transition-all"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-semibold text-gray-900">{t('about.aceTheInterview')}</h4>
                    <p className="text-gray-600 text-sm">{t('about.aceTheInterviewDesc')}</p>
                  </div>
                  <ExternalLink className="w-4 h-4 text-gray-400" />
                </div>
              </a>
              
              <a 
                href="https://ministryofwoke.com/contact/" 
                target="_blank" 
                rel="noopener noreferrer"
                className="p-4 border border-gray-200 rounded-lg hover:border-indigo-300 hover:shadow-md transition-all"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-semibold text-gray-900">{t('about.connect')}</h4>
                    <p className="text-gray-600 text-sm">{t('about.connectDesc')}</p>
                  </div>
                  <ExternalLink className="w-4 h-4 text-gray-400" />
                </div>
              </a>
            </div>
          </div>
        </div>

        {/* Mission Statement */}
        <div id="mission-statement" className="bg-white text-gray-800 rounded-lg shadow-lg p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">{t('about.missionTitle')}</h2>
          
          <div className="prose prose-lg text-gray-700 space-y-4">
            <p>
              {t('about.missionDesc1')}
            </p>
            
            <p>
              {t('about.missionDesc2')}
            </p>
            
            <p>
              {t('about.missionDesc3')}
            </p>
          </div>
        </div>

        {/* Platform Features */}
        <div id="technical" className="bg-white text-gray-800 rounded-lg shadow-lg p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">{t('about.platformFeaturesTitle')}</h2>
          
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">{t('about.featureAnonymousSecure')}</h3>
              <p className="text-gray-600">
                {t('about.featureAnonymousSecureDesc')}
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">{t('about.featureGlobalAccess')}</h3>
              <p className="text-gray-600">
                {t('about.featureGlobalAccessDesc')}
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">{t('about.featureOpenArchive')}</h3>
              <p className="text-gray-600">
                {t('about.featureOpenArchiveDesc')}
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">{t('about.featureFOI')}</h3>
              <p className="text-gray-600">
                {t('about.featureFOIDesc')}
              </p>
            </div>
          </div>
        </div>

        {/* Funding (blank, admin-editable via translations) */}
        <div id="funding" className="bg-white text-gray-800 rounded-lg shadow-lg p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">{t('about.fundingTitle')}</h2>
          <div className="prose prose-lg text-gray-700 space-y-4">
            <p>{t('about.fundingBody')}</p>
          </div>
        </div>

        {/* Hosting on Exoscale */}
        <div id="hosting" className="bg-white text-gray-800 rounded-lg shadow-lg p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">{t('about.hostingTitle')}</h2>
          <div className="prose prose-lg text-gray-700 space-y-4">
            <p>{t('about.hostingBody')}</p>
            <p>
              <a
                className="text-indigo-600 hover:text-indigo-800 underline"
                href="https://github.com/main-salman/haqnow/blob/main/README.md"
                target="_blank"
                rel="noopener noreferrer"
              >
                {t('about.learnMoreDocs')}
              </a>
            </p>
          </div>
        </div>
        </div>
      </div>
      
      {/* Footer */}
      <footer className="border-t border-border bg-muted/10 py-6 mt-8">
        <div className="container mx-auto px-4 flex items-center justify-center">
          <p className="text-sm text-muted-foreground">
            © {new Date().getFullYear()} {t('navigation.brand')}. {t('footer.rights')}
          </p>
        </div>
      </footer>
    </div>
  );
}; 
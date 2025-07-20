import React from 'react';
import { useTranslation } from 'react-i18next';
import { ExternalLink, Globe, Users, Shield } from 'lucide-react';

const AboutPage: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            {t('navigation.about')}
          </h1>
          <div className="w-24 h-1 bg-indigo-600 mx-auto"></div>
        </div>

        {/* Founder Section */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Founded by Salman Naqvi
            </h2>
            <div className="flex justify-center mb-6">
              <a 
                href="https://www.linkedin.com/in/salmannaqvi/" 
                target="_blank" 
                rel="noopener noreferrer"
                className="inline-flex items-center text-indigo-600 hover:text-indigo-800 font-medium"
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                Connect on LinkedIn
              </a>
            </div>
            <blockquote className="text-lg italic text-gray-700 mb-6">
              "I'm passionate about ending wars and human rights of all human beings around the world."
            </blockquote>
          </div>

          {/* Mission Alignment */}
          <div className="grid md:grid-cols-3 gap-6 mb-8">
            <div className="text-center">
              <Globe className="w-12 h-12 text-indigo-600 mx-auto mb-3" />
              <h3 className="font-semibold text-gray-900 mb-2">Global Transparency</h3>
              <p className="text-gray-600 text-sm">Exposing corruption worldwide through document disclosure</p>
            </div>
            <div className="text-center">
              <Users className="w-12 h-12 text-indigo-600 mx-auto mb-3" />
              <h3 className="font-semibold text-gray-900 mb-2">Human Rights</h3>
              <p className="text-gray-600 text-sm">Protecting civilians through accountability and transparency</p>
            </div>
            <div className="text-center">
              <Shield className="w-12 h-12 text-indigo-600 mx-auto mb-3" />
              <h3 className="font-semibold text-gray-900 mb-2">Anti-Corruption</h3>
              <p className="text-gray-600 text-sm">Fighting systemic corruption through evidence-based exposure</p>
            </div>
          </div>

          {/* Connected Projects */}
          <div className="border-t pt-6">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">Connected Projects</h3>
            <div className="grid md:grid-cols-2 gap-4">
              <a 
                href="https://www.ministryofwoke.com" 
                target="_blank" 
                rel="noopener noreferrer"
                className="p-4 border border-gray-200 rounded-lg hover:border-indigo-300 hover:shadow-md transition-all"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-semibold text-gray-900">Ministry of Woke</h4>
                    <p className="text-gray-600 text-sm">Anti-corruption advocacy platform</p>
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
                    <h4 className="font-semibold text-gray-900">Salman Naqvi</h4>
                    <p className="text-gray-600 text-sm">Personal website and portfolio</p>
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
                    <h4 className="font-semibold text-gray-900">Ace The Interview</h4>
                    <p className="text-gray-600 text-sm">Professional development platform</p>
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
                    <h4 className="font-semibold text-gray-900">Connect</h4>
                    <p className="text-gray-600 text-sm">Get in touch directly</p>
                  </div>
                  <ExternalLink className="w-4 h-4 text-gray-400" />
                </div>
              </a>
            </div>
          </div>
        </div>

        {/* Mission Statement */}
        <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Our Anti-Corruption Mission</h2>
          
          <div className="prose prose-lg text-gray-700 space-y-4">
            <p>
              HaqNow.com emerges from a deep commitment to ending systemic corruption that fuels conflicts, 
              undermines human rights, and perpetuates global inequality. Through the power of transparency 
              and document disclosure, we believe that exposing corruption is one of the most effective ways 
              to protect civilians, end wars, and advance human rights worldwide.
            </p>
            
            <p>
              Corruption thrives in darkness, protected by secrecy and enabled by those who profit from 
              inequality and conflict. When corrupt officials, defense contractors, and political elites 
              operate without accountability, the result is often devastating: unnecessary wars, human rights 
              abuses, and the systematic exploitation of vulnerable populations. By creating a secure, 
              anonymous platform for whistleblowers and truth-tellers, HaqNow.com aims to shine light on 
              these dark practices.
            </p>
            
            <p>
              Our work is rooted in the understanding that transparency is not just a democratic ideal—it's 
              a tool for peace and justice. Every document exposed, every corrupt scheme revealed, and every 
              truth brought to light contributes to a world where accountability replaces impunity, where 
              human rights are protected, and where the powerful can no longer operate with complete disregard 
              for human suffering.
            </p>
          </div>
        </div>

        {/* Platform Features */}
        <div className="bg-white rounded-lg shadow-lg p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Platform Features</h2>
          
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Anonymous & Secure</h3>
              <p className="text-gray-600">
                Advanced encryption and anonymization to protect whistleblowers and sources.
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Global Accessibility</h3>
              <p className="text-gray-600">
                Multi-language support including Arabic, French, German, Russian, Polish, and Turkish.
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Open Archive</h3>
              <p className="text-gray-600">
                Searchable database of corruption documents accessible to journalists and researchers.
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Freedom of Information</h3>
              <p className="text-gray-600">
                Comprehensive FOI resources to help citizens demand transparency from their governments.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AboutPage; 
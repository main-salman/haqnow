import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertTriangle, Shield, Eye, Globe, ArrowLeft } from 'lucide-react';

const DisclaimerPage: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation();

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
          Back to Home
        </Button>

        {/* Main Warning Card */}
        <Card className="border-red-200 shadow-lg mb-8">
          <CardHeader className="bg-gradient-to-r from-red-500 to-orange-500 text-white">
            <CardTitle className="text-2xl font-bold flex items-center">
              <AlertTriangle className="h-8 w-8 mr-3" />
              Important Security Disclaimer
            </CardTitle>
          </CardHeader>
          <CardContent className="p-8">
            <div className="prose prose-lg max-w-none">
              <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-8">
                <h3 className="text-xl font-bold text-red-800 mb-4 flex items-center">
                  <Shield className="h-6 w-6 mr-2" />
                  Corporate & Government Computer Warning
                </h3>
                <p className="text-red-700 font-medium mb-4">
                  <strong>DO NOT upload documents from your corporate or government computer.</strong>
                </p>
                <p className="text-red-600 mb-4">
                  Corporations use Data Loss Prevention (DLP) and other similar security software that monitor 
                  <strong> ALL activity</strong>, including what is supposed to be encrypted activity, like logging 
                  into your personal bank account. Your IT department will be able to see:
                </p>
                <ul className="list-disc list-inside text-red-600 space-y-2 ml-4">
                  <li>Whether you visited this website from your corporate computer</li>
                  <li>If you uploaded a document or not</li>
                  <li>Your browsing patterns and activity</li>
                  <li>File access and transfer activities</li>
                </ul>
              </div>

              <div className="bg-orange-50 border border-orange-200 rounded-lg p-6 mb-8">
                <h3 className="text-xl font-bold text-orange-800 mb-4 flex items-center">
                  <Globe className="h-6 w-6 mr-2" />
                  High-Risk Country Warning
                </h3>
                <p className="text-orange-700 font-medium mb-4">
                  In some countries like <strong>Saudi Arabia, China, Iran, Qatar, and Bahrain</strong>, 
                  all internet activities are monitored. You must be extra careful.
                </p>
                <div className="bg-orange-100 border border-orange-300 rounded-md p-4 mb-4">
                  <h4 className="font-semibold text-orange-800 mb-2">In these countries:</h4>
                  <ul className="list-disc list-inside text-orange-700 space-y-1 ml-4">
                    <li>Authorities can see that you visited this website, even from a home computer</li>
                    <li>They may not be able to tell if you uploaded a document (due to encryption)</li>
                    <li>Consider using additional privacy tools (VPN, Tor) for extra protection</li>
                    <li>Be aware of local laws regarding document disclosure and whistleblowing</li>
                  </ul>
                </div>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
                <h3 className="text-xl font-bold text-blue-800 mb-4 flex items-center">
                  <Eye className="h-6 w-6 mr-2" />
                  Privacy Best Practices
                </h3>
                <ul className="list-disc list-inside text-blue-700 space-y-2 ml-4">
                  <li><strong>Use a personal device</strong> - Never use work or government computers</li>
                  <li><strong>Use a secure network</strong> - Avoid public WiFi when possible</li>
                  <li><strong>Consider additional privacy tools</strong> - VPN, Tor browser for high-risk situations</li>
                  <li><strong>Clear browser data</strong> - After visiting, clear your browsing history and cookies</li>
                  <li><strong>Be aware of your environment</strong> - Ensure physical privacy when uploading</li>
                </ul>
              </div>

              <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                <h3 className="text-xl font-bold text-green-800 mb-4">Our Privacy Commitment</h3>
                <p className="text-green-700 mb-4">
                  HaqNow.com provides complete anonymity for document uploads:
                </p>
                <ul className="list-disc list-inside text-green-700 space-y-1 ml-4">
                  <li>We never store IP addresses</li>
                  <li>We never log user activity</li>
                  <li>All uploads are completely anonymous</li>
                  <li>No personal information is required or stored</li>
                </ul>
                <p className="text-green-600 mt-4 font-medium">
                  However, your own security practices are crucial for maintaining your anonymity.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button 
            onClick={() => navigate('/privacy-guaranteed')}
            variant="outline"
            className="border-blue-300 text-blue-700 hover:bg-blue-50"
          >
            Learn More About Our Privacy Protections
          </Button>
          <Button 
            onClick={() => navigate('/')}
            className="bg-green-600 hover:bg-green-700 text-white"
          >
            I Understand - Continue to Homepage
          </Button>
        </div>
      </div>
    </div>
  );
};

export default DisclaimerPage; 
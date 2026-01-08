import React from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation, Trans } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { 
  ArrowLeft, 
  Shield, 
  Lock, 
  Eye, 
  Server, 
  Database, 
  FileText, 
  Github, 
  ExternalLink,
  CheckCircle,
  Users,
  Download,
  Upload,
  Trash2
} from "lucide-react";
import Navigation from "@/components/Navigation";

export default function PrivacyGuaranteedPage() {
  const navigate = useNavigate();
  const { t } = useTranslation();

  const privacyFeatures = [
    {
      icon: <Database className="h-6 w-6" />,
      title: t('privacy.cardZeroIpStorage'),
      description: t('privacy.cardZeroIpDescription'),
      githubLink: "https://github.com/main-salman/haqnow/blob/main/backend/app/database/models.py"
    },
    {
      icon: <Shield className="h-6 w-6" />,
      title: t('privacy.cardAnonymousInterface'),
      description: t('privacy.cardAnonymousDescription'),
      githubLink: "https://github.com/main-salman/haqnow/blob/main/frontend/src/pages/AdminApprovedDocumentsPage.tsx"
    },
    {
      icon: <FileText className="h-6 w-6" />,
      title: t('privacy.cardPrivacyFirstUpload'),
      description: t('privacy.cardPrivacyFirstDescription'),
      githubLink: "https://github.com/main-salman/haqnow/blob/main/backend/app/apis/file_uploader/__init__.py"
    },
    {
      icon: <Server className="h-6 w-6" />,
      title: t('privacy.cardCleanServerLogs'),
      description: t('privacy.cardCleanServerDescription'),
      githubLink: "https://github.com/main-salman/haqnow/blob/main/backend/app/middleware/rate_limit.py"
    },
    {
      icon: <Shield className="h-6 w-6" />,
      title: "Complete Metadata Removal",
      description: "All uploaded documents are automatically stripped of metadata and converted to clean PDFs. Original files are never stored, ensuring no identifying information can trace back to uploaders.",
      githubLink: "https://github.com/main-salman/haqnow/blob/main/backend/app/services/metadata_service.py"
    }
  ];

  const privacyGuarantees = [
    t('privacy.guaranteeNeverLog'),
    t('privacy.guaranteeNeverStore'),
    t('privacy.guaranteeNeverTrack'),
    t('privacy.guaranteeNeverShare'),
    t('privacy.guaranteeNeverRequire'),
    t('privacy.guaranteeNeverCompromise'),
    t('privacy.guaranteeNeverKeepMetadata')
  ];

  const technicalLayers = [
    {
      layer: "Document Processing Layer",
      description: "Automatic metadata stripping and PDF conversion for all uploads",
      status: "✅ COMPLETED"
    },
    {
      layer: "Database Layer",
      description: "Complete IP storage removal and migration",
      status: "✅ COMPLETED"
    },
    {
      layer: "Application Layer",
      description: "Anonymous APIs and interfaces",
      status: "✅ COMPLETED"
    },
    {
      layer: "Web Server Layer",
      description: "Custom log formats and header filtering",
      status: "✅ COMPLETED"
    },
    {
      layer: "System Layer",
      description: "Log filtering and retention policies",
      status: "✅ COMPLETED"
    },
    {
      layer: "Network Layer",
      description: "Proxy downloads and URL masking",
      status: "✅ COMPLETED"
    },
    {
      layer: "Client Layer",
      description: "Clean browser console and masked URLs",
      status: "✅ COMPLETED"
    }
  ];

  return (
    <div className="min-h-screen bg-white">
      <Navigation />
      <div className="p-4 md:p-8">
        <div className="container mx-auto max-w-4xl space-y-8">
          {/* Header */}
          <header className="py-6 px-4 md:px-8 border-b border-border">
            <div className="container mx-auto">
            <div className="text-center">
              <div className="flex items-center justify-center space-x-2 mb-4">
                <Shield className="h-8 w-8 text-primary" />
                <h1 className="text-4xl font-bold font-serif">{t('privacy.title')}</h1>
              </div>
              <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
                {t('privacy.subtitle')}
              </p>
            </div>
          </div>
        </header>

        <main className="container mx-auto px-4 py-8 md:py-12 max-w-6xl">
          {/* Privacy Guarantees Section */}
          <section className="mb-12">
            <Card className="border-primary/20 bg-primary/5">
              <CardHeader className="text-center">
                <CardTitle className="text-2xl font-serif flex items-center justify-center space-x-2">
                  <Lock className="h-6 w-6" />
                  <span>{t('privacy.sectionPrivacyGuarantees')}</span>
                </CardTitle>
                <CardDescription className="text-lg">
                  {t('privacy.commitmentsIntro')}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {privacyGuarantees.map((guarantee, index) => (
                    <div key={index} className="flex items-start space-x-3">
                      <CheckCircle className="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0" />
                      <span className="font-medium">{guarantee}</span>
                    </div>
                  ))}
                </div>
                <div className="mt-6 p-4 bg-green-50 dark:bg-green-950/20 rounded-lg border border-green-200 dark:border-green-800">
                  <p className="text-center font-semibold text-green-800 dark:text-green-200">
                    🛡️ Maximum protection for whistleblowers exposing corruption worldwide
                  </p>
                </div>
              </CardContent>
            </Card>
          </section>

          {/* Privacy Features Section */}
          <section className="mb-12">
            <h2 className="text-3xl font-bold font-serif text-center mb-8">Privacy Implementation</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {privacyFeatures.map((feature, index) => (
                <Card key={index} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <CardTitle className="flex items-center space-x-3">
                      <div className="p-2 bg-primary/10 rounded-lg text-primary">
                        {feature.icon}
                      </div>
                      <span>{feature.title}</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-muted-foreground mb-4">{feature.description}</p>
                    <Button variant="outline" size="sm" asChild>
                      <a href={feature.githubLink} target="_blank" rel="noopener noreferrer">
                        <Github className="h-4 w-4 mr-2" />
                        View Code
                        <ExternalLink className="h-3 w-3 ml-1" />
                      </a>
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>

          {/* Metadata Stripping Process */}
          <section className="mb-12">
            <Card className="border-blue-200 bg-blue-50 dark:bg-blue-950/20 dark:border-blue-800">
              <CardHeader className="text-center">
                <CardTitle className="text-2xl font-serif flex items-center justify-center space-x-2">
                  <Shield className="h-6 w-6 text-blue-600" />
                  <span>Document Privacy Protection Process</span>
                </CardTitle>
                <CardDescription className="text-lg">
                  How we remove metadata from all uploaded documents
                </CardDescription>
              </CardHeader>
              <CardContent>
                {/* Process Diagram */}
                <div className="bg-white dark:bg-gray-900 rounded-lg p-6 mb-6 border border-gray-200 dark:border-gray-700">
                  <div className="flex flex-col space-y-4">
                    {/* Step 1: Upload */}
                    <div className="flex items-center">
                      <div className="flex items-center space-x-3 flex-1">
                        <div className="flex items-center justify-center w-10 h-10 bg-blue-100 dark:bg-blue-900 rounded-full">
                          <Upload className="h-5 w-5 text-blue-600 dark:text-blue-400" />
                        </div>
                        <div>
                          <h4 className="font-semibold">1. File Upload</h4>
                          <p className="text-sm text-gray-600 dark:text-gray-400">User uploads document (PDF, Word, Excel, Image, etc.)</p>
                        </div>
                      </div>
                    </div>

                    {/* Step 2: Processing */}
                    <div className="flex items-center">
                      <div className="flex items-center space-x-3 flex-1">
                        <div className="flex items-center justify-center w-10 h-10 bg-orange-100 dark:bg-orange-900 rounded-full">
                          <Shield className="h-5 w-5 text-orange-600 dark:text-orange-400" />
                        </div>
                        <div>
                          <h4 className="font-semibold">2. Metadata Stripping</h4>
                          <p className="text-sm text-gray-600 dark:text-gray-400">Automatic removal of EXIF data, author info, creation dates, GPS coordinates</p>
                        </div>
                      </div>
                    </div>

                    {/* Step 3: Conversion */}
                    <div className="flex items-center">
                      <div className="flex items-center space-x-3 flex-1">
                        <div className="flex items-center justify-center w-10 h-10 bg-green-100 dark:bg-green-900 rounded-full">
                          <FileText className="h-5 w-5 text-green-600 dark:text-green-400" />
                        </div>
                        <div>
                          <h4 className="font-semibold">3. PDF Conversion</h4>
                          <p className="text-sm text-gray-600 dark:text-gray-400">Convert to clean, standardized PDF format with zero metadata</p>
                        </div>
                      </div>
                    </div>

                    {/* Step 4: Storage */}
                    <div className="flex items-center">
                      <div className="flex items-center space-x-3 flex-1">
                        <div className="flex items-center justify-center w-10 h-10 bg-purple-100 dark:bg-purple-900 rounded-full">
                          <Database className="h-5 w-5 text-purple-600 dark:text-purple-400" />
                        </div>
                        <div>
                          <h4 className="font-semibold">4. Secure Storage</h4>
                          <p className="text-sm text-gray-600 dark:text-gray-400">Only clean PDF stored in database - original file never saved</p>
                        </div>
                      </div>
                    </div>

                    {/* Step 5: Deletion */}
                    <div className="flex items-center">
                      <div className="flex items-center space-x-3 flex-1">
                        <div className="flex items-center justify-center w-10 h-10 bg-red-100 dark:bg-red-900 rounded-full">
                          <Trash2 className="h-5 w-5 text-red-600 dark:text-red-400" />
                        </div>
                        <div>
                          <h4 className="font-semibold">5. Original Deletion</h4>
                          <p className="text-sm text-gray-600 dark:text-gray-400">Original file permanently deleted from memory - no traces remain</p>
                        </div>
                      </div>
                    </div>

                    {/* Step 6: Download */}
                    <div className="flex items-center">
                      <div className="flex items-center space-x-3 flex-1">
                        <div className="flex items-center justify-center w-10 h-10 bg-teal-100 dark:bg-teal-900 rounded-full">
                          <Download className="h-5 w-5 text-teal-600 dark:text-teal-400" />
                        </div>
                        <div>
                          <h4 className="font-semibold">6. Clean Download</h4>
                          <p className="text-sm text-gray-600 dark:text-gray-400">Users download metadata-free PDF with complete privacy protection</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Key Points */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-green-50 dark:bg-green-950/20 rounded-lg border border-green-200 dark:border-green-800">
                    <h4 className="font-semibold text-green-800 dark:text-green-200 mb-2">✅ What Gets Removed</h4>
                    <ul className="text-sm text-green-700 dark:text-green-300 space-y-1">
                      <li>• Author names and organizations</li>
                      <li>• GPS coordinates from photos</li>
                      <li>• Creation and modification dates</li>
                      <li>• Software version information</li>
                      <li>• Device and computer names</li>
                      <li>• Document revision history</li>
                    </ul>
                  </div>
                  <div className="p-4 bg-blue-50 dark:bg-blue-950/20 rounded-lg border border-blue-200 dark:border-blue-800">
                    <h4 className="font-semibold text-blue-800 dark:text-blue-200 mb-2">🔒 When Original Is Deleted</h4>
                    <p className="text-sm text-blue-700 dark:text-blue-300">
                      The original file is <strong>NEVER stored</strong> on our servers. It exists only in temporary memory during the conversion process (seconds) and is immediately discarded after the clean PDF is created.
                    </p>
                  </div>
                </div>

                <div className="mt-6 p-4 bg-amber-50 dark:bg-amber-950/20 rounded-lg border border-amber-200 dark:border-amber-800">
                  <p className="text-center font-semibold text-amber-800 dark:text-amber-200">
                    ⚡ <strong>Real-time Processing:</strong> Metadata stripping happens instantly during upload. Original files are processed and discarded within seconds, leaving zero traces.
                  </p>
                </div>
              </CardContent>
            </Card>
          </section>

          {/* Technical Implementation */}
          <section className="mb-12">
            <Card>
              <CardHeader>
                <CardTitle className="text-2xl font-serif text-center">Infrastructure-Wide Privacy Protection</CardTitle>
                <CardDescription className="text-center">
                  Privacy protections implemented across every layer of our technology stack
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {technicalLayers.map((layer, index) => (
                    <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                      <div>
                        <h4 className="font-semibold">{layer.layer}</h4>
                        <p className="text-sm text-muted-foreground">{layer.description}</p>
                      </div>
                      <Badge variant="secondary" className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                        {layer.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </section>

          {/* Open Source Verification */}
          <section className="mb-12">
            <Card className="border-blue-200 bg-blue-50/50 dark:border-blue-800 dark:bg-blue-950/20">
              <CardHeader>
                <CardTitle className="text-2xl font-serif flex items-center justify-center space-x-2">
                  <Eye className="h-6 w-6" />
                  <span>Open Source & Transparent</span>
                </CardTitle>
                <CardDescription className="text-center text-lg">
                  Our code is public and open to scrutiny - verify our privacy claims yourself
                </CardDescription>
              </CardHeader>
              <CardContent className="text-center space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Card className="border-0 bg-white/50 dark:bg-gray-800/50">
                    <CardContent className="pt-6">
                      <Github className="h-8 w-8 mx-auto mb-2 text-gray-700 dark:text-gray-300" />
                      <h4 className="font-semibold mb-2">Full Source Code</h4>
                      <p className="text-sm text-muted-foreground mb-4">
                        Every line of code is public and auditable
                      </p>
                      <Button variant="outline" size="sm" asChild>
                        <a href="https://github.com/main-salman/haqnow" target="_blank" rel="noopener noreferrer">
                          View Repository
                          <ExternalLink className="h-3 w-3 ml-1" />
                        </a>
                      </Button>
                    </CardContent>
                  </Card>

                  <Card className="border-0 bg-white/50 dark:bg-gray-800/50">
                    <CardContent className="pt-6">
                      <FileText className="h-8 w-8 mx-auto mb-2 text-gray-700 dark:text-gray-300" />
                      <h4 className="font-semibold mb-2">Privacy Implementation</h4>
                      <p className="text-sm text-muted-foreground mb-4">
                        Detailed privacy code examples and documentation
                      </p>
                      <Button variant="outline" size="sm" asChild>
                        <a href="https://github.com/main-salman/haqnow/blob/main/README.md#privacy-compliance--anonymity-guarantees" target="_blank" rel="noopener noreferrer">
                          View Privacy Docs
                          <ExternalLink className="h-3 w-3 ml-1" />
                        </a>
                      </Button>
                    </CardContent>
                  </Card>

                  <Card className="border-0 bg-white/50 dark:bg-gray-800/50">
                    <CardContent className="pt-6">
                      <Server className="h-8 w-8 mx-auto mb-2 text-gray-700 dark:text-gray-300" />
                      <h4 className="font-semibold mb-2">Infrastructure Config</h4>
                      <p className="text-sm text-muted-foreground mb-4">
                        Server configurations and deployment scripts
                      </p>
                      <Button variant="outline" size="sm" asChild>
                        <a href="https://github.com/main-salman/haqnow/tree/main/terraform" target="_blank" rel="noopener noreferrer">
                          View Infrastructure
                          <ExternalLink className="h-3 w-3 ml-1" />
                        </a>
                      </Button>
                    </CardContent>
                  </Card>
                </div>

                <div className="mt-8 p-6 bg-white/70 dark:bg-gray-800/70 rounded-lg border">
                  <h3 className="text-lg font-semibold mb-4">Key Privacy Code Examples</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
                    <div>
                      <h4 className="font-medium mb-2">🗄️ Database Privacy</h4>
                      <code className="text-xs bg-gray-100 dark:bg-gray-800 p-2 rounded block mb-2">
                        # uploader_ip column completely removed<br/>
                        # to_dict() excludes IP from responses
                      </code>
                      <Button variant="link" size="sm" className="p-0 h-auto" asChild>
                        <a href="https://github.com/main-salman/haqnow/blob/main/backend/app/database/models.py#L20-L50" target="_blank" rel="noopener noreferrer">
                          View Database Model <ExternalLink className="h-3 w-3 ml-1" />
                        </a>
                      </Button>
                    </div>
                    <div>
                      <h4 className="font-medium mb-2">🌐 Nginx Privacy</h4>
                      <code className="text-xs bg-gray-100 dark:bg-gray-800 p-2 rounded block mb-2">
                        log_format privacy_log '$time_local "$request"'<br/>
                        # No $remote_addr (IP) logged
                      </code>
                      <Button variant="link" size="sm" className="p-0 h-auto" asChild>
                        <a href="https://github.com/main-salman/haqnow/blob/main/history.txt#L950-L980" target="_blank" rel="noopener noreferrer">
                          View Server Config <ExternalLink className="h-3 w-3 ml-1" />
                        </a>
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </section>

          {/* Collaboration Section */}
          <section className="mb-12">
            <Card className="border-purple-200 bg-purple-50/50 dark:border-purple-800 dark:bg-purple-950/20">
              <CardHeader>
                <CardTitle className="text-2xl font-serif flex items-center justify-center space-x-2">
                  <Users className="h-6 w-6" />
                  <span>Trusted Collaborators Welcome</span>
                </CardTitle>
                <CardDescription className="text-center text-lg">
                  Join our mission to fight corruption through technology and transparency
                </CardDescription>
              </CardHeader>
              <CardContent className="text-center space-y-6">
                <div className="prose dark:prose-invert mx-auto">
                  <p className="text-lg">
                    HaqNow.com is committed to fighting corruption worldwide through anonymous document exposure. 
                    We welcome security researchers, privacy advocates, journalists, and developers who share our mission.
                  </p>
                  <p>
                    If you're interested in collaborating on privacy-focused anti-corruption technology, 
                    contributing security audits, or partnering with our transparency initiatives, we'd love to hear from you.
                  </p>
                </div>
                
                <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                  <Button asChild className="min-w-[200px]">
                    <a href="https://freedom-advocacy.net/contact" target="_blank" rel="noopener noreferrer">
                      <Users className="h-4 w-4 mr-2" />
                      Connect with Us
                      <ExternalLink className="h-3 w-3 ml-1" />
                    </a>
                  </Button>
                  <Button variant="outline" asChild className="min-w-[200px]">
                    <a href="https://github.com/main-salman/haqnow/issues" target="_blank" rel="noopener noreferrer">
                      <Github className="h-4 w-4 mr-2" />
                      Report Issues
                      <ExternalLink className="h-3 w-3 ml-1" />
                    </a>
                  </Button>
                </div>

                <div className="mt-6 p-4 bg-purple-100 dark:bg-purple-900/30 rounded-lg">
                  <p className="text-sm font-medium">
                    <strong>Areas of Interest:</strong> Security auditing, privacy technology, 
                    anti-corruption journalism, transparency tools, whistleblower protection, 
                    and global corruption research.
                  </p>
                </div>
              </CardContent>
            </Card>
          </section>

          {/* Technical Details */}
          <section>
            <Card>
              <CardHeader>
                <CardTitle className="text-2xl font-serif text-center">Complete Privacy Verification</CardTitle>
                <CardDescription className="text-center">
                  All 8 privacy tasks completed with full documentation
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-3">
                    <h4 className="font-semibold text-green-600 dark:text-green-400">✅ Application Level</h4>
                    <ul className="space-y-2 text-sm">
                      <li>• Remove uploader_ip column from database</li>
                      <li>• Remove IP storage from upload API</li>
                      <li>• Remove IP from email notifications</li>
                      <li>• Remove IP from application logging</li>
                      <li>• Remove IP from admin interfaces</li>
                    </ul>
                  </div>
                  <div className="space-y-3">
                    <h4 className="font-semibold text-green-600 dark:text-green-400">✅ Infrastructure Level</h4>
                    <ul className="space-y-2 text-sm">
                      <li>• Update rate limiting (anonymous system)</li>
                      <li>• Configure nginx (no IP logs)</li>
                      <li>• Configure system logs (filtered)</li>
                    </ul>
                    <h4 className="font-semibold text-blue-600 dark:text-blue-400 mt-4">🔒 Additional</h4>
                    <ul className="space-y-2 text-sm">
                      <li>• URL masking for downloads</li>
                      <li>• Clean browser console logs</li>
                    </ul>
                  </div>
                </div>
                
                <Separator className="my-6" />
                
                <div className="text-center">
                  <p className="text-lg font-semibold mb-4">
                    🌍 <strong>TOTAL INFRASTRUCTURE-WIDE ANONYMITY ACHIEVED</strong>
                  </p>
                  <p className="text-muted-foreground">
                    From database storage to web server logs to system logs - no IP addresses are stored, 
                    logged, or tracked anywhere in the entire infrastructure.
                  </p>
                </div>
              </CardContent>
            </Card>
          </section>
        </main>
        
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
      </div>
    </div>
  );
} 
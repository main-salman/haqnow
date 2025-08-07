import React, { useState, useCallback, useEffect } from "react";
// Remove Supabase import - we don't use it anymore
// import { supabase } from "../utils/supabaseClient";
// Remove brain import - we'll use direct fetch instead
// import brain from "../brain";
// import { v4 as uuidv4 } from 'uuid'; // Not available, will use Date.now() + random string
import { useDropzone } from "react-dropzone";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { UploadCloud, FileText, AlertCircle, CheckCircle, Loader2, Shield, ArrowLeft, Camera, Smartphone, AlertTriangle } from "lucide-react";
import { toast } from "sonner";
import { countriesData, Country, State } from "utils/countriesData"; // Added
import HCaptcha from '@hcaptcha/react-hcaptcha';
import Navigation from "@/components/Navigation";

// Mock data - replace with API calls or more robust data source later
// const mockCountries = [
//   { id: "us", name: "United States" },
//   { id: "ca", name: "Canada" },
//   { id: "gb", name: "United Kingdom" },
//   { id: "au", name: "Australia" },
//   // Add more countries as needed
// ];

// const mockStatesProvinces: { [countryId: string]: { id: string, name: string }[] } = {
//   us: [
//     { id: "ca", name: "California" },
//     { id: "ny", name: "New York" },
//     { id: "tx", name: "Texas" },
//   ],
//   ca: [
//     { id: "on", name: "Ontario" },
//     { id: "qc", name: "Quebec" },
//     { id: "bc", name: "British Columbia" },
//   ],
//   gb: [
//     { id: "eng", name: "England" },
//     { id: "sct", name: "Scotland" },
//     { id: "wls", name: "Wales" },
//   ],
//   au: [
//     { id: "nsw", name: "New South Wales" },
//     { id: "vic", name: "Victoria" },
//     { id: "qld", name: "Queensland" },
//   ],
// };

const adminLevels = [
  { id: "federal", name: "Federal / National" },
  { id: "state", name: "State / Provincial / Regional" },
  // { id: "local", name: "Local / Municipal" }, // Future option?
];

export interface FormData {
  title: string;
  description: string;
  country: string;
  stateProvince: string;
  adminLevel: string;
  documentLanguage: string;  // Added document language field
  file: File | null;
}

export default function UploadDocumentPage() {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [formData, setFormData] = useState<FormData>({
    title: "",
    description: "",
    country: "",
    stateProvince: "",
    adminLevel: "",
    documentLanguage: "english",  // Default to English
    file: null,
  });
  const [currentStates, setCurrentStates] = useState<State[]>([]); // Changed type to State[]
  const [errors, setErrors] = useState<Partial<Record<keyof FormData | 'captcha', string>>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [captchaToken, setCaptchaToken] = useState<string | null>(null);
  const [isCameraMode, setIsCameraMode] = useState(false);
  const [showCameraDisclaimer, setShowCameraDisclaimer] = useState(false);
  const [capturedPhotos, setCapturedPhotos] = useState<File[]>([]);

  // Available document languages - comprehensive list for all supported OCR languages
  const documentLanguages = [
    // Major world languages
    { value: "english", label: "English" },
    { value: "arabic", label: "العربية (Arabic)" },
    { value: "chinese_simplified", label: "中文简体 (Chinese Simplified)" },
    { value: "chinese_traditional", label: "中文繁體 (Chinese Traditional)" },
    { value: "french", label: "Français (French)" },
    { value: "german", label: "Deutsch (German)" },
    { value: "spanish", label: "Español (Spanish)" },
    { value: "russian", label: "Русский (Russian)" },
    { value: "hindi", label: "हिन्दी (Hindi)" },
    { value: "japanese", label: "日本語 (Japanese)" },
    { value: "korean", label: "한국어 (Korean)" },
    { value: "portuguese", label: "Português (Portuguese)" },
    { value: "italian", label: "Italiano (Italian)" },
    { value: "polish", label: "Polski (Polish)" },
    { value: "turkish", label: "Türkçe (Turkish)" },
    { value: "dutch", label: "Nederlands (Dutch)" },
    { value: "vietnamese", label: "Tiếng Việt (Vietnamese)" },
    { value: "thai", label: "ไทย (Thai)" },
    { value: "ukrainian", label: "Українська (Ukrainian)" },
    
    // European languages
    { value: "bulgarian", label: "Български (Bulgarian)" },
    { value: "croatian", label: "Hrvatski (Croatian)" },
    { value: "czech", label: "Čeština (Czech)" },
    { value: "danish", label: "Dansk (Danish)" },
    { value: "estonian", label: "Eesti (Estonian)" },
    { value: "finnish", label: "Suomi (Finnish)" },
    { value: "greek", label: "Ελληνικά (Greek)" },
    { value: "hungarian", label: "Magyar (Hungarian)" },
    { value: "icelandic", label: "Íslenska (Icelandic)" },
    { value: "latvian", label: "Latviešu (Latvian)" },
    { value: "lithuanian", label: "Lietuvių (Lithuanian)" },
    { value: "norwegian", label: "Norsk (Norwegian)" },
    { value: "romanian", label: "Română (Romanian)" },
    { value: "serbian", label: "Српски (Serbian)" },
    { value: "slovak", label: "Slovenčina (Slovak)" },
    { value: "slovenian", label: "Slovenščina (Slovenian)" },
    { value: "swedish", label: "Svenska (Swedish)" },
    
    // Asian languages
    { value: "bengali", label: "বাংলা (Bengali)" },
    { value: "gujarati", label: "ગુજરાતી (Gujarati)" },
    { value: "kannada", label: "ಕನ್ನಡ (Kannada)" },
    { value: "malayalam", label: "മലയാളം (Malayalam)" },
    { value: "marathi", label: "मराठी (Marathi)" },
    { value: "nepali", label: "नेपाली (Nepali)" },
    { value: "punjabi", label: "ਪੰਜਾਬੀ (Punjabi)" },
    { value: "tamil", label: "தமிழ் (Tamil)" },
    { value: "telugu", label: "తెలుగు (Telugu)" },
    { value: "urdu", label: "اردو (Urdu)" },
    { value: "persian", label: "فارسی (Persian)" },
    { value: "hebrew", label: "עברית (Hebrew)" },
    { value: "indonesian", label: "Bahasa Indonesia (Indonesian)" },
    { value: "malay", label: "Bahasa Melayu (Malay)" },
    { value: "khmer", label: "ភាសាខ្មែរ (Khmer)" },
    { value: "lao", label: "ລາວ (Lao)" },
    { value: "myanmar", label: "မြန်မာ (Myanmar)" },
    
    // African languages
    { value: "afrikaans", label: "Afrikaans" },
    { value: "amharic", label: "አማርኛ (Amharic)" },
    { value: "swahili", label: "Kiswahili (Swahili)" },
    
    // Other languages
    { value: "azerbaijani", label: "Azərbaycan (Azerbaijani)" },
    { value: "basque", label: "Euskera (Basque)" },
    { value: "belarusian", label: "Беларуская (Belarusian)" },
    { value: "bosnian", label: "Bosanski (Bosnian)" },
    { value: "catalan", label: "Català (Catalan)" },
    { value: "esperanto", label: "Esperanto" },
    { value: "irish", label: "Gaeilge (Irish)" },
    { value: "latin", label: "Latine (Latin)" },
    { value: "macedonian", label: "Македонски (Macedonian)" },
    { value: "maltese", label: "Malti (Maltese)" },
    { value: "welsh", label: "Cymraeg (Welsh)" },
    
    { value: "other", label: "Other (use English OCR)" }
  ];

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles && acceptedFiles.length > 0) {
      const file = acceptedFiles[0];
      
      // Accept all document and image types
      const allowedTypes = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/csv',
        'text/plain',
        'text/rtf',
        'application/rtf',
        'image/jpeg',
        'image/jpg', 
        'image/png',
        'image/gif',
        'image/bmp',
        'image/tiff',
        'image/webp',
        'application/zip',
        'application/x-zip-compressed',
        'application/vnd.oasis.opendocument.text',
        'application/vnd.oasis.opendocument.spreadsheet'
      ];
      
      if (allowedTypes.includes(file.type) || file.name.toLowerCase().match(/\.(pdf|doc|docx|xls|xlsx|csv|txt|rtf|jpg|jpeg|png|gif|bmp|tiff|webp|zip|odt|ods)$/)) {
        setFormData((prev) => ({ ...prev, file }));
        setErrors((prev) => ({ ...prev, file: undefined }));
      } else {
        setErrors((prev) => ({ ...prev, file: "Unsupported file type. Please upload documents, images, or text files." }));
        toast.error("Invalid File Type", { description: "Please upload a supported document or image file." });
      }
    }
  }, []);

  // Function to combine multiple photos into a single ZIP file or handle individually
  const combinePhotosIntoPDF = async (photos: File[]): Promise<File> => {
    if (photos.length === 1) {
      return photos[0];
    }
    
    // For multiple photos, we'll combine them into a single large image
    // This is a simple approach that works better than fake PDFs
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    if (!ctx) {
      throw new Error('Canvas not supported');
    }
    
    // Load all images and calculate total height
    const images = await Promise.all(
      photos.map(photo => {
        return new Promise<HTMLImageElement>((resolve, reject) => {
          const img = new Image();
          img.onload = () => resolve(img);
          img.onerror = reject;
          img.src = URL.createObjectURL(photo);
        });
      })
    );
    
    // Calculate dimensions - use the width of the first image, stack vertically
    const maxWidth = Math.max(...images.map(img => img.width));
    const totalHeight = images.reduce((sum, img) => sum + img.height, 0);
    
    canvas.width = maxWidth;
    canvas.height = totalHeight;
    
    // Draw all images vertically
    let currentY = 0;
    for (const img of images) {
      const x = (maxWidth - img.width) / 2; // Center horizontally
      ctx.drawImage(img, x, currentY);
      currentY += img.height;
    }
    
    // Convert to blob and create file
    return new Promise((resolve) => {
      canvas.toBlob((blob) => {
        if (blob) {
          const combinedName = `document-${photos.length}pages-${Date.now()}.jpg`;
          resolve(new File([blob], combinedName, { type: 'image/jpeg' }));
        }
      }, 'image/jpeg', 0.8);
    });
  };

  // Camera capture functionality
  const handleCameraCapture = async () => {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      toast.error(t('upload.cameraNotSupported'));
      return;
    }

    try {
      setShowCameraDisclaimer(true);
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: 'environment' } // Use back camera on mobile
      });
      
      const video = document.createElement('video');
      const canvas = document.createElement('canvas');
      const context = canvas.getContext('2d');
      
      video.srcObject = stream;
      video.play();
      
      // Create camera modal
      const modal = document.createElement('div');
      modal.className = 'fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center p-4';
      modal.innerHTML = `
        <div class="bg-white rounded-lg p-6 max-w-md w-full">
          <h3 class="text-lg font-semibold mb-4">${t('upload.captureDocument')}</h3>
          <div class="relative">
            <video id="camera-preview" autoplay class="w-full rounded border"></video>
            <div class="mt-4 flex gap-2 justify-center">
              <button id="capture-btn" class="px-4 py-2 bg-primary text-white rounded hover:bg-primary/90">
                ${t('upload.capturePhoto')}
              </button>
              <button id="cancel-btn" class="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400">
                ${t('upload.cancel')}
              </button>
            </div>
          </div>
        </div>
      `;
      
      document.body.appendChild(modal);
      const videoElement = modal.querySelector('#camera-preview') as HTMLVideoElement;
      videoElement.srcObject = stream;
      
      const captureBtn = modal.querySelector('#capture-btn');
      const cancelBtn = modal.querySelector('#cancel-btn');
      
      const cleanup = () => {
        stream.getTracks().forEach(track => track.stop());
        document.body.removeChild(modal);
      };
      
      captureBtn?.addEventListener('click', () => {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context?.drawImage(video, 0, 0);
        
        canvas.toBlob((blob) => {
          if (blob) {
            const file = new File([blob], `document-page-${Date.now()}.jpg`, { type: 'image/jpeg' });
            setCapturedPhotos(prev => [...prev, file]);
            setErrors(prev => ({ ...prev, file: "" }));
            toast.success(t('upload.photoCaptured'));
          }
        }, 'image/jpeg', 0.8);
        
        cleanup();
      });
      
      cancelBtn?.addEventListener('click', cleanup);
      
    } catch (error) {
      console.error('Camera access error:', error);
      toast.error(t('upload.cameraAccessError'));
    }
  };

  const { getRootProps, getInputProps, isDragActive, open } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'text/csv': ['.csv'],
      'text/plain': ['.txt'],
      'text/rtf': ['.rtf'],
      'application/rtf': ['.rtf'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'image/gif': ['.gif'],
      'image/bmp': ['.bmp'],
      'image/tiff': ['.tiff'],
      'image/webp': ['.webp'],
      'application/zip': ['.zip'],
      'application/vnd.oasis.opendocument.text': ['.odt'],
      'application/vnd.oasis.opendocument.spreadsheet': ['.ods']
    },
    multiple: false,
    noClick: true, // We use a custom button to open the dialog
    noKeyboard: true,
  });

  useEffect(() => {
    if (formData.country) {
      const selectedCountry = countriesData.find(c => c.name === formData.country);
      if (selectedCountry) {
        const federalOption: State = { name: "Federal / National" };
        const newStates = [federalOption, ...selectedCountry.states];
        setCurrentStates(newStates);
        // MYA-19: Logic for resetting stateProvince based on new list of states.
        if (formData.adminLevel === 'federal') {
          // If admin level is federal, ensure stateProvince is "Federal / National"
          if (formData.stateProvince !== "Federal / National") {
            setFormData(prev => ({ ...prev, stateProvince: "Federal / National" }));
          }
        } else if (formData.adminLevel === 'state') {
          // If admin level is 'state':
          // Check if the current stateProvince is valid within the newStates.
          // newStates includes "Federal / National" + actual states.
          const isValidInNewStates = newStates.find(s => s.name === formData.stateProvince);
          
          if (!isValidInNewStates) {
            // If not valid (e.g. was from another country), clear it.
            setFormData(prev => ({ ...prev, stateProvince: "" }));
          } else if (formData.stateProvince === "Federal / National" && selectedCountry.states.length > 0) {
            // If it IS "Federal / National" BUT the country HAS other states, it's not a valid choice for 'state' admin level. Clear it.
            setFormData(prev => ({ ...prev, stateProvince: "" }));
          }
          // If it IS "Federal / National" and country has NO other states, it IS a valid choice, so do nothing.
          // If it's a valid state (not "Federal / National"), do nothing.
        } else { // No admin level selected yet, or some other case
            if (!newStates.find(s => s.name === formData.stateProvince)) {
                setFormData(prev => ({ ...prev, stateProvince: "" }));
            }
        }
      } else {
        setCurrentStates([]);
        setFormData(prev => ({ ...prev, stateProvince: "" }));
      }
    } else {
      setCurrentStates([]);
      setFormData(prev => ({ ...prev, stateProvince: "" }));
    }
  }, [formData.country]); // MYA-19: formData.stateProvince removed from deps, logic handled within useEffect and handleSelectChange

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: undefined }));
  };

  const handleSelectChange = (name: keyof FormData, value: string) => {
    setFormData((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: undefined }));

    // If admin level is changed to 'federal', auto-select 'Federal / National' for state/province
    if (name === 'adminLevel' && value === 'federal') {
        const selectedCountryData = countriesData.find(c => c.name === formData.country);
        if (selectedCountryData) { // Ensure country is selected
            setFormData(prev => ({ ...prev, stateProvince: "Federal / National"}));
            setErrors(prev => ({...prev, stateProvince: undefined})); // Clear potential error
        }
    }
    // If country changes, stateProvince is reset by useEffect.
    // If adminLevel changes to 'state', and stateProvince was 'Federal / National', user needs to re-select.
    // The useEffect will handle resetting stateProvince if it's no longer valid for the current country/state list.
    // MYA-19: If a country with no actual states is selected (only 'Federal / National' option),
    // and admin level is 'state', we should clear stateProvince to force re-selection or show error.
    // Also, when country changes, always reset stateProvince.
    if (name === 'country') {
      setFormData(prev => ({ ...prev, stateProvince: "" })); // Always reset state when country changes
    } else if (name === 'adminLevel') {
      if (value === 'federal') {
        const selectedCountryData = countriesData.find(c => c.name === formData.country);
        if (selectedCountryData) { // Ensure country is selected
            setFormData(prev => ({ ...prev, stateProvince: "Federal / National"}));
            setErrors(prev => ({...prev, stateProvince: undefined})); 
        }
      } else if (value === 'state') {
        // If switching to 'state' and current stateProvince is 'Federal / National', clear it 
        // to force user to pick a state, unless 'Federal / National' is the only option (country with no states).
        const selectedCountryData = countriesData.find(c => c.name === formData.country);
        if (formData.stateProvince === "Federal / National") {
            if (selectedCountryData && selectedCountryData.states.length > 0) { // if country has actual states
                 setFormData(prev => ({ ...prev, stateProvince: "" }));
            }
            // If country has no states, 'Federal / National' is fine for stateProvince even with adminLevel 'state'.
        }
      }
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Partial<Record<keyof FormData | 'captcha', string>> = {};

    if (!formData.title.trim()) {
      newErrors.title = "Document title is required.";
    }

    if (!formData.description.trim()) {
      newErrors.description = "Description is required.";
    }

    if (!formData.country.trim()) {
      newErrors.country = "Country is required.";
    }

    if (!formData.documentLanguage.trim()) {
      newErrors.documentLanguage = "Document language is required.";
    }

    if (!formData.file && capturedPhotos.length === 0) {
      newErrors.file = "Please select a file to upload or capture photos with camera.";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) {
        toast.error("Validation Failed", { description: "Please check the form for errors and try again." });
        // Focus first error field - advanced UX
        const firstErrorKey = Object.keys(errors).find(key => errors[key as keyof typeof errors]);
        if(firstErrorKey) {
            const element = document.getElementsByName(firstErrorKey)[0] || document.getElementById(firstErrorKey);
            element?.focus();
        }
        return;
    }

    setIsSubmitting(true);
    toast.loading("Submitting document for review...", { id: "upload-toast" });

    // Prepare file for upload
    let fileToUpload = formData.file;
    
    // If using camera mode with multiple photos, combine them
    if (isCameraMode && capturedPhotos.length > 0) {
      try {
        if (capturedPhotos.length > 1) {
          toast.loading("Combining photos into single image...", { id: "upload-toast" });
        }
        fileToUpload = await combinePhotosIntoPDF(capturedPhotos);
      } catch (error) {
        console.error("Error combining photos:", error);
        toast.error("Error combining photos", { id: "upload-toast", description: "Failed to combine photos. Please try again." });
        setIsSubmitting(false);
        return;
      }
    }
    
    if (!fileToUpload) {
      toast.error("File Missing", { id: "upload-toast", description: "Please select a file to upload or capture photos." });
      setIsSubmitting(false);
      return;
    }

    try {
      // Upload using the new backend API
      toast.loading("Uploading file...", { id: "upload-toast" });
      
      // Create FormData for the backend upload
      const uploadFormData = new FormData();
      uploadFormData.append('file', fileToUpload);
      uploadFormData.append('title', formData.title);
      uploadFormData.append('country', formData.country);
      uploadFormData.append('state', formData.stateProvince || formData.country); // Use country as fallback
      uploadFormData.append('document_language', formData.documentLanguage); // Add document language
      if (formData.description) {
        uploadFormData.append('description', formData.description);
      }

      // Call the backend upload API
      const uploadResponse = await fetch('/api/file-uploader/upload', {
        method: 'POST',
        body: uploadFormData,
      });

      if (!uploadResponse.ok) {
        let errorMessage = "Could not upload file to server.";
        try {
          const errorData = await uploadResponse.json();
          
          // Handle rate limit errors which return an object
          if (errorData.detail && typeof errorData.detail === 'object') {
            const detail = errorData.detail;
            if (detail.message && detail.remaining_time !== undefined) {
              // This is a rate limit error
              const minutes = Math.ceil(detail.remaining_time / 60);
              const seconds = Math.ceil(detail.remaining_time % 60);
              
              if (minutes > 0) {
                errorMessage = `${detail.message} Please wait ${minutes} minute${minutes > 1 ? 's' : ''} and ${seconds} second${seconds !== 1 ? 's' : ''} before trying again.`;
              } else {
                errorMessage = `${detail.message} Please wait ${seconds} second${seconds !== 1 ? 's' : ''} before trying again.`;
              }
            } else {
              // Other structured error
              errorMessage = detail.message || JSON.stringify(detail);
            }
          } else {
            // Simple string error message
            errorMessage = errorData.detail || errorData.message || errorMessage;
          }
        } catch {
          errorMessage = `HTTP ${uploadResponse.status}: ${uploadResponse.statusText}`;
        }
        toast.error("Upload Failed", { 
            id: "upload-toast", 
            description: errorMessage
        });
        setErrors({file: `Upload error: ${errorMessage}`});
        setIsSubmitting(false);
        return;
      }
      
      const responseData = await uploadResponse.json();

      toast.success("Document Submitted!", {
          id: "upload-toast",
          description: "Your document has been successfully submitted for review. Thank you!",
      });
      
      // Reset form
      setFormData({
          title: "", 
          description: "", 
          country: "", 
          stateProvince: "", 
          adminLevel: "", 
          file: null,
          uploader_name: "",
          uploader_email: ""
      });
      
      // Optional: navigate to a thank you page
      // navigate("/thank-you-for-submission");

    } catch (error) {
      toast.error("Unexpected Error", { 
          id: "upload-toast", 
          description: "An unexpected error occurred. Please try again or contact support."
      });
    }
    setIsSubmitting(false);
  };

  return (
    <div className="min-h-screen bg-white">
      <Navigation />
      <div className="py-8 px-4 flex justify-center items-start font-sans">
        <Card className="w-full max-w-2xl shadow-xl">
          <form onSubmit={handleSubmit} noValidate>
            <CardHeader className="text-center">
            
            <CardTitle className="text-3xl font-serif">{t('upload.title')}</CardTitle>
            <CardDescription>
              {t('upload.subtitle')}
            </CardDescription>
            <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-800 text-center">
                📚 <strong>Important:</strong> Please read our{' '}
                <Button
                  variant="link" 
                  className="p-0 h-auto text-blue-600 hover:text-blue-800 underline"
                  onClick={() => navigate('/disclaimer')}
                >
                  Disclaimer and FAQ
                </Button>
                {' '}before uploading for important safety information.
              </p>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* File Upload Section */}
            <div className="space-y-4">
              {/* Upload Options */}
              <div className="flex gap-2 justify-center">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setIsCameraMode(false)}
                  className={!isCameraMode ? "bg-primary text-primary-foreground" : ""}
                >
                  <UploadCloud className="h-4 w-4 mr-2" />
                  {t('upload.uploadFile')}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setIsCameraMode(true);
                    setShowCameraDisclaimer(true);
                  }}
                  className={isCameraMode ? "bg-primary text-primary-foreground" : ""}
                >
                  <Camera className="h-4 w-4 mr-2" />
                  {t('upload.useCamera')}
                </Button>
              </div>

              {/* Camera Disclaimer */}
              {showCameraDisclaimer && isCameraMode && (
                <Card className="border-amber-200 bg-amber-50">
                  <CardContent className="pt-6">
                    <div className="flex items-start space-x-3">
                      <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
                      <div className="space-y-2">
                        <h4 className="font-semibold text-amber-800">{t('upload.cameraDisclaimerTitle')}</h4>
                        <div className="text-sm text-amber-700 space-y-2">
                          <p>{t('upload.cameraDisclaimerP1')}</p>
                          <p>{t('upload.cameraDisclaimerP2')}</p>
                          <div className="mt-3 p-3 bg-amber-100 rounded border-l-4 border-amber-400">
                            <div className="flex items-start space-x-2">
                              <Smartphone className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
                              <div>
                                <p className="font-medium text-amber-800">{t('upload.phoneWarningTitle')}</p>
                                <p className="text-xs text-amber-700 mt-1">{t('upload.phoneWarningText')}</p>
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* File Upload or Camera Interface */}
              {!isCameraMode ? (
                <div {...getRootProps()} className={`p-6 border-2 border-dashed rounded-lg text-center cursor-pointer transition-colors 
                  ${isDragActive ? "border-primary bg-primary/10" : "border-muted-foreground/30 hover:border-primary/70"}
                  ${errors.file ? "border-destructive bg-destructive/10" : ""}
                `}>
                  <input {...getInputProps()} id="file-upload" name="file"/>
                  <UploadCloud className={`mx-auto h-12 w-12 mb-3 ${errors.file ? "text-destructive" : "text-muted-foreground"}`} />
                  {formData.file ? (
                    <div className="text-center">
                      <FileText className="mx-auto h-8 w-8 text-green-600 mb-2" />
                      <p className="font-semibold text-foreground">{formData.file.name}</p>
                      <p className="text-sm text-muted-foreground">({(formData.file.size / 1024 / 1024).toFixed(2)} MB)</p>
                      <Button type="button" variant="link" size="sm" className="text-xs mt-1 text-destructive" onClick={(e) => { e.stopPropagation(); setFormData(p => ({...p, file: null})); }}>Remove file</Button>
                    </div>
                  ) : isDragActive ? (
                    <p className="text-primary font-semibold">Drop the file here ...</p>
                  ) : (
                    <p className="text-muted-foreground">
                      Drag & drop any document or image file here, or <Button type="button" variant="link" className="p-0 h-auto" onClick={open}>click to select</Button>
                    </p>
                  )}
                </div>
              ) : (
                <div className="p-6 border-2 border-dashed border-primary/50 rounded-lg text-center">
                  <Camera className="mx-auto h-12 w-12 mb-3 text-primary" />
                  {capturedPhotos.length > 0 ? (
                    <div className="text-center space-y-4">
                      <div className="text-green-600 mb-4">
                        <FileText className="mx-auto h-8 w-8 mb-2" />
                        <p className="font-semibold">{t('upload.photosCaptures', { count: capturedPhotos.length })}</p>
                        <p className="text-sm text-muted-foreground">
                          Total: {(capturedPhotos.reduce((sum, file) => sum + file.size, 0) / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                      
                      {/* Photo thumbnails */}
                      <div className="grid grid-cols-3 gap-2 max-w-xs mx-auto">
                        {capturedPhotos.map((file, index) => (
                          <div key={index} className="relative">
                            <img 
                              src={URL.createObjectURL(file)} 
                              alt={`Page ${index + 1}`}
                              className="w-full h-16 object-cover rounded border"
                            />
                            <button
                              type="button"
                              onClick={() => setCapturedPhotos(prev => prev.filter((_, i) => i !== index))}
                              className="absolute -top-1 -right-1 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs hover:bg-red-600"
                            >
                              ×
                            </button>
                          </div>
                        ))}
                      </div>
                      
                      <div className="flex gap-2 justify-center">
                        <Button type="button" onClick={handleCameraCapture} variant="outline" size="sm">
                          <Camera className="h-4 w-4 mr-2" />
                          {t('upload.addMorePages')}
                        </Button>
                        <Button 
                          type="button" 
                          variant="link" 
                          size="sm" 
                          className="text-destructive" 
                          onClick={() => setCapturedPhotos([])}
                        >
                          {t('upload.clearAll')}
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div>
                      <p className="text-muted-foreground mb-4">{t('upload.cameraInstructions')}</p>
                      <Button type="button" onClick={handleCameraCapture} className="w-full max-w-xs">
                        <Camera className="h-4 w-4 mr-2" />
                        {t('upload.openCamera')}
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </div>
            {errors.file && <p className="text-sm text-destructive mt-1 flex items-center"><AlertCircle className="h-4 w-4 mr-1" />{errors.file}</p>}

            {/* Supported file types info */}
            <div className="text-xs text-muted-foreground">
              <p>{t('upload.fileNote')}</p>
            </div>

            {/* Form Fields */}
            <div className="space-y-2">
              <Label htmlFor="title">{t('upload.documentTitle')} <span className="text-destructive">*</span></Label>
              <Input id="title" name="title" value={formData.title} onChange={handleChange} placeholder={t('upload.titlePlaceholder')} className={errors.title ? "border-destructive" : ""} aria-invalid={!!errors.title} aria-describedby={errors.title ? "title-error" : undefined} />
              {errors.title && <p id="title-error" className="text-sm text-destructive flex items-center"><AlertCircle className="h-4 w-4 mr-1" />{errors.title}</p>}
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">{t('upload.description')} <span className="text-destructive">*</span></Label>
              <Textarea id="description" name="description" value={formData.description} onChange={handleChange} placeholder={t('upload.descriptionPlaceholder')} rows={4} maxLength={500} className={errors.description ? "border-destructive" : ""} aria-invalid={!!errors.description} aria-describedby={errors.description ? "description-error" : undefined} />
              <div className="text-xs text-muted-foreground text-right">
                {formData.description.length}/500 characters
              </div>
              {errors.description && <p id="description-error" className="text-sm text-destructive flex items-center"><AlertCircle className="h-4 w-4 mr-1" />{errors.description}</p>}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="documentLanguage">Document Language <span className="text-destructive">*</span></Label>
                <Select name="documentLanguage" value={formData.documentLanguage} onValueChange={(value) => handleSelectChange("documentLanguage", value)}>
                  <SelectTrigger id="documentLanguage" className={errors.documentLanguage ? "border-destructive" : ""} aria-invalid={!!errors.documentLanguage} aria-describedby={errors.documentLanguage ? "documentLanguage-error" : undefined}>
                    <SelectValue placeholder="Select document language" />
                  </SelectTrigger>
                  <SelectContent>
                    {documentLanguages.map(lang => <SelectItem key={lang.value} value={lang.value}>{lang.label}</SelectItem>)}
                  </SelectContent>
                </Select>
                {errors.documentLanguage && <p id="documentLanguage-error" className="text-sm text-destructive flex items-center"><AlertCircle className="h-4 w-4 mr-1" />{errors.documentLanguage}</p>}
              </div>

              <div className="space-y-2">
                <Label htmlFor="country">{t('upload.country')} <span className="text-destructive">*</span></Label>
                <Select name="country" value={formData.country} onValueChange={(value) => handleSelectChange("country", value)} >
                  <SelectTrigger id="country" className={errors.country ? "border-destructive" : ""} aria-invalid={!!errors.country} aria-describedby={errors.country ? "country-error" : undefined}>
                    <SelectValue placeholder={t('upload.countryPlaceholder')} />
                  </SelectTrigger>
                  <SelectContent>
                    {countriesData.map(c => <SelectItem key={c.name} value={c.name}>{c.name}</SelectItem>)}
                  </SelectContent>
                </Select>
                {errors.country && <p id="country-error" className="text-sm text-destructive flex items-center"><AlertCircle className="h-4 w-4 mr-1" />{errors.country}</p>}
              </div>

              {/* State/Province Dropdown - Added for MYA-19 */}
              <div className="space-y-2">
                <Label htmlFor="stateProvince">
                  {t('upload.state')}
                  {formData.adminLevel === 'state' && <span className="text-destructive">*</span>}
                </Label>
                <Select 
                  name="stateProvince" 
                  value={formData.stateProvince} 
                  onValueChange={(value) => handleSelectChange("stateProvince", value)}
                  disabled={!formData.country || (formData.adminLevel !== 'federal' && currentStates.length <= 1) || formData.adminLevel === 'federal' || (formData.adminLevel === 'state' && currentStates.length > 0 && currentStates[0].name === "Federal / National" && currentStates.length === 1) }
                >
                  <SelectTrigger id="stateProvince" className={errors.stateProvince ? "border-destructive" : ""} aria-invalid={!!errors.stateProvince} aria-describedby={errors.stateProvince ? "stateProvince-error" : undefined}>
                    <SelectValue placeholder={formData.adminLevel === 'federal' ? "Federal / National (auto)" : t('upload.statePlaceholder')} />
                  </SelectTrigger>
                  <SelectContent>
                    {currentStates.map(s => <SelectItem key={s.name} value={s.name} disabled={s.name === "Federal / National" && formData.adminLevel === 'state' && currentStates.length > 1}>{s.name}</SelectItem>)}
                  </SelectContent>
                </Select>
                {errors.stateProvince && <p id="stateProvince-error" className="text-sm text-destructive flex items-center"><AlertCircle className="h-4 w-4 mr-1" />{errors.stateProvince}</p>}
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="adminLevel">Level <span className="text-destructive">*</span></Label>
                <div className="space-y-3">
                  {adminLevels.map(level => (
                    <div key={level.id} className="flex items-center space-x-2">
                      <input
                        type="radio"
                        id={`adminLevel-${level.id}`}
                        name="adminLevel"
                        value={level.id}
                        checked={formData.adminLevel === level.id}
                        onChange={(e) => handleSelectChange("adminLevel", e.target.value)}
                        className="h-4 w-4 text-primary focus:ring-primary border-gray-300"
                        aria-invalid={!!errors.adminLevel}
                        aria-describedby={errors.adminLevel ? "adminLevel-error" : undefined}
                      />
                      <Label htmlFor={`adminLevel-${level.id}`} className="text-sm font-normal cursor-pointer">
                        {level.name}
                      </Label>
                    </div>
                  ))}
                </div>
                {errors.adminLevel && <p id="adminLevel-error" className="text-sm text-destructive flex items-center"><AlertCircle className="h-4 w-4 mr-1" />{errors.adminLevel}</p>}
              </div>
            </div>



            {/* CAPTCHA Section */}
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <Shield className="h-4 w-4" />
                Security Verification
              </Label>
              <div className="flex justify-center">
                <HCaptcha
                  sitekey="50b2fe65-b00b-4b9e-ad62-3ba471098be2" // Production site key for haqnow.com
                  onVerify={setCaptchaToken}
                  onError={() => setCaptchaToken(null)}
                  onExpire={() => setCaptchaToken(null)}
                />
              </div>
              {errors.captcha && <p className="text-sm text-destructive flex items-center"><AlertCircle className="h-4 w-4 mr-1" />{errors.captcha}</p>}
            </div>

          </CardContent>
          <CardFooter className="flex flex-col items-center space-y-3">
            <Button type="submit" className="w-full md:w-1/2 py-3 text-base" disabled={isSubmitting}>
              {isSubmitting ? (
                <><Loader2 className="mr-2 h-5 w-5 animate-spin" /> {t('upload.uploading')}</>
              ) : (
                <><UploadCloud className="mr-2 h-5 w-5" /> {t('upload.submitButton')}</>
              )}
            </Button>
          </CardFooter>
        </form>
      </Card>
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
}

import React, { useState, useCallback, useEffect, useRef } from "react";
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
import { UploadCloud, FileText, AlertCircle, CheckCircle, Loader2, Shield, ArrowLeft, Camera, Smartphone, AlertTriangle, Clock, CheckCircle2 } from "lucide-react";
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
  files: File[];  // Changed to support multiple files
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
    files: [],  // Changed to support multiple files
  });
  const [currentStates, setCurrentStates] = useState<State[]>([]); // Changed type to State[]
  const [errors, setErrors] = useState<Partial<Record<keyof FormData | 'captcha' | 'consent' | 'file', string>>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [captchaToken, setCaptchaToken] = useState<string | null>(null);
  const [isCameraMode, setIsCameraMode] = useState(false);
  const [showCameraDisclaimer, setShowCameraDisclaimer] = useState(false);
  const [capturedPhotos, setCapturedPhotos] = useState<File[]>([]);
  const [consentChecked, setConsentChecked] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<{
    step: string;
    progress: number;
    queuePosition?: number;
    jobId?: number;
  } | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

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

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles?: any[]) => {
    if (acceptedFiles && acceptedFiles.length > 0) {
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
      
      // Calculate how many files we can still add (max 10 total)
      const currentFileCount = formData.files.length;
      const remainingSlots = Math.max(0, 10 - currentFileCount);
      
      // Filter valid files and limit to remaining slots
      const validFiles = acceptedFiles.filter(file => 
        allowedTypes.includes(file.type) || 
        file.name.toLowerCase().match(/\.(pdf|doc|docx|xls|xlsx|csv|txt|rtf|jpg|jpeg|png|gif|bmp|tiff|webp|zip|odt|ods)$/)
      ).slice(0, remainingSlots);
      
      if (validFiles.length > 0) {
        setFormData((prev) => ({ ...prev, files: [...prev.files, ...validFiles].slice(0, 10) }));
        setErrors((prev) => ({ ...prev, file: undefined }));
        
        if (validFiles.length < acceptedFiles.length) {
          toast.warning("Some files skipped", { 
            description: "Some files were not supported or exceeded the 10 file limit." 
          });
        }
        
        if (validFiles.length > 1) {
          toast.success(`${validFiles.length} files added`, {
            description: "You can upload multiple documents at once."
          });
        } else if (validFiles.length === 1 && currentFileCount > 0) {
          toast.success("File added", {
            description: `${currentFileCount + 1}/10 files selected`
          });
        }
      } else {
        if (remainingSlots === 0) {
          toast.warning("File limit reached", { 
            description: "You can upload a maximum of 10 files. Please remove some files first." 
          });
        } else {
          setErrors((prev) => ({ ...prev, file: "Unsupported file type. Please upload documents, images, or text files." }));
          toast.error("Invalid File Type", { description: "Please upload supported document or image files." });
        }
      }
    }
    
    // Handle rejected files
    if (rejectedFiles && rejectedFiles.length > 0) {
      const reasons = rejectedFiles.map(({ file, errors }) => {
        const errorMessages = errors.map(e => e.message).join(', ');
        return `${file.name}: ${errorMessages}`;
      });
      toast.error("Some files were rejected", {
        description: reasons.join('; ')
      });
    }
  }, [formData.files.length]);

  // Custom function to open file picker with multiple selection
  const handleFileButtonClick = useCallback(() => {
    if (fileInputRef.current) {
      // Ensure multiple attribute is set
      fileInputRef.current.setAttribute('multiple', 'multiple');
      fileInputRef.current.multiple = true;
      fileInputRef.current.click();
    }
  }, []);

  // Handle file selection from custom input
  const handleFileInputChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const fileArray = Array.from(files);
      onDrop(fileArray, []);
      // Reset input so same files can be selected again if needed
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  }, [onDrop]);

  // Function to combine multiple photos into a single image
  const combinePhotosIntoPDF = async (photos: File[]): Promise<File> => {
    if (photos.length === 1) {
      return photos[0];
    }
    
    try {
      console.log(`Combining ${photos.length} photos into single image`);
      
      // For multiple photos, we'll combine them into a single large image
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      
      if (!ctx) {
        throw new Error('Canvas context not available');
      }
      
      // Load all images with better error handling
      const images = await Promise.all(
        photos.map((photo, index) => {
          return new Promise<HTMLImageElement>((resolve, reject) => {
            const img = new Image();
            img.onload = () => {
              console.log(`Image ${index + 1} loaded: ${img.width}x${img.height}`);
              resolve(img);
            };
            img.onerror = (error) => {
              console.error(`Failed to load image ${index + 1}:`, error);
              reject(new Error(`Failed to load image ${index + 1}`));
            };
            img.src = URL.createObjectURL(photo);
          });
        })
      );
      
      // Calculate dimensions - normalize width and stack vertically
      // Use wider base width to preserve details from high-res cameras
      const targetWidth = Math.min(2000, Math.max(...images.map(img => img.width))); 
      let totalHeight = 0;
      
      // Calculate total height based on aspect ratios
      images.forEach((img, index) => {
        const aspectRatio = img.height / img.width;
        const scaledHeight = targetWidth * aspectRatio;
        totalHeight += scaledHeight;
        console.log(`Image ${index + 1}: Original ${img.width}x${img.height}, scaled to ${targetWidth}x${scaledHeight}`);
      });
      
      console.log(`Final canvas size: ${targetWidth}x${totalHeight}`);
      
      // Set canvas size
      canvas.width = targetWidth;
      canvas.height = totalHeight;
      
      // Fill with white background
      ctx.fillStyle = 'white';
      ctx.fillRect(0, 0, targetWidth, totalHeight);
      
      // Draw all images vertically with proper scaling
      let currentY = 0;
      images.forEach((img, index) => {
        const aspectRatio = img.height / img.width;
        const scaledHeight = targetWidth * aspectRatio;
        
        console.log(`Drawing image ${index + 1} at y=${currentY}, height=${scaledHeight}`);
        ctx.drawImage(img, 0, currentY, targetWidth, scaledHeight);
        currentY += scaledHeight;
        
        // Clean up object URL
        URL.revokeObjectURL(img.src);
      });
      
      // Convert to blob with higher quality and better error handling
      return new Promise<File>((resolve, reject) => {
        canvas.toBlob((blob) => {
          if (blob) {
            const combinedName = `combined-document-${photos.length}pages-${Date.now()}.jpg`;
            console.log(`Successfully created combined image: ${combinedName}, size: ${blob.size} bytes`);
            resolve(new File([blob], combinedName, { type: 'image/jpeg' }));
          } else {
            console.error('Failed to create blob from canvas');
            reject(new Error('Failed to create combined image blob'));
          }
        }, 'image/jpeg', 0.95); // Higher quality
      });
      
    } catch (error) {
      console.error('Error combining photos:', error);
      toast.error('Failed to combine photos. Using first photo only.');
      // Fallback: return first photo if combination fails
      return photos[0];
    }
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
        video: {
          facingMode: 'environment',
          width: { ideal: 2560 },
          height: { ideal: 1440 }
        } // Prefer high-res back camera
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
        
        // Use PNG for lossless capture from canvas, then we may recompress later during PDF processing
        canvas.toBlob((blob) => {
          if (blob) {
            const file = new File([blob], `document-page-${Date.now()}.png`, { type: 'image/png' });
            setCapturedPhotos(prev => [...prev, file]);
            setErrors(prev => ({ ...prev, file: "" }));
            toast.success(t('upload.photoCaptured'));
          }
        }, 'image/png');
        
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
    multiple: true,  // Enable multiple file selection
    maxFiles: 10,    // Limit to 10 files
    noClick: true,   // We use a custom button to open the dialog
    noKeyboard: true,
  });

  // Ensure the file input has multiple attribute set
  useEffect(() => {
    if (fileInputRef.current) {
      fileInputRef.current.setAttribute('multiple', 'multiple');
      fileInputRef.current.multiple = true;
    }
  }, []);

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
    const newErrors: Partial<Record<keyof FormData | 'captcha' | 'consent' | 'file', string>> = {};

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

    if (formData.files.length === 0 && capturedPhotos.length === 0) {
      newErrors.file = "Please select at least one file to upload or capture photos with camera.";
    }

    if (!consentChecked) {
      newErrors.consent = "You must confirm authorization to share this document.";
    }

    if (!captchaToken) {
      newErrors.captcha = "Please complete the security verification.";
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
    setUploadProgress({ step: "Uploading file...", progress: 0 });
    toast.loading("Uploading file...", { id: "upload-toast" });

    // Prepare files for upload
    let filesToUpload: File[] = [...formData.files];
    
    // If using camera mode with multiple photos, combine them into one file
    if (isCameraMode && capturedPhotos.length > 0) {
      try {
        if (capturedPhotos.length > 1) {
          toast.loading("Combining photos into single image...", { id: "upload-toast" });
        }
        const combinedFile = await combinePhotosIntoPDF(capturedPhotos);
        filesToUpload = [combinedFile];
      } catch (error) {
        console.error("Error combining photos:", error);
        toast.error("Error combining photos", { id: "upload-toast", description: "Failed to combine photos. Please try again." });
        setIsSubmitting(false);
        return;
      }
    }
    
    if (filesToUpload.length === 0) {
      toast.error("Files Missing", { id: "upload-toast", description: "Please select files to upload or capture photos." });
      setIsSubmitting(false);
      return;
    }

    try {
      // Upload using the backend API
      setUploadProgress({ step: "Scanning for viruses...", progress: 20 });
      toast.loading(`Scanning ${filesToUpload.length} file(s) for viruses...`, { id: "upload-toast" });
      
      // Create FormData for the backend upload
      const uploadFormData = new FormData();
      
      // Use multi-file endpoint if more than one file, otherwise use single file endpoint
      const useMultiUpload = filesToUpload.length > 1;
      
      if (useMultiUpload) {
        // Append all files for multi-upload
        filesToUpload.forEach((file) => {
          uploadFormData.append('files', file);
        });
      } else {
        // Single file upload
        uploadFormData.append('file', filesToUpload[0]);
      }
      
      uploadFormData.append('title', formData.title);
      uploadFormData.append('country', formData.country);
      uploadFormData.append('state', formData.stateProvince || formData.country);
      uploadFormData.append('document_language', formData.documentLanguage);
      if (formData.description) {
        uploadFormData.append('description', formData.description);
      }
      if (captchaToken) {
        uploadFormData.append('captcha_token', captchaToken);
      }

      // Call the appropriate backend upload API
      const uploadEndpoint = useMultiUpload ? '/api/file-uploader/upload-multiple' : '/api/file-uploader/upload';
      const uploadResponse = await fetch(uploadEndpoint, {
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
      
      // Update progress
      setUploadProgress({ 
        step: "Virus scan complete. Metadata removal in progress...", 
        progress: 40,
        jobId: responseData.job_id 
      });
      
      toast.success("Document Uploaded!", {
          id: "upload-toast",
          description: "File uploaded successfully. Processing will continue in the background.",
      });
      
      // Job will be created when document is approved by admin
      // For now, just show upload completion
      setUploadProgress({ 
        step: "Upload complete. Waiting for admin approval (12-24 hours)...", 
        progress: 60 
      });
      
      // Note: Job status polling will start after admin approval
      // Users can check status later via document ID if needed
      
      // Reset form after a delay
      setTimeout(() => {
        setFormData({
            title: "", 
            description: "", 
            country: "", 
            stateProvince: "", 
            adminLevel: "", 
            files: [],  // Reset files array
            documentLanguage: "english"
        });
        setCapturedPhotos([]);
        setConsentChecked(false);
        setCaptchaToken(null);
      }, 2000);

    } catch (error) {
      toast.error("Unexpected Error", { 
          id: "upload-toast", 
          description: "An unexpected error occurred. Please try again or contact support."
      });
    }
    setIsSubmitting(false);
  };

  // Poll for job status
  const pollJobStatus = async (jobId: number) => {
    const maxAttempts = 60; // Poll for up to 5 minutes (60 * 5 seconds)
    let attempts = 0;
    
    const poll = async () => {
      if (attempts >= maxAttempts || !isPolling) {
        setIsPolling(false);
        return;
      }
      
      try {
        const response = await fetch(`/api/document-processing/job-status/${jobId}`);
        if (response.ok) {
          const jobStatus = await response.json();
          
          // Update progress based on job status
          if (jobStatus.status === 'completed') {
            setUploadProgress({ 
              step: "Processing complete! Waiting for admin approval...", 
              progress: 80,
              queuePosition: 0
            });
            setIsPolling(false);
            toast.success("Processing Complete!", {
              id: "upload-toast",
              description: "Your document has been processed and is pending admin approval.",
            });
          } else if (jobStatus.status === 'failed') {
            setUploadProgress({ 
              step: "Processing failed. Please contact support.", 
              progress: 0
            });
            setIsPolling(false);
            toast.error("Processing Failed", {
              id: "upload-toast",
              description: "Document processing failed. Your document was uploaded but needs manual review.",
            });
          } else if (jobStatus.status === 'processing') {
            // Update progress based on current step
            let progressPercent = 50;
            if (jobStatus.current_step) {
              if (jobStatus.current_step.includes("OCR")) progressPercent = 60;
              else if (jobStatus.current_step.includes("tags")) progressPercent = 75;
              else if (jobStatus.current_step.includes("Finalizing")) progressPercent = 90;
            }
            
            setUploadProgress({ 
              step: jobStatus.current_step || "Processing document...", 
              progress: progressPercent,
              queuePosition: jobStatus.queue_position
            });
            
            // Continue polling
            attempts++;
            setTimeout(poll, 5000); // Poll every 5 seconds
          } else if (jobStatus.status === 'pending') {
            setUploadProgress({ 
              step: `Waiting in queue (position ${jobStatus.queue_position || '?'})...`, 
              progress: 45,
              queuePosition: jobStatus.queue_position
            });
            
            // Continue polling
            attempts++;
            setTimeout(poll, 5000);
          }
        } else {
          // Error fetching status, stop polling
          setIsPolling(false);
        }
      } catch (error) {
        console.error("Error polling job status:", error);
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 5000);
        } else {
          setIsPolling(false);
        }
      }
    };
    
    // Start polling
    setTimeout(poll, 2000); // Wait 2 seconds before first poll
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
            
            {/* Document Processing Steps */}
            <div className="mt-6 mb-4 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg">
              <h3 className="text-sm font-semibold text-gray-800 mb-3 text-center">
                {t('upload.processSteps.title')}
              </h3>
              <div className="space-y-2">
                {[
                  { step: 1, text: t('upload.processSteps.step1'), icon: UploadCloud },
                  { step: 2, text: t('upload.processSteps.step2'), icon: Shield },
                  { step: 3, text: t('upload.processSteps.step3'), icon: FileText },
                  { step: 4, text: t('upload.processSteps.step4'), icon: Clock },
                  { step: 5, text: t('upload.processSteps.step5'), icon: CheckCircle2 },
                ].map((item, index) => {
                  const Icon = item.icon;
                  const isActive = uploadProgress && uploadProgress.progress >= (index * 20);
                  return (
                    <div
                      key={item.step}
                      className={`flex items-center gap-2 text-xs transition-all duration-300 ${
                        isActive ? 'text-green-700 font-medium' : 'text-gray-600'
                      }`}
                    >
                      <div
                        className={`flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center transition-all duration-300 ${
                          isActive
                            ? 'bg-green-100 border-2 border-green-500 shadow-sm'
                            : 'bg-gray-100 border-2 border-gray-300'
                        }`}
                      >
                        {isActive ? (
                          <CheckCircle2 className="h-4 w-4 text-green-600" />
                        ) : (
                          <span className="text-xs font-semibold">{item.step}</span>
                        )}
                      </div>
                      <Icon
                        className={`h-3 w-3 flex-shrink-0 transition-colors duration-300 ${
                          isActive ? 'text-green-600' : 'text-gray-400'
                        }`}
                      />
                      <span className="leading-snug">{item.text}</span>
                    </div>
                  );
                })}
              </div>
            </div>
            
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
            {/* Upload Progress Display */}
            {uploadProgress && (
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-blue-900">{uploadProgress.step}</span>
                  {uploadProgress.queuePosition !== undefined && uploadProgress.queuePosition > 0 && (
                    <span className="text-xs text-blue-700">Queue position: {uploadProgress.queuePosition}</span>
                  )}
                </div>
                <div className="w-full bg-blue-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress.progress}%` }}
                  />
                </div>
                {isPolling && (
                  <div className="mt-2 flex items-center gap-2 text-xs text-blue-700">
                    <Loader2 className="h-3 w-3 animate-spin" />
                    <span>Processing in background...</span>
                  </div>
                )}
              </div>
            )}
            {/* File Upload Section */}
            <div className="space-y-4">
              {/* Upload Options */}
              <div className="flex gap-2 justify-center">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => { setIsCameraMode(false); handleFileButtonClick(); }}
                  className={!isCameraMode ? "bg-primary text-primary-foreground" : ""}
                >
                  <UploadCloud className="h-4 w-4 mr-2" />
                  {t('upload.uploadFile')}
                </Button>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple={true}
                  accept="application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,text/csv,text/plain,text/rtf,application/rtf,image/jpeg,image/png,image/gif,image/bmp,image/tiff,image/webp,application/zip,application/vnd.oasis.opendocument.text,application/vnd.oasis.opendocument.spreadsheet,.pdf,.doc,.docx,.xls,.xlsx,.csv,.txt,.rtf,.jpg,.jpeg,.png,.gif,.bmp,.tiff,.webp,.zip,.odt,.ods"
                  onChange={handleFileInputChange}
                  style={{ display: 'none' }}
                />
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
                  <input {...getInputProps({ multiple: true })} id="file-upload" name="file" />
                  <UploadCloud className={`mx-auto h-12 w-12 mb-3 ${errors.file ? "text-destructive" : "text-muted-foreground"}`} />
                  {formData.files.length > 0 ? (
                    <div className="text-center space-y-3">
                      <div className="flex items-center justify-center gap-2">
                        <FileText className="h-8 w-8 text-green-600" />
                        <div>
                          <p className="font-semibold text-foreground">
                            {formData.files.length} file{formData.files.length > 1 ? 's' : ''} selected
                          </p>
                          <p className="text-sm text-muted-foreground">
                            Total: {(formData.files.reduce((sum, f) => sum + f.size, 0) / 1024 / 1024).toFixed(2)} MB
                          </p>
                        </div>
                      </div>
                      
                      {/* File list */}
                      <div className="max-h-32 overflow-y-auto border rounded p-2 bg-muted/20">
                        {formData.files.map((file, index) => (
                          <div key={index} className="flex items-center justify-between py-1 px-2 hover:bg-muted/40 rounded text-sm">
                            <span className="truncate max-w-[200px]">{file.name}</span>
                            <div className="flex items-center gap-2">
                              <span className="text-xs text-muted-foreground">
                                {(file.size / 1024 / 1024).toFixed(1)} MB
                              </span>
                              <button
                                type="button"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  setFormData(p => ({
                                    ...p, 
                                    files: p.files.filter((_, i) => i !== index)
                                  }));
                                }}
                                className="text-destructive hover:text-destructive/80 text-xs font-medium"
                              >
                                ✕
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                      
                      <div className="flex gap-2 justify-center">
                        <Button 
                          type="button" 
                          variant="outline" 
                          size="sm" 
                          onClick={(e) => { e.stopPropagation(); handleFileButtonClick(); }}
                          disabled={formData.files.length >= 10}
                        >
                          Add more files {formData.files.length}/10
                        </Button>
                        <Button 
                          type="button" 
                          variant="link" 
                          size="sm" 
                          className="text-destructive" 
                          onClick={(e) => { e.stopPropagation(); setFormData(p => ({...p, files: []})); }}
                        >
                          Clear all
                        </Button>
                      </div>
                    </div>
                  ) : isDragActive ? (
                    <p className="text-primary font-semibold">Drop the files here ...</p>
                  ) : (
                    <div>
                      <p className="text-muted-foreground mb-2">
                        Drag & drop documents or images here, or <Button type="button" variant="link" className="p-0 h-auto" onClick={handleFileButtonClick}>click to select</Button>
                      </p>
                      <p className="text-xs text-muted-foreground">
                        You can select multiple files (up to 10) at once
                      </p>
                    </div>
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

            {/* Security & supported file types info */}
            <div className="text-xs space-y-2">
              <div className="flex items-center gap-2 text-green-700 bg-green-50 p-2 rounded border border-green-200">
                <Shield className="h-4 w-4 flex-shrink-0" />
                <span><strong>Security:</strong> All uploaded files are automatically scanned for viruses and malware before processing.</span>
              </div>
              <p className="text-muted-foreground">{t('upload.fileNote')}</p>
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



            {/* Consent Confirmation */}
            <div className="space-y-2">
              <div className="flex items-start space-x-2">
                <input
                  id="lawful-consent"
                  type="checkbox"
                  checked={consentChecked}
                  onChange={(e) => {
                    setConsentChecked(e.target.checked);
                    setErrors(prev => ({ ...prev, consent: undefined }));
                  }}
                  className="mt-1 h-4 w-4 text-primary focus:ring-primary border-gray-300"
                  aria-invalid={!!errors.consent}
                  aria-describedby={errors.consent ? 'consent-error' : undefined}
                />
                <Label htmlFor="lawful-consent" className="text-sm font-normal cursor-pointer">
                  This document was obtained through lawful means, and I have the necessary authorization to share it.
                </Label>
              </div>
              {errors.consent && (
                <p id="consent-error" className="text-sm text-destructive flex items-center">
                  <AlertCircle className="h-4 w-4 mr-1" />{errors.consent}
                </p>
              )}
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
            <Button type="submit" className="w-full md:w-1/2 py-3 text-base" disabled={isSubmitting || !consentChecked}>
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

import React, { useState, useCallback, useEffect } from "react";
// Remove Supabase import - we don't use it anymore
// import { supabase } from "../utils/supabaseClient";
// Remove brain import - we'll use direct fetch instead
// import brain from "../brain";
// import { v4 as uuidv4 } from 'uuid'; // Not available, will use Date.now() + random string
import { useDropzone } from "react-dropzone";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { UploadCloud, FileText, AlertCircle, CheckCircle, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { countriesData, Country, State } from "utils/countriesData"; // Added

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

interface FormData {
  title: string;
  description: string;
  country: string;
  stateProvince: string;
  adminLevel: string;
  file: File | null;
  uploader_name: string; // New
  uploader_email: string; // New
}

export default function UploadDocumentPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState<FormData>({
    title: "",
    description: "",
    country: "",
    stateProvince: "",
    adminLevel: "",
    file: null,
    uploader_name: "", // New
    uploader_email: "", // New
  });
  const [currentStates, setCurrentStates] = useState<State[]>([]); // Changed type to State[]
  const [errors, setErrors] = useState<Partial<Record<keyof FormData | 'captcha', string>>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  // const [captchaToken, setCaptchaToken] = useState<string | null>(null); // Placeholder for CAPTCHA integration

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
    if (!formData.title.trim()) newErrors.title = "Document title is required.";
    if (!formData.description.trim()) newErrors.description = "Description is required.";
    if (formData.description.trim().length < 20) newErrors.description = "Description must be at least 20 characters.";
    if (!formData.country) newErrors.country = "Country selection is required.";
    // Adjusted state/province validation
    if (!formData.adminLevel) {
      newErrors.adminLevel = "Administrative level is required.";
    } else if (formData.adminLevel === "federal" && formData.stateProvince !== "Federal / National") {
      // MYA-19: If admin level is federal, stateProvince MUST be 'Federal / National'
      newErrors.stateProvince = "State/Province must be \"Federal / National\" for this admin level.";
    } else if (formData.adminLevel === "state" && (!formData.stateProvince || formData.stateProvince === "Federal / National")) {
        const selectedCountry = countriesData.find(c => c.name === formData.country);
        // Allow "Federal / National" if the country has NO other states listed.
        if (selectedCountry && selectedCountry.states.length > 0 && formData.stateProvince === "Federal / National") {
             newErrors.stateProvince = "Please select an actual State/Province, not Federal/National, for this admin level.";
        } else if (!formData.stateProvince) {
            newErrors.stateProvince = "State/Province is required for this admin level.";
        }
        // If selectedCountry.states.length is 0, then "Federal / National" is the only valid choice for stateProvince when adminLevel is 'state'.
    } else if (formData.adminLevel === "federal" && !formData.stateProvince) { // Should be set by handleSelectChange
      // If admin level is federal, automatically set state/province to 'Federal / National' if not already chosen.
      // This simplifies UX, as there's no other valid choice. The form will re-render with this set.
      // We'll handle this auto-selection in handleSelectChange for adminLevel or directly before submission if preferred.
      // For now, we ensure that *if* it's federal, stateProvince is not empty (implying it needs to be Federal/National)
       if (!formData.stateProvince) newErrors.stateProvince = "Please select \"Federal / National\" for State/Province.";
    }

    if (!formData.file) newErrors.file = "A PDF file is required for upload.";
    // if (!captchaToken) newErrors.captcha = "Please complete the CAPTCHA."; // CAPTCHA validation placeholder

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

    if (!formData.file) {
      toast.error("File Missing", { id: "upload-toast", description: "Please select a PDF file to upload." });
      setIsSubmitting(false);
      return;
    }

    try {
      // Upload using the new backend API
      toast.loading("Uploading file...", { id: "upload-toast" });
      
      // Create FormData for the backend upload
      const uploadFormData = new FormData();
      uploadFormData.append('file', formData.file);
      uploadFormData.append('title', formData.title);
      uploadFormData.append('country', formData.country);
      uploadFormData.append('state', formData.stateProvince || formData.country); // Use country as fallback
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
          errorMessage = errorData.detail || errorData.message || errorMessage;
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
    <div className="min-h-screen bg-muted/40 py-8 px-4 flex justify-center items-start font-sans">
      <Card className="w-full max-w-2xl shadow-xl">
        <form onSubmit={handleSubmit} noValidate>
          <CardHeader className="text-center">
            <CardTitle className="text-3xl font-serif">Upload Corruption Document</CardTitle>
            <CardDescription>
              Expose corruption anonymously. All submissions are reviewed before publication.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* File Upload Section */}
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
            {errors.file && <p className="text-sm text-destructive mt-1 flex items-center"><AlertCircle className="h-4 w-4 mr-1" />{errors.file}</p>}

            {/* Supported file types info */}
            <div className="text-xs text-muted-foreground">
              <p>Supported formats: PDF, Word (DOC/DOCX), Excel (XLS/XLSX), CSV, Text files, Images (JPG, PNG, GIF, BMP, TIFF, WebP), RTF, ODT, ODS, ZIP</p>
            </div>

            {/* Form Fields */}
            <div className="space-y-2">
              <Label htmlFor="title">Document Title <span className="text-destructive">*</span></Label>
              <Input id="title" name="title" value={formData.title} onChange={handleChange} placeholder="e.g., City Council Meeting Minutes March 2024" className={errors.title ? "border-destructive" : ""} aria-invalid={!!errors.title} aria-describedby={errors.title ? "title-error" : undefined} />
              {errors.title && <p id="title-error" className="text-sm text-destructive flex items-center"><AlertCircle className="h-4 w-4 mr-1" />{errors.title}</p>}
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description (min 20 characters) <span className="text-destructive">*</span></Label>
              <Textarea id="description" name="description" value={formData.description} onChange={handleChange} placeholder="Provide a brief summary of the document's content and significance..." rows={4} className={errors.description ? "border-destructive" : ""} aria-invalid={!!errors.description} aria-describedby={errors.description ? "description-error" : undefined} />
              {errors.description && <p id="description-error" className="text-sm text-destructive flex items-center"><AlertCircle className="h-4 w-4 mr-1" />{errors.description}</p>}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="country">Country <span className="text-destructive">*</span></Label>
                <Select name="country" value={formData.country} onValueChange={(value) => handleSelectChange("country", value)} >
                  <SelectTrigger id="country" className={errors.country ? "border-destructive" : ""} aria-invalid={!!errors.country} aria-describedby={errors.country ? "country-error" : undefined}>
                    <SelectValue placeholder="Select country" />
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
                  State / Province 
                  {formData.adminLevel === 'state' && <span className="text-destructive">*</span>}
                </Label>
                <Select 
                  name="stateProvince" 
                  value={formData.stateProvince} 
                  onValueChange={(value) => handleSelectChange("stateProvince", value)}
                  disabled={!formData.country || (formData.adminLevel !== 'federal' && currentStates.length <= 1) || formData.adminLevel === 'federal' || (formData.adminLevel === 'state' && currentStates.length > 0 && currentStates[0].name === "Federal / National" && currentStates.length === 1) }
                >
                  <SelectTrigger id="stateProvince" className={errors.stateProvince ? "border-destructive" : ""} aria-invalid={!!errors.stateProvince} aria-describedby={errors.stateProvince ? "stateProvince-error" : undefined}>
                    <SelectValue placeholder={formData.adminLevel === 'federal' ? "Federal / National (auto)" : "Select state/province"} />
                  </SelectTrigger>
                  <SelectContent>
                    {currentStates.map(s => <SelectItem key={s.name} value={s.name} disabled={s.name === "Federal / National" && formData.adminLevel === 'state' && currentStates.length > 1}>{s.name}</SelectItem>)}
                  </SelectContent>
                </Select>
                {errors.stateProvince && <p id="stateProvince-error" className="text-sm text-destructive flex items-center"><AlertCircle className="h-4 w-4 mr-1" />{errors.stateProvince}</p>}
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="adminLevel">Administrative Level <span className="text-destructive">*</span></Label>
                <Select name="adminLevel" value={formData.adminLevel} onValueChange={(value) => handleSelectChange("adminLevel", value)}>
                  <SelectTrigger id="adminLevel" className={errors.adminLevel ? "border-destructive" : ""} aria-invalid={!!errors.adminLevel} aria-describedby={errors.adminLevel ? "adminLevel-error" : undefined}>
                    <SelectValue placeholder="Select admin level" />
                  </SelectTrigger>
                  <SelectContent>
                    {adminLevels.map(level => <SelectItem key={level.id} value={level.id}>{level.name}</SelectItem>)}
                  </SelectContent>
                </Select>
                {errors.adminLevel && <p id="adminLevel-error" className="text-sm text-destructive flex items-center"><AlertCircle className="h-4 w-4 mr-1" />{errors.adminLevel}</p>}
              </div>
            </div>

            {/* Uploader Info (Optional) */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="uploader_name">Your Name (Optional)</Label>
                <Input id="uploader_name" name="uploader_name" value={formData.uploader_name} onChange={handleChange} placeholder="e.g., Jane Doe" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="uploader_email">Your Email (Optional)</Label>
                <Input id="uploader_email" name="uploader_email" type="email" value={formData.uploader_email} onChange={handleChange} placeholder="e.g., jane.doe@example.com" />
              </div>
            </div>

            {/* CAPTCHA Placeholder */}
            <div className="space-y-2">
              <Label>CAPTCHA</Label>
              <div className="p-4 border rounded-md bg-muted/50 text-center text-muted-foreground">
                [CAPTCHA (e.g., hCaptcha, reCAPTCHA) will be integrated here]
                {/* Example: <HCaptcha sitekey="your-site-key" onVerify={setCaptchaToken} /> */}
              </div>
              {errors.captcha && <p className="text-sm text-destructive flex items-center"><AlertCircle className="h-4 w-4 mr-1" />{errors.captcha}</p>}
            </div>

          </CardContent>
          <CardFooter className="flex flex-col items-center space-y-3">
            <p className="text-xs text-muted-foreground text-center px-4">
                By submitting, you confirm that this document exposes legitimate corruption and that you have the right to share it anonymously.
            </p>
            <Button type="submit" className="w-full md:w-1/2 py-3 text-base" disabled={isSubmitting}>
              {isSubmitting ? (
                <><Loader2 className="mr-2 h-5 w-5 animate-spin" /> Submitting...</>
              ) : (
                <><UploadCloud className="mr-2 h-5 w-5" /> Submit Document for Review</>
              )}
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}

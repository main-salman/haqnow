import React, { useEffect, useState } from "react";
import { useTranslation, Trans } from "react-i18next";
import { Instagram, Linkedin, Youtube, ArrowUpRight, Music } from "lucide-react";
import Version from "./Version";

interface SocialMediaLinks {
  instagram: string;
  linkedin: string;
  tiktok: string;
  youtube: string;
  upscrolled: string;
}

// Resilient default fallbacks in case API is slow or unavailable
const DEFAULT_LINKS: SocialMediaLinks = {
  instagram: "https://www.instagram.com/haqnow_org/",
  linkedin: "https://www.linkedin.com/company/haqnow/",
  tiktok: "https://www.tiktok.com/@haqnow",
  youtube: "https://www.youtube.com/@haqnow-org",
  upscrolled: "https://share.upscrolled.com/en/user/a8f5f0b6-7dcb-4501-a869-4036311cdf72",
};

export default function Footer() {
  const { t, i18n } = useTranslation();
  const [links, setLinks] = useState<SocialMediaLinks>(DEFAULT_LINKS);

  useEffect(() => {
    const controller = new AbortController();
    const fetchSocialLinks = async () => {
      try {
        const res = await fetch("/api/site-settings/social-media", {
          signal: controller.signal,
        });
        if (res.ok) {
          const data = (await res.json()) as Partial<SocialMediaLinks>;
          setLinks({
            instagram: data.instagram || DEFAULT_LINKS.instagram,
            linkedin: data.linkedin || DEFAULT_LINKS.linkedin,
            tiktok: data.tiktok || DEFAULT_LINKS.tiktok,
            youtube: data.youtube || DEFAULT_LINKS.youtube,
            upscrolled: data.upscrolled || DEFAULT_LINKS.upscrolled,
          });
        }
      } catch (err) {
        console.warn("Failed to fetch social media links, using secure defaults:", err);
      }
    };

    fetchSocialLinks();
    return () => controller.abort();
  }, []);

  // Set RTL support based on active language (e.g. Arabic)
  const isRtl = i18n.language === "ar";

  return (
    <footer className="border-t border-border bg-muted/10 py-8 mt-12 w-full">
      <div className="container mx-auto px-4 flex flex-col items-center justify-center space-y-6">
        
        {/* Premium Social Media Links Section */}
        <div className="flex flex-wrap items-center justify-center gap-6" dir={isRtl ? "rtl" : "ltr"}>
          {/* Instagram */}
          {links.instagram && (
            <a
              href={links.instagram}
              target="_blank"
              rel="noopener noreferrer"
              className="group flex items-center justify-center p-2.5 rounded-full border border-gray-200 bg-white hover:border-[#E1306C]/30 hover:shadow-[0_0_15px_rgba(225,48,108,0.15)] text-gray-500 hover:text-[#E1306C] transition-all duration-300 transform hover:-translate-y-0.5"
              aria-label="Instagram"
            >
              <Instagram className="h-5 w-5 transition-transform duration-300 group-hover:scale-110" />
            </a>
          )}

          {/* LinkedIn */}
          {links.linkedin && (
            <a
              href={links.linkedin}
              target="_blank"
              rel="noopener noreferrer"
              className="group flex items-center justify-center p-2.5 rounded-full border border-gray-200 bg-white hover:border-[#0077B5]/30 hover:shadow-[0_0_15px_rgba(0,119,181,0.15)] text-gray-500 hover:text-[#0077B5] transition-all duration-300 transform hover:-translate-y-0.5"
              aria-label="LinkedIn"
            >
              <Linkedin className="h-5 w-5 transition-transform duration-300 group-hover:scale-110" />
            </a>
          )}

          {/* TikTok */}
          {links.tiktok && (
            <a
              href={links.tiktok}
              target="_blank"
              rel="noopener noreferrer"
              className="group flex items-center justify-center p-2.5 rounded-full border border-gray-200 bg-white hover:border-[#FE2C55]/30 hover:shadow-[0_0_15px_rgba(254,44,85,0.15)] text-gray-500 hover:text-[#FE2C55] transition-all duration-300 transform hover:-translate-y-0.5"
              aria-label="TikTok"
            >
              <Music className="h-5 w-5 transition-transform duration-300 group-hover:scale-110" />
            </a>
          )}

          {/* YouTube */}
          {links.youtube && (
            <a
              href={links.youtube}
              target="_blank"
              rel="noopener noreferrer"
              className="group flex items-center justify-center p-2.5 rounded-full border border-gray-200 bg-white hover:border-[#FF0000]/30 hover:shadow-[0_0_15px_rgba(255,0,0,0.15)] text-gray-500 hover:text-[#FF0000] transition-all duration-300 transform hover:-translate-y-0.5"
              aria-label="YouTube"
            >
              <Youtube className="h-5 w-5 transition-transform duration-300 group-hover:scale-110" />
            </a>
          )}

          {/* Upscrolled */}
          {links.upscrolled && (
            <a
              href={links.upscrolled}
              target="_blank"
              rel="noopener noreferrer"
              className="group flex items-center gap-1.5 px-4 py-2 rounded-full border border-gray-200 bg-white hover:border-[#8B5CF6]/30 hover:shadow-[0_0_15px_rgba(139,92,246,0.15)] text-gray-500 hover:text-[#8B5CF6] text-sm font-medium transition-all duration-300 transform hover:-translate-y-0.5"
              aria-label="Upscrolled Profile"
            >
              <span>Upscrolled</span>
              <ArrowUpRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
            </a>
          )}
        </div>

        {/* Content Translation / Info Section */}
        <div className="flex flex-col items-center justify-center space-y-2.5 w-full text-center">
          <p className="text-sm text-muted-foreground max-w-2xl leading-relaxed">
            {t("footer.copyright")}
          </p>
          <p className="text-xs text-muted-foreground max-w-3xl leading-relaxed mb-2 opacity-80">
            {t("footer.complianceJargon")}
          </p>
          <p className="text-sm text-muted-foreground font-medium max-w-2xl leading-relaxed">
            {t("footer.privacyPromise")}
          </p>
          <div className="flex flex-wrap items-center justify-center text-sm text-muted-foreground gap-2 pt-1">
            <span>
              <Trans
                i18nKey="footer.poweredBy"
                components={{
                  link: (
                    <a
                      className="text-indigo-600 hover:text-indigo-800 underline font-medium transition-colors"
                      href="https://thaura.ai/home"
                      target="_blank"
                      rel="noopener noreferrer"
                    />
                  ),
                }}
              />
            </span>
            <span className="hidden sm:inline text-gray-300">|</span>
            <div className="flex items-center">
              <span className="text-xs text-gray-400 uppercase tracking-wider">{t("footer.versionLabel", "Build")}</span>
              <Version />
            </div>
          </div>
        </div>

      </div>
    </footer>
  );
}

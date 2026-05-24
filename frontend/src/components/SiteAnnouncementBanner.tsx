import React, { useEffect, useState } from "react";
import { useTranslation, Trans } from "react-i18next";

interface Announcement {
  enabled: boolean;
  content: string;
}

export default function SiteAnnouncementBanner() {
  const { t } = useTranslation();
  const [announcement, setAnnouncement] = useState<Announcement | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const fetchAnnouncement = async () => {
      try {
        const res = await fetch("/api/site-settings/announcement", {
          signal: controller.signal,
        });
        if (!res.ok) return;
        const data = (await res.json()) as Announcement;
        setAnnouncement(data);
      } catch {}
    };
    fetchAnnouncement();
    return () => controller.abort();
  }, []);

  if (!announcement?.enabled || !announcement.content) return null;

  // Check if the banner contains default Freedom Advocacy Network or weekly meeting text
  const isDefaultContent = 
    announcement.content.includes("Freedom Advocacy Network") || 
    announcement.content.includes("weekly meeting") ||
    announcement.content.includes("sister organization");

  return (
    <div className="w-full bg-amber-50 border-b border-amber-200 text-amber-900">
      <div className="container mx-auto px-4 py-2 text-sm">
        {isDefaultContent ? (
          <Trans
            i18nKey="homepage.announcementBanner"
            defaults="Check out weekly meeting by our sister organization <link>Freedom Advocacy Network</link>"
            components={{
              link: (
                <a
                  className="underline hover:text-amber-750 font-semibold transition-colors"
                  href="https://freedom-advocacy.net/"
                  target="_blank"
                  rel="noopener noreferrer"
                />
              )
            }}
          />
        ) : (
          <span dangerouslySetInnerHTML={{ __html: announcement.content }} />
        )}
      </div>
    </div>
  );
}

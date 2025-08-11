import React, { useEffect, useState } from "react";

interface Announcement {
  enabled: boolean;
  content: string;
}

export default function SiteAnnouncementBanner() {
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

  return (
    <div className="w-full bg-amber-50 border-b border-amber-200 text-amber-900">
      <div className="container mx-auto px-4 py-2 text-sm" dangerouslySetInnerHTML={{ __html: announcement.content }} />
    </div>
  );
}



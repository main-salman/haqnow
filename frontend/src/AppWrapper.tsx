import { useEffect, useState } from "react";
import { RouterProvider } from "react-router-dom";
import { DEFAULT_THEME } from "./constants/default-theme";
import { Head } from "./internal-components/Head";
import { ThemeProvider } from "./internal-components/ThemeProvider";
import { OuterErrorBoundary } from "./prod-components/OuterErrorBoundary";
import { router } from "./router";
import "./i18n"; // Initialize i18n system
import { initializeTranslations } from "./i18n";

export const AppWrapper = () => {
  const [translationsLoaded, setTranslationsLoaded] = useState(false);

  useEffect(() => {
    // Load dynamic translations from admin-controlled database before rendering
    const loadTranslations = async () => {
      try {
        await initializeTranslations();
        console.log("✅ All translations loaded, rendering app...");
      } catch (error) {
        console.warn("⚠️ Translation loading failed, using static fallback:", error);
      } finally {
        setTranslationsLoaded(true);
      }
    };
    
    loadTranslations();
  }, []);

  // Show loading screen until translations are ready
  if (!translationsLoaded) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        fontFamily: 'system-ui, sans-serif',
        color: '#666'
      }}>
        Loading...
      </div>
    );
  }

  return (
    <OuterErrorBoundary>
      <ThemeProvider defaultTheme={DEFAULT_THEME}>
        <RouterProvider router={router} />
        <Head />
      </ThemeProvider>
    </OuterErrorBoundary>
  );
};

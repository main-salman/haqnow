import { useEffect } from "react";
import { RouterProvider } from "react-router-dom";
import { DEFAULT_THEME } from "./constants/default-theme";
import { Head } from "./internal-components/Head";
import { ThemeProvider } from "./internal-components/ThemeProvider";
import { OuterErrorBoundary } from "./prod-components/OuterErrorBoundary";
import { router } from "./router";
import "./i18n"; // Initialize i18n system
import { initializeTranslations } from "./i18n";

export const AppWrapper = () => {
  useEffect(() => {
    // Load dynamic translations from admin-controlled database
    initializeTranslations();
  }, []);

  return (
    <OuterErrorBoundary>
      <ThemeProvider defaultTheme={DEFAULT_THEME}>
        <RouterProvider router={router} />
        <Head />
      </ThemeProvider>
    </OuterErrorBoundary>
  );
};

import { RouterProvider } from "react-router-dom";
import { DEFAULT_THEME } from "./constants/default-theme";
import { Head } from "./internal-components/Head";
import { ThemeProvider } from "./internal-components/ThemeProvider";
import { OuterErrorBoundary } from "./prod-components/OuterErrorBoundary";
import { router } from "./router";

export const AppWrapper = () => {
  return (
    <OuterErrorBoundary>
      <ThemeProvider defaultTheme={DEFAULT_THEME}>
        <RouterProvider router={router} />
        <Head />
      </ThemeProvider>
    </OuterErrorBoundary>
  );
};

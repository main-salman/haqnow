import type { ReactNode } from "react";
import { ErrorBoundary } from "react-error-boundary";

interface Props {
  children: ReactNode;
}

export const OuterErrorBoundary = ({ children }: Props) => {
  return (
    <ErrorBoundary
      fallback={null}
      onError={(error) => {
        console.error("Caught error in AppWrapper", error.message, error.stack);
      }}
    >
      {children}
    </ErrorBoundary>
  );
};

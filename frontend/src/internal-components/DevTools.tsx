import { useEffect } from "react";
import { MessageEmitter } from "../dev-components/Beacon";
import { InternalErrorBoundary } from "../dev-components/InternalErrorBoundary";
import { UserErrorBoundary } from "../dev-components/UserErrorBoundary";

interface Props {
  children: React.ReactNode;
  shouldRender: boolean;
}

function logReason(event: PromiseRejectionEvent) {
  console.error(event?.reason);
}

/**
 * Render extra dev tools around the app when in dev mode,
 * but only render the app itself in prod mode
 */
export const DevTools = ({ children, shouldRender }: Props) => {
  useEffect(() => {
    if (shouldRender) {
      window.addEventListener("unhandledrejection", logReason);

      return () => {
        window.removeEventListener("unhandledrejection", logReason);
      };
    }
  }, [shouldRender]);

  if (shouldRender) {
    return (
      <InternalErrorBoundary>
        <UserErrorBoundary>
          <MessageEmitter>{children}</MessageEmitter>
        </UserErrorBoundary>
      </InternalErrorBoundary>
    );
  }

  return <>{children}</>;
};

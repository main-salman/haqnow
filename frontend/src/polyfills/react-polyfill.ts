import React from "react";

type ReactWithUse = typeof React & { use: (promise: any) => any };

// Polyfill for React.use if it doesn't exist
if (!("use" in React)) {
  (React as ReactWithUse).use = function use(promise) {
    if (
      typeof promise === "object" &&
      promise !== null &&
      typeof promise.then === "function"
    ) {
      // For promises, we need to handle the suspense mechanism
      let status = promise.status;
      if (status === undefined) {
        // Attach status to the promise
        let suspender = promise;
        suspender.status = "pending";
        suspender.then(
          (result) => {
            if (suspender.status === "pending") {
              suspender.status = "fulfilled";
              suspender.value = result;
            }
          },
          (error) => {
            if (suspender.status === "pending") {
              suspender.status = "rejected";
              suspender.reason = error;
            }
          },
        );
        throw suspender;
      } else if (status === "fulfilled") {
        return promise.value;
      } else if (status === "rejected") {
        throw promise.reason;
      } else {
        throw promise;
      }
    } else if (
      typeof promise === "object" &&
      promise !== null &&
      typeof promise._context !== "undefined"
    ) {
      // For React Context
      return React.useContext(promise._context || promise);
    } else if (
      typeof promise === "object" &&
      promise !== null &&
      typeof promise.$$typeof !== "undefined"
    ) {
      // For React Context (alternative check)
      return React.useContext(promise);
    } else {
      // For other context-like objects
      return React.useContext(promise);
    }
  };
}

export default React;

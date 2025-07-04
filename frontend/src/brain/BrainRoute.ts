import { HandleHealthzData } from "./data-contracts";

export namespace Brain {
  /**
   * No description
   * @name handle_healthz
   * @summary Handle Healthz
   * @request GET:/_healthz
   */
  export namespace handle_healthz {
    export type RequestParams = {};
    export type RequestQuery = {};
    export type RequestBody = never;
    export type RequestHeaders = {};
    export type ResponseBody = HandleHealthzData;
  }
}

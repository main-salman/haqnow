import { HandleHealthzData } from "./data-contracts";
import { HttpClient, RequestParams } from "./http-client";

export class Brain<SecurityDataType = unknown> extends HttpClient<SecurityDataType> {
  /**
   * No description
   *
   * @name handle_healthz
   * @summary Handle Healthz
   * @request GET:/_healthz
   */
  handle_healthz = (params: RequestParams = {}) =>
    this.request<HandleHealthzData, any>({
      path: `/_healthz`,
      method: "GET",
      ...params,
    });
}

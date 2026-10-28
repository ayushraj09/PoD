import "server-only";
import DodoPayments from "dodopayments";

export const dodo = () =>
  new DodoPayments({
    bearerToken: process.env.DODO_API_KEY!,
    environment: process.env.DODO_ENVIRONMENT === "live_mode" ? "live_mode" : "test_mode",
  });

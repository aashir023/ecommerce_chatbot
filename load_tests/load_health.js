// load_health.js
import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  stages: [
    { duration: "1m", target: 5 },
    { duration: "1m", target: 10 },
    { duration: "1m", target: 15 },
    { duration: "1m", target: 20 },
  ],
  thresholds: {
    http_req_failed: ["rate<0.02"],
    http_req_duration: ["p(95)<1500"],
  },
};

const BASE = "https://ecommerce-chatbot-proxy.aashirali619.workers.dev";

export default function () {
  const res = http.get(`${BASE}/health`);
  check(res, { "health 200": (r) => r.status === 200 });
  sleep(1); // prevents unrealistic hammering
}

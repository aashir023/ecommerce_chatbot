import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  scenarios: {
    capped_chat_test: {
      executor: "shared-iterations",
      vus: 5,
      iterations: 150, // hard cap on total requests
      maxDuration: "10m",
    },
  },
  thresholds: {
    http_req_failed: ["rate<0.05"],
    http_req_duration: ["p(95)<20000"],
  },
};

const BASE = "https://ecommerce-chatbot-proxy.aashirali619.workers.dev";

export default function () {
  // unique user per iteration keeps history short => lower token cost
  const uid = `budget_user_${__VU}_${__ITER}`;

  const payload = JSON.stringify({
    user_id: uid,
    message: "Warranty details for TCL LED 75 inch?",
  });

  const res = http.post(`${BASE}/chat`, payload, {
    headers: { "Content-Type": "application/json" },
    timeout: "40s",
  });

  check(res, {
    "chat 200": (r) => r.status === 200,
    "has reply": (r) => {
      try {
        const body = JSON.parse(r.body);
        return typeof body.reply === "string" && body.reply.length > 0;
      } catch {
        return false;
      }
    },
  });

  sleep(1);
}

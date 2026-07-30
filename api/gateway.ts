export const config = {
  runtime: "edge",
};

type ServiceConfig = {
  url: string;
  method: "GET" | "POST";
  keyEnv: string;
  buildHeaders: (key: string) => Record<string, string>;
  keyQueryName?: string;
};

const SERVICES: Record<string, ServiceConfig> = {
  brave: {
    url: "https://api.search.brave.com/res/v1/web/search",
    method: "GET",
    keyEnv: "BRAVE_SEARCH_API_KEY",
    buildHeaders: (key) => ({
      Accept: "application/json",
      "Accept-Encoding": "gzip",
      "X-Subscription-Token": key,
    }),
  },
  google_places: {
    url: "https://places.googleapis.com/v1/places:searchText",
    method: "POST",
    keyEnv: "GOOGLE_MAPS_API_KEY",
    buildHeaders: (key) => ({
      "Content-Type": "application/json",
      "X-Goog-Api-Key": key,
      "X-Goog-FieldMask":
        "places.displayName,places.formattedAddress,places.websiteUri," +
        "places.internationalPhoneNumber,places.googleMapsUri," +
        "places.businessStatus,places.primaryTypeDisplayName",
    }),
  },
  serpapi: {
    url: "https://serpapi.com/search.json",
    method: "GET",
    keyEnv: "SERPAPI_API_KEY",
    keyQueryName: "api_key",
    buildHeaders: () => ({ Accept: "application/json" }),
  },
  foursquare: {
    url: "https://places-api.foursquare.com/places/search",
    method: "GET",
    keyEnv: "FOURSQUARE_API_KEY",
    buildHeaders: (key) => ({
      Accept: "application/json",
      Authorization: `Bearer ${key}`,
      "X-Places-Api-Version": "2025-06-17",
    }),
  },
  opencorporates: {
    url: "https://api.opencorporates.com/v0.4/companies/search",
    method: "GET",
    keyEnv: "OPENCORPORATES_API_TOKEN",
    keyQueryName: "api_token",
    buildHeaders: () => ({ Accept: "application/json" }),
  },
  pdl: {
    url: "https://api.peopledatalabs.com/v5/company/search",
    method: "GET",
    keyEnv: "PDL_API_KEY",
    buildHeaders: (key) => ({
      Accept: "application/json",
      "X-api-key": key,
    }),
  },
};

export default async function handler(req: Request): Promise<Response> {
  const expectedToken = process.env.TRADELEAD_GATEWAY_TOKEN || "";
  const suppliedToken = req.headers.get("X-TradeLead-Gateway-Token") || "";
  if (!expectedToken || suppliedToken !== expectedToken) {
    return jsonResponse({ error: "Unauthorized" }, 401);
  }

  const incomingUrl = new URL(req.url);
  const serviceName = (incomingUrl.searchParams.get("service") || "").toLowerCase();
  const service = SERVICES[serviceName];
  if (!service) {
    return jsonResponse({ error: "Unsupported gateway service" }, 400);
  }
  if (req.method !== service.method) {
    return jsonResponse({ error: `Expected ${service.method}` }, 405);
  }

  const providerKey = process.env[service.keyEnv] || "";
  if (!providerKey) {
    return jsonResponse({ error: `${service.keyEnv} is not configured` }, 503);
  }

  const targetUrl = new URL(service.url);
  incomingUrl.searchParams.forEach((value, name) => {
    if (name !== "service") {
      targetUrl.searchParams.append(name, value);
    }
  });
  if (service.keyQueryName) {
    targetUrl.searchParams.set(service.keyQueryName, providerKey);
  }

  try {
    const upstream = await fetch(targetUrl, {
      method: service.method,
      headers: service.buildHeaders(providerKey),
      body: service.method === "POST" ? await req.text() : undefined,
      redirect: "follow",
    });
    const body = await upstream.arrayBuffer();
    return new Response(body, {
      status: upstream.status,
      headers: {
        "Content-Type":
          upstream.headers.get("Content-Type") || "application/json",
        "Cache-Control": "no-store",
      },
    });
  } catch (error) {
    return jsonResponse(
      { error: `Gateway request failed: ${(error as Error).message}` },
      502,
    );
  }
}

function jsonResponse(payload: unknown, status: number): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
    },
  });
}

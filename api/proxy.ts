export const config = {
  runtime: 'edge',
};

export default async function handler(req: Request): Promise<Response> {
  const url = new URL(req.url);
  const target = url.searchParams.get("url");

  if (!target) {
    return new Response("TradeLead Proxy OK. Use ?url=https://...", {
      status: 200,
      headers: { "Content-Type": "text/plain" },
    });
  }

  try {
    const response = await fetch(target, {
      method: "GET",
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        Accept:
          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
      },
      redirect: "follow",
    });

    const body = await response.text();

    return new Response(body, {
      status: 200,
      headers: {
        "Content-Type":
          response.headers.get("Content-Type") || "text/html",
        "Access-Control-Allow-Origin": "*",
      },
    });
  } catch (e) {
    return new Response("Proxy error: " + (e as Error).message, {
      status: 502,
    });
  }
}

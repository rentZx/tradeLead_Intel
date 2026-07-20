// Cloudflare Worker - HTTP Proxy for TradeLead Intel V3
// Deploy via Cloudflare Dashboard → Workers & Pages → Create → Worker
// This worker runs on Cloudflare's global edge network (outside China)
// Usage: https://your-worker.workers.dev/?url=https://target-site.com/page

addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})

async function handleRequest(request) {
  const url = new URL(request.url)
  const target = url.searchParams.get('url')
  
  if (!target) {
    return new Response('TradeLead Proxy OK. Use ?url=https://...', { 
      status: 200,
      headers: { 'Content-Type': 'text/plain' } 
    })
  }

  try {
    const targetUrl = new URL(target)
    
    // Only allow HTTPS to prevent abuse
    if (targetUrl.protocol !== 'https:') {
      return new Response('Only HTTPS URLs allowed', { status: 400 })
    }

    const response = await fetch(target, {
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
      },
      redirect: 'follow',
    })

    const body = await response.text()
    
    return new Response(body, {
      status: 200,
      headers: {
        'Content-Type': response.headers.get('Content-Type') || 'text/html',
        'Access-Control-Allow-Origin': '*',
      }
    })
  } catch (e) {
    return new Response('Proxy error: ' + e.message, { status: 502 })
  }
}

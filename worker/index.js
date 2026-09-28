// Отдаёт mp3 из статики с поддержкой Range-запросов (206 Partial Content).
// Статика Workers на запрос с Range отвечает 200 с полным телом, а iOS Safari для <audio> требует 206.
export default {
  async fetch(request, env) {
    const asset = await env.ASSETS.fetch(request);
    if (asset.status !== 200) return asset;

    const headers = new Headers(asset.headers);
    headers.set("Accept-Ranges", "bytes");
    const range = /^bytes=(\d*)-(\d*)$/.exec(request.headers.get("Range") ?? "");
    if (request.method !== "GET" || !range || (range[1] === "" && range[2] === "")) {
      return new Response(asset.body, { status: 200, headers });
    }

    const body = await asset.arrayBuffer();
    const size = body.byteLength;
    // bytes=start-end | bytes=start- | bytes=-suffixLength
    const start = range[1] === "" ? Math.max(size - Number(range[2]), 0) : Number(range[1]);
    const end = range[1] === "" || range[2] === "" ? size - 1 : Math.min(Number(range[2]), size - 1);
    if (start > end) {
      return new Response(null, { status: 416, headers: { "Content-Range": `bytes */${size}` } });
    }

    headers.set("Content-Range", `bytes ${start}-${end}/${size}`);
    headers.set("Content-Length", String(end - start + 1));
    return new Response(body.slice(start, end + 1), { status: 206, headers });
  },
};

export default {
  async fetch(request, env) {
    const origin = request.headers.get("Origin") || "";
    // Handle CORS preflight
    if (request.method === "OPTIONS") return cors(new Response(null, { status: 204 }), origin);

    const url = `https://ws.audioscrobbler.com/2.0/?method=user.getRecentTracks`
              + `&user=tonic-lastfm&limit=1&format=json&api_key=${env.LASTFM_API_KEY}`;

    const res  = await fetch(url);
    const data = await res.json();
    const track = data.recenttracks?.track?.[0];

    if (!track) {
      return cors(Response.json({ nowPlaying: false, track: null, artist: null }), origin);
    }

    return cors(Response.json({
      nowPlaying: track["@attr"]?.nowplaying === "true",
      track:  track.name,
      artist: track.artist["#text"],
      url:    track.url || null,
    }), origin);
  }
};

const ALLOWED_ORIGINS = new Set([
  "https://www.nicsheehan.com",
  "https://staging.nicsheehan.pages.dev",
]);

function cors(r, origin) {
  const h = new Headers(r.headers);
  const allowed = ALLOWED_ORIGINS.has(origin) ? origin : "https://www.nicsheehan.com";
  h.set("Access-Control-Allow-Origin", allowed);
  h.set("Access-Control-Allow-Methods", "GET, OPTIONS");
  h.set("Vary", "Origin");
  return new Response(r.body, { status: r.status, headers: h });
}

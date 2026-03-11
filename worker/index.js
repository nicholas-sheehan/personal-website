export default {
  async fetch(request, env) {
    // Handle CORS preflight
    if (request.method === "OPTIONS") return cors(new Response(null, { status: 204 }));

    const url = `https://ws.audioscrobbler.com/2.0/?method=user.getRecentTracks`
              + `&user=tonic-lastfm&limit=1&format=json&api_key=${env.LASTFM_API_KEY}`;

    const res  = await fetch(url);
    const data = await res.json();
    const track = data.recenttracks?.track?.[0];

    if (!track) {
      return cors(Response.json({ nowPlaying: false, track: null, artist: null }));
    }

    return cors(Response.json({
      nowPlaying: track["@attr"]?.nowplaying === "true",
      track:  track.name,
      artist: track.artist["#text"],
      url:    track.url || null,
    }));
  }
};

function cors(r) {
  const h = new Headers(r.headers);
  h.set("Access-Control-Allow-Origin", "https://www.nicsheehan.com");
  h.set("Access-Control-Allow-Methods", "GET, OPTIONS");
  return new Response(r.body, { status: r.status, headers: h });
}

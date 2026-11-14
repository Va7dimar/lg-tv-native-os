// The owner's list: edit this file to reorder, hide or rename things.
window.IMPETUS_CONFIG = {
  selfId: "org.va7dimar.home",

  // The focal door in the control room.
  appleTv: { id: "com.webos.app.hdmi2", label: "APPLE TV" },

  // TV apps opened at a set place (webOS launch params). Unverified on this
  // TV until the first run: if one lands on the app's start screen instead,
  // fix or drop its params here.
  shortcuts: [
    { id: "youtube.leanback.v4", label: "YOUTUBE", place: "Áskriftir",
      params: { contentTarget: "https://www.youtube.com/tv#/browse?c=FEsubscriptions" } },
    { id: "youtube.leanback.v4", label: "YOUTUBE", place: "Horfa síðar",
      params: { contentTarget: "https://www.youtube.com/tv#/watch?list=WL" } },
    { id: "spotify-beehive", label: "SPOTIFY", place: "Heim" }
  ],

  // App ids listed here come first, in this order; the rest follow by name.
  order: ["youtube.leanback.v4", "netflix", "com.disney.disneyplus-prod", "amazon", "spotify-beehive"],
  // App ids never shown. Inputs are not apps (they are system apps) and never
  // show in the list; only the Apple TV door above reaches one.
  hide: [],
  // Short names for apps whose title is too long for a bar.
  labels: { "spotify-beehive": "Spotify", "ui30": "Rakuten TV", "berlin.philharmonic": "Berliner Phil.", "org.webosbrew.hbchannel": "Homebrew" },

  idleSeconds: 60,
  connectionsEverySeconds: 5
};

// The owner's list: edit this file to reorder, hide or rename things.
window.IMPETUS_CONFIG = {
  selfId: "org.va7dimar.home",
  // Where the app is installed on the TV; used only when the page cannot
  // read its own folder from its address.
  appDir: "/media/developer/apps/usr/palm/applications/org.va7dimar.home",

  // The focal door in the control room.
  appleTv: { id: "com.webos.app.hdmi2", label: "APPLE TV" },

  // TV apps opened at a set place (webOS launch params). Unverified on this
  // TV until the first run: if one lands on the app's start screen instead,
  // fix or drop its params here.
  shortcuts: [
    { id: "youtube.leanback.v4", label: "YOUTUBE", place: "Subscriptions",
      params: { contentTarget: "https://www.youtube.com/tv#/browse?c=FEsubscriptions" } },
    { id: "youtube.leanback.v4", label: "YOUTUBE", place: "Watch later",
      params: { contentTarget: "https://www.youtube.com/tv#/watch?list=WL" } },
    { id: "spotify-beehive", label: "SPOTIFY", place: "Home" }
  ],

  // Scenes: one press opens what you watch and sets the TV around it. Up to
  // three are drawn. Every part is optional; a part this TV cannot do is
  // left out, and a scene with no part left is not drawn.
  //   launch                 app id, or "last" for what was on before Impetus
  //   pictureMode            cinema, game, vivid, ... (the TV's own names)
  //   picture                values set at once: backlight, contrast,
  //                          brightness, color, sharpness, colorTemperature,
  //                          energySaving
  //   sunMode                values set after sunset; the scene ends at sunrise
  //   screenOffAfterSeconds  the screen goes dark, the sound stays on
  //   volumeMax              the volume is lowered to this if it is higher
  //   sleepMinutes           standby after this long, with a 2 minute notice
  // Everything a scene changes is put back when it goes off.
  scenes: [
    { id: "film", label: "FILM NIGHT", does: "Apple TV · cinema · dim and warm after sunset",
      launch: "com.webos.app.hdmi2", pictureMode: "cinema",
      // Unconfirmed until the TV session: a negative colorTemperature is
      // taken to be the warm side. If the picture goes blue, flip the sign.
      sunMode: { backlight: 30, colorTemperature: -20 } },
    { id: "music", label: "MUSIC", does: "Spotify · screen off, sound on",
      launch: "spotify-beehive", screenOffAfterSeconds: 20 },
    { id: "winddown", label: "WIND DOWN", does: "Dim · quiet · standby in 60 min",
      launch: "last", picture: { backlight: 25 }, volumeMax: 12, sleepMinutes: 60 }
  ],

  // App ids listed here come first, in this order; the rest follow by name.
  order: ["youtube.leanback.v4", "com.disney.disneyplus-prod", "spotify-beehive"],
  // App ids never shown. Inputs are not apps (they are system apps) and never
  // show in the list; only the Apple TV door above reaches one.
  hide: ["netflix", "amazon", "ui30", "tv.twitch.tv.starshot.lg"],   // Netflix, Prime Video, Rakuten TV, Twitch
  // Short names for apps whose title is too long for a bar.
  labels: { "spotify-beehive": "Spotify", "berlin.philharmonic": "Berliner Phil.", "org.webosbrew.hbchannel": "Homebrew" },

  idleSeconds: 60,       // no key for this long: back to the living room
  stateEverySeconds: 5,  // scene and shield state, while the control room is open
  stillEverySeconds: 3,  // the APPLE TV still, while the control room is open
  engineEverySeconds: 5  // vitals, talkers and log, while the engine room is open
};

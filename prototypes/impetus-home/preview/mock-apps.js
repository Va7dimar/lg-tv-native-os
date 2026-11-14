// A stand-in app list for the PC preview, in the shape SAM's listApps gives:
// a few streaming apps, and the TV's own hidden and system entries that the
// page must leave out.
window.MOCK_APPS = [
  { id: "amazon", title: "Prime Video", visible: true, systemApp: false },
  { id: "berlin.philharmonic", title: "Berliner Philharmoniker", visible: true, systemApp: false },
  { id: "cdp-30", title: "Plex", visible: true, systemApp: false },
  { id: "com.disney.disneyplus-prod", title: "Disney+", visible: true, systemApp: false },
  { id: "com.webos.app.acrhdmi1", title: "LivePlus", visible: false, systemApp: true, "class": { hidden: true } },
  { id: "com.webos.app.acrhdmi2", title: "LivePlus", visible: false, systemApp: true, "class": { hidden: true } },
  { id: "com.webos.app.adhdmi1", title: "Ad Overlay App", visible: false, systemApp: true, "class": { hidden: true } },
  { id: "com.webos.app.adhdmi2", title: "Ad Overlay App", visible: false, systemApp: true, "class": { hidden: true } },
  { id: "com.webos.app.browser", title: "Web Browser", visible: true, systemApp: true },
  { id: "com.webos.app.discovery", title: "Apps", visible: true, systemApp: true },
  { id: "com.webos.app.hdmi1", title: "HDMI1", visible: false, systemApp: true },
  { id: "com.webos.app.hdmi2", title: "HDMI2", visible: false, systemApp: true },
  { id: "com.webos.app.hdmi3", title: "HDMI3", visible: false, systemApp: true },
  { id: "com.webos.app.hdmi4", title: "HDMI4", visible: false, systemApp: true },
  { id: "com.webos.app.homeconnect", title: "Home Dashboard", visible: true, systemApp: true },
  { id: "com.webos.app.livetv", title: "Live TV", visible: false, systemApp: true },
  { id: "com.webos.app.mediadiscovery", title: "Media Player", visible: true, systemApp: true, "class": { hidden: false } },
  { id: "com.webos.app.sportsteamsettings", title: "Sports Alert", visible: true, systemApp: true },
  { id: "com.webos.exampleapp.qmlapp.livetv", title: "com.webos.exampleapp.qmlapp.livetv", visible: false, systemApp: true, "class": { hidden: false } },
  { id: "netflix", title: "Netflix", visible: true, systemApp: false },
  { id: "org.webosbrew.hbchannel", title: "Homebrew Channel", visible: true, systemApp: false },
  { id: "spotify-beehive", title: "Spotify - Music and Podcasts", visible: true, systemApp: false },
  { id: "tv.twitch.tv.starshot.lg", title: "Twitch", visible: true, systemApp: false },
  { id: "ui30", title: "Rakuten TV", visible: true, systemApp: false },
  { id: "youtube.leanback.v4", title: "YouTube", visible: true, systemApp: false }
];
// The TV's bridge to its services: every call succeeds; listApps gives the list above.
window.PalmServiceBridge = function () {
  var s = this;
  s.call = function (u, p) {
    setTimeout(function () {
      s.onservicecallback(JSON.stringify(/listApps/.test(u) ? { returnValue: true, apps: window.MOCK_APPS } : { returnValue: true }));
    }, 50);
  };
};

# Vendored wl_webos_shell protocol

Source: webOS OSE `webos-wayland-extensions`

- Repository: https://github.com/webosose/webos-wayland-extensions
- File: `protocol/webos-shell.xml`
- Commit: `4b243378b451bd139466c242ae1e58753fea0fbf`
- Git blob: `cb3cabcef35810be06d881f373a62d67afa79ccd`
- Raw SHA256: `1f862d806f806b9bd0470a71551a6bab7a3d1a695799afa7a14c2e8989d7aa2e`
- Size: 9757 bytes
- License: Apache-2.0. The upstream copyright header is inside `protocol/webos-shell.xml`. The full license text from the same commit is `LICENSE` in this directory (upstream path `LICENSE`).

The XML is unmodified. `wayland-hello` does not generate code from it and does not hard-code its opcodes.

## Why opcodes are not compiled in

`wl_webos_shell` on webOS TV stays at version 1 while requests are inserted, so the same name can sit at a different opcode on a different release. This client binds the interface only after `dlopen` of `libwayland-webos-client.so.1` and a name-plus-signature match against that library's `wl_interface` tables. If the library or a required signature is missing, no `wl_webos_shell` request is sent.

## Public TV dump used as a cross-check, not as the implementation

webosbrew publishes interfaces extracted from TV images: https://github.com/webosbrew/wayland-protocols commit `87f3ebdb5c5cc7cfb9d6dbb1e59c4cd7ab2fd74a`, file `protocols/dumped/tv-6.4.0/webos.xml`, raw SHA256 `398f7604ee3b7118865ca642e1e5f53cfb39705b8b21eee8c839bfa752d62c78`. That dump is not vendored here.

Request opcodes that match this OSE file and that dump:

| Request | OSE opcode | tv-6.4.0 opcode | Signature |
|---|---|---|---|
| `wl_webos_shell.get_system_pip` | 0 | 0 | (none) |
| `wl_webos_shell.get_shell_surface` | 1 | 1 | new_id, object |
| `wl_webos_shell_surface.set_location_hint` | 0 | 0 | uint |
| `wl_webos_shell_surface.set_state` | 1 | 1 | uint |
| `wl_webos_shell_surface.set_property` | 2 | 2 | string, string |
| `wl_webos_shell_surface.set_key_mask` | 3 | 3 | uint |

The next request does not match: OSE version 2 adds `set_addon`, while the tv-6.4.0 dump has `set_size`. This client never sends that slot.

The OSE `state` enum gives `fullscreen` the value 3 and `default` the value 0. The tv-6.4.0 dump does not record enum values, and there is no dump for webOS 6.5.3 (the 65NANO756PR release, which advertised `wl_webos_shell` version 1). The numeric state and the `webos_key` mask bits are therefore OSE assumptions, logged on every send, and they are sent only after the runtime library has confirmed the request name and signature.

`set_property` in the OSE XML is an open string pair. The name `appId` is the conventional webOS shell property; it is not an enum in the XML.

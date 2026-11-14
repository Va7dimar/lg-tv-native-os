/*
 * wayland-hello: minimal, bounded, legacy-ABI Wayland client prototype.
 *
 * PROTOTYPE ONLY. No hardware compatibility guarantee. See README.md.
 *
 * Design constraints (see README):
 *  - libwayland-client is dlopen()ed at runtime; only symbols present in
 *    libwayland-client 1.0.x are required (wl_proxy_create + wl_proxy_marshal,
 *    the pre-1.4 constructor pattern). wl_proxy_marshal_flags /
 *    wl_proxy_marshal_constructor / wl_proxy_get_version are NOT used.
 *    wl_display_prepare_read / read_events / cancel_read / get_error are
 *    optional (resolved if present, otherwise a fallback path is used).
 *  - No Wayland headers needed: wl_interface / wl_message layouts are the
 *    stable public ABI and are declared locally; interface objects are
 *    resolved from the runtime library via dlsym.
 *  - SIGALRM hard-exit is armed BEFORE connecting; its handler performs no
 *    I/O and only calls _exit(124). All waits use poll() with a monotonic
 *    deadline.
 *  - Every constructor/bind proxy is NULL-checked before it is marshalled or
 *    given a listener; every listener install return value is checked.
 *  - SHM backing is reserved with posix_fallocate() before mmap() so an
 *    exhausted tmpfs fails closed instead of raising SIGBUS on first write.
 *  - Only wl_shell (legacy) is used for a surface unless --webos-shell is
 *    requested. If the chosen shell is absent, or the webOS interface cannot
 *    be read back from libwayland-webos-client.so.1, the client fails closed.
 *    It never opens DRM, fbdev, or evdev nodes and never touches services.
 *  - --input binds every advertised wl_seat (capped) and prints each raw
 *    wl_keyboard key code to stdout. It does not open /dev/input. The
 *    2026-11-08 probe shows those nodes are owned by surface-manager.
 */
#define _GNU_SOURCE
#include "menu.h"
#include "photo_frame.h"
#include <dlfcn.h>
#include <errno.h>
#include <stdbool.h>
#include <fcntl.h>
#include <limits.h>
#include <poll.h>
#include <signal.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <time.h>
#include <stddef.h>
#include <unistd.h>
#include <link.h>

#define HELLO_VERSION "0.10-prototype"

/* ---- limits ------------------------------------------------------------ */
#define DEFAULT_DURATION_S 10
#define MAX_DURATION_S     30
#define DEMO_DURATION_S    120
#define SAM_DURATION_S     90  /* safety cap: past the ~31s Home reclaim, always ends */
#define DEMO_MAX_BUFS      8
#define DEFAULT_W          640
#define DEFAULT_H          360
#define MAX_W              1920
#define MAX_H              1080
#define MAX_GLOBALS        128
#define MAX_SEATS          8
#define GRACE_S            5   /* SIGALRM fires at duration + GRACE_S, max 35s */
#define MAX_SHM_BYTES      ((size_t)MAX_W * (size_t)MAX_H * 4u)  /* 8 MiB hard cap */

/* exit codes */
#define EX_OK        0
#define EX_USAGE     2
#define EX_CONNECT   3
#define EX_PROTO     4
#define EX_NOSHELL   5
#define EX_LIB       6
#define EX_ALLOC     7
#define EX_NOSEAT    8
#define EX_NOWEBOS   9
#define EX_NOLUNA    10
#define EX_HARD      124

/* ---- stable libwayland ABI, declared locally -------------------------- */
struct wl_proxy;
struct wl_display;
struct wl_message { const char *name; const char *signature; const struct wl_interface **types; };
struct wl_interface {
	const char *name; int version;
	int method_count; const struct wl_message *methods;
	int event_count; const struct wl_message *events;
};

static struct {
	void *h;
	struct wl_display *(*display_connect)(const char *);
	void (*display_disconnect)(struct wl_display *);
	int (*display_get_fd)(struct wl_display *);
	int (*display_dispatch)(struct wl_display *);
	int (*display_dispatch_pending)(struct wl_display *);
	int (*display_flush)(struct wl_display *);
	/* optional */
	int (*display_prepare_read)(struct wl_display *);
	int (*display_read_events)(struct wl_display *);
	void (*display_cancel_read)(struct wl_display *);
	int (*display_get_error)(struct wl_display *);
	/* proxies (1.0 API) */
	struct wl_proxy *(*proxy_create)(struct wl_proxy *, const struct wl_interface *);
	void (*proxy_marshal)(struct wl_proxy *, uint32_t, ...);
	int (*proxy_add_listener)(struct wl_proxy *, void (**)(void), void *);
	void (*proxy_destroy)(struct wl_proxy *);
	/* interface objects */
	const struct wl_interface *i_registry, *i_callback, *i_compositor, *i_shm,
		*i_shm_pool, *i_buffer, *i_surface, *i_shell, *i_shell_surface,
		*i_seat, *i_keyboard, *i_pointer, *i_output;
} W;

/* ---- options ----------------------------------------------------------- */
struct opts {
	int dry_run;
	int parse_only;
	int demo;
	int menu;
	int photo_frame;            /* PHOTO_FRAME_OFF / A / B */
	int size_cli;
	int luna_register;
	int heartbeat_ms;
	int input;
	int webos_shell;
	int webos_key_mask;
	int exit_on_leave;
	int egl;
	int sam_launch;
	int sam_lifecycle2;
	int duration_cli;
	int duration_s;
	int width, height;          /* initial buffer */
	int max_w, max_h;           /* cap for configure-driven resize */
	int no_fullscreen;
	const char *runtime_dir;
	const char *display_name;
	const char *app_id;
	const char *window_type;    /* set with --webos-shell; default CARD */
	uint32_t color;             /* 0xRRGGBB */
};

static void elog(const char *fmt, ...);
static void olog(const char *fmt, ...);
static void arm_countdown(const char *trigger);
static void luna_iterate(void);
static void luna_check_ack(int at_deadline);
static void cleanup(void);

static void usage(FILE *f)
{
	fprintf(f,
"usage: wayland-hello [options]\n"
"  --dry-run            connect, print registry globals, exit (no surfaces)\n"
"  --input              bind wl_seat; log keys/pointer; arrows move a square\n"
"  --demo               interactive mode (implies --input)\n"
"                       spare SHM buffer so a redraw does not wait for release;\n"
"                       runs until BACK or EXIT; --duration is the safety cap\n"
"                       (default %d, max %d). Without --demo/--menu the cap stays %d.\n"
"                       SAM launch JSON as argv[1] also selects --demo;\n"
"                       lifecycle v2 (interfaceMethod registerApp) adds\n"
"                       --luna-register, --webos-shell overlay, 90s cap.\n"
"                       A packaged menu sidecar selects --menu instead of --demo.\n"
"                       A packaged photo-frame sidecar (A or B) selects the\n"
"                       fullscreen photograph-test instead of --demo/--menu.\n"
"  --photo-frame A|B    fullscreen photograph-test (implies --input).\n"
"                       MODE A: focusable wl_shell fullscreen. MODE B: the\n"
"                       proven wl_webos_shell OVERLAY path. Both detect the\n"
"                       panel size from wl_output (fallback 1920x1080), paint\n"
"                       edge-to-edge color + corner markers + a large timer,\n"
"                       and self-exit after 120s. MODE A overlays focus_enter\n"
"                       and the last key. A packaged sidecar selects the mode\n"
"                       on SAM launch. SHM-only; cannot combine with --menu,\n"
"                       --demo, or --egl.\n"
"  --menu               full-screen tile menu (implies --input). Arrows move\n"
"                       focus; OK/ENTER activate (hypothesis); BACK returns or\n"
"                       exits. Demo tile enters --demo; About is static; Exit\n"
"                       exits 0. Same spare-buffer redraw as --demo. Selection\n"
"                       does not advance when a redraw cannot be shown.\n"
"  --luna-register      dlopen libluna-service2; subscribe to registerApp\n"
"                       exit 10 unless a top-level registered reply arrives\n"
"                       within 2s (OSE sends that reply in the same call)\n"
"                       relaunch re-asserts fullscreen; pause is logged; close exits\n"
"  --heartbeat-ms N     shm redraw every N ms while idle (100..60000)\n"
"  --webos-shell        wl_webos_shell instead of wl_shell (fail closed)\n"
"  --webos-key-mask     with --webos-shell, set_key_mask for BACK and EXIT\n"
"  --exit-on-leave      exit when a focused wl_keyboard leaves\n"
"  --egl                try GLES2 via dlopen; shm if the libraries differ\n"
"  --app-id ID          app id (default wayland-hello-prototype)\n"
"  --window-type TYPE   with --webos-shell, set_property _WEBOS_WINDOW_TYPE\n"
"                       (default _WEBOS_WINDOW_TYPE_CARD)\n"
"  --duration N         on-screen seconds after first configure or frame (1..%d, default %d)\n"
"  --size WxH           initial buffer size (default %dx%d, max %dx%d)\n"
"  --max-size WxH       cap for compositor-requested sizes (default %dx%d)\n"
"  --color RRGGBB       base color (default 204080)\n"
"  --no-fullscreen      wl_shell set_toplevel, or webOS state default\n"
"  --runtime-dir DIR    override XDG_RUNTIME_DIR (default env, else /tmp/xdg)\n"
"  --display NAME       override WAYLAND_DISPLAY (default env, else wayland-0)\n"
"  --parse-only         print parsed configuration and exit (no connect)\n"
"  --version, --help\n",
	DEMO_DURATION_S, DEMO_DURATION_S, MAX_DURATION_S,
	MAX_DURATION_S, DEFAULT_DURATION_S, DEFAULT_W, DEFAULT_H, MAX_W, MAX_H, MAX_W, MAX_H);
}

static int parse_int(const char *s, int lo, int hi, int *out)
{
	char *end; long v;
	if (!s || !*s) return -1;
	errno = 0;
	v = strtol(s, &end, 10);
	if (errno || *end || v < lo || v > hi) return -1;
	*out = (int)v;
	return 0;
}

static int parse_size(const char *s, int maxw, int maxh, int *w, int *h)
{
	char buf[32]; char *x;
	if (!s || strlen(s) >= sizeof buf) return -1;
	strcpy(buf, s);
	x = strchr(buf, 'x');
	if (!x) return -1;
	*x = 0;
	if (parse_int(buf, 1, maxw, w) || parse_int(x + 1, 1, maxh, h)) return -1;
	return 0;
}

/* SAM native launch: argv[1] is a JSON document. First-match is enough:
 * the live launch document puts appId / interfaceMethod at the top level. */
static char g_app_id_buf[65];
static char g_window_type_buf[80];
static char *g_argv_store[64];

static int looks_like_json_object(const char *s)
{
	if (!s) return 0;
	while (*s == ' ' || *s == '\t' || *s == '\n' || *s == '\r') s++;
	return *s == '{';
}

static int json_copy_string(const char *json, const char *key, char *out, size_t cap)
{
	char pat[80];
	const char *p, *q;
	size_t n = 0;
	if (!json || !key || !out || cap < 2) return -1;
	if (snprintf(pat, sizeof pat, "\"%s\"", key) >= (int)sizeof pat) return -1;
	p = strstr(json, pat);
	if (!p) return -1;
	q = p + strlen(pat);
	while (*q == ' ' || *q == '\t') q++;
	if (*q != ':') return -1;
	q++;
	while (*q == ' ' || *q == '\t') q++;
	if (*q != '"') return -1;
	q++;
	while (*q && *q != '"' && n + 1 < cap) {
		if (*q == '\\' && q[1]) q++;
		out[n++] = *q++;
	}
	if (*q != '"') return -1;
	out[n] = 0;
	return 0;
}

static int json_top_int(const char *json, const char *key, int *out)
{
	char pat[80];
	const char *p, *q;
	char *end;
	long v;
	if (!json || !key || !out) return -1;
	if (snprintf(pat, sizeof pat, "\"%s\"", key) >= (int)sizeof pat) return -1;
	p = strstr(json, pat);
	if (!p) return -1;
	q = p + strlen(pat);
	while (*q == ' ' || *q == '\t') q++;
	if (*q != ':') return -1;
	q++;
	while (*q == ' ' || *q == '\t') q++;
	if (*q == '"' || !*q) return -1;
	errno = 0;
	v = strtol(q, &end, 10);
	if (errno || end == q || v < 0 || v > 100) return -1;
	*out = (int)v;
	return 0;
}

static int app_id_token_ok(const char *s)
{
	const char *p;
	int n = 0;
	if (!s || !*s) return 0;
	for (p = s; *p; p++, n++) {
		unsigned char c = (unsigned char)*p;
		if (n >= 64 || !(c == '.' || c == '_' || c == '-' ||
		    (c >= '0' && c <= '9') || (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z')))
			return 0;
	}
	return 1;
}

static int strip_sam_json_argv(int argc, char **argv, char ***out_argv, const char **launch_json)
{
	int i, n = 0;
	*launch_json = NULL;
	if (argc < 2 || !looks_like_json_object(argv[1])) {
		*out_argv = argv;
		return argc;
	}
	if (argc > (int)(sizeof g_argv_store / sizeof g_argv_store[0]) - 1)
		argc = (int)(sizeof g_argv_store / sizeof g_argv_store[0]) - 1;
	*launch_json = argv[1];
	g_argv_store[n++] = argv[0];
	for (i = 2; i < argc; i++)
		g_argv_store[n++] = argv[i];
	g_argv_store[n] = NULL;
	*out_argv = g_argv_store;
	return n;
}

static int read_appinfo_sidecar(int *lifecycle, char *id_out, size_t id_cap)
{
	char path[512], buf[2048];
	ssize_t n;
	int fd, ver = 0;
	if (lifecycle) *lifecycle = 0;
	if (id_out && id_cap) id_out[0] = 0;
	n = readlink("/proc/self/exe", path, sizeof path - 1);
	if (n <= 0) return -1;
	path[n] = 0;
	{
		char *slash = strrchr(path, '/');
		if (!slash || slash - path + 13 >= (ssize_t)sizeof path) return -1;
		memcpy(slash + 1, "appinfo.json", 13);
	}
	fd = open(path, O_RDONLY);
	if (fd < 0) return -1;
	n = read(fd, buf, sizeof buf - 1);
	close(fd);
	if (n <= 0) return -1;
	buf[n] = 0;
	if (lifecycle) {
		json_top_int(buf, "nativeLifeCycleInterfaceVersion", &ver);
		*lifecycle = ver;
	}
	if (id_out && id_cap)
		json_copy_string(buf, "id", id_out, id_cap);
	return 0;
}

static int read_heartbeat_sidecar(void)
{
	char path[512], buf[16];
	ssize_t n, i;
	int fd, v = 0;
	n = readlink("/proc/self/exe", path, sizeof path - 1);
	if (n <= 0) return 0;
	path[n] = 0;
	{
		char *slash = strrchr(path, '/');
		if (!slash || slash - path + 14 >= (ssize_t)sizeof path) return 0;
		memcpy(slash + 1, "heartbeat-ms", 13);
	}
	fd = open(path, O_RDONLY);
	if (fd < 0) return 0;
	n = read(fd, buf, sizeof buf - 1);
	close(fd);
	if (n <= 0) return 0;
	buf[n] = 0;
	for (i = 0; i < n; i++) {
		if (buf[i] >= '0' && buf[i] <= '9') {
			v = v * 10 + (buf[i] - '0');
			if (v > 60000) return 0;
		} else if (buf[i] == '\n' || buf[i] == '\r' || buf[i] == ' ') {
			break;
		} else {
			return 0;
		}
	}
	if (v < 100 || v > 60000) return 0;
	return v;
}

/* Opt-in menu IPK: a sidecar next to the ELF, same pattern as heartbeat-ms.
 * SAM launches the ELF (appinfo main), so the old launch.sh --menu rewrite
 * cannot select the tile launcher. Presence of the file is enough. */
static int read_menu_sidecar(void)
{
	char path[512];
	ssize_t n;
	int fd;
	n = readlink("/proc/self/exe", path, sizeof path - 1);
	if (n <= 0) return 0;
	path[n] = 0;
	{
		char *slash = strrchr(path, '/');
		if (!slash || slash - path + 5 >= (ssize_t)sizeof path) return 0;
		memcpy(slash + 1, "menu", 5);
	}
	fd = open(path, O_RDONLY);
	if (fd < 0) return 0;
	close(fd);
	return 1;
}

/* Opt-in photograph-test IPK: sidecar next to the ELF, body A or B.
 * Presence+parse is enough; SAM launches the ELF (appinfo main). */
static int read_photo_frame_sidecar(int *mode)
{
	char path[512], buf[16];
	ssize_t n;
	int fd;
	if (mode) *mode = PHOTO_FRAME_OFF;
	n = readlink("/proc/self/exe", path, sizeof path - 1);
	if (n <= 0) return 0;
	path[n] = 0;
	{
		char *slash = strrchr(path, '/');
		if (!slash || slash - path + 12 >= (ssize_t)sizeof path) return 0;
		memcpy(slash + 1, "photo-frame", 12);
	}
	fd = open(path, O_RDONLY);
	if (fd < 0) return 0;
	n = read(fd, buf, sizeof buf - 1);
	close(fd);
	if (n <= 0) return 0;
	buf[n] = 0;
	return photo_frame_parse_mode(buf, mode) == 0;
}

static void apply_photo_frame_mode(struct opts *o)
{
	if (!o || !o->photo_frame) return;
	o->demo = 0;
	o->menu = 0;
	o->input = 1;
	o->egl = 0;
	o->no_fullscreen = 0;
	if (!o->duration_cli)
		o->duration_s = DEMO_DURATION_S;
	if (!o->heartbeat_ms)
		o->heartbeat_ms = 1000;
	if (o->photo_frame == PHOTO_FRAME_A) {
		o->webos_shell = 0;
		o->window_type = NULL;
	} else if (o->photo_frame == PHOTO_FRAME_B) {
		o->webos_shell = 1;
		snprintf(g_window_type_buf, sizeof g_window_type_buf, "%s",
		         "_WEBOS_WINDOW_TYPE_OVERLAY");
		o->window_type = g_window_type_buf;
	} else if (o->photo_frame == PHOTO_FRAME_C) {
		/* Gate test: webOS shell + appId + CARD, the type OSE SAM counts as foreground. */
		o->webos_shell = 1;
		snprintf(g_window_type_buf, sizeof g_window_type_buf, "%s",
		         "_WEBOS_WINDOW_TYPE_CARD");
		o->window_type = g_window_type_buf;
	}
}

static void apply_sam_launch(struct opts *o, const char *launch_json)
{
	char method[40];
	char from_json[65];
	const char *env_appid;
	int ver = 0;
	if (!launch_json) return;
	o->sam_launch = 1;
	method[0] = 0;
	from_json[0] = 0;
	json_copy_string(launch_json, "interfaceMethod", method, sizeof method);
	json_top_int(launch_json, "interfaceVersion", &ver);
	if (ver != 2)
		json_top_int(launch_json, "nativeLifeCycleInterfaceVersion", &ver);
	if (ver == 2 || strcmp(method, "registerApp") == 0)
		o->sam_lifecycle2 = 1;
	{
		int app_ver = 0;
		char from_app[65];
		from_app[0] = 0;
		if (read_appinfo_sidecar(&app_ver, from_app, sizeof from_app) == 0) {
			if (!o->sam_lifecycle2 && app_ver == 2)
				o->sam_lifecycle2 = 1;
			if (app_id_token_ok(from_app) && !from_json[0])
				snprintf(from_json, sizeof from_json, "%s", from_app);
		}
	}
	env_appid = getenv("APPID");
	if (app_id_token_ok(env_appid)) {
		snprintf(g_app_id_buf, sizeof g_app_id_buf, "%s", env_appid);
		o->app_id = g_app_id_buf;
	} else if (json_copy_string(launch_json, "appId", from_json, sizeof from_json) == 0 &&
	           app_id_token_ok(from_json)) {
		snprintf(g_app_id_buf, sizeof g_app_id_buf, "%s", from_json);
		o->app_id = g_app_id_buf;
	} else if (app_id_token_ok(from_json)) {
		snprintf(g_app_id_buf, sizeof g_app_id_buf, "%s", from_json);
		o->app_id = g_app_id_buf;
	}
	if (read_menu_sidecar())
		o->menu = 1;
	{
		int pm = PHOTO_FRAME_OFF;
		if (read_photo_frame_sidecar(&pm))
			o->photo_frame = pm;
	}
	if (o->photo_frame) {
		o->menu = 0;
		o->demo = 0;
	} else if (o->menu)
		o->demo = 0;
	else if (!o->demo)
		o->demo = 1;
	o->input = 1;
	if (!o->duration_cli)
		o->duration_s = o->sam_lifecycle2 ? SAM_DURATION_S : DEMO_DURATION_S;
	if (o->sam_lifecycle2) {
		o->luna_register = 1;
		o->webos_shell = 1;
		if (!o->window_type || !strcmp(o->window_type, "_WEBOS_WINDOW_TYPE_CARD")) {
			snprintf(g_window_type_buf, sizeof g_window_type_buf, "%s", "_WEBOS_WINDOW_TYPE_OVERLAY");
			o->window_type = g_window_type_buf;
		}
	}
	if (o->photo_frame)
		apply_photo_frame_mode(o);
	if (!o->heartbeat_ms)
		o->heartbeat_ms = read_heartbeat_sidecar();
	if (!getenv("XDG_RUNTIME_DIR") || !getenv("XDG_RUNTIME_DIR")[0])
		o->runtime_dir = "/tmp/xdg";
	if (!getenv("WAYLAND_DISPLAY") || !getenv("WAYLAND_DISPLAY")[0])
		o->display_name = "wayland-0";
}

static int open_wh6_log(void)
{
	const char *path = getenv("WAYLAND_HELLO_LOG");
	int fd;
	if (path && (!path[0] || strcmp(path, "-") == 0)) return 0;
	if (!path) path = "/tmp/wh6.log";
	fd = open(path, O_WRONLY | O_CREAT | O_APPEND, 0644);
	if (fd < 0) return -1;
	if (dup2(fd, STDOUT_FILENO) < 0 || dup2(fd, STDERR_FILENO) < 0) {
		close(fd);
		return -1;
	}
	if (fd > STDERR_FILENO) close(fd);
	setvbuf(stdout, NULL, _IOLBF, 0);
	setvbuf(stderr, NULL, _IOLBF, 0);
	return 0;
}

/* returns 0 ok, 1 exit-success (help/version), -1 usage error.
 * allow_long_duration is set when argv[1] was SAM launch JSON, so --duration
 * may use the demo range before apply_sam_launch runs. */
static int parse_opts(int argc, char **argv, struct opts *o, int allow_long_duration)
{
	const char *e;
	int i, duration_set = 0, duration_val = DEFAULT_DURATION_S;
	memset(o, 0, sizeof *o);
	o->duration_s = DEFAULT_DURATION_S;
	o->width = DEFAULT_W; o->height = DEFAULT_H;
	o->max_w = MAX_W; o->max_h = MAX_H;
	o->color = 0x204080;
	o->app_id = "wayland-hello-prototype";
	o->duration_cli = 0;
	e = getenv("XDG_RUNTIME_DIR");
	o->runtime_dir = (e && *e) ? e : "/tmp/xdg";
	e = getenv("WAYLAND_DISPLAY");
	o->display_name = (e && *e) ? e : "wayland-0";

	for (i = 1; i < argc; i++) {
		const char *a = argv[i];
		const char *v = (i + 1 < argc) ? argv[i + 1] : NULL;
		if (!strcmp(a, "--dry-run")) o->dry_run = 1;
		else if (!strcmp(a, "--parse-only")) o->parse_only = 1;
		else if (!strcmp(a, "--demo")) o->demo = 1;
		else if (!strcmp(a, "--menu")) o->menu = 1;
		else if (!strcmp(a, "--photo-frame")) {
			int m = PHOTO_FRAME_OFF;
			if (photo_frame_parse_mode(v, &m)) {
				elog("error: --photo-frame must be A or B\n");
				return -1;
			}
			o->photo_frame = m;
			i++;
		}
		else if (!strcmp(a, "--luna-register")) o->luna_register = 1;
		else if (!strcmp(a, "--heartbeat-ms")) {
			if (parse_int(v, 100, 60000, &o->heartbeat_ms)) {
				elog("error: --heartbeat-ms must be 100..60000\n");
				return -1;
			}
			i++;
		}
		else if (!strcmp(a, "--input")) o->input = 1;
		else if (!strcmp(a, "--webos-shell")) o->webos_shell = 1;
		else if (!strcmp(a, "--webos-key-mask")) o->webos_key_mask = 1;
		else if (!strcmp(a, "--exit-on-leave")) o->exit_on_leave = 1;
		else if (!strcmp(a, "--egl")) o->egl = 1;
		else if (!strcmp(a, "--no-fullscreen")) o->no_fullscreen = 1;
		else if (!strcmp(a, "--help") || !strcmp(a, "-h")) { usage(stdout); return 1; }
		else if (!strcmp(a, "--version")) { printf("wayland-hello %s\n", HELLO_VERSION); return 1; }
		else if (!strcmp(a, "--duration")) {
			if (parse_int(v, 1, DEMO_DURATION_S, &duration_val)) {
				elog("error: --duration must be 1..%d\n", DEMO_DURATION_S); return -1;
			}
			duration_set = 1;
			o->duration_cli = 1;
			i++;
		} else if (!strcmp(a, "--size")) {
			if (parse_size(v, MAX_W, MAX_H, &o->width, &o->height)) {
				elog("error: --size must be WxH within %dx%d\n", MAX_W, MAX_H); return -1;
			}
			o->size_cli = 1;
			i++;
		} else if (!strcmp(a, "--max-size")) {
			if (parse_size(v, MAX_W, MAX_H, &o->max_w, &o->max_h)) {
				elog("error: --max-size must be WxH within %dx%d\n", MAX_W, MAX_H); return -1;
			}
			i++;
		} else if (!strcmp(a, "--window-type")) {
			const char *p;
			int n = 0;
			/* luna-surfacemanager reads the property _WEBOS_WINDOW_TYPE. */
			if (!v || strncmp(v, "_WEBOS_WINDOW_TYPE_", 19) != 0) {
				elog("error: --window-type must look like _WEBOS_WINDOW_TYPE_OVERLAY\n");
				return -1;
			}
			for (p = v; *p; p++, n++) {
				unsigned char c = (unsigned char)*p;
				if (n >= 64 || !(c == '_' || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9'))) {
					elog("error: --window-type must look like _WEBOS_WINDOW_TYPE_OVERLAY\n");
					return -1;
				}
			}
			o->window_type = v; i++;
		} else if (!strcmp(a, "--app-id")) {
			const char *p;
			int n = 0;
			if (!v || !*v) { elog("error: --app-id must be 1..64 of [A-Za-z0-9._-]\n"); return -1; }
			for (p = v; *p; p++, n++) {
				unsigned char c = (unsigned char)*p;
				if (n >= 64 || !(c == '.' || c == '_' || c == '-' ||
				    (c >= '0' && c <= '9') || (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z'))) {
					elog("error: --app-id must be 1..64 of [A-Za-z0-9._-]\n");
					return -1;
				}
			}
			o->app_id = v; i++;
		} else if (!strcmp(a, "--color")) {
			char *end; unsigned long c;
			if (!v || strlen(v) != 6) { elog("error: --color RRGGBB\n"); return -1; }
			c = strtoul(v, &end, 16);
			if (*end) { elog("error: --color RRGGBB\n"); return -1; }
			o->color = (uint32_t)c;
			i++;
		} else if (!strcmp(a, "--runtime-dir")) {
			if (!v || v[0] != '/' || strlen(v) > 200) {
				elog("error: --runtime-dir must be an absolute path\n"); return -1;
			}
			o->runtime_dir = v; i++;
		} else if (!strcmp(a, "--display")) {
			if (!v || !*v || strchr(v, '/') || strlen(v) > 64) {
				elog("error: --display must be a plain socket name\n"); return -1;
			}
			o->display_name = v; i++;
		} else {
			elog("error: unknown option '%s'\n", a);
			usage(stderr);
			return -1;
		}
	}
	/* env-provided values get the same validation */
	if (o->runtime_dir[0] != '/' || strlen(o->runtime_dir) > 200) {
		elog("error: XDG_RUNTIME_DIR must be an absolute path\n"); return -1;
	}
	if (strchr(o->display_name, '/') || strlen(o->display_name) > 64) {
		elog("error: WAYLAND_DISPLAY must be a plain socket name\n"); return -1;
	}
	if (o->width > o->max_w) o->width = o->max_w;
	if (o->height > o->max_h) o->height = o->max_h;
	if (o->webos_key_mask && !o->webos_shell) {
		elog("error: --webos-key-mask requires --webos-shell\n");
		return -1;
	}
	if (o->window_type && !o->webos_shell) {
		elog("error: --window-type requires --webos-shell\n");
		return -1;
	}
	if (o->webos_shell && !o->window_type)
		o->window_type = "_WEBOS_WINDOW_TYPE_CARD";
	if (o->demo && o->menu) {
		elog("error: --menu and --demo cannot be combined; use Demo from the menu\n");
		return -1;
	}
	if (o->photo_frame && o->menu) {
		elog("error: --photo-frame and --menu cannot be combined\n");
		return -1;
	}
	if (o->photo_frame && o->demo) {
		elog("error: --photo-frame and --demo cannot be combined\n");
		return -1;
	}
	if (o->menu && o->egl) {
		elog("error: --menu is SHM-only; omit --egl\n");
		return -1;
	}
	if (o->photo_frame && o->egl) {
		elog("error: --photo-frame is SHM-only; omit --egl\n");
		return -1;
	}
	if (o->photo_frame)
		apply_photo_frame_mode(o);
	if (o->demo) {
		o->input = 1;
		o->duration_s = duration_set ? duration_val : DEMO_DURATION_S;
	} else if (o->menu) {
		o->input = 1;
		o->duration_s = duration_set ? duration_val : DEMO_DURATION_S;
	} else if (o->photo_frame) {
		o->duration_s = duration_set ? duration_val : DEMO_DURATION_S;
	} else if (duration_set) {
		if (duration_val > MAX_DURATION_S && !allow_long_duration) {
			elog("error: --duration must be 1..%d\n", MAX_DURATION_S); return -1;
		}
		o->duration_s = duration_val;
	}
	return 0;
}

/* ---- hard exit / deadline --------------------------------------------- */
static volatile sig_atomic_t g_stop;

/* Hard-deadline handler: NO I/O of any kind. A write() to stderr could block
 * forever on a full pipe and defeat the hard bound, so the handler does the
 * single async-signal-safe thing it needs and nothing else. Exit status 124
 * is the only signal that the hard deadline fired. */
static void on_alarm(int sig)
{
	(void)sig;
	_exit(EX_HARD);
}

static void on_term(int sig) { (void)sig; g_stop = 1; }

static int64_t now_ms(void)
{
	struct timespec ts;
	clock_gettime(CLOCK_MONOTONIC, &ts);
	return (int64_t)ts.tv_sec * 1000 + ts.tv_nsec / 1000000;
}

static int64_t g_t0;
static int64_t g_deadline;
static int64_t g_alarm_at;
static int g_show_armed;

static int64_t elapsed_ms(void)
{
	int64_t n = now_ms();
	if (!g_t0) g_t0 = n;
	return n - g_t0;
}

static void elog(const char *fmt, ...)
{
	va_list ap;
	fprintf(stderr, "t=%lld ", (long long)elapsed_ms());
	va_start(ap, fmt);
	vfprintf(stderr, fmt, ap);
	va_end(ap);
	fflush(stderr);
}

static void olog(const char *fmt, ...)
{
	va_list ap;
	fprintf(stdout, "t=%lld ", (long long)elapsed_ms());
	va_start(ap, fmt);
	vfprintf(stdout, fmt, ap);
	va_end(ap);
	fflush(stdout);
}

static int remaining_ms(void)
{
	int64_t r = g_deadline - now_ms();
	if (r <= 0) return 0;
	return r > INT_MAX ? INT_MAX : (int)r;
}

/* ---- dynamic loading -------------------------------------------------- */
#define REQ(field, sym) do { *(void **)(&W.field) = dlsym(W.h, sym); \
	if (!W.field) { elog("error: missing symbol %s\n", sym); return -1; } } while (0)
#define OPT(field, sym) do { *(void **)(&W.field) = dlsym(W.h, sym); } while (0)

static int load_wayland(void)
{
	static const char *names[] = { "libwayland-client.so.0", "libwayland-client.so", NULL };
	int i;
	for (i = 0; names[i] && !W.h; i++) W.h = dlopen(names[i], RTLD_NOW | RTLD_LOCAL);
	if (!W.h) { elog("error: dlopen libwayland-client failed: %s\n", dlerror()); return -1; }
	REQ(display_connect, "wl_display_connect");
	REQ(display_disconnect, "wl_display_disconnect");
	REQ(display_get_fd, "wl_display_get_fd");
	REQ(display_dispatch, "wl_display_dispatch");
	REQ(display_dispatch_pending, "wl_display_dispatch_pending");
	REQ(display_flush, "wl_display_flush");
	OPT(display_prepare_read, "wl_display_prepare_read");
	OPT(display_read_events, "wl_display_read_events");
	OPT(display_cancel_read, "wl_display_cancel_read");
	OPT(display_get_error, "wl_display_get_error");
	REQ(proxy_create, "wl_proxy_create");
	REQ(proxy_marshal, "wl_proxy_marshal");
	REQ(proxy_add_listener, "wl_proxy_add_listener");
	REQ(proxy_destroy, "wl_proxy_destroy");
	REQ(i_registry, "wl_registry_interface");
	REQ(i_callback, "wl_callback_interface");
	REQ(i_compositor, "wl_compositor_interface");
	REQ(i_shm, "wl_shm_interface");
	REQ(i_shm_pool, "wl_shm_pool_interface");
	REQ(i_buffer, "wl_buffer_interface");
	REQ(i_surface, "wl_surface_interface");
	REQ(i_shell, "wl_shell_interface");
	REQ(i_shell_surface, "wl_shell_surface_interface");
	OPT(i_seat, "wl_seat_interface");
	OPT(i_keyboard, "wl_keyboard_interface");
	OPT(i_pointer, "wl_pointer_interface");
	OPT(i_output, "wl_output_interface");
	if (!(W.display_prepare_read && W.display_read_events && W.display_cancel_read))
		W.display_prepare_read = NULL; /* use all-or-nothing */
	return 0;
}

/* ---- protocol opcodes (core wayland.xml, version-1 requests only) ----- */
enum { DISPLAY_SYNC = 0, DISPLAY_GET_REGISTRY = 1 };
enum { REGISTRY_BIND = 0 };
enum { COMPOSITOR_CREATE_SURFACE = 0 };
enum { SHM_CREATE_POOL = 0 };
enum { SHM_POOL_CREATE_BUFFER = 0, SHM_POOL_DESTROY = 1 };
enum { BUFFER_DESTROY = 0 };
enum { SURFACE_DESTROY = 0, SURFACE_ATTACH = 1, SURFACE_DAMAGE = 2, SURFACE_FRAME = 3, SURFACE_COMMIT = 6 };
enum { SHELL_GET_SHELL_SURFACE = 0 };
enum { SHSURF_PONG = 0, SHSURF_SET_TOPLEVEL = 3, SHSURF_SET_FULLSCREEN = 5, SHSURF_SET_TITLE = 8, SHSURF_SET_CLASS = 9 };
enum { SEAT_GET_POINTER = 0, SEAT_GET_KEYBOARD = 1 };
#define WL_SHM_FORMAT_XRGB8888 1
/* wl_keyboard.key carries the evdev code (wayland.xml). XKB keycode = evdev + 8.
 * linux/input-event-codes.h values assumed below. webOS DOM keyCode 461 is a
 * different namespace and is logged as unknown if it arrives here. */
#define KEY_ESC_EVDEV  1
#define KEY_ENTER_EVDEV 28
#define KEY_UP_EVDEV   103
#define KEY_LEFT_EVDEV 105
#define KEY_RIGHT_EVDEV 106
#define KEY_DOWN_EVDEV 108
#define KEY_BACK_EVDEV 158
#define KEY_EXIT_EVDEV 174
#define KEY_OK_EVDEV   352
#define SQ_SIZE 40
#define SQ_STEP 40

/* pre-1.4 constructor pattern: create proxy, then marshal with it as new_id */
static struct wl_proxy *new_obj(struct wl_proxy *factory, const struct wl_interface *iface)
{
	return W.proxy_create(factory, iface);
}

/* ---- client state ----------------------------------------------------- */
struct global { uint32_t name, version; char iface[64]; };

struct buf {
	struct wl_proxy *buffer;
	void *data;
	size_t size;
	int w, h;
	int busy;
	int gen;
};

struct seat_slot {
	int index;
	uint32_t global_name;
	uint32_t version;
	struct wl_proxy *seat, *keyboard, *pointer;
	char label[64];
	int kb_entered;
};

enum {
	REASON_DEADLINE = 0,
	REASON_SIGNAL,
	REASON_BACK,
	REASON_ESC,
	REASON_EXITKEY,
	REASON_WEBOS_CLOSE,
	REASON_KB_LEAVE,
	REASON_LUNA_CLOSE,
	REASON_LUNA_REJECT,
	REASON_MENU_EXIT
};

static struct {
	struct opts *o;
	struct wl_display *display;
	struct wl_proxy *registry;
	struct global globals[MAX_GLOBALS];
	int nglobals, globals_truncated;
	uint32_t compositor_name, shm_name, shell_name, output_name;
	uint32_t webos_name, webos_advertised;
	struct wl_proxy *compositor, *shm, *shell, *surface, *shell_surface, *output;
	struct wl_proxy *webos_shell, *webos_shell_surface;
	const struct wl_interface *webos_shell_iface, *webos_surf_iface;
	void *webos_dl;
	int op_get_shell_surface, op_set_state, op_set_property, op_set_key_mask;
	struct seat_slot seats[MAX_SEATS];
	int nseats, seats_truncated;
	int have_xrgb;
	int want_w, want_h;
	int cur_w, cur_h;
	int resize_pending;
	struct buf buf;
	struct buf spare[DEMO_MAX_BUFS];
	int nspare;
	struct wl_proxy *frame_cb; /* at most one SHM wl_surface.frame callback */
	int buf_gen_next;
	int n_commits, n_frame_done, n_releases, n_deferred, n_redraws;
	int n_focus_enter, n_focus_leave, n_ptr_enter, n_ptr_leave, model_suppressed;
	int output_w, output_h;
	uint32_t last_key;
	char last_key_name[32];
	int n_heartbeat;
	int64_t heartbeat_next;
	int luna_polls;
	int luna_replies;
	int luna_acked;
	int n_restore;
	int need_restore;
	int n_persist_alive;
	int64_t persist_next;
	int model_key_set;
	uint32_t model_key;
	int64_t model_log_ms;
	int egl_frame_noted;
	int fatal;
	int quit;
	int reason;
	uint32_t bg;
	int sq_x, sq_y, sq;
	int color_i;
	int dirty;
	int egl_on;
	float nudge_x, nudge_y;
	int frame;
	struct menu_state menu;
	int menu_keymap_logged;
} S;

/* registry listener */
static void reg_global(void *data, struct wl_proxy *r, uint32_t name, const char *iface, uint32_t ver)
{
	(void)data; (void)r;
	if (S.nglobals < MAX_GLOBALS) {
		struct global *g = &S.globals[S.nglobals++];
		g->name = name; g->version = ver;
		snprintf(g->iface, sizeof g->iface, "%s", iface ? iface : "(null)");
	} else S.globals_truncated = 1;
	if (!iface) return;
	if (!strcmp(iface, "wl_compositor") && !S.compositor_name) S.compositor_name = name;
	else if (!strcmp(iface, "wl_shm") && !S.shm_name) S.shm_name = name;
	else if (!strcmp(iface, "wl_shell") && !S.shell_name) S.shell_name = name;
	else if (!strcmp(iface, "wl_output") && !S.output_name) S.output_name = name;
	else if (!strcmp(iface, "wl_webos_shell") && !S.webos_name) {
		S.webos_name = name; S.webos_advertised = ver;
	} else if (!strcmp(iface, "wl_seat")) {
		if (S.nseats < MAX_SEATS) {
			struct seat_slot *s = &S.seats[S.nseats++];
			s->index = S.nseats - 1;
			s->global_name = name;
			s->version = ver;
			snprintf(s->label, sizeof s->label, "-");
		} else if (!S.seats_truncated) {
			S.seats_truncated = 1;
			elog("warn: extra wl_seat ignored (cap %d)\n", MAX_SEATS);
		}
	}
}
static void reg_global_remove(void *data, struct wl_proxy *r, uint32_t name)
{ (void)data; (void)r; (void)name; }
static void *registry_listener[] = { (void *)reg_global, (void *)reg_global_remove };

/* sync callback */
static void cb_done(void *data, struct wl_proxy *cb, uint32_t serial)
{ (void)cb; (void)serial; *(int *)data = 1; }
static void *callback_listener[] = { (void *)cb_done };

/* shm format */
static void shm_format(void *data, struct wl_proxy *shm, uint32_t fmt)
{ (void)data; (void)shm; if (fmt == WL_SHM_FORMAT_XRGB8888) S.have_xrgb = 1; }
static void *shm_listener[] = { (void *)shm_format };

/* wl_output. Bound at version 1 (geometry + mode). CURRENT flag is 0x1. */
static void output_geometry(void *data, struct wl_proxy *output, int32_t x, int32_t y,
                            int32_t pw, int32_t ph, int32_t subpixel,
                            const char *make, const char *model, int32_t transform)
{
	(void)data; (void)output;
	elog("photo-frame: output-geometry x=%d y=%d phys=%dx%d subpixel=%d make=%s model=%s transform=%d\n",
	     (int)x, (int)y, (int)pw, (int)ph, (int)subpixel,
	     make ? make : "-", model ? model : "-", (int)transform);
}
static void output_mode(void *data, struct wl_proxy *output, uint32_t flags,
                        int32_t width, int32_t height, int32_t refresh)
{
	(void)data; (void)output;
	elog("photo-frame: output-mode flags=%u %dx%d refresh=%d current=%d\n",
	     flags, (int)width, (int)height, (int)refresh, (flags & 1u) ? 1 : 0);
	if (width < 1 || height < 1) return;
	if ((flags & 1u) || S.output_w == 0 || S.output_h == 0) {
		S.output_w = (int)width;
		S.output_h = (int)height;
	}
}
static void *output_listener[] = { (void *)output_geometry, (void *)output_mode };

/* buffer release is defined after present(); the listener only needs a declaration */
static void buf_release(void *data, struct wl_proxy *b);
static void *buffer_listener[] = { (void *)buf_release };

/* shell surface. ping is answered with pong before any other work. */
static void ss_ping(void *data, struct wl_proxy *ss, uint32_t serial)
{
	(void)data;
	elog("shell: ping serial=%u\n", serial);
	W.proxy_marshal(ss, SHSURF_PONG, serial);
	elog("shell: pong serial=%u\n", serial);
}
static void ss_configure(void *data, struct wl_proxy *ss, uint32_t edges, int32_t w, int32_t h)
{
	int32_t raw_w = w, raw_h = h;
	(void)data; (void)ss;
	arm_countdown("configure");
	if (w <= 0 || h <= 0) {
		elog("shell: configure edges=%u raw=%dx%d action=client-decides\n", edges, raw_w, raw_h);
		return;
	}
	if (w > S.o->max_w) w = S.o->max_w;
	if (h > S.o->max_h) h = S.o->max_h;
	if (w != S.cur_w || h != S.cur_h) {
		S.want_w = w; S.want_h = h; S.resize_pending = 1;
		elog("resize: requested raw=%dx%d clamped=%dx%d current=%dx%d gen=%d\n",
		     raw_w, raw_h, w, h, S.cur_w, S.cur_h, S.buf.gen);
	}
	elog("shell: configure edges=%u raw=%dx%d clamped=%dx%d\n", edges, raw_w, raw_h, w, h);
}
static void ss_popup_done(void *data, struct wl_proxy *ss)
{
	(void)data; (void)ss;
	elog("shell: popup_done\n");
}
static void *shell_surface_listener[] = { (void *)ss_ping, (void *)ss_configure, (void *)ss_popup_done };

#define LISTEN(p, l, d) W.proxy_add_listener((p), (void (**)(void))(l), (d))

/* ---- bounded event pump ----------------------------------------------- */
/* returns -1 on connection/protocol error, 0 otherwise */
static int pump_once(int timeout_ms)
{
	struct pollfd pfd;
	int fd = W.display_get_fd(S.display), r;

	if (W.display_prepare_read) {
		while (W.display_prepare_read(S.display) != 0)
			if (W.display_dispatch_pending(S.display) < 0) return -1;
	} else {
		if (W.display_dispatch_pending(S.display) < 0) return -1;
	}
	if (W.display_flush(S.display) < 0 && errno != EAGAIN) {
		if (W.display_prepare_read) W.display_cancel_read(S.display);
		return -1;
	}
	pfd.fd = fd; pfd.events = POLLIN; pfd.revents = 0;
	r = poll(&pfd, 1, timeout_ms);
	if (r < 0 && errno != EINTR) {
		if (W.display_prepare_read) W.display_cancel_read(S.display);
		return -1;
	}
	if (W.display_prepare_read) {
		if (r > 0 && (pfd.revents & POLLIN)) {
			if (W.display_read_events(S.display) < 0) return -1;
		} else W.display_cancel_read(S.display);
		if (W.display_dispatch_pending(S.display) < 0) return -1;
	} else if (r > 0 && (pfd.revents & POLLIN)) {
		/* legacy path: fd is readable so dispatch() reads without long block;
		 * SIGALRM still bounds the worst case. */
		if (W.display_dispatch(S.display) < 0) return -1;
	}
	if (r > 0 && (pfd.revents & (POLLHUP | POLLERR)) && !(pfd.revents & POLLIN)) return -1;
	luna_iterate();
	return 0;
}

static int roundtrip_bounded(void)
{
	int done = 0;
	struct wl_proxy *cb = new_obj((struct wl_proxy *)S.display, W.i_callback);
	if (!cb) { elog("error: wl_callback proxy allocation failed\n"); return -1; }
	/* listener before the request is sent; on failure nothing went on the wire */
	if (LISTEN(cb, callback_listener, &done) != 0) {
		elog("error: wl_callback listener install failed\n");
		W.proxy_destroy(cb);
		return -1;
	}
	W.proxy_marshal((struct wl_proxy *)S.display, DISPLAY_SYNC, cb);
	while (!done) {
		int ms;
		if (S.quit || S.fatal) { W.proxy_destroy(cb); return -1; }
		luna_check_ack(0);
		if (S.quit || S.fatal) { W.proxy_destroy(cb); return -1; }
		ms = remaining_ms();
		if (ms == 0 || g_stop) { elog("error: roundtrip deadline exceeded\n"); W.proxy_destroy(cb); return -1; }
		if (pump_once(ms > 100 ? 100 : ms) < 0) { W.proxy_destroy(cb); return -1; }
	}
	W.proxy_destroy(cb);
	return 0;
}

static void report_display_error(void)
{
	if (W.display_get_error && S.display) {
		int e = W.display_get_error(S.display);
		if (e) elog("error: display error %d (%s)\n", e, strerror(e));
	}
}

/* ---- SHM buffer ------------------------------------------------------- */
/* Creates an unlinked temp file of exactly `size` bytes with its backing
 * store RESERVED. ftruncate() alone only creates a sparse file: on a full
 * tmpfs the first store through the mapping would raise SIGBUS. Instead
 * posix_fallocate() must return 0, otherwise we fail closed. Any non-zero
 * result (ENOSPC, EFBIG, EINVAL, ENODEV, EOPNOTSUPP/unsupported FS, ...) is
 * a failure; no ftruncate fallback is attempted. On failure returns -1 with
 * errno set. */
static int make_shm_file(const char *dir, size_t size)
{
	char path[256];
	struct stat st;
	int fd, r, e;
	if (size == 0 || size > MAX_SHM_BYTES || size > (size_t)INT32_MAX) { errno = EINVAL; return -1; }
	if (snprintf(path, sizeof path, "%s/wayland-hello-XXXXXX", dir) >= (int)sizeof path) { errno = ENAMETOOLONG; return -1; }
	fd = mkstemp(path);
	if (fd < 0) return -1;
	unlink(path);
	(void)fcntl(fd, F_SETFD, FD_CLOEXEC);
	/* posix_fallocate returns an error number (does not set errno). Retry
	 * only on EINTR, and only while the soft deadline has not passed;
	 * SIGALRM remains the hard bound. */
	do {
		r = posix_fallocate(fd, 0, (off_t)size);
	} while (r == EINTR && !g_stop && remaining_ms() > 0);
	if (r != 0) {
		elog("error: posix_fallocate(%zu) failed: %s; refusing sparse SHM (SIGBUS risk)\n",
		        size, strerror(r));
		close(fd); errno = r; return -1;
	}
	/* verify the file really is the size we will map and declare */
	if (fstat(fd, &st) < 0) { e = errno; close(fd); errno = e; return -1; }
	if (st.st_size != (off_t)size) {
		elog("error: shm file size %lld != %zu after fallocate\n", (long long)st.st_size, size);
		close(fd); errno = EIO; return -1;
	}
	return fd;
}

static int use_spare_bufs(void)
{
	return S.o && (S.o->demo || S.o->menu || S.o->photo_frame);
}

static void log_menu_keymap_once(void)
{
	int i, n;
	const struct menu_key_map *tab;
	if (S.menu_keymap_logged) return;
	S.menu_keymap_logged = 1;
	tab = menu_keymap(&n);
	elog("menu: independent module; host supplies SHM pixels, wl_seat keys, spare-buffer redraw; no luna\n");
	for (i = 0; i < n; i++)
		elog("menu: keymap name=%s code=%u class=%s status=%s note=%s\n",
		     tab[i].name, tab[i].code, menu_key_class_name(tab[i].klass),
		     tab[i].status, tab[i].note);
}

static void paint(struct buf *b, uint32_t rgb)
{
	uint32_t *px = b->data;
	int x, y;
	if (S.o && S.o->photo_frame) {
		struct photo_frame_state st;
		memset(&st, 0, sizeof st);
		st.mode = S.o->photo_frame;
		st.seconds = (int)(elapsed_ms() / 1000);
		if (st.seconds < 0) st.seconds = 0;
		st.buf_w = b->w;
		st.buf_h = b->h;
		st.focus_enter = S.n_focus_enter;
		st.focus_leave = S.n_focus_leave;
		st.ptr_enter = S.n_ptr_enter;
		st.ptr_leave = S.n_ptr_leave;
		st.last_key = S.last_key;
		st.last_key_name = S.last_key_name[0] ? S.last_key_name : "-";
		if ((S.o->photo_frame == PHOTO_FRAME_B || S.o->photo_frame == PHOTO_FRAME_C) && S.o->window_type)
			st.window_type = S.o->window_type;
		else
			st.window_type = photo_frame_window_type(S.o->photo_frame);
		photo_frame_paint(&st, px, b->w, b->h);
		return;
	}
	if (S.o && S.o->menu && S.menu.screen != MENU_SCREEN_DEMO) {
		menu_paint(&S.menu, px, b->w, b->h);
		return;
	}
	for (y = 0; y < b->h; y++)
		for (x = 0; x < b->w; x++) {
			uint32_t c = 0xff000000u | rgb;
			if (((x / 64) + (y / 64)) & 1) c = 0xff000000u | ((rgb >> 1) & 0x7f7f7fu);
			if (x < 8 || y < 8 || x >= b->w - 8 || y >= b->h - 8) c = 0xffffffffu;
			if (S.o && S.o->input && S.sq > 0 &&
			    x >= S.sq_x && y >= S.sq_y && x < S.sq_x + S.sq && y < S.sq_y + S.sq)
				c = 0xff00ff00u;
			px[(size_t)y * b->w + x] = c;
		}
}

static void destroy_buf(struct buf *b)
{
	if (!b->buffer && !(b->data && b->data != MAP_FAILED)) return;
	if (b->busy)
		elog("buf: destroy-before-release gen=%d busy=1 size=%dx%d (wl_buffer.destroy before release leaves contents undefined; not treated as the cause of focus loss)\n",
		     b->gen, b->w, b->h);
	else
		elog("buf: destroy gen=%d busy=0 size=%dx%d\n", b->gen, b->w, b->h);
	if (b->buffer) { W.proxy_marshal(b->buffer, BUFFER_DESTROY); W.proxy_destroy(b->buffer); }
	if (b->data && b->data != MAP_FAILED) munmap(b->data, b->size);
	memset(b, 0, sizeof *b);
}

/* returns 0 ok, EX_ALLOC on allocation/SHM failure, EX_PROTO on listener
 * install failure. On failure the caller's cleanup()/destroy_buf() releases
 * whatever is recorded in *b. */
static int create_buf(struct buf *b, int w, int h)
{
	struct wl_proxy *pool;
	int stride, fd;
	size_t size;
	if (w < 1 || h < 1 || w > MAX_W || h > MAX_H) return EX_ALLOC;
	stride = w * 4;
	size = (size_t)stride * (size_t)h;   /* <= 1920*1080*4 = 8 MiB */
	if (size > MAX_SHM_BYTES || size > (size_t)INT32_MAX) return EX_ALLOC;
	fd = make_shm_file(S.o->runtime_dir, size);
	if (fd < 0) { elog("error: shm file in %s: %s\n", S.o->runtime_dir, strerror(errno)); return EX_ALLOC; }
	b->data = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
	if (b->data == MAP_FAILED) {
		elog("error: mmap shm: %s\n", strerror(errno));
		close(fd); b->data = NULL; return EX_ALLOC;
	}
	b->size = size; b->w = w; b->h = h; b->busy = 0;
	b->gen = ++S.buf_gen_next;
	S.cur_w = w; S.cur_h = h;
	elog("buf: create gen=%d %dx%d busy=0\n", b->gen, w, h);
	paint(b, S.bg);   /* safe: backing reserved by posix_fallocate */

	pool = new_obj(S.shm, W.i_shm_pool);
	if (!pool) { elog("error: wl_shm_pool proxy allocation failed\n"); close(fd); return EX_ALLOC; }
	W.proxy_marshal(S.shm, SHM_CREATE_POOL, pool, fd, (int32_t)size);
	close(fd);  /* fd is dup'ed into the outgoing message by libwayland */

	b->buffer = new_obj(pool, W.i_buffer);
	if (!b->buffer) {
		elog("error: wl_buffer proxy allocation failed\n");
		W.proxy_marshal(pool, SHM_POOL_DESTROY); W.proxy_destroy(pool);
		return EX_ALLOC;
	}
	/* listener before create_buffer is sent; on failure no server object exists */
	if (LISTEN(b->buffer, buffer_listener, b) != 0) {
		elog("error: wl_buffer listener install failed\n");
		W.proxy_destroy(b->buffer); b->buffer = NULL;
		W.proxy_marshal(pool, SHM_POOL_DESTROY); W.proxy_destroy(pool);
		return EX_PROTO;
	}
	W.proxy_marshal(pool, SHM_POOL_CREATE_BUFFER, b->buffer, 0, w, h, stride, WL_SHM_FORMAT_XRGB8888);
	W.proxy_marshal(pool, SHM_POOL_DESTROY);
	W.proxy_destroy(pool);
	return 0;
}

/* Arms the soft countdown once. Triggers are "configure", "commit-queued",
 * or "egl-swap". This is the same arming moment as 0.3. It does not measure
 * visible pixels, and a frame callback does not arm or rearm it. Focus,
 * sync, buffer release and wl_callback.done are not proof of visibility. */
static void arm_countdown(const char *trigger)
{
	int64_t now, until;
	if (g_show_armed || !S.o) return;
	g_show_armed = 1;
	now = now_ms();
	until = now + (int64_t)S.o->duration_s * 1000;
	if (g_alarm_at && until > g_alarm_at - 1000) until = g_alarm_at - 1000;
	if (until < now) until = now;
	g_deadline = until;
	elog("info: countdown-armed trigger=%s\n", trigger);
}

/* SHM-only. One pending wl_callback. Listener is not the roundtrip's stack int. */
static void frame_done(void *data, struct wl_proxy *cb, uint32_t server_ts)
{
	(void)data;
	S.n_frame_done++;
	elog("frame: callback done local_ms=%lld server_ts=%u (undefined base; not subtracted from local time; not a visibility proof)\n",
	     (long long)elapsed_ms(), server_ts);
	if (cb && cb == S.frame_cb) {
		W.proxy_destroy(S.frame_cb);
		S.frame_cb = NULL;
		elog("frame: callback proxy destroyed\n");
	}
}
static void *frame_listener[] = { (void *)frame_done };

static void queue_frame_callback(void)
{
	struct wl_proxy *cb;
	if (S.frame_cb) {
		elog("frame: request skipped pending cap=1\n");
		return;
	}
	cb = new_obj((struct wl_proxy *)S.display, W.i_callback);
	if (!cb) {
		elog("frame: callback proxy allocation failed; committing without a frame request (not a failed present)\n");
		return;
	}
	if (LISTEN(cb, frame_listener, NULL) != 0) {
		elog("frame: callback listener install failed; committing without a frame request (not a failed present)\n");
		W.proxy_destroy(cb);
		return;
	}
	W.proxy_marshal(S.surface, SURFACE_FRAME, cb);
	S.frame_cb = cb;
	elog("frame: request queued before commit (shm only; egl frame callbacks are not covered)\n");
}

static void present_buf(struct buf *b)
{
	arm_countdown("commit-queued");
	queue_frame_callback();
	W.proxy_marshal(S.surface, SURFACE_ATTACH, b->buffer, 0, 0);
	W.proxy_marshal(S.surface, SURFACE_DAMAGE, 0, 0, b->w, b->h);
	W.proxy_marshal(S.surface, SURFACE_COMMIT);
	b->busy = 1;
	S.n_commits++;
	elog("buf: commit-queued seq=%d gen=%d busy=1\n", S.n_commits, b->gen);
}

static void present(void)
{
	present_buf(&S.buf);
}

/* Suppress only an immediate repeat of the same key. A different key still logs. */
static int model_log_ok(uint32_t key)
{
	int64_t now = elapsed_ms();
	if (S.model_key_set && key == S.model_key && S.model_log_ms && now - S.model_log_ms < 100) {
		S.model_suppressed++;
		return 0;
	}
	S.model_key_set = 1;
	S.model_key = key;
	S.model_log_ms = now;
	return 1;
}

static void destroy_spares(void)
{
	int i;
	for (i = 0; i < S.nspare; i++)
		destroy_buf(&S.spare[i]);
	S.nspare = 0;
}

/* Demo redraw. The 30 s SAM run committed one buffer and got releases=0, so
 * painting that buffer again was deferred. A free buffer is painted instead.
 * A busy buffer is never written. */
static struct buf *demo_buffer(void)
{
	int i, rc, w, h;
	struct buf *b;
	if (S.buf.buffer && !S.buf.busy) return &S.buf;
	for (i = 0; i < S.nspare; i++)
		if (S.spare[i].buffer && !S.spare[i].busy) return &S.spare[i];
	if (S.nspare >= DEMO_MAX_BUFS) return NULL;
	w = S.buf.w > 0 ? S.buf.w : S.o->width;
	h = S.buf.h > 0 ? S.buf.h : S.o->height;
	b = &S.spare[S.nspare];
	rc = create_buf(b, w, h);
	if (rc != 0) { destroy_buf(b); S.fatal = rc; return NULL; }
	S.nspare++;
	elog("buf: spare gen=%d nspare=%d cap=%d\n", b->gen, S.nspare, DEMO_MAX_BUFS);
	return b;
}

/* 1 if a buffer was painted and committed, 0 if the redraw was deferred. */
static int request_redraw(void)
{
	struct buf *b;
	if (use_spare_bufs()) {
		b = demo_buffer();
		if (!b) {
			if (S.fatal) return 0;
			S.dirty = 1;
			S.n_deferred++;
			elog("redraw: deferred spare-cap=%d\n", DEMO_MAX_BUFS);
			return 0;
		}
	} else {
		if (!S.buf.buffer || !S.buf.data) return 0;
		if (S.buf.busy) {
			S.dirty = 1;
			S.n_deferred++;
			elog("redraw: deferred gen=%d busy=1\n", S.buf.gen);
			return 0;
		}
		b = &S.buf;
	}
	S.n_redraws++;
	elog("redraw: queued gen=%d busy=0\n", b->gen);
	paint(b, S.bg);
	present_buf(b);
	S.dirty = 0;
	return 1;
}

/* Keep shown tile == logical selection. On this TV releases=0, so after
 * DEMO_MAX_BUFS spares a deferred redraw would otherwise leave OK acting
 * on a tile the compositor is not displaying. Revert and drop dirty: the
 * last committed frame already matches the held state. */
static int menu_commit_visual(const struct menu_state *prev)
{
	if (request_redraw())
		return 1;
	S.menu = *prev;
	S.dirty = 0;
	elog("menu: selection held spare-cap=%d shown=%s screen=%s\n",
	     DEMO_MAX_BUFS, menu_focus_label(&S.menu), menu_screen_name(S.menu.screen));
	return 0;
}

/* buffer release — defined above as a listener; redraw if input changed while busy */
static void buf_release(void *data, struct wl_proxy *b)
{
	struct buf *buf = data;
	(void)b;
	buf->busy = 0;
	S.n_releases++;
	elog("buf: release gen=%d busy=0\n", buf->gen);
	if (S.dirty && !S.quit && buf->data && buf->buffer) request_redraw();
}

/* ---- main ------------------------------------------------------------- */
static void print_config(const struct opts *o)
{
	int i, n, tx, ty, tw, th;
	const struct menu_key_map *tab;
	printf("dry_run=%d\ndemo=%d\nmenu=%d\nphoto_frame=%s\nluna_register=%d\nheartbeat_ms=%d\ninput=%d\nwebos_shell=%d\nwebos_key_mask=%d\nexit_on_leave=%d\negl=%d\nsam_launch=%d\nsam_lifecycle2=%d\napp_id=%s\nwindow_type=%s\nduration_s=%d\n"
	       "size=%dx%d\nmax_size=%dx%d\ncolor=%06x\nfullscreen=%d\n"
	       "runtime_dir=%s\ndisplay=%s\n",
	       o->dry_run, o->demo, o->menu, photo_frame_mode_name(o->photo_frame), o->luna_register, o->heartbeat_ms, o->input, o->webos_shell, o->webos_key_mask, o->exit_on_leave, o->egl,
	       o->sam_launch, o->sam_lifecycle2, o->app_id,
	       o->window_type ? o->window_type : (o->photo_frame ? photo_frame_window_type(o->photo_frame) : "-"),
	       o->duration_s, o->width, o->height, o->max_w, o->max_h,
	       (unsigned)o->color, !o->no_fullscreen, o->runtime_dir, o->display_name);
	if (o->photo_frame)
		printf("photo_frame_label=%s\nphoto_frame_window=%s\n",
		       photo_frame_mode_label(o->photo_frame),
		       photo_frame_window_type(o->photo_frame));
	if (!o->menu) return;
	printf("menu_tiles=Demo,About,Exit\n");
	tab = menu_keymap(&n);
	for (i = 0; i < n; i++)
		printf("menu_key name=%s code=%u class=%s status=%s note=%s\n",
		       tab[i].name, tab[i].code, menu_key_class_name(tab[i].klass),
		       tab[i].status, tab[i].note);
	for (i = 0; i < MENU_TILE_COUNT; i++) {
		if (menu_tile_rect(o->width, o->height, i, &tx, &ty, &tw, &th) == 0)
			printf("menu_tile index=%d rect=%d,%d,%d,%d\n", i, tx, ty, tw, th);
	}
}

/* ---- input (wl_seat only; never opens /dev/input) ---------------------- */
static const uint32_t k_palette[] = {
	0x204080u, 0xff0000u, 0x00aa00u, 0x0000ffu, 0xffaa00u, 0xff00ffu, 0x00ffffu, 0xffffffu
};
#define N_PALETTE ((int)(sizeof k_palette / sizeof k_palette[0]))

static void clamp_square(int w, int h)
{
	int maxx, maxy;
	if (S.sq < 8) S.sq = 8;
	maxx = w - S.sq - 8;
	maxy = h - S.sq - 8;
	if (maxx < 8) maxx = 8;
	if (maxy < 8) maxy = 8;
	if (S.sq_x < 8) S.sq_x = 8;
	if (S.sq_y < 8) S.sq_y = 8;
	if (S.sq_x > maxx) S.sq_x = maxx;
	if (S.sq_y > maxy) S.sq_y = maxy;
}

static void nudge_clamp(void)
{
	if (S.nudge_x > 0.8f) S.nudge_x = 0.8f;
	if (S.nudge_x < -0.8f) S.nudge_x = -0.8f;
	if (S.nudge_y > 0.8f) S.nudge_y = 0.8f;
	if (S.nudge_y < -0.8f) S.nudge_y = -0.8f;
}

static void copy_token(const char *in, char *out, size_t n)
{
	size_t i;
	if (!in || !in[0]) { snprintf(out, n, "-"); return; }
	for (i = 0; in[i] && i + 1 < n; i++) {
		unsigned char c = (unsigned char)in[i];
		out[i] = (c > 32 && c < 127) ? (char)c : '.';
	}
	out[i] = 0;
}

static const char *key_name(uint32_t code)
{
	switch (code) {
	case KEY_ESC_EVDEV: return "KEY_ESC";
	case KEY_ENTER_EVDEV: return "KEY_ENTER";
	case KEY_UP_EVDEV: return "KEY_UP";
	case KEY_LEFT_EVDEV: return "KEY_LEFT";
	case KEY_RIGHT_EVDEV: return "KEY_RIGHT";
	case KEY_DOWN_EVDEV: return "KEY_DOWN";
	case KEY_BACK_EVDEV: return "KEY_BACK";
	case KEY_EXIT_EVDEV: return "KEY_EXIT";
	case KEY_OK_EVDEV: return "KEY_OK";
	default: return "unknown";
	}
}

static void on_key(struct seat_slot *seat, uint32_t code, uint32_t state, uint32_t serial, uint32_t time)
{
	const char *name = key_name(code);
	const char *st = state == 1 ? "pressed" : (state == 0 ? "released" : "other");
	char label[64];
	copy_token(seat->label, label, sizeof label);
	/* stdout is the mapping log for the first on-TV run. One line, flushed. */
	olog("keycode raw=%u state=%s seat=%d name=%s\n", code, st, seat->index, label);
	elog("input: key seat=%d name=%s code=%u xkb_keycode=%u state=%s assumed_evdev=%s serial=%u time=%u\n",
	        seat->index, label, code, code + 8u, st, name, serial, time);
	fflush(stderr);
	if (state != 1) return;
	if (S.o && S.o->photo_frame) {
		S.last_key = code;
		snprintf(S.last_key_name, sizeof S.last_key_name, "%s", name);
		elog("photo-frame: key code=%u name=%s kb_enter=%d kb_leave=%d ptr_enter=%d\n",
		     code, name, S.n_focus_enter, S.n_focus_leave, S.n_ptr_enter);
		if (code == KEY_BACK_EVDEV) { S.quit = 1; S.reason = REASON_BACK; return; }
		if (code == KEY_ESC_EVDEV) { S.quit = 1; S.reason = REASON_ESC; return; }
		if (code == KEY_EXIT_EVDEV) { S.quit = 1; S.reason = REASON_EXITKEY; return; }
		request_redraw();
		return;
	}
	if (S.o && S.o->menu) {
		const struct menu_key_map *hit = NULL;
		enum menu_key_class klass = menu_classify_key(code, &hit);
		enum menu_action act;
		struct menu_state prev = S.menu;
		if (klass == MENU_KEY_UNKNOWN)
			elog("menu: unknown-keycode raw=%u (not in keymap table)\n", code);
		else
			elog("menu: key name=%s code=%u class=%s status=%s screen=%s focus=%s\n",
			     hit->name, hit->code, menu_key_class_name(klass), hit->status,
			     menu_screen_name(S.menu.screen), menu_focus_label(&S.menu));
		act = menu_handle_key(&S.menu, code);
		if (act == MENU_ACTION_EXIT) {
			S.quit = 1;
			S.reason = (klass == MENU_KEY_BACK) ? REASON_BACK : REASON_MENU_EXIT;
			elog("menu: exit reason=%s\n", S.reason == REASON_BACK ? "back-key" : "menu-exit");
			return;
		}
		if (act == MENU_ACTION_ENTER_DEMO) {
			elog("menu: activate Demo; entering existing demo (arrows move square; BACK returns)\n");
			menu_commit_visual(&prev);
			return;
		}
		if (act == MENU_ACTION_LEAVE_DEMO) {
			elog("menu: back from demo; screen=tiles focus=%s\n", menu_focus_label(&S.menu));
			menu_commit_visual(&prev);
			return;
		}
		if (act == MENU_ACTION_REDRAW) {
			elog("menu: screen=%s focus=%s\n", menu_screen_name(S.menu.screen), menu_focus_label(&S.menu));
			menu_commit_visual(&prev);
			return;
		}
		if (S.menu.screen == MENU_SCREEN_DEMO) {
			if (code == KEY_LEFT_EVDEV || code == KEY_RIGHT_EVDEV || code == KEY_UP_EVDEV || code == KEY_DOWN_EVDEV) {
				if (S.buf.w > 0) {
					if (code == KEY_LEFT_EVDEV) S.sq_x -= SQ_STEP;
					if (code == KEY_RIGHT_EVDEV) S.sq_x += SQ_STEP;
					if (code == KEY_UP_EVDEV) S.sq_y -= SQ_STEP;
					if (code == KEY_DOWN_EVDEV) S.sq_y += SQ_STEP;
					clamp_square(S.buf.w, S.buf.h);
					if (model_log_ok(code))
						elog("input: model square x=%d y=%d size=%d\n", S.sq_x, S.sq_y, S.sq);
					request_redraw();
				}
			}
			return;
		}
		return;
	}
	if (code == KEY_BACK_EVDEV) { S.quit = 1; S.reason = REASON_BACK; return; }
	if (code == KEY_ESC_EVDEV) { S.quit = 1; S.reason = REASON_ESC; return; }
	if (code == KEY_EXIT_EVDEV) { S.quit = 1; S.reason = REASON_EXITKEY; return; }
	if (code == KEY_LEFT_EVDEV || code == KEY_RIGHT_EVDEV || code == KEY_UP_EVDEV || code == KEY_DOWN_EVDEV) {
		if (S.egl_on) {
			if (code == KEY_LEFT_EVDEV) S.nudge_x -= 0.08f;
			if (code == KEY_RIGHT_EVDEV) S.nudge_x += 0.08f;
			if (code == KEY_UP_EVDEV) S.nudge_y += 0.08f;
			if (code == KEY_DOWN_EVDEV) S.nudge_y -= 0.08f;
			nudge_clamp();
			elog("input: nudge %.2f,%.2f\n", S.nudge_x, S.nudge_y);
		} else if (S.buf.w > 0) {
			if (code == KEY_LEFT_EVDEV) S.sq_x -= SQ_STEP;
			if (code == KEY_RIGHT_EVDEV) S.sq_x += SQ_STEP;
			if (code == KEY_UP_EVDEV) S.sq_y -= SQ_STEP;
			if (code == KEY_DOWN_EVDEV) S.sq_y += SQ_STEP;
			clamp_square(S.buf.w, S.buf.h);
			if (model_log_ok(code))
				elog("input: model square x=%d y=%d size=%d\n", S.sq_x, S.sq_y, S.sq);
			request_redraw();
		}
		return;
	}
	S.color_i = (S.color_i + 1) % N_PALETTE;
	if (k_palette[S.color_i] == S.bg) S.color_i = (S.color_i + 1) % N_PALETTE;
	S.bg = k_palette[S.color_i];
	if (model_log_ok(code))
		elog("input: model color %06x\n", S.bg);
	if (!S.egl_on) request_redraw();
}

static void kb_keymap(void *data, struct wl_proxy *kb, uint32_t format, int32_t fd, uint32_t size)
{
	struct seat_slot *seat = data;
	const char *fname = format == 0 ? "no_keymap" : (format == 1 ? "xkb_v1" : "unknown");
	char prefix[64];
	(void)kb;
	prefix[0] = 0;
	elog("input: keymap seat=%d format=%u (%s) size=%u\n", seat->index, format, fname, size);
	if (format == 1 && fd >= 0 && size > 0 && size <= 262144u) {
		void *p = mmap(NULL, size, PROT_READ, MAP_PRIVATE, fd, 0);
		if (p != MAP_FAILED) {
			size_t n = size < 48 ? size : 48, i, o = 0;
			const char *s = p;
			for (i = 0; i < n && o + 1 < sizeof prefix; i++) {
				unsigned char c = (unsigned char)s[i];
				prefix[o++] = (c >= 32 && c < 127) ? (char)c : '.';
			}
			prefix[o] = 0;
			munmap(p, size);
		} else snprintf(prefix, sizeof prefix, "(unreadable)");
	} else snprintf(prefix, sizeof prefix, "(not-mapped)");
	elog("input: keymap seat=%d prefix=%s\n", seat->index, prefix);
	fflush(stderr);
	if (fd >= 0) close(fd);
}

static const char *surface_whose(struct wl_proxy *surface)
{
	if (!surface) return "null";
	if (S.surface && surface == S.surface) return "ours";
	return "other";
}

static void kb_enter(void *data, struct wl_proxy *kb, uint32_t serial, struct wl_proxy *surface, void *keys)
{
	struct seat_slot *seat = data;
	(void)kb; (void)keys;
	seat->kb_entered = 1;
	S.n_focus_enter++;
	elog("input: keyboard enter seat=%d surface=%s name=%s serial=%u\n",
	     seat->index, surface_whose(surface), seat->label, serial);
	if (S.o && S.o->photo_frame) {
		elog("photo-frame: focus_enter=%d focus_leave=%d ptr_enter=%d\n",
		     S.n_focus_enter, S.n_focus_leave, S.n_ptr_enter);
		request_redraw();
	}
}
static void kb_leave(void *data, struct wl_proxy *kb, uint32_t serial, struct wl_proxy *surface)
{
	struct seat_slot *seat = data;
	(void)kb;
	S.n_focus_leave++;
	elog("input: keyboard leave seat=%d surface=%s name=%s serial=%u entered=%d\n",
	     seat->index, surface_whose(surface), seat->label, serial, seat->kb_entered);
	if (S.o && S.o->photo_frame) {
		elog("photo-frame: focus_enter=%d focus_leave=%d ptr_enter=%d\n",
		     S.n_focus_enter, S.n_focus_leave, S.n_ptr_enter);
		request_redraw();
	}
	if (S.o && S.o->exit_on_leave && seat->kb_entered) {
		S.quit = 1;
		S.reason = REASON_KB_LEAVE;
		elog("info: exit-on-leave seat=%d\n", seat->index);
	}
}
static void kb_key(void *data, struct wl_proxy *kb, uint32_t serial, uint32_t time, uint32_t key, uint32_t state)
{
	(void)kb;
	on_key(data, key, state, serial, time);
}
static void kb_mods(void *data, struct wl_proxy *kb, uint32_t serial, uint32_t dep, uint32_t lat, uint32_t lock, uint32_t group)
{
	struct seat_slot *seat = data;
	(void)kb; (void)serial;
	elog("input: modifiers seat=%d depressed=0x%x latched=0x%x locked=0x%x group=%u\n",
	        seat->index, dep, lat, lock, group);
	fflush(stderr);
}
static void *keyboard_listener[] = {
	(void *)kb_keymap, (void *)kb_enter, (void *)kb_leave, (void *)kb_key, (void *)kb_mods
};

static void split_fixed(int32_t v, int *whole, int *milli)
{
	int neg = v < 0;
	int64_t a = neg ? -(int64_t)v : (int64_t)v;
	*whole = (int)(a / 256);
	*milli = (int)((a % 256) * 1000 / 256);
	if (neg) *whole = -*whole;
}

static void ptr_enter(void *data, struct wl_proxy *p, uint32_t serial, struct wl_proxy *surf, int32_t x, int32_t y)
{
	struct seat_slot *seat = data;
	int xw, xm, yw, ym;
	(void)p; (void)surf;
	split_fixed(x, &xw, &xm); split_fixed(y, &yw, &ym);
	S.n_ptr_enter++;
	elog("input: pointer enter seat=%d serial=%u x=%d.%03d y=%d.%03d raw_x=%d raw_y=%d\n",
	        seat->index, serial, xw, xm, yw, ym, (int)x, (int)y);
	if (S.o && S.o->photo_frame) {
		elog("photo-frame: ptr_enter=%d ptr_leave=%d kb_enter=%d\n",
		     S.n_ptr_enter, S.n_ptr_leave, S.n_focus_enter);
		request_redraw();
	}
	fflush(stderr);
}
static void ptr_leave(void *data, struct wl_proxy *p, uint32_t serial, struct wl_proxy *surf)
{
	struct seat_slot *seat = data;
	(void)p; (void)surf;
	S.n_ptr_leave++;
	elog("input: pointer leave seat=%d serial=%u\n", seat->index, serial);
	if (S.o && S.o->photo_frame)
		elog("photo-frame: ptr_enter=%d ptr_leave=%d kb_enter=%d\n",
		     S.n_ptr_enter, S.n_ptr_leave, S.n_focus_enter);
}
static void ptr_motion(void *data, struct wl_proxy *p, uint32_t time, int32_t x, int32_t y)
{
	struct seat_slot *seat = data;
	int xw, xm, yw, ym;
	(void)p;
	split_fixed(x, &xw, &xm); split_fixed(y, &yw, &ym);
	elog("input: pointer motion seat=%d time=%u x=%d.%03d y=%d.%03d raw_x=%d raw_y=%d\n",
	        seat->index, time, xw, xm, yw, ym, (int)x, (int)y);
	fflush(stderr);
}
static void ptr_button(void *data, struct wl_proxy *p, uint32_t serial, uint32_t time, uint32_t button, uint32_t state)
{
	struct seat_slot *seat = data;
	(void)p;
	elog("input: pointer button seat=%d serial=%u time=%u evdev=%u state=%u\n",
	        seat->index, serial, time, button, state);
	fflush(stderr);
}
static void ptr_axis(void *data, struct wl_proxy *p, uint32_t time, uint32_t axis, int32_t value)
{
	struct seat_slot *seat = data;
	(void)p;
	elog("input: pointer axis seat=%d time=%u axis=%u raw=%d\n", seat->index, time, axis, (int)value);
}
static void *pointer_listener[] = {
	(void *)ptr_enter, (void *)ptr_leave, (void *)ptr_motion, (void *)ptr_button, (void *)ptr_axis
};

static void seat_caps(void *data, struct wl_proxy *seat, uint32_t caps)
{
	struct seat_slot *s = data;
	elog("input: seat index=%d global=%u name=%s caps=0x%x\n",
	        s->index, s->global_name, s->label, caps);
	fflush(stderr);
	if ((caps & 2u) && !s->keyboard && W.i_keyboard) {
		struct wl_proxy *kb = new_obj(seat, W.i_keyboard);
		if (!kb) { elog("error: wl_keyboard proxy allocation failed\n"); S.fatal = EX_ALLOC; return; }
		if (LISTEN(kb, keyboard_listener, s) != 0) {
			W.proxy_destroy(kb);
			elog("error: wl_keyboard listener install failed\n");
			S.fatal = EX_PROTO;
			return;
		}
		s->keyboard = kb;
		W.proxy_marshal(seat, SEAT_GET_KEYBOARD, kb);
	} else if (!(caps & 2u) && s->keyboard) {
		W.proxy_destroy(s->keyboard); s->keyboard = NULL;
	}
	if ((caps & 1u) && !s->pointer && W.i_pointer) {
		struct wl_proxy *pt = new_obj(seat, W.i_pointer);
		if (!pt) { elog("error: wl_pointer proxy allocation failed\n"); S.fatal = EX_ALLOC; return; }
		if (LISTEN(pt, pointer_listener, s) != 0) {
			W.proxy_destroy(pt);
			elog("error: wl_pointer listener install failed\n");
			S.fatal = EX_PROTO;
			return;
		}
		s->pointer = pt;
		W.proxy_marshal(seat, SEAT_GET_POINTER, pt);
	} else if (!(caps & 1u) && s->pointer) {
		W.proxy_destroy(s->pointer); s->pointer = NULL;
	}
}

static void seat_name(void *data, struct wl_proxy *seat, const char *name)
{
	struct seat_slot *s = data;
	(void)seat;
	copy_token(name, s->label, sizeof s->label);
	elog("input: seat index=%d global=%u name=%s\n", s->index, s->global_name, s->label);
	fflush(stderr);
}
static void *seat_listener[] = { (void *)seat_caps, (void *)seat_name };

/* ---- optional libraries (not libwayland-client) ----------------------- */
static void *dlopen_extra(const char *soname)
{
	const char *dir = getenv("WAYLAND_HELLO_LIB_DIR");
	char path[512];
	void *h;
	if (dir && dir[0]) {
		if (snprintf(path, sizeof path, "%s/%s", dir, soname) >= (int)sizeof path) {
			elog("error: dlopen path too long for %s\n", soname);
			return NULL;
		}
		h = dlopen(path, RTLD_NOW | RTLD_LOCAL);
		if (!h) elog("error: dlopen %s failed: %s\n", path, dlerror());
		return h;
	}
	h = dlopen(soname, RTLD_NOW | RTLD_LOCAL);
	if (!h) elog("error: dlopen %s failed: %s\n", soname, dlerror());
	return h;
}

/* ---- optional luna registration (dlopen; not a NEEDED library) -------- */
/*
 * webOS OSE native apps call
 * luna://com.webos.service.applicationmanager/registerApp
 * (nativeqt ServiceRequest.cpp; native-app overview). SAM binds
 * registerNativeApp to the same handler (ApplicationManager.cpp).
 * NativeContainer.cpp exports LS2_NAME as "<appId>-<n>" and registerApp
 * looks the caller up by that bus name, then by app id.
 * LSGmainAttach plus g_main_context_iteration(NULL, FALSE) pumps replies
 * from the Wayland poll loop without a blocking GLib loop.
 */
struct ls_error {
	int error_code;
	char *message;
	const char *file;
	int line;
	const char *func;
	void *padding;
	unsigned long magic;
};
struct ls_handle;
struct ls_message;

static struct {
	void *h_luna;
	void *h_glib;
	void *loop;
	struct ls_handle *sh;
	bool (*error_init)(struct ls_error *);
	void (*error_free)(struct ls_error *);
	bool (*ls_register)(const char *, struct ls_handle **, struct ls_error *);
	bool (*ls_attach)(struct ls_handle *, void *, struct ls_error *);
	bool (*ls_call)(struct ls_handle *, const char *, const char *,
	                bool (*)(struct ls_handle *, struct ls_message *, void *),
	                void *, unsigned long *, struct ls_error *);
	const char *(*payload)(struct ls_message *);
	bool (*ls_unregister)(struct ls_handle *, struct ls_error *);
	void *(*loop_new)(void *, int);
	void (*loop_unref)(void *);
	int (*iterate)(void *, int);
	int up;
	int noted_no_reply;
	int64_t call_ms;
} Luna;

#define LUNA_REGISTER_ACK_MS 2000

static const char *luna_skip_ws(const char *p)
{
	while (*p == ' ' || *p == '\t' || *p == '\n' || *p == '\r') p++;
	return p;
}

/* Skip one JSON value. Strings and nested objects/arrays are not searched. */
static const char *luna_skip_value(const char *p)
{
	if (*p == '"') {
		p++;
		while (*p && *p != '"') {
			if (*p == '\\' && p[1]) p += 2;
			else p++;
		}
		if (*p == '"') p++;
		return p;
	}
	if (*p == '{' || *p == '[') {
		char open = *p;
		char close = (open == '{') ? '}' : ']';
		int depth = 1;
		p++;
		while (*p && depth) {
			if (*p == '"') {
				p = luna_skip_value(p);
				continue;
			}
			if (*p == open) depth++;
			else if (*p == close) depth--;
			if (*p) p++;
		}
		return p;
	}
	while (*p && *p != ',' && *p != '}' && *p != ']' &&
	       *p != ' ' && *p != '\t' && *p != '\n' && *p != '\r')
		p++;
	return p;
}

/* Value of a top-level key, or NULL. Nested keys do not match. */
static const char *luna_top_value(const char *payload, const char *key)
{
	const char *p;
	size_t klen;
	if (!payload || !key) return NULL;
	p = luna_skip_ws(payload);
	if (*p != '{') return NULL;
	p++;
	klen = strlen(key);
	while (*p) {
		const char *ks, *ke;
		p = luna_skip_ws(p);
		if (*p == '}' || *p == '\0') return NULL;
		if (*p == ',') { p++; continue; }
		if (*p != '"') return NULL;
		ks = ++p;
		while (*p && *p != '"') {
			if (*p == '\\' && p[1]) p += 2;
			else p++;
		}
		if (*p != '"') return NULL;
		ke = p++;
		p = luna_skip_ws(p);
		if (*p != ':') return NULL;
		p = luna_skip_ws(p + 1);
		if ((size_t)(ke - ks) == klen && memcmp(ks, key, klen) == 0)
			return p;
		p = luna_skip_value(p);
	}
	return NULL;
}

static int luna_top_string_is(const char *payload, const char *key, const char *lit)
{
	const char *v = luna_top_value(payload, key);
	size_t n;
	if (!v || *v != '"' || !lit) return 0;
	v++;
	n = strlen(lit);
	return strncmp(v, lit, n) == 0 && v[n] == '"';
}

static int luna_top_false(const char *payload, const char *key)
{
	const char *v = luna_top_value(payload, key);
	if (!v || strncmp(v, "false", 5) != 0) return 0;
	return v[5] == '\0' || v[5] == ',' || v[5] == '}' ||
	       v[5] == ' ' || v[5] == '\n' || v[5] == '\r' || v[5] == '\t';
}

static int luna_top_key(const char *payload, const char *key)
{
	return luna_top_value(payload, key) != NULL;
}

static void persist_restore_foreground(const char *event)
{
	uint32_t st;
	if (!event) event = "?";
	S.n_restore++;
	if (!S.o) {
		elog("persist: restore-foreground event=%s deferred n=%d\n", event, S.n_restore);
		S.need_restore = 1;
		return;
	}
	st = S.o->no_fullscreen ? 0u : 3u;
	if (S.webos_shell_surface && S.op_set_state >= 0 && W.proxy_marshal) {
		W.proxy_marshal(S.webos_shell_surface, (uint32_t)S.op_set_state, st);
		elog("persist: restore-foreground event=%s webos set_state=%u n=%d\n", event, st, S.n_restore);
	} else if (S.shell_surface && W.proxy_marshal) {
		if (S.o->no_fullscreen) W.proxy_marshal(S.shell_surface, SHSURF_SET_TOPLEVEL);
		else W.proxy_marshal(S.shell_surface, SHSURF_SET_FULLSCREEN, 0u, 0u, (struct wl_proxy *)NULL);
		elog("persist: restore-foreground event=%s wl_shell n=%d\n", event, S.n_restore);
	} else {
		elog("persist: restore-foreground event=%s deferred (no surface yet) n=%d\n", event, S.n_restore);
		S.need_restore = 1;
		return;
	}
	S.need_restore = 0;
	if (!S.egl_on) request_redraw();
}

static bool luna_on_reply(struct ls_handle *sh, struct ls_message *msg, void *ctx)
{
	const char *payload = Luna.payload ? Luna.payload(msg) : NULL;
	char buf[513];
	size_t n;
	(void)sh; (void)ctx;
	S.luna_replies++;
	if (!payload) {
		elog("luna: reply (null)\n");
		return true;
	}
	n = strlen(payload);
	if (n > 512) n = 512;
	memcpy(buf, payload, n);
	buf[n] = 0;
	elog("luna: reply %s%s\n", buf, payload[n] ? "..." : "");
	if (luna_top_string_is(payload, "event", "close")) {
		elog("luna: event=close\n");
		S.quit = 1;
		S.reason = REASON_LUNA_CLOSE;
	} else if (luna_top_false(payload, "returnValue") ||
	           ((luna_top_key(payload, "errorCode") || luna_top_key(payload, "errorText")) &&
	            !luna_top_string_is(payload, "event", "registered") &&
	            !luna_top_string_is(payload, "event", "relaunch") &&
	            !luna_top_string_is(payload, "event", "pause"))) {
		elog("luna: reply rejected\n");
		S.quit = 1;
		S.fatal = EX_NOLUNA;
		S.reason = REASON_LUNA_REJECT;
	} else if (luna_top_string_is(payload, "event", "relaunch")) {
		elog("luna: event=relaunch\n");
		/* OSE nativeqt showFullScreen() on relaunch; no client ack is required
		 * (RunningApp::sendEvent just responds on the subscription). */
		persist_restore_foreground("relaunch");
	} else if (luna_top_string_is(payload, "event", "registered")) {
		elog("luna: event=registered\n");
		S.luna_acked = 1;
	} else if (luna_top_string_is(payload, "event", "pause")) {
		elog("luna: event=pause\n");
		/* Stay mapped. Overlay is what should keep pixels above Home. */
	} else {
		elog("luna: event=other\n");
	}
	return true;
}

static void luna_iterate(void)
{
	if (!Luna.iterate) return;
	S.luna_polls++;
	/* Non-blocking. NULL is the default context, the same one
	 * g_main_loop_new(NULL, FALSE) attached via LSGmainAttach. */
	Luna.iterate(NULL, 0);
}

/* OSE RunningApp::registerApp replies in that call with event=registered.
 * No public path was found where a successful registerApp stays silent,
 * so a missing top-level ack is fail-closed rather than a flag. */
static void luna_check_ack(int at_deadline)
{
	long long waited;
	if (!Luna.up || S.luna_acked || S.quit || S.fatal) return;
	if (!S.o || !S.o->luna_register) return;
	waited = (long long)(elapsed_ms() - Luna.call_ms);
	if (waited < LUNA_REGISTER_ACK_MS && !at_deadline) return;
	if (!Luna.noted_no_reply) {
		elog("luna: no registerApp reply after %lldms\n", waited);
		Luna.noted_no_reply = 1;
	}
	S.quit = 1;
	S.fatal = EX_NOLUNA;
	S.reason = REASON_LUNA_REJECT;
}

static void luna_shutdown(void)
{
	struct ls_error err;
	if (Luna.ls_unregister && Luna.sh) {
		if (Luna.error_init) Luna.error_init(&err);
		Luna.ls_unregister(Luna.sh, &err);
		if (Luna.error_free) Luna.error_free(&err);
		Luna.sh = NULL;
	}
	if (Luna.loop && Luna.loop_unref) {
		Luna.loop_unref(Luna.loop);
		Luna.loop = NULL;
	}
	Luna.error_init = NULL;
	Luna.error_free = NULL;
	Luna.ls_register = NULL;
	Luna.ls_attach = NULL;
	Luna.ls_call = NULL;
	Luna.payload = NULL;
	Luna.ls_unregister = NULL;
	Luna.loop_new = NULL;
	Luna.loop_unref = NULL;
	Luna.iterate = NULL;
	if (Luna.h_luna) { dlclose(Luna.h_luna); Luna.h_luna = NULL; }
	if (Luna.h_glib) { dlclose(Luna.h_glib); Luna.h_glib = NULL; }
	Luna.up = 0;
}

static void luna_log_lserror(const char *what, struct ls_error *err)
{
	char msg[160];
	const char *src;
	size_t i, o = 0;
	int code = err ? err->error_code : -1;
	src = (err && err->message) ? err->message : "-";
	for (i = 0; src[i] && o + 1 < sizeof msg; i++) {
		unsigned char c = (unsigned char)src[i];
		if (c >= 32 && c < 127) msg[o++] = (char)c;
	}
	msg[o] = 0;
	elog("luna: %s failed code=%d message=%s. Failing closed.\n", what, code, msg[0] ? msg : "-");
}

static int luna_name_ok(const char *s)
{
	const char *p;
	int n = 0;
	if (!s || !*s) return 0;
	for (p = s; *p; p++, n++) {
		unsigned char c = (unsigned char)*p;
		if (n >= 80 || !(c == '.' || c == '_' || c == '-' ||
		    (c >= '0' && c <= '9') || (c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z')))
			return 0;
	}
	return 1;
}

static void *luna_sym(void *h, const char *name)
{
	void *p = dlsym(h, name);
	if (!p) elog("error: missing symbol %s\n", name);
	return p;
}

static void *luna_dlopen_named(const char *soname, const char *absolute)
{
	const char *dir = getenv("WAYLAND_HELLO_LIB_DIR");
	char path[512];
	void *h;
	if (dir && dir[0]) {
		if (snprintf(path, sizeof path, "%s/%s", dir, soname) >= (int)sizeof path) {
			elog("error: dlopen path too long for %s\n", soname);
			return NULL;
		}
	} else {
		snprintf(path, sizeof path, "%s", absolute);
	}
	h = dlopen(path, RTLD_NOW | RTLD_LOCAL);
	if (!h) elog("error: dlopen %s failed: %s\n", path, dlerror());
	return h;
}

static int luna_start(const char *app_id)
{
	struct ls_error err;
	const char *env_name = getenv("LS2_NAME");
	const char *reg_name;
	const char *uri = "luna://com.webos.service.applicationmanager/registerApp";
	const char *body = "{\"subscribe\":true}";
	unsigned long token = 0;
	if (!luna_name_ok(app_id)) {
		elog("error: --luna-register needs an app id; failing closed\n");
		return -1;
	}
	if (luna_name_ok(env_name)) {
		reg_name = env_name;
		elog("luna: register name=%s source=LS2_NAME\n", reg_name);
	} else {
		reg_name = app_id;
		elog("luna: register name=%s source=app-id\n", reg_name);
		if (env_name && *env_name)
			elog("luna: LS2_NAME is set but not a usable service name; using the app id\n");
	}
	{
		char exe[256];
		ssize_t n = readlink("/proc/self/exe", exe, sizeof exe - 1);
		if (n > 0) {
			exe[n] = '\0';
			elog("luna: exe=%s\n", exe);
		} else {
			elog("luna: exe=unknown\n");
		}
	}
	Luna.h_glib = luna_dlopen_named("libglib-2.0.so.0", "/usr/lib/libglib-2.0.so.0");
	Luna.h_luna = luna_dlopen_named("libluna-service2.so.3", "/usr/lib/libluna-service2.so.3");
	if (!Luna.h_glib || !Luna.h_luna) {
		elog("error: libglib-2.0.so.0 or libluna-service2.so.3 did not load. Failing closed.\n");
		luna_shutdown();
		return -1;
	}
	Luna.error_init = luna_sym(Luna.h_luna, "LSErrorInit");
	Luna.error_free = luna_sym(Luna.h_luna, "LSErrorFree");
	Luna.ls_register = luna_sym(Luna.h_luna, "LSRegister");
	Luna.ls_attach = luna_sym(Luna.h_luna, "LSGmainAttach");
	Luna.ls_call = luna_sym(Luna.h_luna, "LSCall");
	Luna.payload = luna_sym(Luna.h_luna, "LSMessageGetPayload");
	Luna.ls_unregister = luna_sym(Luna.h_luna, "LSUnregister");
	Luna.loop_new = luna_sym(Luna.h_glib, "g_main_loop_new");
	Luna.loop_unref = luna_sym(Luna.h_glib, "g_main_loop_unref");
	Luna.iterate = luna_sym(Luna.h_glib, "g_main_context_iteration");
	if (!Luna.error_init || !Luna.error_free || !Luna.ls_register || !Luna.ls_attach ||
	    !Luna.ls_call || !Luna.payload || !Luna.ls_unregister ||
	    !Luna.loop_new || !Luna.loop_unref || !Luna.iterate) {
		elog("error: luna/glib symbols incomplete. Failing closed.\n");
		luna_shutdown();
		return -1;
	}
	Luna.error_init(&err);
	if (!Luna.ls_register(reg_name, &Luna.sh, &err) || !Luna.sh) {
		luna_log_lserror("LSRegister", &err);
		Luna.error_free(&err);
		luna_shutdown();
		return -1;
	}
	Luna.loop = Luna.loop_new(NULL, 0);
	if (!Luna.loop || !Luna.ls_attach(Luna.sh, Luna.loop, &err)) {
		luna_log_lserror(Luna.loop ? "LSGmainAttach" : "g_main_loop_new", &err);
		Luna.error_free(&err);
		luna_shutdown();
		return -1;
	}
	elog("luna: LSCall %s %s\n", uri, body);
	if (!Luna.ls_call(Luna.sh, uri, body, luna_on_reply, NULL, &token, &err)) {
		luna_log_lserror("LSCall", &err);
		Luna.error_free(&err);
		luna_shutdown();
		return -1;
	}
	Luna.error_free(&err);
	Luna.call_ms = elapsed_ms();
	Luna.up = 1;
	luna_iterate();
	luna_check_ack(0);
	return 0;
}

static int method_slot(const struct wl_interface *iface, const char *method, const char *sig_a, const char *sig_b, int required, int *out)
{
	int i;
	*out = -1;
	if (!iface || iface->method_count < 0 || iface->method_count > 32 || (iface->method_count > 0 && !iface->methods)) {
		elog("error: webos interface for %s is not usable\n", method);
		return -1;
	}
	for (i = 0; i < iface->method_count; i++) {
		const struct wl_message *m = &iface->methods[i];
		if (!m->name || strcmp(m->name, method) != 0) continue;
		if (!m->signature || (strcmp(m->signature, sig_a) != 0 && !(sig_b && strcmp(m->signature, sig_b) == 0))) {
			elog("error: webos %s signature '%s' is not '%s'%s%s; refusing to send it\n",
			        method, m->signature ? m->signature : "(null)", sig_a,
			        sig_b ? " or " : "", sig_b ? sig_b : "");
			return -1;
		}
		*out = i;
		return 0;
	}
	if (!required) return 0;
	elog("error: webos method %s is not in the runtime interface\n", method);
	return -1;
}

static int resolve_webos(void)
{
	const struct wl_interface *shell, *surf;
	S.webos_dl = dlopen_extra("libwayland-webos-client.so.1");
	if (!S.webos_dl) {
		elog("error: wl_webos_shell is advertised but libwayland-webos-client.so.1 did not load; refusing to guess opcodes. Failing closed.\n");
		return -1;
	}
	shell = dlsym(S.webos_dl, "wl_webos_shell_interface");
	surf = dlsym(S.webos_dl, "wl_webos_shell_surface_interface");
	if (!shell || !surf || !shell->name || strcmp(shell->name, "wl_webos_shell") != 0 ||
	    !surf->name || strcmp(surf->name, "wl_webos_shell_surface") != 0) {
		elog("error: runtime webos interfaces missing or renamed; failing closed\n");
		dlclose(S.webos_dl); S.webos_dl = NULL;
		return -1;
	}
	if (shell->version < 1 || surf->version < 1) {
		elog("error: runtime webos interface version < 1; failing closed\n");
		dlclose(S.webos_dl); S.webos_dl = NULL;
		return -1;
	}
	S.op_set_key_mask = -1;
	if (method_slot(shell, "get_shell_surface", "no", "n?o", 1, &S.op_get_shell_surface) ||
	    method_slot(surf, "set_state", "u", NULL, 1, &S.op_set_state) ||
	    method_slot(surf, "set_property", "ss", NULL, 1, &S.op_set_property) ||
	    (S.o->webos_key_mask && method_slot(surf, "set_key_mask", "u", NULL, 1, &S.op_set_key_mask))) {
		dlclose(S.webos_dl); S.webos_dl = NULL;
		return -1;
	}
	S.webos_shell_iface = shell;
	S.webos_surf_iface = surf;
	elog("info: webos runtime shell_version=%d surface_version=%d advertised=%u get_shell_surface=%d set_state=%d set_property=%d set_key_mask=%d\n",
	        shell->version, surf->version, S.webos_advertised, S.op_get_shell_surface,
	        S.op_set_state, S.op_set_property, S.op_set_key_mask);
	return 0;
}

/* One listener slot per event index. The proxy has a single data pointer, so
 * the opcode is baked into the function. Names come from the runtime interface. */
static char webos_ev_name[16][48];
static char webos_ev_sig[16][12];
struct webos_arr { size_t size; size_t alloc; void *data; };

static void webos_note_close(int idx)
{
	if (!strcmp(webos_ev_name[idx], "close")) {
		S.quit = 1;
		S.reason = REASON_WEBOS_CLOSE;
	}
}
static void webos_on_empty(int idx)
{
	elog("webos: event %s signature=%s\n", webos_ev_name[idx], webos_ev_sig[idx]);
	webos_note_close(idx);
}
static void webos_on_u(int idx, uint32_t v)
{
	elog("webos: event %s value=%u\n", webos_ev_name[idx], v);
}
static void webos_on_ii(int idx, int32_t x, int32_t y)
{
	elog("webos: event %s x=%d y=%d\n", webos_ev_name[idx], (int)x, (int)y);
}
static void webos_on_array(int idx, struct webos_arr *a)
{
	int n = 0, i;
	char buf[128];
	size_t o = 0;
	buf[0] = 0;
	if (a && a->data && a->size >= 4 && a->size <= 256) {
		n = (int)(a->size / 4);
		if (n > 8) n = 8;
		for (i = 0; i < n && o + 12 < sizeof buf; i++) {
			int32_t v;
			memcpy(&v, (char *)a->data + (size_t)i * 4, 4);
			o += (size_t)snprintf(buf + o, sizeof buf - o, "%s%d", i ? "," : "", (int)v);
		}
	}
	elog("webos: event %s array_bytes=%zu values=%s\n", webos_ev_name[idx], a ? a->size : 0, buf);
}

#define WE_EMPTY(n) static void webos_e_##n(void *d, struct wl_proxy *p) { (void)d; (void)p; webos_on_empty(n); }
#define WE_U(n) static void webos_u_##n(void *d, struct wl_proxy *p, uint32_t v) { (void)d; (void)p; webos_on_u(n, v); }
#define WE_II(n) static void webos_i_##n(void *d, struct wl_proxy *p, int32_t x, int32_t y) { (void)d; (void)p; webos_on_ii(n, x, y); }
#define WE_A(n) static void webos_a_##n(void *d, struct wl_proxy *p, struct webos_arr *a) { (void)d; (void)p; webos_on_array(n, a); }
#define WE_ALL(n) WE_EMPTY(n) WE_U(n) WE_II(n) WE_A(n)
WE_ALL(0) WE_ALL(1) WE_ALL(2) WE_ALL(3) WE_ALL(4) WE_ALL(5) WE_ALL(6) WE_ALL(7)
WE_ALL(8) WE_ALL(9) WE_ALL(10) WE_ALL(11) WE_ALL(12) WE_ALL(13) WE_ALL(14) WE_ALL(15)
#undef WE_EMPTY
#undef WE_U
#undef WE_II
#undef WE_A
#undef WE_ALL

static void *webos_e_slot[16] = {
	(void *)webos_e_0,(void *)webos_e_1,(void *)webos_e_2,(void *)webos_e_3,
	(void *)webos_e_4,(void *)webos_e_5,(void *)webos_e_6,(void *)webos_e_7,
	(void *)webos_e_8,(void *)webos_e_9,(void *)webos_e_10,(void *)webos_e_11,
	(void *)webos_e_12,(void *)webos_e_13,(void *)webos_e_14,(void *)webos_e_15
};
static void *webos_u_slot[16] = {
	(void *)webos_u_0,(void *)webos_u_1,(void *)webos_u_2,(void *)webos_u_3,
	(void *)webos_u_4,(void *)webos_u_5,(void *)webos_u_6,(void *)webos_u_7,
	(void *)webos_u_8,(void *)webos_u_9,(void *)webos_u_10,(void *)webos_u_11,
	(void *)webos_u_12,(void *)webos_u_13,(void *)webos_u_14,(void *)webos_u_15
};
static void *webos_i_slot[16] = {
	(void *)webos_i_0,(void *)webos_i_1,(void *)webos_i_2,(void *)webos_i_3,
	(void *)webos_i_4,(void *)webos_i_5,(void *)webos_i_6,(void *)webos_i_7,
	(void *)webos_i_8,(void *)webos_i_9,(void *)webos_i_10,(void *)webos_i_11,
	(void *)webos_i_12,(void *)webos_i_13,(void *)webos_i_14,(void *)webos_i_15
};
static void *webos_a_slot[16] = {
	(void *)webos_a_0,(void *)webos_a_1,(void *)webos_a_2,(void *)webos_a_3,
	(void *)webos_a_4,(void *)webos_a_5,(void *)webos_a_6,(void *)webos_a_7,
	(void *)webos_a_8,(void *)webos_a_9,(void *)webos_a_10,(void *)webos_a_11,
	(void *)webos_a_12,(void *)webos_a_13,(void *)webos_a_14,(void *)webos_a_15
};
static void *webos_listener[16];

static int install_webos_listener(struct wl_proxy *proxy)
{
	int i, n;
	const struct wl_interface *iface = S.webos_surf_iface;
	n = iface->event_count;
	if (n < 0 || n > 16 || (n > 0 && !iface->events)) {
		elog("warn: webos event_count=%d; listener not installed\n", n);
		return 0;
	}
	for (i = 0; i < n; i++) {
		const struct wl_message *e = &iface->events[i];
		const char *sig = (e && e->signature) ? e->signature : "";
		snprintf(webos_ev_name[i], sizeof webos_ev_name[i], "%s", (e && e->name) ? e->name : "?");
		snprintf(webos_ev_sig[i], sizeof webos_ev_sig[i], "%s", sig);
		if (!strcmp(sig, "u")) webos_listener[i] = webos_u_slot[i];
		else if (!strcmp(sig, "ii")) webos_listener[i] = webos_i_slot[i];
		else if (!strcmp(sig, "a")) webos_listener[i] = webos_a_slot[i];
		else webos_listener[i] = webos_e_slot[i];
		elog("info: webos event[%d] %s signature=%s\n", i, webos_ev_name[i], webos_ev_sig[i]);
	}
	if (n > 0 && LISTEN(proxy, webos_listener, NULL) != 0) return -1;
	return 0;
}

/* ---- EGL via dlopen; shm remains if any step fails -------------------- */
static const float k_tri[24][6] = {
	{ 0.45000f, 0.00000f, -0.22500f, 0.38971f, -0.22500f, -0.38971f },
	{ 0.43467f, 0.11647f, -0.31820f, 0.31820f, -0.11647f, -0.43467f },
	{ 0.38971f, 0.22500f, -0.38971f, 0.22500f, 0.00000f, -0.45000f },
	{ 0.31820f, 0.31820f, -0.43467f, 0.11647f, 0.11647f, -0.43467f },
	{ 0.22500f, 0.38971f, -0.45000f, 0.00000f, 0.22500f, -0.38971f },
	{ 0.11647f, 0.43467f, -0.43467f, -0.11647f, 0.31820f, -0.31820f },
	{ 0.00000f, 0.45000f, -0.38971f, -0.22500f, 0.38971f, -0.22500f },
	{ -0.11647f, 0.43467f, -0.31820f, -0.31820f, 0.43467f, -0.11647f },
	{ -0.22500f, 0.38971f, -0.22500f, -0.38971f, 0.45000f, 0.00000f },
	{ -0.31820f, 0.31820f, -0.11647f, -0.43467f, 0.43467f, 0.11647f },
	{ -0.38971f, 0.22500f, 0.00000f, -0.45000f, 0.38971f, 0.22500f },
	{ -0.43467f, 0.11647f, 0.11647f, -0.43467f, 0.31820f, 0.31820f },
	{ -0.45000f, 0.00000f, 0.22500f, -0.38971f, 0.22500f, 0.38971f },
	{ -0.43467f, -0.11647f, 0.31820f, -0.31820f, 0.11647f, 0.43467f },
	{ -0.38971f, -0.22500f, 0.38971f, -0.22500f, 0.00000f, 0.45000f },
	{ -0.31820f, -0.31820f, 0.43467f, -0.11647f, -0.11647f, 0.43467f },
	{ -0.22500f, -0.38971f, 0.45000f, 0.00000f, -0.22500f, 0.38971f },
	{ -0.11647f, -0.43467f, 0.43467f, 0.11647f, -0.31820f, 0.31820f },
	{ 0.00000f, -0.45000f, 0.38971f, 0.22500f, -0.38971f, 0.22500f },
	{ 0.11647f, -0.43467f, 0.31820f, 0.31820f, -0.43467f, 0.11647f },
	{ 0.22500f, -0.38971f, 0.22500f, 0.38971f, -0.45000f, 0.00000f },
	{ 0.31820f, -0.31820f, 0.11647f, 0.43467f, -0.43467f, -0.11647f },
	{ 0.38971f, -0.22500f, 0.00000f, 0.45000f, -0.38971f, -0.22500f },
	{ 0.43467f, -0.11647f, -0.11647f, 0.43467f, -0.31820f, -0.31820f }
};

struct egl_api {
	void *h_wlegl, *h_egl, *h_gles;
	void *window, *dpy, *cfg, *surf, *ctx;
	int inited, prog, pos_attr;
	unsigned vbo;
	void *(*window_create)(struct wl_proxy *, int, int);
	void (*window_destroy)(void *);
	void (*window_resize)(void *, int, int, int, int);
	void *(*GetDisplay)(void *);
	unsigned (*Initialize)(void *, int *, int *);
	unsigned (*ChooseConfig)(void *, const int *, void **, int, int *);
	void *(*CreateWindowSurface)(void *, void *, void *, const int *);
	void *(*CreateContext)(void *, void *, void *, const int *);
	unsigned (*MakeCurrent)(void *, void *, void *, void *);
	unsigned (*SwapBuffers)(void *, void *);
	unsigned (*BindAPI)(unsigned);
	int (*GetError)(void);
	unsigned (*Terminate)(void *);
	unsigned (*DestroySurface)(void *, void *);
	unsigned (*DestroyContext)(void *, void *);
	void (*ClearColor)(float, float, float, float);
	void (*Clear)(unsigned);
	void (*Viewport)(int, int, int, int);
	unsigned (*CreateShader)(unsigned);
	void (*ShaderSource)(unsigned, int, const char *const *, const int *);
	void (*CompileShader)(unsigned);
	void (*GetShaderiv)(unsigned, unsigned, int *);
	void (*GetShaderInfoLog)(unsigned, int, int *, char *);
	void (*DeleteShader)(unsigned);
	unsigned (*CreateProgram)(void);
	void (*AttachShader)(unsigned, unsigned);
	void (*LinkProgram)(unsigned);
	void (*GetProgramiv)(unsigned, unsigned, int *);
	void (*UseProgram)(unsigned);
	void (*GenBuffers)(int, unsigned *);
	void (*BindBuffer)(unsigned, unsigned);
	void (*BufferData)(unsigned, ptrdiff_t, const void *, unsigned);
	int (*GetAttribLocation)(unsigned, const char *);
	void (*EnableVertexAttribArray)(unsigned);
	void (*VertexAttribPointer)(unsigned, int, unsigned, unsigned char, int, const void *);
	void (*DrawArrays)(unsigned, int, int);
};
static struct egl_api E;

static void egl_shutdown(void)
{
	if (E.MakeCurrent && E.dpy) E.MakeCurrent(E.dpy, NULL, NULL, NULL);
	if (E.DestroySurface && E.dpy && E.surf) E.DestroySurface(E.dpy, E.surf);
	if (E.DestroyContext && E.dpy && E.ctx) E.DestroyContext(E.dpy, E.ctx);
	if (E.window_destroy && E.window) E.window_destroy(E.window);
	if (E.Terminate && E.dpy && E.inited) E.Terminate(E.dpy);
	if (E.h_gles) dlclose(E.h_gles);
	if (E.h_egl) dlclose(E.h_egl);
	if (E.h_wlegl) dlclose(E.h_wlegl);
	memset(&E, 0, sizeof E);
	S.egl_on = 0;
}

static int egl_sym(void *h, const char *lib, void **dst, const char *name)
{
	*dst = dlsym(h, name);
	if (!*dst) {
		elog("egl: missing symbol %s in %s\n", name, lib);
		return -1;
	}
	return 0;
}

static int egl_float_abi_ok(void *handle, const char *soname)
{
#if defined(__arm__) && !defined(__ARM_PCS_VFP)
	struct link_map *map = NULL;
	unsigned char hdr[64];
	int fd, n;
	uint32_t flags;
	if (dlinfo(handle, 2 /* RTLD_DI_LINKMAP */, &map) != 0 || !map || !map->l_name || !map->l_name[0]) {
		elog("egl: %s: cannot resolve loaded path; not calling\n", soname);
		return -1;
	}
	fd = open(map->l_name, O_RDONLY | O_CLOEXEC);
	if (fd < 0) {
		elog("egl: %s: open %s failed: %s; not calling\n", soname, map->l_name, strerror(errno));
		return -1;
	}
	n = read(fd, hdr, sizeof hdr);
	close(fd);
	if (n < 52 || hdr[0] != 0x7f || hdr[1] != 'E' || hdr[2] != 'L' || hdr[3] != 'F' || hdr[4] != 1) {
		elog("egl: %s is not ELF32; soft-float client will not call it\n", soname);
		return -1;
	}
	flags = (uint32_t)hdr[36] | ((uint32_t)hdr[37] << 8) | ((uint32_t)hdr[38] << 16) | ((uint32_t)hdr[39] << 24);
	elog("egl: %s e_flags=0x%08x\n", soname, flags);
	if (flags & 0x400u) {
		elog("egl: %s has the hard-float ABI flag; not calling\n", soname);
		return -1;
	}
	if ((flags & 0x200u) == 0) {
		elog("egl: %s has no soft-float ABI flag; not calling\n", soname);
		return -1;
	}
	return 0;
#else
	(void)handle;
	elog("egl: %s float-ABI check skipped (this binary is not ARM soft-float)\n", soname);
	return 0;
#endif
}

static int egl_shader(unsigned kind, const char *src)
{
	unsigned sh;
	int ok = 0;
	const char *p = src;
	sh = E.CreateShader(kind);
	E.ShaderSource(sh, 1, &p, NULL);
	E.CompileShader(sh);
	E.GetShaderiv(sh, 0x8B81 /* GL_COMPILE_STATUS */, &ok);
	if (!ok) {
		char log[256];
		log[0] = 0;
		E.GetShaderInfoLog(sh, (int)sizeof log, NULL, log);
		elog("egl: shader compile failed: %s\n", log);
		E.DeleteShader(sh);
		return 0;
	}
	E.AttachShader(E.prog, sh);
	E.DeleteShader(sh);
	return 1;
}

static int egl_init(int w, int h)
{
	static const int cfg_attr[] = {
		0x3033, 0x0004, 0x3040, 0x0004, 0x3024, 8, 0x3023, 8, 0x3022, 8, 0x3021, 8, 0x3038
	};
	static const int ctx_attr[] = { 0x3098, 2, 0x3038 };
	static const char *vs = "attribute vec2 pos;\nvoid main(){ gl_Position=vec4(pos,0.0,1.0); }\n";
	static const char *fs = "precision mediump float;\nvoid main(){ gl_FragColor=vec4(1.0,1.0,1.0,1.0); }\n";
	int ncfg = 0, maj = 0, min = 0, linked = 0;
	void *cfg = NULL;
#define NEED(h, lib, field, name) do { if (egl_sym((h), (lib), (void **)&E.field, (name))) return -1; } while (0)
	memset(&E, 0, sizeof E);
	E.h_wlegl = dlopen_extra("libwayland-egl.so.1");
	if (!E.h_wlegl) return -1;
	if (egl_float_abi_ok(E.h_wlegl, "libwayland-egl.so.1")) return -1;
	NEED(E.h_wlegl, "libwayland-egl.so.1", window_create, "wl_egl_window_create");
	NEED(E.h_wlegl, "libwayland-egl.so.1", window_destroy, "wl_egl_window_destroy");
	NEED(E.h_wlegl, "libwayland-egl.so.1", window_resize, "wl_egl_window_resize");
	E.h_egl = dlopen_extra("libEGL.so.1");
	if (!E.h_egl) return -1;
	if (egl_float_abi_ok(E.h_egl, "libEGL.so.1")) return -1;
	NEED(E.h_egl, "libEGL.so.1", GetDisplay, "eglGetDisplay");
	NEED(E.h_egl, "libEGL.so.1", Initialize, "eglInitialize");
	NEED(E.h_egl, "libEGL.so.1", ChooseConfig, "eglChooseConfig");
	NEED(E.h_egl, "libEGL.so.1", CreateWindowSurface, "eglCreateWindowSurface");
	NEED(E.h_egl, "libEGL.so.1", CreateContext, "eglCreateContext");
	NEED(E.h_egl, "libEGL.so.1", MakeCurrent, "eglMakeCurrent");
	NEED(E.h_egl, "libEGL.so.1", SwapBuffers, "eglSwapBuffers");
	NEED(E.h_egl, "libEGL.so.1", BindAPI, "eglBindAPI");
	NEED(E.h_egl, "libEGL.so.1", GetError, "eglGetError");
	NEED(E.h_egl, "libEGL.so.1", Terminate, "eglTerminate");
	NEED(E.h_egl, "libEGL.so.1", DestroySurface, "eglDestroySurface");
	NEED(E.h_egl, "libEGL.so.1", DestroyContext, "eglDestroyContext");
	E.h_gles = dlopen_extra("libGLESv2.so.2");
	if (!E.h_gles) return -1;
	if (egl_float_abi_ok(E.h_gles, "libGLESv2.so.2")) return -1;
	NEED(E.h_gles, "libGLESv2.so.2", ClearColor, "glClearColor");
	NEED(E.h_gles, "libGLESv2.so.2", Clear, "glClear");
	NEED(E.h_gles, "libGLESv2.so.2", Viewport, "glViewport");
	NEED(E.h_gles, "libGLESv2.so.2", CreateShader, "glCreateShader");
	NEED(E.h_gles, "libGLESv2.so.2", ShaderSource, "glShaderSource");
	NEED(E.h_gles, "libGLESv2.so.2", CompileShader, "glCompileShader");
	NEED(E.h_gles, "libGLESv2.so.2", GetShaderiv, "glGetShaderiv");
	NEED(E.h_gles, "libGLESv2.so.2", GetShaderInfoLog, "glGetShaderInfoLog");
	NEED(E.h_gles, "libGLESv2.so.2", DeleteShader, "glDeleteShader");
	NEED(E.h_gles, "libGLESv2.so.2", CreateProgram, "glCreateProgram");
	NEED(E.h_gles, "libGLESv2.so.2", AttachShader, "glAttachShader");
	NEED(E.h_gles, "libGLESv2.so.2", LinkProgram, "glLinkProgram");
	NEED(E.h_gles, "libGLESv2.so.2", GetProgramiv, "glGetProgramiv");
	NEED(E.h_gles, "libGLESv2.so.2", UseProgram, "glUseProgram");
	NEED(E.h_gles, "libGLESv2.so.2", GenBuffers, "glGenBuffers");
	NEED(E.h_gles, "libGLESv2.so.2", BindBuffer, "glBindBuffer");
	NEED(E.h_gles, "libGLESv2.so.2", BufferData, "glBufferData");
	NEED(E.h_gles, "libGLESv2.so.2", GetAttribLocation, "glGetAttribLocation");
	NEED(E.h_gles, "libGLESv2.so.2", EnableVertexAttribArray, "glEnableVertexAttribArray");
	NEED(E.h_gles, "libGLESv2.so.2", VertexAttribPointer, "glVertexAttribPointer");
	NEED(E.h_gles, "libGLESv2.so.2", DrawArrays, "glDrawArrays");
#undef NEED
	E.dpy = E.GetDisplay(S.display);
	if (!E.dpy || !E.Initialize(E.dpy, &maj, &min)) {
		elog("egl: eglGetDisplay/eglInitialize failed (0x%x)\n", E.GetError());
		return -1;
	}
	E.inited = 1;
	if (!E.BindAPI(0x30A0) || !E.ChooseConfig(E.dpy, cfg_attr, &cfg, 1, &ncfg) || ncfg < 1) {
		elog("egl: no GLES2 window config (0x%x)\n", E.GetError());
		return -1;
	}
	E.cfg = cfg;
	E.window = E.window_create(S.surface, w, h);
	if (!E.window) { elog("egl: wl_egl_window_create failed\n"); return -1; }
	E.surf = E.CreateWindowSurface(E.dpy, E.cfg, E.window, NULL);
	E.ctx = E.CreateContext(E.dpy, E.cfg, NULL, ctx_attr);
	if (!E.surf || !E.ctx || !E.MakeCurrent(E.dpy, E.surf, E.surf, E.ctx)) {
		elog("egl: context/surface failed (0x%x)\n", E.GetError());
		return -1;
	}
	E.prog = (int)E.CreateProgram();
	if (!egl_shader(0x8B31, vs) || !egl_shader(0x8B30, fs)) return -1;
	E.LinkProgram((unsigned)E.prog);
	E.GetProgramiv((unsigned)E.prog, 0x8B82, &linked);
	if (!linked) { elog("egl: program link failed\n"); return -1; }
	E.pos_attr = E.GetAttribLocation((unsigned)E.prog, "pos");
	E.GenBuffers(1, &E.vbo);
	E.Viewport(0, 0, w, h);
	S.cur_w = w; S.cur_h = h;
	elog("info: egl GLES2 ready %dx%d (clear + rotating triangle)\n", w, h);
	return 0;
}

static void egl_draw(void)
{
	float v[6];
	float r, g, b;
	int i, step;
	if (!S.egl_on) return;
	r = (float)((S.bg >> 16) & 255) / 255.0f;
	g = (float)((S.bg >> 8) & 255) / 255.0f;
	b = (float)(S.bg & 255) / 255.0f;
	E.ClearColor(r, g, b, 1.0f);
	E.Clear(0x00004000);
	step = S.frame % 24;
	S.frame++;
	for (i = 0; i < 6; i++) v[i] = k_tri[step][i] + ((i & 1) ? S.nudge_y : S.nudge_x);
	E.UseProgram((unsigned)E.prog);
	E.BindBuffer(0x8892, E.vbo);
	E.BufferData(0x8892, (ptrdiff_t)sizeof v, v, 0x88E4);
	if (E.pos_attr >= 0) {
		E.EnableVertexAttribArray((unsigned)E.pos_attr);
		E.VertexAttribPointer((unsigned)E.pos_attr, 2, 0x1406, 0, 0, (const void *)0);
	}
	E.DrawArrays(0x0004, 0, 3);
	if (!E.SwapBuffers(E.dpy, E.surf)) {
		elog("egl: eglSwapBuffers failed (0x%x); dropping EGL and using shm\n", E.GetError());
		egl_shutdown();
		if (!S.buf.buffer) {
			int brc = create_buf(&S.buf, S.cur_w > 0 ? S.cur_w : S.o->width, S.cur_h > 0 ? S.cur_h : S.o->height);
			if (brc != 0) S.fatal = brc;
			else present();
		}
	} else {
		arm_countdown("egl-swap");
		if (!S.egl_frame_noted) {
			S.egl_frame_noted = 1;
			elog("egl: wl_surface.frame callbacks are not instrumented on this path\n");
		}
	}
}

static const char *reason_text(void)
{
	if (S.reason == REASON_BACK) return "back-key";
	if (S.reason == REASON_ESC) return "escape";
	if (S.reason == REASON_EXITKEY) return "exit-key";
	if (S.reason == REASON_MENU_EXIT) return "menu-exit";
	if (S.reason == REASON_WEBOS_CLOSE) return "webos-close";
	if (S.reason == REASON_KB_LEAVE) return "keyboard-leave";
	if (S.reason == REASON_LUNA_CLOSE) return "luna-close";
	if (S.reason == REASON_LUNA_REJECT) return "luna-reject";
	if (S.reason == REASON_SIGNAL || g_stop) return "signal";
	return "deadline";
}

static void log_summary(void)
{
	elog("summary: commits=%d frame_done=%d frame_pending=%d releases=%d deferred_redraws=%d redraws_queued=%d focus_enter=%d focus_leave=%d model_repeats_suppressed=%d luna_replies=%d luna_polls=%d persist_restore=%d persist_alive=%d\n",
	     S.n_commits, S.n_frame_done, S.frame_cb ? 1 : 0, S.n_releases, S.n_deferred,
	     S.n_redraws, S.n_focus_enter, S.n_focus_leave, S.model_suppressed,
	     S.luna_replies, S.luna_polls, S.n_restore, S.n_persist_alive);
	if (S.o && S.o->photo_frame)
		elog("photo-frame: summary mode=%s type=%s buf=%dx%d kb_enter=%d kb_leave=%d ptr_enter=%d ptr_leave=%d last_key=%u name=%s\n",
		     photo_frame_mode_name(S.o->photo_frame),
		     photo_frame_window_type(S.o->photo_frame),
		     S.buf.w, S.buf.h, S.n_focus_enter, S.n_focus_leave,
		     S.n_ptr_enter, S.n_ptr_leave,
		     S.last_key, S.last_key_name[0] ? S.last_key_name : "-");
}

/* -1 = keep going. Otherwise the process should return this code.
 * Used when a luna reply arrives before a surface exists. */
static int finish_luna_stop(void)
{
	int code;
	if (!S.fatal && !S.quit) return -1;
	code = S.fatal ? S.fatal : EX_OK;
	elog("info: exiting (%s)\n", reason_text());
	log_summary();
	cleanup();
	return code;
}

static void cleanup(void)
{
	int i;
	luna_shutdown();
	egl_shutdown();
	if (S.frame_cb && W.proxy_destroy) {
		W.proxy_destroy(S.frame_cb);
		S.frame_cb = NULL;
		elog("frame: pending callback destroyed during cleanup\n");
	}
	destroy_spares();
	if (S.buf.buffer || S.buf.data) destroy_buf(&S.buf);
	if (S.shell_surface) W.proxy_destroy(S.shell_surface);
	if (S.webos_shell_surface && W.proxy_destroy) W.proxy_destroy(S.webos_shell_surface);
	for (i = 0; i < S.nseats; i++) {
		if (S.seats[i].keyboard) W.proxy_destroy(S.seats[i].keyboard);
		if (S.seats[i].pointer) W.proxy_destroy(S.seats[i].pointer);
		if (S.seats[i].seat) W.proxy_destroy(S.seats[i].seat);
	}
	if (S.surface && W.proxy_marshal) {
		W.proxy_marshal(S.surface, SURFACE_DESTROY);
		W.proxy_destroy(S.surface);
	}
	if (S.webos_shell && W.proxy_destroy) W.proxy_destroy(S.webos_shell);
	if (S.shell) W.proxy_destroy(S.shell);
	if (S.output && W.proxy_destroy) W.proxy_destroy(S.output);
	if (S.shm) W.proxy_destroy(S.shm);
	if (S.compositor) W.proxy_destroy(S.compositor);
	if (S.registry) W.proxy_destroy(S.registry);
	if (S.display && W.display_flush) { W.display_flush(S.display); W.display_disconnect(S.display); }
	S.display = NULL;
	if (S.webos_dl) { dlclose(S.webos_dl); S.webos_dl = NULL; }
}

/* controlled failure helpers: report, release everything, return exit code */
static int fail_alloc(const char *what)
{
	elog("error: %s proxy allocation failed; failing closed\n", what);
	cleanup();
	return EX_ALLOC;
}

static int fail_listener(const char *what)
{
	elog("error: %s listener install failed; failing closed\n", what);
	cleanup();
	return EX_PROTO;
}

static int bind_seats(void)
{
	int i;
	for (i = 0; i < S.nseats; i++) {
		struct seat_slot *s = &S.seats[i];
		uint32_t bv = s->version ? s->version : 1;
		if (bv > 3) bv = 3;
		s->seat = new_obj(S.registry, W.i_seat);
		if (!s->seat) return fail_alloc("wl_seat");
		if (LISTEN(s->seat, seat_listener, s) != 0) return fail_listener("wl_seat");
		W.proxy_marshal(S.registry, REGISTRY_BIND, s->global_name, W.i_seat->name, bv, s->seat);
		elog("info: bind wl_seat index=%d global=%u advertised=%u bind=%u\n",
		        s->index, s->global_name, s->version, bv);
	}
	return 0;
}

int main(int argc, char **argv)
{
	struct opts o;
	struct sigaction sa;
	int rc, i;
	char **opt_argv = argv;
	int opt_argc = argc;
	const char *launch_json = NULL;

	g_t0 = now_ms();
	setvbuf(stdout, NULL, _IOLBF, 0);
	setvbuf(stderr, NULL, _IOLBF, 0);
	opt_argc = strip_sam_json_argv(argc, argv, &opt_argv, &launch_json);
	rc = parse_opts(opt_argc, opt_argv, &o, launch_json != NULL);
	if (rc > 0) return EX_OK;
	if (rc < 0) return EX_USAGE;
	if (launch_json) apply_sam_launch(&o, launch_json);
	if (o.parse_only) { print_config(&o); return EX_OK; }
	if (o.sam_launch) {
		if (open_wh6_log() != 0)
			elog("warn: could not open /tmp/wh6.log; continuing on current stdout\n");
		elog("----- wayland-hello sam-launch -----\n");
		elog("sam: lifecycle2=%d app_id=%s window_type=%s duration_s=%d webos_shell=%d luna_register=%d photo_frame=%s\n",
		     o.sam_lifecycle2, o.app_id, o.window_type ? o.window_type : (o.photo_frame ? photo_frame_window_type(o.photo_frame) : "-"),
		     o.duration_s, o.webos_shell, o.luna_register, photo_frame_mode_name(o.photo_frame));
		if (launch_json) elog("sam: argv1=%s\n", launch_json);
	}
	S.o = &o;
	S.bg = o.color;
	S.sq = SQ_SIZE;
	S.sq_x = 100;
	S.sq_y = 100;
	if (o.menu) menu_init(&S.menu);
	S.last_key_name[0] = '-';
	S.last_key_name[1] = 0;

	/* 1. Hard exit armed BEFORE anything touches the compositor. */
	memset(&sa, 0, sizeof sa);
	sa.sa_handler = on_alarm;
	sigemptyset(&sa.sa_mask);
	sigaction(SIGALRM, &sa, NULL);
	sa.sa_handler = on_term;
	sigaction(SIGINT, &sa, NULL);
	sigaction(SIGTERM, &sa, NULL);
	signal(SIGPIPE, SIG_IGN);
	alarm((unsigned)(o.duration_s + GRACE_S));
	{
		int64_t t = now_ms();
		g_alarm_at = t + (int64_t)(o.duration_s + GRACE_S) * 1000;
		g_deadline = t + (int64_t)o.duration_s * 1000;
	}

	if (load_wayland() < 0) return EX_LIB;
	if (o.input && (!W.i_seat || !W.i_keyboard || !W.i_pointer)) {
		elog("error: libwayland-client is missing wl_seat, wl_keyboard or wl_pointer\n");
		return EX_LIB;
	}
	if (o.luna_register) {
		if (luna_start(o.app_id) < 0) return EX_NOLUNA;
		/* A reply can arrive on the first non-blocking poll, before connect. */
		{
			int stop = finish_luna_stop();
			if (stop >= 0) return stop;
		}
	}

	/* libwayland 1.x only resolves a relative name against XDG_RUNTIME_DIR. */
	if (setenv("XDG_RUNTIME_DIR", o.runtime_dir, 1) < 0) return EX_CONNECT;
	elog("info: wayland-hello %s connecting to %s/%s (deadline %ds, hard exit %ds)\n",
	        HELLO_VERSION, o.runtime_dir, o.display_name, o.duration_s, o.duration_s + GRACE_S);
	/* NOTE: wl_display_connect() on a unix socket is a local connect(); a
	 * listening-but-stalled peer cannot block it beyond the SIGALRM bound. */
	S.display = W.display_connect(o.display_name);
	if (!S.display) { elog("error: wl_display_connect failed: %s\n", strerror(errno)); return EX_CONNECT; }

	S.registry = new_obj((struct wl_proxy *)S.display, W.i_registry);
	if (!S.registry) return fail_alloc("wl_registry");
	if (LISTEN(S.registry, registry_listener, NULL) != 0) return fail_listener("wl_registry");
	W.proxy_marshal((struct wl_proxy *)S.display, DISPLAY_GET_REGISTRY, S.registry);
	if (roundtrip_bounded() < 0) {
		report_display_error();
		{
			int stop = finish_luna_stop();
			if (stop >= 0) return stop;
		}
		cleanup();
		return EX_PROTO;
	}
	{
		int stop = finish_luna_stop();
		if (stop >= 0) return stop;
	}

	olog("globals: %d%s\n", S.nglobals, S.globals_truncated ? " (truncated)" : "");
	for (i = 0; i < S.nglobals; i++)
		olog("global name=%u interface=%s version=%u\n",
		     S.globals[i].name, S.globals[i].iface, S.globals[i].version);

	if (o.dry_run) { olog("dry-run: no surfaces created\n"); cleanup(); return EX_OK; }

	if (o.input && S.nseats == 0) {
		elog("error: --input requires wl_seat; none advertised; failing closed\n");
		cleanup(); return EX_NOSEAT;
	}
	if (o.webos_shell) {
		if (!S.webos_name) {
			elog("error: --webos-shell requested but wl_webos_shell was not advertised; failing closed\n");
			cleanup(); return EX_NOWEBOS;
		}
		if (resolve_webos() < 0) { cleanup(); return EX_NOWEBOS; }
	} else if (!S.shell_name) {
		elog("error: wl_shell not advertised; failing closed (no xdg-shell, no DRM fallback)\n");
		cleanup(); return EX_NOSHELL;
	}
	if (!S.compositor_name || !S.shm_name) {
		elog("error: wl_compositor/wl_shm missing; failing closed\n");
		cleanup(); return EX_PROTO;
	}
	if (o.input) {
		elog("info: input via wl_seat only (no evdev device open)\n");
		olog("keycode-log assumption=wl_keyboard_key_is_evdev back=%u esc=%u exit=%u ok=%u enter=%u\n",
		     (unsigned)KEY_BACK_EVDEV, (unsigned)KEY_ESC_EVDEV, (unsigned)KEY_EXIT_EVDEV,
		     (unsigned)KEY_OK_EVDEV, (unsigned)KEY_ENTER_EVDEV);
	}

	/* Bind compositor/shm at version 1. Seat bind is capped at version 3 so
	 * repeat_info (keyboard since 4) is not delivered. webOS opcodes come
	 * only from the runtime interface, resolved above. */
	S.compositor = new_obj(S.registry, W.i_compositor);
	if (!S.compositor) return fail_alloc("wl_compositor");
	W.proxy_marshal(S.registry, REGISTRY_BIND, S.compositor_name, W.i_compositor->name, 1u, S.compositor);

	S.shm = new_obj(S.registry, W.i_shm);
	if (!S.shm) return fail_alloc("wl_shm");
	if (LISTEN(S.shm, shm_listener, NULL) != 0) return fail_listener("wl_shm");
	W.proxy_marshal(S.registry, REGISTRY_BIND, S.shm_name, W.i_shm->name, 1u, S.shm);

	if (o.photo_frame) {
		if (S.output_name && W.i_output) {
			S.output = new_obj(S.registry, W.i_output);
			if (!S.output) return fail_alloc("wl_output");
			if (LISTEN(S.output, output_listener, NULL) != 0) return fail_listener("wl_output");
			W.proxy_marshal(S.registry, REGISTRY_BIND, S.output_name, W.i_output->name, 1u, S.output);
			elog("info: bind wl_output global=%u version=1\n", S.output_name);
		} else {
			elog("photo-frame: no wl_output advertised; using fallback size\n");
		}
	}

	if (!o.webos_shell) {
		S.shell = new_obj(S.registry, W.i_shell);
		if (!S.shell) return fail_alloc("wl_shell");
		W.proxy_marshal(S.registry, REGISTRY_BIND, S.shell_name, W.i_shell->name, 1u, S.shell);
	} else {
		uint32_t bv = S.webos_advertised;
		if (bv > (uint32_t)S.webos_shell_iface->version) bv = (uint32_t)S.webos_shell_iface->version;
		if (bv < 1) { elog("error: wl_webos_shell version 0; failing closed\n"); cleanup(); return EX_NOWEBOS; }
		S.webos_shell = new_obj(S.registry, S.webos_shell_iface);
		if (!S.webos_shell) return fail_alloc("wl_webos_shell");
		W.proxy_marshal(S.registry, REGISTRY_BIND, S.webos_name, S.webos_shell_iface->name, bv, S.webos_shell);
		elog("info: bind wl_webos_shell advertised=%u bind=%u\n", S.webos_advertised, bv);
	}
	if (o.input) {
		rc = bind_seats();
		if (rc != 0) return rc;
	}

	if (roundtrip_bounded() < 0) {
		report_display_error();
		{
			int stop = finish_luna_stop();
			if (stop >= 0) return stop;
		}
		cleanup();
		return EX_PROTO;
	}
	{
		int stop = finish_luna_stop();
		if (stop >= 0) return stop;
	}
	if (!S.have_xrgb)
		elog("warn: compositor did not announce XRGB8888 (mandatory format); continuing\n");

	if (o.photo_frame) {
		const char *src = NULL;
		int fw = o.size_cli ? o.width : 0;
		int fh = o.size_cli ? o.height : 0;
		int pw = 0, ph = 0;
		photo_frame_pick_size(S.output_w, S.output_h, 0, 0, fw, fh,
		                      o.max_w, o.max_h, &pw, &ph, &src);
		o.width = pw;
		o.height = ph;
		elog("photo-frame: pick %dx%d source=%s output=%dx%d max=%dx%d size_cli=%d\n",
		     pw, ph, src ? src : "-", S.output_w, S.output_h, o.max_w, o.max_h, o.size_cli);
	}

	S.surface = new_obj(S.compositor, W.i_surface);
	if (!S.surface) return fail_alloc("wl_surface");
	W.proxy_marshal(S.compositor, COMPOSITOR_CREATE_SURFACE, S.surface);

	if (o.webos_shell) {
		uint32_t st = o.no_fullscreen ? 0u : 3u;
		S.webos_shell_surface = new_obj(S.webos_shell, S.webos_surf_iface);
		if (!S.webos_shell_surface) return fail_alloc("wl_webos_shell_surface");
		if (install_webos_listener(S.webos_shell_surface) != 0) return fail_listener("wl_webos_shell_surface");
		W.proxy_marshal(S.webos_shell, (uint32_t)S.op_get_shell_surface, S.webos_shell_surface, S.surface);
		/* Properties before set_state, and both before the first commit.
		 * The 0.4 client sent set_state(fullscreen=3) first, while appId was
		 * still unset. OSE luna-surfacemanager applies appId, _WEBOS_WINDOW_TYPE
		 * and displayAffinity from set_property; overlay/popup models keep a
		 * surface only when displayAffinity equals the display id (OSE default
		 * is 0). Fullscreen remains OSE value 3, not switched to maximized 2:
		 * the XML gives both, and this TV has not shown which number it uses. */
		W.proxy_marshal(S.webos_shell_surface, (uint32_t)S.op_set_property, "appId", o.app_id);
		elog("webos: set_property opcode=%d name=appId value=%s\n", S.op_set_property, o.app_id);
		if (o.window_type) {
			W.proxy_marshal(S.webos_shell_surface, (uint32_t)S.op_set_property, "_WEBOS_WINDOW_TYPE", o.window_type);
			elog("webos: set_property opcode=%d name=_WEBOS_WINDOW_TYPE value=%s\n", S.op_set_property, o.window_type);
		}
		W.proxy_marshal(S.webos_shell_surface, (uint32_t)S.op_set_property, "displayAffinity", "0");
		elog("webos: set_property opcode=%d name=displayAffinity value=0\n", S.op_set_property);
		W.proxy_marshal(S.webos_shell_surface, (uint32_t)S.op_set_state, st);
		elog("webos: set_state opcode=%d value=%u (OSE default=0 minimized=1 maximized=2 fullscreen=3; fullscreen is an assumption, not verified TV semantics; properties were sent first, before this call and before the first commit)\n",
		        S.op_set_state, st);
		if (o.webos_key_mask) {
			/* OSE webos_key: default 0xFFFFFFF8 omits home|back|exit. OR back|exit.
			 * tests/run_tests.py checks these numbers against the vendored XML. */
			uint32_t mask = 0xFFFFFFF8u | 2u | 4u;
			W.proxy_marshal(S.webos_shell_surface, (uint32_t)S.op_set_key_mask, mask);
			elog("info: webos set_key_mask opcode=%d value=0x%x (opt-in; OSE back=2 exit=4 default=0xfffffff8)\n",
			        S.op_set_key_mask, mask);
		} else elog("info: webos set_key_mask not requested\n");
	} else {
		S.shell_surface = new_obj(S.shell, W.i_shell_surface);
		if (!S.shell_surface) return fail_alloc("wl_shell_surface");
		if (LISTEN(S.shell_surface, shell_surface_listener, NULL) != 0) return fail_listener("wl_shell_surface");
		W.proxy_marshal(S.shell, SHELL_GET_SHELL_SURFACE, S.shell_surface, S.surface);
		/* Plain wl_shell has no webOS property map. LSM registered that path as
		 * a CARD with an empty app_id. set_title and set_class both carry the
		 * app id so a later run can see whether LSM copies either one. */
		W.proxy_marshal(S.shell_surface, SHSURF_SET_TITLE, o.app_id);
		elog("shell: set_title opcode=%d value=%s\n", SHSURF_SET_TITLE, o.app_id);
		W.proxy_marshal(S.shell_surface, SHSURF_SET_CLASS, o.app_id);
		elog("shell: set_class opcode=%d value=%s\n", SHSURF_SET_CLASS, o.app_id);
		if (o.no_fullscreen) W.proxy_marshal(S.shell_surface, SHSURF_SET_TOPLEVEL);
		else W.proxy_marshal(S.shell_surface, SHSURF_SET_FULLSCREEN, 0u, 0u, (struct wl_proxy *)NULL);
	}

	if (o.egl) {
		if (egl_init(o.width, o.height) == 0) S.egl_on = 1;
		else {
			elog("info: egl unavailable; falling back to shm\n");
			egl_shutdown();
		}
	}
	if (!S.egl_on) {
		clamp_square(o.width, o.height);
		rc = create_buf(&S.buf, o.width, o.height);
		if (rc != 0) { cleanup(); return rc; }
		present();
		if (o.photo_frame)
			elog("info: photo-frame mode=%s type=%s buf=%dx%d output=%dx%d heartbeat_ms=%d safety=%ds spare cap %d\n",
			     photo_frame_mode_name(o.photo_frame),
			     photo_frame_window_type(o.photo_frame),
			     S.buf.w, S.buf.h, S.output_w, S.output_h,
			     o.heartbeat_ms, o.duration_s, DEMO_MAX_BUFS);
		else if (o.demo && o.webos_shell)
			elog("info: demo wl_webos_shell type=%s; running until BACK (%u) or EXIT (%u); safety cap %ds; spare cap %d\n",
			     o.window_type ? o.window_type : "-", (unsigned)KEY_BACK_EVDEV,
			     (unsigned)KEY_EXIT_EVDEV, o.duration_s, DEMO_MAX_BUFS);
		else if (o.demo)
			elog("info: demo plain wl_shell; running until BACK (%u) or EXIT (%u); safety cap %ds; spare cap %d\n",
			     (unsigned)KEY_BACK_EVDEV, (unsigned)KEY_EXIT_EVDEV, o.duration_s, DEMO_MAX_BUFS);
		else if (o.menu) {
			int i, tx, ty, tw, th;
			log_menu_keymap_once();
			elog("info: menu plain wl_shell; tiles Demo/About/Exit; safety cap %ds; spare cap %d\n",
			     o.duration_s, DEMO_MAX_BUFS);
			for (i = 0; i < MENU_TILE_COUNT; i++) {
				if (menu_tile_rect(S.buf.w, S.buf.h, i, &tx, &ty, &tw, &th) == 0)
					elog("menu: tile index=%d label=%s rect=%d,%d,%d,%d\n",
					     i, i == 0 ? "DEMO" : (i == 1 ? "ABOUT" : "EXIT"), tx, ty, tw, th);
			}
			elog("menu: screen=%s focus=%s\n", menu_screen_name(S.menu.screen), menu_focus_label(&S.menu));
		} else
			elog("info: surface committed %dx%d; running until deadline\n", S.buf.w, S.buf.h);
		if (S.need_restore) persist_restore_foreground("surface-ready");
	}

	rc = EX_OK;
	if (o.heartbeat_ms) S.heartbeat_next = elapsed_ms() + o.heartbeat_ms;
	S.persist_next = elapsed_ms() + 5000;
	while (!g_stop && !S.quit && !S.fatal) {
		int ms = remaining_ms();
		int slice = S.egl_on ? 16 : 100;
		int64_t now_hb;
		luna_check_ack(0);
		if (S.quit || S.fatal) break;
		if (ms == 0) break;
		now_hb = elapsed_ms();
		if (now_hb >= S.persist_next) {
			S.n_persist_alive++;
			S.persist_next = now_hb + 5000;
			elog("persist: alive t=%lld enter=%d leave=%d restores=%d luna_replies=%d\n",
			     (long long)now_hb, S.n_focus_enter, S.n_focus_leave, S.n_restore, S.luna_replies);
		}
		if (o.heartbeat_ms && !S.egl_on) {
			now_hb = elapsed_ms();
			if (now_hb >= S.heartbeat_next) {
				S.n_heartbeat++;
				S.heartbeat_next = now_hb + o.heartbeat_ms;
				if (o.photo_frame)
					elog("photo-frame: tick t=%lld s=%d mode=%s type=%s buf=%dx%d kb_enter=%d kb_leave=%d last_key=%u name=%s\n",
					     (long long)now_hb, (int)(now_hb / 1000),
					     photo_frame_mode_name(o.photo_frame),
					     photo_frame_window_type(o.photo_frame),
					     S.buf.w, S.buf.h, S.n_focus_enter, S.n_focus_leave,
					     S.last_key, S.last_key_name[0] ? S.last_key_name : "-");
				elog("heartbeat: tick n=%d\n", S.n_heartbeat);
				request_redraw();
				if (S.fatal) { rc = S.fatal; break; }
			}
		}
		if (pump_once(ms > slice ? slice : ms) < 0) {
			elog("error: connection lost\n"); report_display_error(); rc = EX_PROTO; break;
		}
		if (S.fatal) { rc = S.fatal; break; }
		if (S.resize_pending) {
			S.resize_pending = 0;
			if (S.egl_on && E.window_resize) {
				E.window_resize(E.window, S.want_w, S.want_h, 0, 0);
				E.Viewport(0, 0, S.want_w, S.want_h);
				S.cur_w = S.want_w; S.cur_h = S.want_h;
			} else if (!S.egl_on) {
				elog("resize: apply old_gen=%d old=%dx%d busy=%d new=%dx%d\n",
				     S.buf.gen, S.buf.w, S.buf.h, S.buf.busy, S.want_w, S.want_h);
				destroy_spares();
				destroy_buf(&S.buf);
				clamp_square(S.want_w, S.want_h);
				rc = create_buf(&S.buf, S.want_w, S.want_h);
				if (rc != 0) break;
				elog("resize: applied new_gen=%d %dx%d\n", S.buf.gen, S.buf.w, S.buf.h);
				present();
			}
		}
		if (S.egl_on) egl_draw();
	}
	if (S.reason == REASON_DEADLINE && !g_stop) luna_check_ack(1);
	if (S.fatal && rc == EX_OK) rc = S.fatal;
	elog("info: exiting (%s)\n", reason_text());
	log_summary();
	cleanup();
	return rc;
}

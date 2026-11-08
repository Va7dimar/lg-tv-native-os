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
 *  - Only wl_shell (legacy) is used for a surface. If wl_shell is absent the
 *    client fails closed. It never opens DRM/fbdev and never touches services.
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
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
#include <unistd.h>

#define HELLO_VERSION "0.1-prototype"

/* ---- limits ------------------------------------------------------------ */
#define DEFAULT_DURATION_S 10
#define MAX_DURATION_S     30
#define DEFAULT_W          640
#define DEFAULT_H          360
#define MAX_W              1920
#define MAX_H              1080
#define MAX_GLOBALS        128
#define GRACE_S            2   /* SIGALRM fires at duration + GRACE_S */
#define MAX_SHM_BYTES      ((size_t)MAX_W * (size_t)MAX_H * 4u)  /* 8 MiB hard cap */

/* exit codes */
#define EX_OK        0
#define EX_USAGE     2
#define EX_CONNECT   3
#define EX_PROTO     4
#define EX_NOSHELL   5
#define EX_LIB       6
#define EX_ALLOC     7
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
		*i_shm_pool, *i_buffer, *i_surface, *i_shell, *i_shell_surface;
} W;

/* ---- options ----------------------------------------------------------- */
struct opts {
	int dry_run;
	int parse_only;
	int duration_s;
	int width, height;          /* initial buffer */
	int max_w, max_h;           /* cap for configure-driven resize */
	int no_fullscreen;
	const char *runtime_dir;
	const char *display_name;
	uint32_t color;             /* 0xRRGGBB */
};

static void usage(FILE *f)
{
	fprintf(f,
"usage: wayland-hello [options]\n"
"  --dry-run            connect, print registry globals, exit (no surfaces)\n"
"  --duration N         total hard time limit in seconds (1..%d, default %d)\n"
"  --size WxH           initial buffer size (default %dx%d, max %dx%d)\n"
"  --max-size WxH       cap for compositor-requested sizes (default %dx%d)\n"
"  --color RRGGBB       base color (default 204080)\n"
"  --no-fullscreen      use set_toplevel instead of set_fullscreen\n"
"  --runtime-dir DIR    override XDG_RUNTIME_DIR (default env, else /tmp/xdg)\n"
"  --display NAME       override WAYLAND_DISPLAY (default env, else wayland-0)\n"
"  --parse-only         print parsed configuration and exit (no connect)\n"
"  --version, --help\n",
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

/* returns 0 ok, 1 exit-success (help/version), -1 usage error */
static int parse_opts(int argc, char **argv, struct opts *o)
{
	const char *e;
	int i;
	memset(o, 0, sizeof *o);
	o->duration_s = DEFAULT_DURATION_S;
	o->width = DEFAULT_W; o->height = DEFAULT_H;
	o->max_w = MAX_W; o->max_h = MAX_H;
	o->color = 0x204080;
	e = getenv("XDG_RUNTIME_DIR");
	o->runtime_dir = (e && *e) ? e : "/tmp/xdg";
	e = getenv("WAYLAND_DISPLAY");
	o->display_name = (e && *e) ? e : "wayland-0";

	for (i = 1; i < argc; i++) {
		const char *a = argv[i];
		const char *v = (i + 1 < argc) ? argv[i + 1] : NULL;
		if (!strcmp(a, "--dry-run")) o->dry_run = 1;
		else if (!strcmp(a, "--parse-only")) o->parse_only = 1;
		else if (!strcmp(a, "--no-fullscreen")) o->no_fullscreen = 1;
		else if (!strcmp(a, "--help") || !strcmp(a, "-h")) { usage(stdout); return 1; }
		else if (!strcmp(a, "--version")) { printf("wayland-hello %s\n", HELLO_VERSION); return 1; }
		else if (!strcmp(a, "--duration")) {
			if (parse_int(v, 1, MAX_DURATION_S, &o->duration_s)) {
				fprintf(stderr, "error: --duration must be 1..%d\n", MAX_DURATION_S); return -1;
			}
			i++;
		} else if (!strcmp(a, "--size")) {
			if (parse_size(v, MAX_W, MAX_H, &o->width, &o->height)) {
				fprintf(stderr, "error: --size must be WxH within %dx%d\n", MAX_W, MAX_H); return -1;
			}
			i++;
		} else if (!strcmp(a, "--max-size")) {
			if (parse_size(v, MAX_W, MAX_H, &o->max_w, &o->max_h)) {
				fprintf(stderr, "error: --max-size must be WxH within %dx%d\n", MAX_W, MAX_H); return -1;
			}
			i++;
		} else if (!strcmp(a, "--color")) {
			char *end; unsigned long c;
			if (!v || strlen(v) != 6) { fprintf(stderr, "error: --color RRGGBB\n"); return -1; }
			c = strtoul(v, &end, 16);
			if (*end) { fprintf(stderr, "error: --color RRGGBB\n"); return -1; }
			o->color = (uint32_t)c;
			i++;
		} else if (!strcmp(a, "--runtime-dir")) {
			if (!v || v[0] != '/' || strlen(v) > 200) {
				fprintf(stderr, "error: --runtime-dir must be an absolute path\n"); return -1;
			}
			o->runtime_dir = v; i++;
		} else if (!strcmp(a, "--display")) {
			if (!v || !*v || strchr(v, '/') || strlen(v) > 64) {
				fprintf(stderr, "error: --display must be a plain socket name\n"); return -1;
			}
			o->display_name = v; i++;
		} else {
			fprintf(stderr, "error: unknown option '%s'\n", a);
			usage(stderr);
			return -1;
		}
	}
	/* env-provided values get the same validation */
	if (o->runtime_dir[0] != '/' || strlen(o->runtime_dir) > 200) {
		fprintf(stderr, "error: XDG_RUNTIME_DIR must be an absolute path\n"); return -1;
	}
	if (strchr(o->display_name, '/') || strlen(o->display_name) > 64) {
		fprintf(stderr, "error: WAYLAND_DISPLAY must be a plain socket name\n"); return -1;
	}
	if (o->width > o->max_w) o->width = o->max_w;
	if (o->height > o->max_h) o->height = o->max_h;
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

static int64_t g_deadline;

static int remaining_ms(void)
{
	int64_t r = g_deadline - now_ms();
	if (r <= 0) return 0;
	return r > INT_MAX ? INT_MAX : (int)r;
}

/* ---- dynamic loading -------------------------------------------------- */
#define REQ(field, sym) do { *(void **)(&W.field) = dlsym(W.h, sym); \
	if (!W.field) { fprintf(stderr, "error: missing symbol %s\n", sym); return -1; } } while (0)
#define OPT(field, sym) do { *(void **)(&W.field) = dlsym(W.h, sym); } while (0)

static int load_wayland(void)
{
	static const char *names[] = { "libwayland-client.so.0", "libwayland-client.so", NULL };
	int i;
	for (i = 0; names[i] && !W.h; i++) W.h = dlopen(names[i], RTLD_NOW | RTLD_LOCAL);
	if (!W.h) { fprintf(stderr, "error: dlopen libwayland-client failed: %s\n", dlerror()); return -1; }
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
enum { SURFACE_DESTROY = 0, SURFACE_ATTACH = 1, SURFACE_DAMAGE = 2, SURFACE_COMMIT = 6 };
enum { SHELL_GET_SHELL_SURFACE = 0 };
enum { SHSURF_PONG = 0, SHSURF_SET_TOPLEVEL = 3, SHSURF_SET_FULLSCREEN = 5, SHSURF_SET_TITLE = 8 };
#define WL_SHM_FORMAT_XRGB8888 1

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
};

static struct {
	struct opts *o;
	struct wl_display *display;
	struct wl_proxy *registry;
	struct global globals[MAX_GLOBALS];
	int nglobals, globals_truncated;
	uint32_t compositor_name, shm_name, shell_name;
	struct wl_proxy *compositor, *shm, *shell, *surface, *shell_surface;
	int have_xrgb;
	int want_w, want_h;   /* from configure, clamped; 0 = none */
	int resize_pending;
	struct buf buf;
	int protocol_error;
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

/* buffer release */
static void buf_release(void *data, struct wl_proxy *b)
{ (void)b; ((struct buf *)data)->busy = 0; }
static void *buffer_listener[] = { (void *)buf_release };

/* shell surface */
static void ss_ping(void *data, struct wl_proxy *ss, uint32_t serial)
{ (void)data; W.proxy_marshal(ss, SHSURF_PONG, serial); }
static void ss_configure(void *data, struct wl_proxy *ss, uint32_t edges, int32_t w, int32_t h)
{
	(void)data; (void)ss; (void)edges;
	if (w <= 0 || h <= 0) return;           /* 0 = client decides */
	if (w > S.o->max_w) w = S.o->max_w;      /* bounded allocation */
	if (h > S.o->max_h) h = S.o->max_h;
	if (w != S.buf.w || h != S.buf.h) { S.want_w = w; S.want_h = h; S.resize_pending = 1; }
	fprintf(stderr, "info: configure %dx%d (clamped)\n", w, h);
}
static void ss_popup_done(void *data, struct wl_proxy *ss) { (void)data; (void)ss; }
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
	return 0;
}

static int roundtrip_bounded(void)
{
	int done = 0;
	struct wl_proxy *cb = new_obj((struct wl_proxy *)S.display, W.i_callback);
	if (!cb) { fprintf(stderr, "error: wl_callback proxy allocation failed\n"); return -1; }
	/* listener before the request is sent; on failure nothing went on the wire */
	if (LISTEN(cb, callback_listener, &done) != 0) {
		fprintf(stderr, "error: wl_callback listener install failed\n");
		W.proxy_destroy(cb);
		return -1;
	}
	W.proxy_marshal((struct wl_proxy *)S.display, DISPLAY_SYNC, cb);
	while (!done) {
		int ms = remaining_ms();
		if (ms == 0 || g_stop) { fprintf(stderr, "error: roundtrip deadline exceeded\n"); W.proxy_destroy(cb); return -1; }
		if (pump_once(ms > 100 ? 100 : ms) < 0) { W.proxy_destroy(cb); return -1; }
	}
	W.proxy_destroy(cb);
	return 0;
}

static void report_display_error(void)
{
	if (W.display_get_error && S.display) {
		int e = W.display_get_error(S.display);
		if (e) fprintf(stderr, "error: display error %d (%s)\n", e, strerror(e));
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
		fprintf(stderr, "error: posix_fallocate(%zu) failed: %s; refusing sparse SHM (SIGBUS risk)\n",
		        size, strerror(r));
		close(fd); errno = r; return -1;
	}
	/* verify the file really is the size we will map and declare */
	if (fstat(fd, &st) < 0) { e = errno; close(fd); errno = e; return -1; }
	if (st.st_size != (off_t)size) {
		fprintf(stderr, "error: shm file size %lld != %zu after fallocate\n", (long long)st.st_size, size);
		close(fd); errno = EIO; return -1;
	}
	return fd;
}

static void paint(struct buf *b, uint32_t rgb)
{
	uint32_t *px = b->data;
	int x, y;
	for (y = 0; y < b->h; y++)
		for (x = 0; x < b->w; x++) {
			uint32_t c = 0xff000000u | rgb;
			if (((x / 64) + (y / 64)) & 1) c = 0xff000000u | ((rgb >> 1) & 0x7f7f7fu);
			if (x < 8 || y < 8 || x >= b->w - 8 || y >= b->h - 8) c = 0xffffffffu;
			px[(size_t)y * b->w + x] = c;
		}
}

static void destroy_buf(struct buf *b)
{
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
	if (fd < 0) { fprintf(stderr, "error: shm file in %s: %s\n", S.o->runtime_dir, strerror(errno)); return EX_ALLOC; }
	b->data = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
	if (b->data == MAP_FAILED) {
		fprintf(stderr, "error: mmap shm: %s\n", strerror(errno));
		close(fd); b->data = NULL; return EX_ALLOC;
	}
	b->size = size; b->w = w; b->h = h;
	paint(b, S.o->color);   /* safe: backing reserved by posix_fallocate */

	pool = new_obj(S.shm, W.i_shm_pool);
	if (!pool) { fprintf(stderr, "error: wl_shm_pool proxy allocation failed\n"); close(fd); return EX_ALLOC; }
	W.proxy_marshal(S.shm, SHM_CREATE_POOL, pool, fd, (int32_t)size);
	close(fd);  /* fd is dup'ed into the outgoing message by libwayland */

	b->buffer = new_obj(pool, W.i_buffer);
	if (!b->buffer) {
		fprintf(stderr, "error: wl_buffer proxy allocation failed\n");
		W.proxy_marshal(pool, SHM_POOL_DESTROY); W.proxy_destroy(pool);
		return EX_ALLOC;
	}
	/* listener before create_buffer is sent; on failure no server object exists */
	if (LISTEN(b->buffer, buffer_listener, b) != 0) {
		fprintf(stderr, "error: wl_buffer listener install failed\n");
		W.proxy_destroy(b->buffer); b->buffer = NULL;
		W.proxy_marshal(pool, SHM_POOL_DESTROY); W.proxy_destroy(pool);
		return EX_PROTO;
	}
	W.proxy_marshal(pool, SHM_POOL_CREATE_BUFFER, b->buffer, 0, w, h, stride, WL_SHM_FORMAT_XRGB8888);
	W.proxy_marshal(pool, SHM_POOL_DESTROY);
	W.proxy_destroy(pool);
	return 0;
}

static void present(void)
{
	W.proxy_marshal(S.surface, SURFACE_ATTACH, S.buf.buffer, 0, 0);
	W.proxy_marshal(S.surface, SURFACE_DAMAGE, 0, 0, S.buf.w, S.buf.h);
	W.proxy_marshal(S.surface, SURFACE_COMMIT);
	S.buf.busy = 1;
}

/* ---- main ------------------------------------------------------------- */
static void print_config(const struct opts *o)
{
	printf("dry_run=%d\nduration_s=%d\nsize=%dx%d\nmax_size=%dx%d\ncolor=%06x\nfullscreen=%d\n"
	       "runtime_dir=%s\ndisplay=%s\n",
	       o->dry_run, o->duration_s, o->width, o->height, o->max_w, o->max_h,
	       (unsigned)o->color, !o->no_fullscreen, o->runtime_dir, o->display_name);
}

static void cleanup(void)
{
	if (S.buf.buffer || S.buf.data) destroy_buf(&S.buf);
	if (S.shell_surface) W.proxy_destroy(S.shell_surface);
	if (S.surface) { W.proxy_marshal(S.surface, SURFACE_DESTROY); W.proxy_destroy(S.surface); }
	if (S.shell) W.proxy_destroy(S.shell);
	if (S.shm) W.proxy_destroy(S.shm);
	if (S.compositor) W.proxy_destroy(S.compositor);
	if (S.registry) W.proxy_destroy(S.registry);
	if (S.display) { W.display_flush(S.display); W.display_disconnect(S.display); }
}

/* controlled failure helpers: report, release everything, return exit code */
static int fail_alloc(const char *what)
{
	fprintf(stderr, "error: %s proxy allocation failed; failing closed\n", what);
	cleanup();
	return EX_ALLOC;
}

static int fail_listener(const char *what)
{
	fprintf(stderr, "error: %s listener install failed; failing closed\n", what);
	cleanup();
	return EX_PROTO;
}

int main(int argc, char **argv)
{
	struct opts o;
	struct sigaction sa;
	int rc, i;

	rc = parse_opts(argc, argv, &o);
	if (rc > 0) return EX_OK;
	if (rc < 0) return EX_USAGE;
	if (o.parse_only) { print_config(&o); return EX_OK; }
	S.o = &o;

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
	g_deadline = now_ms() + (int64_t)o.duration_s * 1000;

	if (load_wayland() < 0) return EX_LIB;

	/* libwayland 1.x only resolves a relative name against XDG_RUNTIME_DIR. */
	if (setenv("XDG_RUNTIME_DIR", o.runtime_dir, 1) < 0) return EX_CONNECT;
	fprintf(stderr, "info: connecting to %s/%s (deadline %ds, hard exit %ds)\n",
	        o.runtime_dir, o.display_name, o.duration_s, o.duration_s + GRACE_S);
	/* NOTE: wl_display_connect() on a unix socket is a local connect(); a
	 * listening-but-stalled peer cannot block it beyond the SIGALRM bound. */
	S.display = W.display_connect(o.display_name);
	if (!S.display) { fprintf(stderr, "error: wl_display_connect failed: %s\n", strerror(errno)); return EX_CONNECT; }

	S.registry = new_obj((struct wl_proxy *)S.display, W.i_registry);
	if (!S.registry) return fail_alloc("wl_registry");
	if (LISTEN(S.registry, registry_listener, NULL) != 0) return fail_listener("wl_registry");
	W.proxy_marshal((struct wl_proxy *)S.display, DISPLAY_GET_REGISTRY, S.registry);
	if (roundtrip_bounded() < 0) { report_display_error(); cleanup(); return EX_PROTO; }

	printf("globals: %d%s\n", S.nglobals, S.globals_truncated ? " (truncated)" : "");
	for (i = 0; i < S.nglobals; i++)
		printf("global name=%u interface=%s version=%u\n",
		       S.globals[i].name, S.globals[i].iface, S.globals[i].version);
	fflush(stdout);

	if (o.dry_run) { printf("dry-run: no surfaces created\n"); cleanup(); return EX_OK; }

	if (!S.shell_name) {
		fprintf(stderr, "error: wl_shell not advertised; failing closed (no xdg-shell, no DRM fallback)\n");
		cleanup(); return EX_NOSHELL;
	}
	if (!S.compositor_name || !S.shm_name) {
		fprintf(stderr, "error: wl_compositor/wl_shm missing; failing closed\n");
		cleanup(); return EX_PROTO;
	}

	/* Bind everything at version 1 (lowest assumptions).
	 * Rule for every constructor below: allocate the proxy, NULL-check it,
	 * install its listener (if any) and check the return value, and only
	 * THEN marshal the request that names it as new_id. A failure before
	 * marshal means nothing referencing that object was sent. */
	S.compositor = new_obj(S.registry, W.i_compositor);
	if (!S.compositor) return fail_alloc("wl_compositor");
	W.proxy_marshal(S.registry, REGISTRY_BIND, S.compositor_name, W.i_compositor->name, 1u, S.compositor);

	S.shm = new_obj(S.registry, W.i_shm);
	if (!S.shm) return fail_alloc("wl_shm");
	if (LISTEN(S.shm, shm_listener, NULL) != 0) return fail_listener("wl_shm");
	W.proxy_marshal(S.registry, REGISTRY_BIND, S.shm_name, W.i_shm->name, 1u, S.shm);

	S.shell = new_obj(S.registry, W.i_shell);
	if (!S.shell) return fail_alloc("wl_shell");
	W.proxy_marshal(S.registry, REGISTRY_BIND, S.shell_name, W.i_shell->name, 1u, S.shell);

	if (roundtrip_bounded() < 0) { report_display_error(); cleanup(); return EX_PROTO; }
	if (!S.have_xrgb)  /* XRGB8888 is mandatory per protocol; warn only */
		fprintf(stderr, "warn: compositor did not announce XRGB8888 (mandatory format); continuing\n");

	S.surface = new_obj(S.compositor, W.i_surface);
	if (!S.surface) return fail_alloc("wl_surface");
	W.proxy_marshal(S.compositor, COMPOSITOR_CREATE_SURFACE, S.surface);

	S.shell_surface = new_obj(S.shell, W.i_shell_surface);
	if (!S.shell_surface) return fail_alloc("wl_shell_surface");
	if (LISTEN(S.shell_surface, shell_surface_listener, NULL) != 0) return fail_listener("wl_shell_surface");
	W.proxy_marshal(S.shell, SHELL_GET_SHELL_SURFACE, S.shell_surface, S.surface);
	W.proxy_marshal(S.shell_surface, SHSURF_SET_TITLE, "wayland-hello");
	if (o.no_fullscreen) W.proxy_marshal(S.shell_surface, SHSURF_SET_TOPLEVEL);
	else W.proxy_marshal(S.shell_surface, SHSURF_SET_FULLSCREEN, 0u /*default*/, 0u, (struct wl_proxy *)NULL);

	rc = create_buf(&S.buf, o.width, o.height);
	if (rc != 0) { cleanup(); return rc; }
	present();
	fprintf(stderr, "info: surface committed %dx%d; running until deadline\n", S.buf.w, S.buf.h);

	rc = EX_OK;
	while (!g_stop) {
		int ms = remaining_ms();
		if (ms == 0) break;
		if (pump_once(ms > 100 ? 100 : ms) < 0) {
			fprintf(stderr, "error: connection lost\n"); report_display_error(); rc = EX_PROTO; break;
		}
		if (S.resize_pending) {
			S.resize_pending = 0;
			/* old buffer may still be held; we destroy it (client-side) and
			 * allocate a new bounded one. Only one buffer ever allocated. */
			destroy_buf(&S.buf);
			{
				int brc = create_buf(&S.buf, S.want_w, S.want_h);
				if (brc != 0) { rc = brc; break; }
			}
			present();
		}
	}
	fprintf(stderr, "info: exiting (%s)\n", g_stop ? "signal" : "deadline");
	cleanup();
	return rc;
}

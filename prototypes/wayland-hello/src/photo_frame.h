/*
 * Fullscreen photograph-test pattern. Independent of Wayland and luna.
 *
 * The host (wayland_hello.c) supplies an XRGB8888 buffer, elapsed seconds,
 * focus counts, and the last key. This module chooses a panel-sized buffer
 * and paints an unmistakable frame: solid fill, labeled corner boxes, a
 * large timer, and the current mode / window type.
 *
 * MODE A is a focusable fullscreen surface. MODE B is the already-proven
 * wl_webos_shell overlay path, but at full panel resolution.
 */
#ifndef WAYLAND_HELLO_PHOTO_FRAME_H
#define WAYLAND_HELLO_PHOTO_FRAME_H

#include <stdint.h>

enum photo_frame_mode {
	PHOTO_FRAME_OFF = 0,
	PHOTO_FRAME_A = 1,
	PHOTO_FRAME_B = 2,
	PHOTO_FRAME_C = 3
};

enum photo_frame_corner {
	PHOTO_CORNER_TL = 0,
	PHOTO_CORNER_TR = 1,
	PHOTO_CORNER_BL = 2,
	PHOTO_CORNER_BR = 3
};

#define PHOTO_FRAME_FALLBACK_W 1920
#define PHOTO_FRAME_FALLBACK_H 1080
#define PHOTO_FRAME_CORNER_COUNT 4

struct photo_frame_state {
	int mode;
	int seconds;
	int buf_w, buf_h;
	int focus_enter, focus_leave;
	int ptr_enter, ptr_leave;
	uint32_t last_key;
	const char *last_key_name;
	const char *window_type;
};

/* Sidecar / CLI body: "A", "A\n", "b". Returns 0 and writes PHOTO_FRAME_A/B. */
int photo_frame_parse_mode(const char *text, int *mode);

const char *photo_frame_mode_name(int mode);
/* Short on-screen label: "FOCUSABLE FULLSCREEN" / "NON-FOCUSABLE OVERLAY". */
const char *photo_frame_mode_label(int mode);
/* Default window-type token painted and logged for that mode. */
const char *photo_frame_window_type(int mode);

/*
 * Prefer a compositor configure, then a wl_output mode, then fallback_w/h
 * (1920x1080 when fallback is 0). Clamp to max. source is
 * "configure", "wl_output", or "fallback".
 */
int photo_frame_pick_size(int output_w, int output_h,
                          int configure_w, int configure_h,
                          int fallback_w, int fallback_h,
                          int max_w, int max_h,
                          int *w, int *h, const char **source);

int photo_frame_corner_rect(int w, int h, int corner, int *x, int *y, int *cw, int *ch);
const char *photo_frame_corner_label(int corner);

void photo_frame_paint(const struct photo_frame_state *st, uint32_t *px, int w, int h);

/* Distinctive fills so host tests can sample pixels. XRGB with 0xff alpha. */
#define PHOTO_COL_A_BG      0xffff00d0u  /* bright magenta */
#define PHOTO_COL_B_BG      0xff00c8ffu  /* bright cyan */
#define PHOTO_COL_C_BG      0xff20d060u  /* bright green */
#define PHOTO_COL_CORNER    0xfffff200u  /* yellow box */
#define PHOTO_COL_CORNER_IN 0xff101010u  /* near-black interior */
#define PHOTO_COL_TEXT      0xffffffffu
#define PHOTO_COL_HUD_BG    0xff101018u
#define PHOTO_COL_TIMER     0xffffff00u

#endif

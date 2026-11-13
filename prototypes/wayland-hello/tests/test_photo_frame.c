/*
 * Host unit tests for src/photo_frame.c. No Wayland, no TV.
 * Built by tests/run_tests.py against the production module.
 */
#include "photo_frame.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int failed;

static void check(const char *name, int cond)
{
	if (cond)
		printf("ok  %s\n", name);
	else {
		failed++;
		printf("FAIL %s\n", name);
	}
}

static uint32_t pix(const uint32_t *px, int w, int h, int x, int y)
{
	if (x < 0 || y < 0 || x >= w || y >= h) return 0;
	return px[(size_t)y * (size_t)w + (size_t)x];
}

int main(void)
{
	int mode = 99, w = 0, h = 0, x = 0, y = 0, cw = 0, ch = 0;
	const char *src = NULL;
	uint32_t *buf;
	struct photo_frame_state st;
	int cx, cy;

	check("parse A", photo_frame_parse_mode("A", &mode) == 0 && mode == PHOTO_FRAME_A);
	check("parse A newline", photo_frame_parse_mode("A\n", &mode) == 0 && mode == PHOTO_FRAME_A);
	check("parse a lowercase", photo_frame_parse_mode("a\r\n", &mode) == 0 && mode == PHOTO_FRAME_A);
	check("parse B", photo_frame_parse_mode("B\n", &mode) == 0 && mode == PHOTO_FRAME_B);
	check("parse b spaces", photo_frame_parse_mode("  b  ", &mode) == 0 && mode == PHOTO_FRAME_B);
	check("reject empty", photo_frame_parse_mode("", &mode) != 0);
	check("reject C", photo_frame_parse_mode("C\n", &mode) != 0);
	check("reject AB", photo_frame_parse_mode("AB", &mode) != 0);
	check("reject null", photo_frame_parse_mode(NULL, &mode) != 0);

	check("mode name A", strcmp(photo_frame_mode_name(PHOTO_FRAME_A), "A") == 0);
	check("mode name B", strcmp(photo_frame_mode_name(PHOTO_FRAME_B), "B") == 0);
	check("mode label A is focusable", strstr(photo_frame_mode_label(PHOTO_FRAME_A), "FOCUSABLE") != NULL);
	check("mode label B is overlay", strstr(photo_frame_mode_label(PHOTO_FRAME_B), "OVERLAY") != NULL);
	check("window type A is wl_shell fullscreen",
	      strcmp(photo_frame_window_type(PHOTO_FRAME_A), "wl_shell-fullscreen") == 0);
	check("window type B is overlay",
	      strcmp(photo_frame_window_type(PHOTO_FRAME_B), "_WEBOS_WINDOW_TYPE_OVERLAY") == 0);

	check("pick prefers configure over output",
	      photo_frame_pick_size(1280, 720, 1920, 1080, 0, 0, 1920, 1080, &w, &h, &src) == 0
	      && w == 1920 && h == 1080 && src && strcmp(src, "configure") == 0);
	check("pick uses output when configure is 0",
	      photo_frame_pick_size(1280, 720, 0, 0, 0, 0, 1920, 1080, &w, &h, &src) == 0
	      && w == 1280 && h == 720 && src && strcmp(src, "wl_output") == 0);
	check("pick falls back to 1920x1080",
	      photo_frame_pick_size(0, 0, 0, 0, 0, 0, 1920, 1080, &w, &h, &src) == 0
	      && w == 1920 && h == 1080 && src && strcmp(src, "fallback") == 0);
	check("pick uses explicit fallback before 1920x1080",
	      photo_frame_pick_size(0, 0, 0, 0, 800, 600, 1920, 1080, &w, &h, &src) == 0
	      && w == 800 && h == 600 && src && strcmp(src, "fallback") == 0);
	check("pick clamps oversized output",
	      photo_frame_pick_size(3840, 2160, 0, 0, 0, 0, 1920, 1080, &w, &h, &src) == 0
	      && w == 1920 && h == 1080 && src && strcmp(src, "wl_output") == 0);
	check("pick clamps oversized configure",
	      photo_frame_pick_size(0, 0, 5000, 3000, 0, 0, 1920, 1080, &w, &h, &src) == 0
	      && w == 1920 && h == 1080);
	check("pick rejects incomplete output pair",
	      photo_frame_pick_size(1920, 0, 0, 0, 0, 0, 1920, 1080, &w, &h, &src) == 0
	      && w == 1920 && h == 1080 && strcmp(src, "fallback") == 0);

	check("corner TL at origin 1920x1080",
	      photo_frame_corner_rect(1920, 1080, PHOTO_CORNER_TL, &x, &y, &cw, &ch) == 0
	      && x == 0 && y == 0 && cw >= 64 && ch >= 48);
	check("corner TR touches right edge",
	      photo_frame_corner_rect(1920, 1080, PHOTO_CORNER_TR, &x, &y, &cw, &ch) == 0
	      && y == 0 && x + cw == 1920);
	check("corner BL touches bottom",
	      photo_frame_corner_rect(1920, 1080, PHOTO_CORNER_BL, &x, &y, &cw, &ch) == 0
	      && x == 0 && y + ch == 1080);
	check("corner BR touches both far edges",
	      photo_frame_corner_rect(1920, 1080, PHOTO_CORNER_BR, &x, &y, &cw, &ch) == 0
	      && x + cw == 1920 && y + ch == 1080);
	check("corner labels",
	      strcmp(photo_frame_corner_label(PHOTO_CORNER_TL), "TL") == 0
	      && strcmp(photo_frame_corner_label(PHOTO_CORNER_TR), "TR") == 0
	      && strcmp(photo_frame_corner_label(PHOTO_CORNER_BL), "BL") == 0
	      && strcmp(photo_frame_corner_label(PHOTO_CORNER_BR), "BR") == 0);
	check("tiny buffer has no corners",
	      photo_frame_corner_rect(8, 8, PHOTO_CORNER_TL, &x, &y, &cw, &ch) != 0);

	buf = calloc((size_t)1920 * 1080, sizeof *buf);
	if (!buf) {
		printf("FAIL alloc 1920x1080\n");
		return 1;
	}
	memset(&st, 0, sizeof st);
	st.mode = PHOTO_FRAME_A;
	st.seconds = 42;
	st.buf_w = 1920;
	st.buf_h = 1080;
	st.focus_enter = 1;
	st.focus_leave = 0;
	st.last_key = 106;
	st.last_key_name = "KEY_RIGHT";
	st.window_type = photo_frame_window_type(PHOTO_FRAME_A);
	photo_frame_paint(&st, buf, 1920, 1080);

	check("mode A fill reaches a mid-left pixel",
	      pix(buf, 1920, 1080, 200, 540) == PHOTO_COL_A_BG);
	check("mode A TL corner is yellow at 0,0",
	      pix(buf, 1920, 1080, 0, 0) == PHOTO_COL_CORNER);
	check("mode A TR corner is yellow at 1919,0",
	      pix(buf, 1920, 1080, 1919, 0) == PHOTO_COL_CORNER);
	check("mode A BL corner is yellow at 0,1079",
	      pix(buf, 1920, 1080, 0, 1079) == PHOTO_COL_CORNER);
	check("mode A BR corner is yellow at 1919,1079",
	      pix(buf, 1920, 1080, 1919, 1079) == PHOTO_COL_CORNER);

	photo_frame_corner_rect(1920, 1080, PHOTO_CORNER_TL, &x, &y, &cw, &ch);
	cx = x + cw / 2;
	cy = y + ch / 2;
	check("mode A TL interior is dark so the label reads",
	      pix(buf, 1920, 1080, cx, cy) == PHOTO_COL_CORNER_IN
	      || pix(buf, 1920, 1080, cx, cy) == PHOTO_COL_TEXT
	      || pix(buf, 1920, 1080, cx, cy) == PHOTO_COL_TIMER);

	{
		int found_timer = 0, xx, yy;
		for (yy = 400; yy < 680 && !found_timer; yy++)
			for (xx = 700; xx < 1220 && !found_timer; xx++)
				if (pix(buf, 1920, 1080, xx, yy) == PHOTO_COL_TIMER)
					found_timer = 1;
		check("mode A paints a large timer in yellow", found_timer);
	}

	memset(buf, 0, (size_t)1920 * 1080 * sizeof *buf);
	st.mode = PHOTO_FRAME_B;
	st.focus_enter = 0;
	st.last_key = 0;
	st.last_key_name = "-";
	st.window_type = photo_frame_window_type(PHOTO_FRAME_B);
	st.seconds = 90;
	photo_frame_paint(&st, buf, 1920, 1080);
	check("mode B fill is cyan not magenta",
	      pix(buf, 1920, 1080, 200, 540) == PHOTO_COL_B_BG);
	check("mode B still paints every corner",
	      pix(buf, 1920, 1080, 0, 0) == PHOTO_COL_CORNER
	      && pix(buf, 1920, 1080, 1919, 0) == PHOTO_COL_CORNER
	      && pix(buf, 1920, 1080, 0, 1079) == PHOTO_COL_CORNER
	      && pix(buf, 1920, 1080, 1919, 1079) == PHOTO_COL_CORNER);

	/* Tiny buffer must not overflow. */
	{
		uint32_t tiny[4] = {0, 0, 0, 0};
		st.mode = PHOTO_FRAME_A;
		photo_frame_paint(&st, tiny, 2, 2);
		check("tiny paint fills 2x2 without crashing",
		      tiny[0] == PHOTO_COL_A_BG || tiny[0] == PHOTO_COL_CORNER);
	}

	free(buf);
	printf("%d failed\n", failed);
	return failed ? 1 : 0;
}

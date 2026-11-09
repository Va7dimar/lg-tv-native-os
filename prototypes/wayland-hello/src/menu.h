/*
 * Independent launcher-menu module for wayland-hello.
 *
 * No Wayland, no luna, no dlopen. The host (wayland_hello.c) supplies an
 * XRGB8888 pixel buffer and wl_seat evdev key codes. This file does not
 * launch other apps.
 *
 * Host dependencies (not linked; the .c is compiled next to wayland_hello.c):
 *   - spare-buffer redraw in the host (compositor may never release)
 *   - existing --demo square paint when the Demo tile is activated
 *   - the same evdev codes --demo already names (arrows confirmed on TV;
 *     OK/BACK/ENTER/EXIT/ESC are hypotheses — see menu_keymap())
 */
#ifndef WAYLAND_HELLO_MENU_H
#define WAYLAND_HELLO_MENU_H

#include <stdint.h>

#define MENU_TILE_COUNT 3

enum menu_screen {
	MENU_SCREEN_TILES = 0,
	MENU_SCREEN_ABOUT,
	MENU_SCREEN_DEMO
};

enum menu_action {
	MENU_ACTION_NONE = 0,
	MENU_ACTION_REDRAW,
	MENU_ACTION_EXIT,
	MENU_ACTION_ENTER_DEMO,
	MENU_ACTION_LEAVE_DEMO
};

enum menu_key_class {
	MENU_KEY_UNKNOWN = 0,
	MENU_KEY_LEFT,
	MENU_KEY_RIGHT,
	MENU_KEY_UP,
	MENU_KEY_DOWN,
	MENU_KEY_ACTIVATE,
	MENU_KEY_BACK,
	MENU_KEY_EXIT
};

/* status is "confirmed" (seen on this TV) or "hypothesis" (linux evdev name, not in TV logs). */
struct menu_key_map {
	uint32_t code;
	enum menu_key_class klass;
	const char *name;
	const char *status;
	const char *note;
};

struct menu_state {
	int screen;
	int focus;  /* 0 .. MENU_TILE_COUNT-1 */
};

void menu_init(struct menu_state *m);
const struct menu_key_map *menu_keymap(int *count);
const char *menu_key_class_name(enum menu_key_class c);
enum menu_key_class menu_classify_key(uint32_t code, const struct menu_key_map **hit);
enum menu_action menu_handle_key(struct menu_state *m, uint32_t code);
void menu_paint(const struct menu_state *m, uint32_t *px, int w, int h);
const char *menu_focus_label(const struct menu_state *m);
const char *menu_screen_name(int screen);
/* Tile rectangle in the same coordinates menu_paint uses. Returns 0 if index is valid. */
int menu_tile_rect(int w, int h, int index, int *x, int *y, int *tw, int *th);

/* Distinctive fills so host tests can sample pixels. XRGB with 0xff alpha. */
#define MENU_COL_BG         0xff101820u
#define MENU_COL_ABOUT_BG   0xff081018u
#define MENU_COL_TILE       0xff2a3a55u
#define MENU_COL_TILE_FOCUS 0xffd4a017u
#define MENU_COL_BORDER     0xff8aa0c0u
#define MENU_COL_FOCUS_BRD  0xfffff0a0u
#define MENU_COL_TEXT       0xffffffffu

#endif

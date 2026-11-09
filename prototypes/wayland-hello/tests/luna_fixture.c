/* Host stand-in for libluna-service2.so.3 and libglib-2.0.so.0.
 * The test loads this file under both sonames (one inode) so the
 * registration and the main-context pump share state. */
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct ls_error {
	int error_code;
	char *message;
	const char *file;
	int line;
	const char *func;
	void *padding;
	unsigned long magic;
};

static bool (*saved_cb)(void *, void *, void *);
static char saved_payload[512];
static int iterations;
static int logged_iter;

static const char *script_name(void)
{
	const char *s = getenv("WAYLAND_HELLO_LUNA_SCRIPT");
	return (s && s[0]) ? s : "default";
}

bool LSErrorInit(struct ls_error *e)
{
	if (e) memset(e, 0, sizeof *e);
	return true;
}

void LSErrorFree(struct ls_error *e)
{
	(void)e;
}

bool LSRegister(const char *name, void **sh, struct ls_error *e)
{
	(void)e;
	fprintf(stderr, "fixture: LSRegister %s\n", name ? name : "(null)");
	if (!strcmp(script_name(), "register-fail")) return false;
	if (sh) *sh = (void *)1;
	return true;
}

#ifndef LUNA_OMIT_ATTACH
bool LSGmainAttach(void *sh, void *loop, struct ls_error *e)
{
	(void)sh; (void)loop; (void)e;
	fprintf(stderr, "fixture: LSGmainAttach\n");
	return true;
}
#endif

bool LSCall(void *sh, const char *uri, const char *payload,
            bool (*cb)(void *, void *, void *), void *user,
            unsigned long *token, struct ls_error *e)
{
	(void)sh; (void)user; (void)e;
	fprintf(stderr, "fixture: LSCall %s %s\n", uri ? uri : "", payload ? payload : "");
	if (!strcmp(script_name(), "call-fail")) return false;
	saved_cb = cb;
	if (token) *token = 7;
	snprintf(saved_payload, sizeof saved_payload,
	         "{\"returnValue\":true,\"event\":\"registered\",\"subscribed\":true}");
	return true;
}

const char *LSMessageGetPayload(void *msg)
{
	(void)msg;
	return saved_payload;
}

bool LSUnregister(void *sh, struct ls_error *e)
{
	(void)sh; (void)e;
	fprintf(stderr, "fixture: LSUnregister\n");
	return true;
}

void *g_main_loop_new(void *ctx, int running)
{
	(void)ctx; (void)running;
	return (void *)2;
}

void g_main_loop_unref(void *loop)
{
	(void)loop;
}

int g_main_context_iteration(void *ctx, int may_block)
{
	const char *script = script_name();
	if (!logged_iter) {
		fprintf(stderr, "fixture: iterate ctx=%s block=%d\n", ctx ? "set" : "null", may_block);
		logged_iter = 1;
	}
	iterations++;
	if (!saved_cb) return 0;
	if (iterations == 1 && !strcmp(script, "reject")) {
		snprintf(saved_payload, sizeof saved_payload,
		         "{\"returnValue\":false,\"errorText\":\"not running\"}");
		saved_cb((void *)1, (void *)1, NULL);
		saved_cb = NULL;
		return 0;
	}
	if (iterations == 1 && !strcmp(script, "nested-close")) {
		snprintf(saved_payload, sizeof saved_payload,
		         "{\"parameters\":{\"event\":\"relaunch\"},\"returnValue\":true,\"event\":\"close\"}");
		saved_cb((void *)1, (void *)1, NULL);
		saved_cb = NULL;
		return 0;
	}
	if (iterations == 1) {
		saved_cb((void *)1, (void *)1, NULL);
	} else if (iterations == 4 && strcmp(script, "close-late") != 0) {
		snprintf(saved_payload, sizeof saved_payload,
		         "{\"returnValue\":true,\"event\":\"relaunch\",\"parameters\":{}}");
		saved_cb((void *)1, (void *)1, NULL);
	}
	if (!strcmp(script, "relaunch-only")) return 0;
	if ((!strcmp(script, "default") && iterations == 8) ||
	    (!strcmp(script, "close-late") && iterations == 30)) {
		snprintf(saved_payload, sizeof saved_payload,
		         "{\"returnValue\":true,\"event\":\"close\"}");
		saved_cb((void *)1, (void *)1, NULL);
		saved_cb = NULL;
	}
	return 0;
}

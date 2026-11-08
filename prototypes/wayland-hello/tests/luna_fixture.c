/* Host stand-in for libluna-service2.so.3 and libglib-2.0.so.0.
 * The test loads this file under both sonames (one inode) so the
 * registration and the main-context pump share state. */
#include <stdbool.h>
#include <stdio.h>
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
static char saved_payload[256];
static int iterations;

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
	if (sh) *sh = (void *)1;
	return true;
}

bool LSGmainAttach(void *sh, void *loop, struct ls_error *e)
{
	(void)sh; (void)loop; (void)e;
	fprintf(stderr, "fixture: LSGmainAttach\n");
	return true;
}

bool LSCall(void *sh, const char *uri, const char *payload,
            bool (*cb)(void *, void *, void *), void *user,
            unsigned long *token, struct ls_error *e)
{
	(void)sh; (void)user; (void)e;
	fprintf(stderr, "fixture: LSCall %s %s\n", uri ? uri : "", payload ? payload : "");
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
	(void)ctx; (void)may_block;
	iterations++;
	if (!saved_cb) return 0;
	if (iterations == 1) {
		saved_cb((void *)1, (void *)1, NULL);
	} else if (iterations == 4) {
		snprintf(saved_payload, sizeof saved_payload,
		         "{\"returnValue\":true,\"event\":\"relaunch\",\"parameters\":{}}");
		saved_cb((void *)1, (void *)1, NULL);
	} else if (iterations == 8) {
		snprintf(saved_payload, sizeof saved_payload,
		         "{\"returnValue\":true,\"event\":\"close\"}");
		saved_cb((void *)1, (void *)1, NULL);
	}
	return 0;
}

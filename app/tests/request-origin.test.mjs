import assert from "node:assert/strict";
import test from "node:test";
import { acceptsOrigin } from "../lib/request-origin.mjs";

function request(origin, host = "127.0.0.1:3000", extra = {}) {
  return new Request("http://localhost:3000/api/dashboard", {
    headers: { host, ...(origin ? { origin } : {}), ...extra },
  });
}

test("accepts legitimate loopback writes despite Next's normalized internal hostname", () => {
  assert.equal(acceptsOrigin(request("http://127.0.0.1:3000")), true);
});

test("accepts localhost and normalizes default ports", () => {
  assert.equal(acceptsOrigin(request("http://localhost:3000", "localhost:3000")), true);
  assert.equal(acceptsOrigin(request("http://localhost", "localhost:80")), true);
});

test("rejects different hosts, schemes and ports", () => {
  assert.equal(acceptsOrigin(request("https://127.0.0.1:3000")), false);
  assert.equal(acceptsOrigin(request("http://127.0.0.1:3001")), false);
  assert.equal(acceptsOrigin(request("http://example.com")), false);
});

test("does not trust an arbitrary forwarded host", () => {
  assert.equal(acceptsOrigin(request("http://example.com", "127.0.0.1:3000", {
    "x-forwarded-host": "example.com",
  })), false);
});

test("rejects malformed or opaque origins and missing public host", () => {
  assert.equal(acceptsOrigin(request("not an origin")), false);
  assert.equal(acceptsOrigin(request("null")), false);
  assert.equal(acceptsOrigin(new Request("http://localhost/api/dashboard", {
    headers: { origin: "http://localhost" },
  })), false);
});

test("accepts local CLI requests without a browser Origin", () => {
  assert.equal(acceptsOrigin(request()), true);
});

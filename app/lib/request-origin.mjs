/** Compare browser Origin with the public Host, not Next's internally normalized request URL.
 * @param {Request} request
 */
export function acceptsOrigin(request) {
  const origin = request.headers.get("origin");
  if (!origin) return true; // Local CLI/API requests do not send a browser Origin header.
  const host = request.headers.get("host");
  if (!host) return false;
  try {
    const protocol = new URL(request.url).protocol;
    return new URL(origin).origin === new URL(`${protocol}//${host}`).origin;
  } catch {
    return false;
  }
}

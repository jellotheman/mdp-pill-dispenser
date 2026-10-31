export function prettyTime(value: string) {
  const [hour, minute] = value.split(":").map(Number);
  return `${hour % 12 || 12}:${String(minute).padStart(2, "0")} ${hour < 12 ? "am" : "pm"}`;
}

export function prettyDate(value: string) {
  return new Date(value).toLocaleString("en-IN", {
    timeZone: "Asia/Kolkata", month: "short", day: "numeric", hour: "numeric", minute: "2-digit",
  });
}

export function indiaDate(value: string | Date) {
  return new Date(value).toLocaleDateString("en-CA", { timeZone: "Asia/Kolkata" });
}

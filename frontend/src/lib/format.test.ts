import { describe, expect, it } from "vitest";

import { formatDuration, formatPercent } from "./format";

describe("formatDuration", () => {
  it("returns a placeholder when the duration is unavailable", () => {
    expect(formatDuration(null)).toBe("-");
  });

  it("formats a duration with milliseconds", () => {
    expect(formatDuration(1250)).toBe("1.250 ms");
  });
});

describe("formatPercent", () => {
  it("formats percentages with at most one decimal place", () => {
    expect(formatPercent(12.56)).toBe("12,6%");
  });
});

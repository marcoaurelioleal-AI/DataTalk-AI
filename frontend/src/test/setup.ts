import "@testing-library/jest-dom/vitest";

class TestResizeObserver implements ResizeObserver {
  constructor(private readonly callback: ResizeObserverCallback) {}

  disconnect(): void {}

  observe(target: Element): void {
    const contentRect = new DOMRectReadOnly(0, 0, 800, 288);
    this.callback(
      [{ target, contentRect, borderBoxSize: [], contentBoxSize: [], devicePixelContentBoxSize: [] }],
      this,
    );
  }

  unobserve(): void {}
}

globalThis.ResizeObserver = TestResizeObserver;

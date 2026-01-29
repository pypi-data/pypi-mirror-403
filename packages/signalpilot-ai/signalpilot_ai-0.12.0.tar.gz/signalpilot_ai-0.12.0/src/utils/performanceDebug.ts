/**
 * Performance Debugging Utility
 *
 * Tracks timing, call counts, and memory usage to help identify performance bottlenecks.
 * Access via window.perfDebug in the browser console.
 */

interface TimingEntry {
  name: string;
  startTime: number;
  endTime?: number;
  duration?: number;
  callCount: number;
  totalDuration: number;
  avgDuration: number;
  maxDuration: number;
  minDuration: number;
  lastCallStack?: string;
}

interface SubscriptionEntry {
  name: string;
  count: number;
  lastSubscribeTime: number;
  unsubscribeCount: number;
}

interface StateUpdateEntry {
  storeName: string;
  updateCount: number;
  lastUpdateTime: number;
  lastUpdateKeys: string[];
  totalUpdateSize: number;
}

class PerformanceDebugger {
  private static instance: PerformanceDebugger;
  private timings: Map<string, TimingEntry> = new Map();
  private subscriptions: Map<string, SubscriptionEntry> = new Map();
  private stateUpdates: Map<string, StateUpdateEntry> = new Map();
  private activeTimers: Map<string, number> = new Map();
  private enabled: boolean = true;
  private logToConsole: boolean = true;

  private constructor() {
    // Expose to window for debugging
    if (typeof window !== 'undefined') {
      (window as any).perfDebug = this;
    }
  }

  public static getInstance(): PerformanceDebugger {
    if (!PerformanceDebugger.instance) {
      PerformanceDebugger.instance = new PerformanceDebugger();
    }
    return PerformanceDebugger.instance;
  }

  /**
   * Enable/disable performance tracking
   */
  public setEnabled(enabled: boolean): void {
    this.enabled = enabled;
    console.log(
      `[PerfDebug] Performance tracking ${enabled ? 'enabled' : 'disabled'}`
    );
  }

  /**
   * Enable/disable console logging
   */
  public setLogToConsole(log: boolean): void {
    this.logToConsole = log;
  }

  /**
   * Start timing an operation
   */
  public startTimer(name: string, captureStack: boolean = false): void {
    if (!this.enabled) return;

    const now = performance.now();
    this.activeTimers.set(name, now);

    if (!this.timings.has(name)) {
      this.timings.set(name, {
        name,
        startTime: now,
        callCount: 0,
        totalDuration: 0,
        avgDuration: 0,
        maxDuration: 0,
        minDuration: Infinity
      });
    }

    const entry = this.timings.get(name)!;
    entry.startTime = now;
    entry.callCount++;

    if (captureStack) {
      entry.lastCallStack = new Error().stack;
    }

    if (this.logToConsole) {
      console.log(`[PerfDebug] START: ${name} (call #${entry.callCount})`);
    }
  }

  /**
   * End timing an operation
   */
  public endTimer(name: string): number {
    if (!this.enabled) return 0;

    const startTime = this.activeTimers.get(name);
    if (startTime === undefined) {
      console.warn(`[PerfDebug] No active timer for: ${name}`);
      return 0;
    }

    const now = performance.now();
    const duration = now - startTime;
    this.activeTimers.delete(name);

    const entry = this.timings.get(name)!;
    entry.endTime = now;
    entry.duration = duration;
    entry.totalDuration += duration;
    entry.avgDuration = entry.totalDuration / entry.callCount;
    entry.maxDuration = Math.max(entry.maxDuration, duration);
    entry.minDuration = Math.min(entry.minDuration, duration);

    if (this.logToConsole) {
      const emoji = duration > 100 ? '🔴' : duration > 50 ? '🟡' : '🟢';
      console.log(
        `[PerfDebug] END: ${name} ${emoji} ${duration.toFixed(2)}ms (avg: ${entry.avgDuration.toFixed(2)}ms, calls: ${entry.callCount})`
      );
    }

    // Warn if operation is slow
    if (duration > 100) {
      console.warn(
        `[PerfDebug] SLOW OPERATION: ${name} took ${duration.toFixed(2)}ms`
      );
    }

    return duration;
  }

  /**
   * Track a subscription being created
   */
  public trackSubscription(name: string): void {
    if (!this.enabled) return;

    if (!this.subscriptions.has(name)) {
      this.subscriptions.set(name, {
        name,
        count: 0,
        lastSubscribeTime: Date.now(),
        unsubscribeCount: 0
      });
    }

    const entry = this.subscriptions.get(name)!;
    entry.count++;
    entry.lastSubscribeTime = Date.now();

    if (this.logToConsole) {
      console.log(
        `[PerfDebug] SUBSCRIBE: ${name} (active: ${entry.count}, total unsubscribed: ${entry.unsubscribeCount})`
      );
    }

    // Warn if too many subscriptions
    if (entry.count > 5) {
      console.warn(
        `[PerfDebug] SUBSCRIPTION LEAK? ${name} has ${entry.count} active subscriptions`
      );
    }
  }

  /**
   * Track a subscription being removed
   */
  public trackUnsubscription(name: string): void {
    if (!this.enabled) return;

    const entry = this.subscriptions.get(name);
    if (entry) {
      entry.count = Math.max(0, entry.count - 1);
      entry.unsubscribeCount++;

      if (this.logToConsole) {
        console.log(
          `[PerfDebug] UNSUBSCRIBE: ${name} (remaining: ${entry.count})`
        );
      }
    }
  }

  /**
   * Track a state update
   */
  public trackStateUpdate(
    storeName: string,
    keys: string[],
    estimatedSize?: number
  ): void {
    if (!this.enabled) return;

    if (!this.stateUpdates.has(storeName)) {
      this.stateUpdates.set(storeName, {
        storeName,
        updateCount: 0,
        lastUpdateTime: Date.now(),
        lastUpdateKeys: [],
        totalUpdateSize: 0
      });
    }

    const entry = this.stateUpdates.get(storeName)!;
    entry.updateCount++;
    entry.lastUpdateTime = Date.now();
    entry.lastUpdateKeys = keys;
    if (estimatedSize) {
      entry.totalUpdateSize += estimatedSize;
    }

    if (this.logToConsole) {
      console.log(
        `[PerfDebug] STATE UPDATE: ${storeName} - keys: [${keys.join(', ')}] (update #${entry.updateCount})`
      );
    }

    // Warn if updates are too frequent
    if (entry.updateCount > 100) {
      console.warn(
        `[PerfDebug] EXCESSIVE UPDATES: ${storeName} has been updated ${entry.updateCount} times`
      );
    }
  }

  /**
   * Estimate the size of an object in bytes
   */
  public estimateObjectSize(obj: any): number {
    try {
      const str = JSON.stringify(obj, (key, value) => {
        // Handle non-serializable values
        if (value instanceof Map) return `[Map: ${value.size} entries]`;
        if (value instanceof Set) return `[Set: ${value.size} entries]`;
        if (typeof value === 'function') return '[Function]';
        if (value instanceof HTMLElement) return '[HTMLElement]';
        return value;
      });
      return str ? str.length * 2 : 0; // UTF-16 characters are 2 bytes
    } catch {
      return -1; // Can't serialize
    }
  }

  /**
   * Get timing statistics
   */
  public getTimingStats(): TimingEntry[] {
    return Array.from(this.timings.values()).sort(
      (a, b) => b.totalDuration - a.totalDuration
    );
  }

  /**
   * Get subscription statistics
   */
  public getSubscriptionStats(): SubscriptionEntry[] {
    return Array.from(this.subscriptions.values()).sort(
      (a, b) => b.count - a.count
    );
  }

  /**
   * Get state update statistics
   */
  public getStateUpdateStats(): StateUpdateEntry[] {
    return Array.from(this.stateUpdates.values()).sort(
      (a, b) => b.updateCount - a.updateCount
    );
  }

  /**
   * Print a summary report to the console
   */
  public printReport(): void {
    console.group('📊 Performance Debug Report');

    console.group('⏱️ Timing Statistics (sorted by total duration)');
    const timings = this.getTimingStats();
    if (timings.length === 0) {
      console.log('No timing data collected');
    } else {
      console.table(
        timings.map(t => ({
          Name: t.name,
          Calls: t.callCount,
          'Total (ms)': t.totalDuration.toFixed(2),
          'Avg (ms)': t.avgDuration.toFixed(2),
          'Max (ms)': t.maxDuration.toFixed(2),
          'Min (ms)':
            t.minDuration === Infinity ? 'N/A' : t.minDuration.toFixed(2)
        }))
      );
    }
    console.groupEnd();

    console.group('🔗 Subscription Statistics (sorted by active count)');
    const subs = this.getSubscriptionStats();
    if (subs.length === 0) {
      console.log('No subscription data collected');
    } else {
      console.table(
        subs.map(s => ({
          Name: s.name,
          Active: s.count,
          Unsubscribed: s.unsubscribeCount,
          'Potential Leak': s.count > 5 ? '⚠️ YES' : 'No'
        }))
      );
    }
    console.groupEnd();

    console.group('📝 State Update Statistics (sorted by update count)');
    const updates = this.getStateUpdateStats();
    if (updates.length === 0) {
      console.log('No state update data collected');
    } else {
      console.table(
        updates.map(u => ({
          Store: u.storeName,
          Updates: u.updateCount,
          'Last Keys': u.lastUpdateKeys.join(', '),
          Excessive: u.updateCount > 100 ? '⚠️ YES' : 'No'
        }))
      );
    }
    console.groupEnd();

    console.groupEnd();
  }

  /**
   * Clear all collected data
   */
  public clear(): void {
    this.timings.clear();
    this.subscriptions.clear();
    this.stateUpdates.clear();
    this.activeTimers.clear();
    console.log('[PerfDebug] All data cleared');
  }

  /**
   * Get active timers (operations that haven't completed)
   */
  public getActiveTimers(): string[] {
    return Array.from(this.activeTimers.keys());
  }

  /**
   * Check for potential memory leaks
   */
  public checkForLeaks(): {
    subscriptionLeaks: string[];
    excessiveUpdates: string[];
  } {
    const subscriptionLeaks = Array.from(this.subscriptions.values())
      .filter(s => s.count > 5)
      .map(s => `${s.name}: ${s.count} active subscriptions`);

    const excessiveUpdates = Array.from(this.stateUpdates.values())
      .filter(u => u.updateCount > 100)
      .map(u => `${u.storeName}: ${u.updateCount} updates`);

    if (subscriptionLeaks.length > 0 || excessiveUpdates.length > 0) {
      console.group('⚠️ Potential Performance Issues Detected');
      if (subscriptionLeaks.length > 0) {
        console.warn('Subscription Leaks:', subscriptionLeaks);
      }
      if (excessiveUpdates.length > 0) {
        console.warn('Excessive State Updates:', excessiveUpdates);
      }
      console.groupEnd();
    }

    return { subscriptionLeaks, excessiveUpdates };
  }
}

// Export singleton instance
export const perfDebug = PerformanceDebugger.getInstance();

// Convenience functions
export const startTimer = (name: string, captureStack?: boolean) =>
  perfDebug.startTimer(name, captureStack);
export const endTimer = (name: string) => perfDebug.endTimer(name);
export const trackSubscription = (name: string) =>
  perfDebug.trackSubscription(name);
export const trackUnsubscription = (name: string) =>
  perfDebug.trackUnsubscription(name);
export const trackStateUpdate = (
  storeName: string,
  keys: string[],
  size?: number
) => perfDebug.trackStateUpdate(storeName, keys, size);

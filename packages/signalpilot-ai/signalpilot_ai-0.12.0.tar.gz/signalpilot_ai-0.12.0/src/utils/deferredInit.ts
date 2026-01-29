/**
 * DeferredInit - Schedules work to run without blocking the main thread
 *
 * This utility ensures that JupyterLab's plugin activation can return quickly
 * by deferring all I/O and heavy computation to later in the event loop.
 *
 * Key insight: Simply using `void asyncFunc()` or removing `await` does NOT
 * make code non-blocking if the async function does synchronous work before
 * its first internal `await`. This scheduler uses setTimeout(0) to truly
 * yield to the event loop.
 */

type Priority = 'critical' | 'high' | 'normal' | 'idle';

interface DeferredTask {
  name: string;
  fn: () => Promise<void> | void;
  priority: Priority;
}

class DeferredInitScheduler {
  private criticalQueue: DeferredTask[] = [];
  private highQueue: DeferredTask[] = [];
  private normalQueue: DeferredTask[] = [];
  private idleQueue: DeferredTask[] = [];
  private isProcessing = false;
  private completedTasks = new Set<string>();
  private taskPromises = new Map<string, Promise<void>>();

  /**
   * Schedule a task to run later without blocking
   *
   * @param name - Unique name for the task (used for deduplication)
   * @param fn - The function to execute
   * @param priority - Task priority:
   *   - 'critical': Runs first via setTimeout(0), needed for basic UI
   *   - 'high': Runs after critical, important for functionality
   *   - 'normal': Runs during idle time via requestIdleCallback
   *   - 'idle': Runs when browser is truly idle, nice-to-have
   */
  schedule(
    name: string,
    fn: () => Promise<void> | void,
    priority: Priority = 'normal'
  ): Promise<void> {
    // Prevent duplicate scheduling
    if (this.completedTasks.has(name)) {
      console.log(`[DeferredInit] Task already completed: ${name}`);
      return Promise.resolve();
    }

    // Return existing promise if task is already scheduled
    if (this.taskPromises.has(name)) {
      console.log(`[DeferredInit] Task already scheduled: ${name}`);
      return this.taskPromises.get(name)!;
    }

    const task = { name, fn, priority };

    // Create a promise that will be resolved when the task completes
    let resolvePromise: () => void;
    let rejectPromise: (error: Error) => void;
    const promise = new Promise<void>((resolve, reject) => {
      resolvePromise = resolve;
      rejectPromise = reject;
    });

    // Wrap the function to handle promise resolution
    const wrappedFn = async () => {
      try {
        await fn();
        this.completedTasks.add(name);
        resolvePromise();
      } catch (error) {
        console.error(`[DeferredInit] Task failed: ${name}`, error);
        rejectPromise(error as Error);
      } finally {
        this.taskPromises.delete(name);
      }
    };

    task.fn = wrappedFn;
    this.taskPromises.set(name, promise);

    switch (priority) {
      case 'critical':
        this.criticalQueue.push(task);
        break;
      case 'high':
        this.highQueue.push(task);
        break;
      case 'normal':
        this.normalQueue.push(task);
        break;
      case 'idle':
        this.idleQueue.push(task);
        break;
    }

    console.log(`[DeferredInit] Scheduled ${priority}: ${name}`);

    if (!this.isProcessing) {
      this.startProcessing();
    }

    return promise;
  }

  /**
   * Wait for a specific task to complete
   */
  async waitFor(name: string): Promise<void> {
    if (this.completedTasks.has(name)) {
      return;
    }
    const promise = this.taskPromises.get(name);
    if (promise) {
      await promise;
    }
  }

  /**
   * Check if a task has completed
   */
  isCompleted(name: string): boolean {
    return this.completedTasks.has(name);
  }

  /**
   * Wait for all tasks of a specific priority or higher to complete
   */
  async waitForPriority(priority: Priority): Promise<void> {
    const priorities: Priority[] = ['critical', 'high', 'normal', 'idle'];
    const targetIndex = priorities.indexOf(priority);
    const relevantPriorities = priorities.slice(0, targetIndex + 1);

    const promises: Promise<void>[] = [];
    for (const [, promise] of this.taskPromises) {
      promises.push(promise);
    }
    await Promise.all(promises);
  }

  private startProcessing(): void {
    this.isProcessing = true;

    // Process critical tasks first using setTimeout(0) to yield to event loop
    if (this.criticalQueue.length > 0) {
      setTimeout(() => this.processCriticalQueue(), 0);
    } else if (this.highQueue.length > 0) {
      setTimeout(() => this.processHighQueue(), 0);
    } else if (this.normalQueue.length > 0) {
      this.scheduleIdleWork(() => this.processNormalQueue());
    } else if (this.idleQueue.length > 0) {
      this.scheduleIdleWork(() => this.processIdleQueue(), 5000);
    } else {
      this.isProcessing = false;
    }
  }

  private scheduleIdleWork(callback: () => void, timeout = 2000): void {
    if ('requestIdleCallback' in window) {
      (window as Window).requestIdleCallback(() => callback(), { timeout });
    } else {
      // Fallback for browsers without requestIdleCallback
      setTimeout(callback, 50);
    }
  }

  private async processCriticalQueue(): Promise<void> {
    // Process all critical tasks sequentially
    while (this.criticalQueue.length > 0) {
      const task = this.criticalQueue.shift()!;
      const start = performance.now();
      console.log(`[DeferredInit] Running critical: ${task.name}`);

      try {
        await task.fn();
        console.log(
          `[DeferredInit] Completed critical: ${task.name} (${(performance.now() - start).toFixed(1)}ms)`
        );
      } catch (error) {
        console.error(
          `[DeferredInit] Critical task failed: ${task.name}`,
          error
        );
      }

      // Yield between critical tasks to keep UI responsive
      await this.yieldToEventLoop();
    }
    this.startProcessing();
  }

  private async processHighQueue(): Promise<void> {
    // Process one high-priority task at a time, yielding between each
    const task = this.highQueue.shift();
    if (task) {
      const start = performance.now();
      console.log(`[DeferredInit] Running high: ${task.name}`);

      try {
        await task.fn();
        console.log(
          `[DeferredInit] Completed high: ${task.name} (${(performance.now() - start).toFixed(1)}ms)`
        );
      } catch (error) {
        console.error(`[DeferredInit] High task failed: ${task.name}`, error);
      }
    }

    // Yield to event loop, then continue
    setTimeout(() => this.startProcessing(), 0);
  }

  private async processNormalQueue(): Promise<void> {
    // Process in batches during idle time
    const batchSize = 2;
    const batch = this.normalQueue.splice(0, batchSize);

    for (const task of batch) {
      const start = performance.now();
      console.log(`[DeferredInit] Running normal: ${task.name}`);

      try {
        await task.fn();
        console.log(
          `[DeferredInit] Completed normal: ${task.name} (${(performance.now() - start).toFixed(1)}ms)`
        );
      } catch (error) {
        console.error(`[DeferredInit] Normal task failed: ${task.name}`, error);
      }

      // Yield between tasks
      await this.yieldToEventLoop();
    }

    this.startProcessing();
  }

  private async processIdleQueue(): Promise<void> {
    const task = this.idleQueue.shift();
    if (task) {
      const start = performance.now();
      console.log(`[DeferredInit] Running idle: ${task.name}`);

      try {
        await task.fn();
        console.log(
          `[DeferredInit] Completed idle: ${task.name} (${(performance.now() - start).toFixed(1)}ms)`
        );
      } catch (error) {
        console.error(`[DeferredInit] Idle task failed: ${task.name}`, error);
      }
    }
    this.startProcessing();
  }

  private yieldToEventLoop(): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, 0));
  }

  /**
   * Reset the scheduler (useful for testing)
   */
  reset(): void {
    this.criticalQueue = [];
    this.highQueue = [];
    this.normalQueue = [];
    this.idleQueue = [];
    this.isProcessing = false;
    this.completedTasks.clear();
    this.taskPromises.clear();
  }

  /**
   * Get the current status of the scheduler
   */
  getStatus(): {
    isProcessing: boolean;
    queueSizes: Record<Priority, number>;
    completedCount: number;
    pendingCount: number;
  } {
    return {
      isProcessing: this.isProcessing,
      queueSizes: {
        critical: this.criticalQueue.length,
        high: this.highQueue.length,
        normal: this.normalQueue.length,
        idle: this.idleQueue.length
      },
      completedCount: this.completedTasks.size,
      pendingCount: this.taskPromises.size
    };
  }
}

// Export singleton instance
export const deferredInit = new DeferredInitScheduler();

// Export class for testing
export { DeferredInitScheduler };
export type { Priority, DeferredTask };

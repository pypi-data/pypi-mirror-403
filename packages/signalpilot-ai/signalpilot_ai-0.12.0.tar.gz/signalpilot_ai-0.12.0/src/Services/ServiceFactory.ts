import { IChatService } from '../LLM/IChatService';
import { AnthropicService } from '../LLM/Anthropic/AnthropicService';

/**
 * Types of available AI service providers
 */
export enum ServiceProvider {
  ANTHROPIC = 'claude'
}

/**
 * Factory for creating chat service instances
 */
export class ServiceFactory {
  private static instanceCache: Map<ServiceProvider, IChatService> = new Map();

  /**
   * Create or return a cached chat service instance based on provider type
   * @param provider The service provider to use
   * @returns An instance of IChatService
   */
  static createService(provider: ServiceProvider): IChatService {
    const cached = this.instanceCache.get(provider);
    if (cached) {
      return cached;
    }

    let instance: IChatService;
    switch (provider) {
      case ServiceProvider.ANTHROPIC:
        instance = new AnthropicService();
        break;
      default:
        throw new Error(`Unknown service provider: ${provider}`);
    }

    this.instanceCache.set(provider, instance);
    return instance;
  }
}

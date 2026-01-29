/**
 * Framework M Studio API Configuration
 *
 * Per ADR-0005, supports multiple deployment scenarios:
 * - Same Origin (default): /studio/api
 * - Subdomain: api.example.com
 * - CDN: Full URL in config
 */

export interface FrameworkConfig {
  apiBaseUrl: string;
  metaBaseUrl?: string;
  wsBaseUrl?: string;
}

// Read config from window or environment
declare global {
  interface Window {
    __FRAMEWORK_CONFIG__?: FrameworkConfig;
  }
}

const defaultConfig: FrameworkConfig = {
  // Use relative path to leverage Vite proxy in dev or same-origin in prod
  apiBaseUrl: "/studio/api",
  metaBaseUrl: "/studio/api",
};

export const config: FrameworkConfig = {
  ...defaultConfig,
  ...window.__FRAMEWORK_CONFIG__,
};

export const API_URL = config.apiBaseUrl;

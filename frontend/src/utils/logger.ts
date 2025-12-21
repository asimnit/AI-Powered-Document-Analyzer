/**
 * Logger Utility
 * 
 * Centralized logging for the frontend application.
 * Provides different log levels and formatted console output.
 * Can be extended to send logs to external services (Sentry, LogRocket, etc.)
 */

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface LogConfig {
  enableDebug: boolean;
  enableInfo: boolean;
  enableConsole: boolean;
}

class Logger {
  private config: LogConfig = {
    enableDebug: import.meta.env.DEV, // Only debug in development
    enableInfo: true,
    enableConsole: true,
  };

  /**
   * Get console style for log level
   */
  private getStyle(level: LogLevel): string {
    const styles = {
      debug: 'color: #6B7280; font-weight: normal',
      info: 'color: #3B82F6; font-weight: bold',
      warn: 'color: #F59E0B; font-weight: bold',
      error: 'color: #EF4444; font-weight: bold; font-size: 14px',
    };
    return styles[level];
  }

  /**
   * Debug level - Detailed information for debugging
   * Only logged in development mode
   */
  debug(message: string, data?: any): void {
    if (!this.config.enableDebug || !this.config.enableConsole) return;
    
    console.log(`%c🔍 ${message}`, this.getStyle('debug'), data || '');
  }

  /**
   * Info level - General informational messages
   */
  info(message: string, data?: any): void {
    if (!this.config.enableInfo || !this.config.enableConsole) return;
    
    console.log(`%cℹ️  ${message}`, this.getStyle('info'), data || '');
  }

  /**
   * Warning level - Something unexpected but not critical
   */
  warn(message: string, data?: any): void {
    if (!this.config.enableConsole) return;
    
    console.warn(`%c⚠️  ${message}`, this.getStyle('warn'), data || '');
  }

  /**
   * Error level - Error occurred
   */
  error(message: string, error?: any): void {
    if (!this.config.enableConsole) return;
    
    console.error(`%c❌ ${message}`, this.getStyle('error'), error || '');
    
    // In production, you might want to send errors to a service like Sentry
    // if (import.meta.env.PROD) {
    //   // Send to error tracking service
    // }
  }

  /**
   * API request logging
   */
  apiRequest(method: string, url: string, data?: any): void {
    this.debug(`API Request: ${method} ${url}`, data);
  }

  /**
   * API response logging
   */
  apiResponse(method: string, url: string, status: number, data?: any): void {
    if (status >= 200 && status < 300) {
      this.debug(`API Response: ${method} ${url} - ${status}`, data);
    } else if (status >= 400) {
      this.error(`API Error: ${method} ${url} - ${status}`, data);
    }
  }

  /**
   * User action logging
   */
  userAction(action: string, details?: any): void {
    this.info(`User Action: ${action}`, details);
  }

  /**
   * Navigation logging
   */
  navigation(from: string, to: string): void {
    this.debug(`Navigation: ${from} → ${to}`);
  }
}

// Export singleton instance
export const logger = new Logger();

// Export type for convenience
export type { LogLevel };

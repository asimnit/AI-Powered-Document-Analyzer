/**
 * WebSocket Hook for Real-Time Document Updates
 * 
 * Connects to the backend WebSocket endpoint and listens for document status updates
 */

import { useEffect, useRef, useState } from 'react';

interface DocumentUpdate {
  document_id: number;
  status: string;
  message?: string;
  chunks?: number;
  word_count?: number;
  language?: string;
}

interface WebSocketMessage {
  type: string;
  data: DocumentUpdate | any;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  lastUpdate: DocumentUpdate | null;
  error: string | null;
}

export const useWebSocket = (onDocumentUpdate?: (update: DocumentUpdate) => void): UseWebSocketReturn => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<DocumentUpdate | null>(null);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | undefined>(undefined);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;

  useEffect(() => {
    const connect = () => {
      const token = localStorage.getItem('access_token');
      
      console.log('🔍 useWebSocket: Checking for token...', token ? 'Token found' : 'No token');
      
      if (!token) {
        console.log('⚠️ No auth token available, skipping WebSocket connection');
        return;
      }

      // WebSocket URL - use ws:// for http and wss:// for https
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//localhost:8000/ws?token=${token}`;

      console.log('🔌 Connecting to WebSocket...', wsUrl.substring(0, 50) + '...');
      
      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          console.log('✅ WebSocket connected successfully');
          setIsConnected(true);
          setError(null);
          reconnectAttemptsRef.current = 0;
        };

        ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            console.log('📨 WebSocket message received:', message);

            if (message.type === 'document_status_update') {
              const update = message.data as DocumentUpdate;
              setLastUpdate(update);
              
              // Call the callback if provided
              if (onDocumentUpdate) {
                onDocumentUpdate(update);
              }
            } else if (message.type === 'connection_established') {
              console.log('🎉 Connection established:', message.data);
            } else if (message.type === 'heartbeat') {
              // Heartbeat response, no action needed
            }
          } catch (err) {
            console.error('❌ Error parsing WebSocket message:', err);
          }
        };

        ws.onerror = (event) => {
          console.error('❌ WebSocket error:', event);
          setError('WebSocket connection error');
        };

        ws.onclose = (event) => {
          console.log('🔌 WebSocket closed:', event.code, event.reason);
          setIsConnected(false);
          wsRef.current = null;

          // Attempt to reconnect if not deliberately closed
          if (event.code !== 1000 && reconnectAttemptsRef.current < maxReconnectAttempts) {
            reconnectAttemptsRef.current++;
            const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
            console.log(`🔄 Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})...`);
            
            reconnectTimeoutRef.current = setTimeout(() => {
              connect();
            }, delay);
          } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
            setError('Failed to connect after multiple attempts');
          }
        };
      } catch (err) {
        console.error('Error creating WebSocket:', err);
        setError('Failed to create WebSocket connection');
      }
    };

    // Initial connection
    connect();

    // Cleanup on unmount
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      
      if (wsRef.current) {
        console.log('🔌 Closing WebSocket connection');
        wsRef.current.close(1000, 'Component unmounting');
        wsRef.current = null;
      }
    };
  }, [onDocumentUpdate]);

  // Send heartbeat every 30 seconds to keep connection alive
  useEffect(() => {
    if (!isConnected || !wsRef.current) return;

    const heartbeatInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send('ping');
      }
    }, 30000);

    return () => clearInterval(heartbeatInterval);
  }, [isConnected]);

  return {
    isConnected,
    lastUpdate,
    error
  };
};

/**
 * Chat Window Component
 * 
 * Main chat area displaying messages and handling user input
 */

import React, { useEffect, useRef, useState } from 'react';
import { useChatStore } from '../store/chatStore';
import MessageBubble from './MessageBubble';
import ChatInput from './ChatInput';
import StoreSelector from './StoreSelector';

const ChatWindow: React.FC = () => {
  const {
    currentConversation,
    messages,
    attachedStores,
    askQuestion,
    askingQuestion,
    fetchMessages,
    fetchAttachedStores,
    attachStores,
    detachStore,
  } = useChatStore();

  const [showStoreSelector, setShowStoreSelector] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load messages and stores when conversation changes
  useEffect(() => {
    if (currentConversation) {
      fetchMessages(currentConversation.id);
      fetchAttachedStores(currentConversation.id);
    }
  }, [currentConversation?.id]);

  const handleSendMessage = async (content: string) => {
    if (!currentConversation) return;
    await askQuestion(currentConversation.id, content);
  };

  const handleAttachStores = async (storeIds: number[]) => {
    if (!currentConversation) return;
    await attachStores(currentConversation.id, storeIds);
    setShowStoreSelector(false);
  };

  const handleDetachStore = async (storeId: number) => {
    if (!currentConversation) return;
    await detachStore(currentConversation.id, storeId);
  };

  // No conversation selected
  if (!currentConversation) {
    return (
      <div className="h-full flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100">
        <div className="text-center">
          <div className="w-24 h-24 mx-auto mb-6 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center">
            <svg
              className="w-12 h-12 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-800 mb-2">
            Welcome to Chat
          </h2>
          <p className="text-gray-600">
            Select a conversation or create a new one to start chatting
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header with Attached Stores */}
      <div className="px-6 py-4 border-b border-gray-200 bg-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-800">
              {currentConversation.title || 'New Conversation'}
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              {currentConversation.messages?.length || 0} messages
            </p>
          </div>

          <button
            onClick={() => setShowStoreSelector(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
            Attach Stores ({attachedStores.length}/5)
          </button>
        </div>

        {/* Attached Stores */}
        {attachedStores.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {attachedStores.map((store) => (
              <div
                key={store.store_id}
                className="flex items-center gap-2 px-3 py-1 bg-purple-50 border border-purple-200 rounded-full text-sm"
              >
                <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
                  />
                </svg>
                <span className="font-medium text-purple-800">{store.store_name}</span>
                <span className="text-purple-600">({store.document_count})</span>
                <button
                  onClick={() => handleDetachStore(store.store_id)}
                  className="ml-1 text-purple-400 hover:text-purple-600"
                >
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center text-gray-500">
              {attachedStores.length === 0 ? (
                <>
                  <svg
                    className="w-16 h-16 mx-auto mb-4 text-gray-300"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
                    />
                  </svg>
                  <p className="text-lg font-medium mb-2">No stores attached</p>
                  <p className="text-sm">Attach document stores to start chatting</p>
                </>
              ) : (
                <>
                  <svg
                    className="w-16 h-16 mx-auto mb-4 text-gray-300"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                    />
                  </svg>
                  <p className="text-lg font-medium mb-2">Start the conversation</p>
                  <p className="text-sm">Ask a question about your documents</p>
                </>
              )}
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            {askingQuestion && (
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm font-medium">
                  AI
                </div>
                <div className="flex-1 p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-2 text-gray-500">
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-300 border-t-blue-500"></div>
                    <span className="text-sm">Thinking...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Chat Input */}
      <div className="border-t border-gray-200 bg-white p-4">
        <ChatInput
          onSend={handleSendMessage}
          disabled={attachedStores.length === 0 || askingQuestion}
          placeholder={
            attachedStores.length === 0
              ? 'Attach stores first...'
              : askingQuestion
              ? 'Waiting for response...'
              : 'Ask a question about your documents...'
          }
        />
      </div>

      {/* Store Selector Modal */}
      {showStoreSelector && (
        <StoreSelector
          currentStoreIds={attachedStores.map((s) => s.store_id)}
          onAttach={handleAttachStores}
          onClose={() => setShowStoreSelector(false)}
        />
      )}
    </div>
  );
};

export default ChatWindow;

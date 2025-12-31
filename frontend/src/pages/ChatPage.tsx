/**
 * Chat Page
 * 
 * Main chat interface with conversations sidebar and chat window
 */

import React, { useEffect, useState } from 'react';
import { useChatStore } from '../store/chatStore';
import ConversationList from '../components/ConversationList';
import ChatWindow from '../components/ChatWindow';

const ChatPage: React.FC = () => {
  const { fetchConversations } = useChatStore();
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    fetchConversations();
  }, []);

  return (
    <div className="h-[calc(100vh-8rem)] flex rounded-lg overflow-hidden shadow-lg bg-white">
        {/* Conversations Sidebar */}
        <div
          className={`${
            sidebarOpen ? 'w-80' : 'w-0'
          } transition-all duration-300 overflow-hidden border-r border-gray-200`}
        >
          <ConversationList />
        </div>

        {/* Toggle Sidebar Button */}
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="absolute top-20 left-0 z-10 bg-white border border-gray-200 rounded-r-lg px-2 py-4 hover:bg-gray-50 transition-colors"
          style={{ left: sidebarOpen ? '20rem' : '0' }}
        >
          <svg
            className={`w-4 h-4 transition-transform ${sidebarOpen ? '' : 'rotate-180'}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
        </button>

        {/* Chat Window */}
        <div className="flex-1 flex flex-col">
          <ChatWindow />
        </div>
      </div>
  );
};

export default ChatPage;

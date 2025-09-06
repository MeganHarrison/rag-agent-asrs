'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, FileText, Info } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  tables?: string[];
  figures?: string[];
  topics?: string[];
}

export function FMGlobalChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const topics = [
    'fire_protection',
    'seismic_design',
    'rack_design',
    'crane_systems',
    'clearances',
    'cost_optimization'
  ];

  const exampleQuestions = [
    'What are the aisle width requirements for Class IV commodities?',
    'Show me Table 2-1 spacing requirements',
    'How can I optimize sprinkler costs?',
    'What seismic bracing is required?'
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = { role: 'user' as const, content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Use streaming endpoint for better UX
      const response = await fetch('/api/fm-global', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: input,
          asrs_topic: selectedTopic,
          conversation_history: messages.map(m => `${m.role}: ${m.content}`).slice(-6)
        }),
      });

      if (!response.ok) throw new Error('Failed to get response');

      const data = await response.json();
      
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.response,
        tables: data.tables_referenced,
        figures: data.figures_referenced,
        topics: data.asrs_topics
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.'
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExampleClick = (question: string) => {
    setInput(question);
  };

  return (
    <div className="flex flex-col h-[600px] max-w-4xl mx-auto bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-4 rounded-t-lg">
        <h2 className="text-xl font-bold">FM Global 8-34 ASRS Expert</h2>
        <p className="text-sm opacity-90">Fire Protection & Design Optimization Assistant</p>
      </div>

      {/* Topic Selection */}
      <div className="p-3 border-b bg-gray-50">
        <div className="flex flex-wrap gap-2">
          {topics.map(topic => (
            <button
              key={topic}
              onClick={() => setSelectedTopic(topic === selectedTopic ? null : topic)}
              className={`px-3 py-1 text-sm rounded-full transition-colors ${
                selectedTopic === topic
                  ? 'bg-blue-600 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100 border'
              }`}
            >
              {topic.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center py-8">
            <FileText className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-700 mb-2">
              Ask about FM Global 8-34 Requirements
            </h3>
            <p className="text-gray-500 mb-4">
              Get expert guidance on ASRS fire protection design
            </p>
            <div className="space-y-2">
              {exampleQuestions.map((question, idx) => (
                <button
                  key={idx}
                  onClick={() => handleExampleClick(question)}
                  className="block w-full text-left p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors text-sm"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((message, idx) => (
            <div
              key={idx}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[80%] p-3 rounded-lg ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                <p className="whitespace-pre-wrap">{message.content}</p>
                
                {/* Show references if available */}
                {message.tables && message.tables.length > 0 && (
                  <div className="mt-2 pt-2 border-t border-gray-300">
                    <span className="text-xs font-semibold">Tables: </span>
                    {message.tables.map((table, i) => (
                      <span key={i} className="text-xs bg-white/20 px-1 py-0.5 rounded mr-1">
                        {table}
                      </span>
                    ))}
                  </div>
                )}
                
                {message.figures && message.figures.length > 0 && (
                  <div className="mt-1">
                    <span className="text-xs font-semibold">Figures: </span>
                    {message.figures.map((figure, i) => (
                      <span key={i} className="text-xs bg-white/20 px-1 py-0.5 rounded mr-1">
                        {figure}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 p-3 rounded-lg">
              <Loader2 className="w-5 h-5 animate-spin" />
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t bg-gray-50">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about FM Global 8-34 requirements..."
            className="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-600"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
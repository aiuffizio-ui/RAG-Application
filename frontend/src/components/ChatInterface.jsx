import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, AlertCircle } from 'lucide-react';
import MessageBubble from './MessageBubble';
import SourceDisplay from './SourceDisplay';
import apiService from '../services/api';

export default function ChatInterface({ config }) {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!input.trim() || loading) return;

        const userMessage = input.trim();
        setInput('');
        setError(null);

        // Add user message
        setMessages((prev) => [...prev, { type: 'user', content: userMessage }]);
        setLoading(true);

        try {
            apiService.setApiKey(config.apiKey);

            if (config.stream) {
                // Streaming mode
                let aiMessage = { type: 'ai', content: '', sources: [] };
                let streamedContent = '';

                for await (const chunk of apiService.streamQuery(
                    userMessage,
                    config.topK
                )) {
                    if (chunk.type === 'sources') {
                        aiMessage.sources = chunk.data;
                    } else if (chunk.type === 'token') {
                        streamedContent += chunk.data;
                        setMessages((prev) => {
                            const newMessages = [...prev];
                            const lastMessage = newMessages[newMessages.length - 1];
                            if (lastMessage && lastMessage.type === 'ai') {
                                lastMessage.content = streamedContent;
                            } else {
                                newMessages.push({ ...aiMessage, content: streamedContent });
                            }
                            return newMessages;
                        });
                    } else if (chunk.type === 'error') {
                        setError(chunk.data);
                        aiMessage.fallback = chunk.fallback;
                        setMessages((prev) => [...prev, aiMessage]);
                    }
                }
            } else {
                // Non-streaming mode
                const response = await apiService.query(userMessage, config.topK);

                if (response.error) {
                    setError(response.error);
                    setMessages((prev) => [
                        ...prev,
                        {
                            type: 'ai',
                            content: 'Generation failed. See fallback docs below.',
                            fallback: response.fallback_docs,
                        },
                    ]);
                } else {
                    setMessages((prev) => [
                        ...prev,
                        {
                            type: 'ai',
                            content: response.answer,
                            sources: response.sources,
                        },
                    ]);
                }
            }
        } catch (err) {
            setError(err.message || 'Failed to get response');
            setMessages((prev) => [
                ...prev,
                {
                    type: 'ai',
                    content: 'Sorry, something went wrong. Please try again.',
                },
            ]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full bg-gradient-to-br from-gray-900 via-gray-900 to-black">
            {/* Header */}
            <div className="flex-shrink-0 border-b border-gray-800 bg-gray-900/50 backdrop-blur-sm">
                <div className="max-w-4xl mx-auto px-4 py-4">
                    <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                        Uffizio Knowledge Assistant
                    </h1>
                    <p className="text-sm text-gray-400 mt-1">
                        Ask me anything about Uffizio products
                    </p>
                </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-4 py-6">
                <div className="max-w-4xl mx-auto">
                    {messages.length === 0 && (
                        <div className="text-center py-12">
                            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 mb-4">
                                <span className="text-2xl">🤖</span>
                            </div>
                            <h2 className="text-xl font-semibold text-gray-300 mb-2">
                                Start a conversation
                            </h2>
                            <p className="text-gray-500">
                                Ask questions about Trakzee, SmartBus, SmartWaste, or any other
                                Uffizio product
                            </p>
                        </div>
                    )}

                    {messages.map((msg, idx) => (
                        <div key={idx}>
                            {msg.type === 'user' ? (
                                <MessageBubble message={msg.content} isUser={true} />
                            ) : (
                                <>
                                    {msg.sources && <SourceDisplay sources={msg.sources} />}
                                    <MessageBubble message={msg.content} isUser={false} />
                                    {msg.fallback && config.debug && (
                                        <div className="mb-4 p-4 rounded-lg bg-yellow-900/20 border border-yellow-700">
                                            <p className="text-xs font-medium text-yellow-400 mb-2">
                                                Fallback Documents:
                                            </p>
                                            {msg.fallback.map((doc, i) => (
                                                <pre
                                                    key={i}
                                                    className="text-xs text-gray-300 whitespace-pre-wrap mb-2"
                                                >
                                                    {JSON.stringify(doc, null, 2)}
                                                </pre>
                                            ))}
                                        </div>
                                    )}
                                </>
                            )}
                        </div>
                    ))}

                    {loading && !config.stream && (
                        <div className="flex justify-start mb-4">
                            <div className="bg-gray-800 rounded-2xl px-4 py-3 border border-gray-700">
                                <Loader2 className="w-5 h-5 text-purple-400 animate-spin" />
                            </div>
                        </div>
                    )}

                    {error && (
                        <div className="mb-4 p-4 rounded-lg bg-red-900/20 border border-red-700 flex items-start gap-3">
                            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                            <div>
                                <p className="text-sm font-medium text-red-400">Error</p>
                                <p className="text-sm text-red-300">{error}</p>
                            </div>
                        </div>
                    )}

                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* Input */}
            <div className="flex-shrink-0 border-t border-gray-800 bg-gray-900/50 backdrop-blur-sm">
                <div className="max-w-4xl mx-auto px-4 py-4">
                    <form onSubmit={handleSubmit} className="flex gap-2">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="Ask a question..."
                            disabled={loading}
                            className="flex-1 px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
                        />
                        <button
                            type="submit"
                            disabled={loading || !input.trim()}
                            className="px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium flex items-center gap-2"
                        >
                            {loading ? (
                                <Loader2 className="w-5 h-5 animate-spin" />
                            ) : (
                                <Send className="w-5 h-5" />
                            )}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
}

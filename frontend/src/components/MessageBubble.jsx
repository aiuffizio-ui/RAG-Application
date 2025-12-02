import React from 'react';

export default function MessageBubble({ message, isUser }) {
    return (
        <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
            <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${isUser
                        ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white'
                        : 'bg-gray-800 text-gray-100 border border-gray-700'
                    }`}
            >
                <p className="text-sm whitespace-pre-wrap">{message}</p>
            </div>
        </div>
    );
}

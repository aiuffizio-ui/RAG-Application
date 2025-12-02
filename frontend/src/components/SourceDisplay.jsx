import React, { useState } from 'react';
import { ExternalLink, ChevronDown, ChevronUp } from 'lucide-react';

export default function SourceDisplay({ sources }) {
    const [expanded, setExpanded] = useState(false);

    if (!sources || sources.length === 0) {
        return null;
    }

    return (
        <div className="mb-4 rounded-xl bg-gray-800/50 border border-gray-700 overflow-hidden">
            <button
                onClick={() => setExpanded(!expanded)}
                className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-gray-800/80 transition-colors"
            >
                <span className="text-sm font-medium text-gray-300">
                    Sources ({sources.length})
                </span>
                {expanded ? (
                    <ChevronUp className="w-4 h-4 text-gray-400" />
                ) : (
                    <ChevronDown className="w-4 h-4 text-gray-400" />
                )}
            </button>

            {expanded && (
                <div className="px-4 pb-4 space-y-2">
                    {sources.map((source, idx) => (
                        <div
                            key={idx}
                            className="p-3 rounded-lg bg-gray-900/50 border border-gray-700 hover:border-gray-600 transition-colors"
                        >
                            <div className="flex items-start justify-between gap-2">
                                <div className="flex-1">
                                    <p className="text-xs font-mono text-purple-400 mb-1">
                                        {source.chunk_id}
                                    </p>
                                    <p className="text-sm text-gray-300 line-clamp-2">
                                        {source.snippet}
                                    </p>
                                    {source.score !== undefined && (
                                        <p className="text-xs text-gray-500 mt-1">
                                            Score: {source.score.toFixed(4)}
                                        </p>
                                    )}
                                </div>
                                <ExternalLink className="w-4 h-4 text-gray-500 flex-shrink-0" />
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

import React, { useState, useEffect } from 'react';
import ChatInterface from './components/ChatInterface';
import Settings from './components/Settings';
import apiService from './services/api';
import { Database, AlertCircle } from 'lucide-react';

function App() {
    const [config, setConfig] = useState({
        apiKey: apiService.getApiKey(),
        topK: 8,
        stream: true,
        debug: false,
    });

    const [healthStatus, setHealthStatus] = useState(null);

    useEffect(() => {
        apiService.setApiKey(config.apiKey);
    }, [config.apiKey]);

    useEffect(() => {
        // Check health on mount
        apiService
            .health()
            .then((data) => setHealthStatus(data))
            .catch((err) => setHealthStatus({ status: 'error', error: err.message }));
    }, []);

    return (
        <div className="h-screen flex flex-col bg-gray-900">
            {/* Top bar with health status and settings */}
            <div className="flex-shrink-0 bg-gray-900 border-b border-gray-800 px-4 py-2 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    {healthStatus && (
                        <div className="flex items-center gap-2 text-xs">
                            {healthStatus.status === 'ok' ? (
                                <>
                                    <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                                    <span className="text-gray-400">
                                        {healthStatus.index_present ? 'Index Ready' : 'No Index'}
                                    </span>
                                    {!healthStatus.index_present && (
                                        <span className="text-yellow-500 flex items-center gap-1">
                                            <AlertCircle className="w-3 h-3" />
                                            Run ingestion first
                                        </span>
                                    )}
                                </>
                            ) : (
                                <>
                                    <div className="w-2 h-2 rounded-full bg-red-500" />
                                    <span className="text-red-400">Backend Offline</span>
                                </>
                            )}
                        </div>
                    )}
                </div>

                <div className="flex items-center gap-2">
                    <a
                        href="https://github.com/uffizio"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-gray-500 hover:text-gray-400 transition-colors"
                    >
                        Powered by Uffizio
                    </a>
                    <Settings config={config} onConfigChange={setConfig} />
                </div>
            </div>

            {/* Main chat interface */}
            <div className="flex-1 overflow-hidden">
                <ChatInterface config={config} />
            </div>
        </div>
    );
}

export default App;

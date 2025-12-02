import React, { useState } from 'react';
import { Settings as SettingsIcon, X } from 'lucide-react';

export default function Settings({ config, onConfigChange }) {
    const [isOpen, setIsOpen] = useState(false);

    const handleChange = (key, value) => {
        onConfigChange({ ...config, [key]: value });
    };

    return (
        <>
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="p-2 rounded-lg bg-gray-800 hover:bg-gray-700 border border-gray-700 transition-colors"
                title="Settings"
            >
                <SettingsIcon className="w-5 h-5 text-gray-300" />
            </button>

            {isOpen && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
                    <div className="bg-gray-900 rounded-2xl border border-gray-700 p-6 w-full max-w-md shadow-2xl">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-xl font-bold text-white">Settings</h2>
                            <button
                                onClick={() => setIsOpen(false)}
                                className="p-1 rounded-lg hover:bg-gray-800 transition-colors"
                            >
                                <X className="w-5 h-5 text-gray-400" />
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-2">
                                    API Key
                                </label>
                                <input
                                    type="password"
                                    value={config.apiKey}
                                    onChange={(e) => handleChange('apiKey', e.target.value)}
                                    className="w-full px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                                    placeholder="Enter your API key"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-2">
                                    Top K Results ({config.topK})
                                </label>
                                <input
                                    type="range"
                                    min="1"
                                    max="20"
                                    value={config.topK}
                                    onChange={(e) => handleChange('topK', parseInt(e.target.value))}
                                    className="w-full accent-purple-600"
                                />
                            </div>

                            <div className="flex items-center justify-between">
                                <label className="text-sm font-medium text-gray-300">
                                    Enable Streaming
                                </label>
                                <button
                                    onClick={() => handleChange('stream', !config.stream)}
                                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${config.stream ? 'bg-purple-600' : 'bg-gray-700'
                                        }`}
                                >
                                    <span
                                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${config.stream ? 'translate-x-6' : 'translate-x-1'
                                            }`}
                                    />
                                </button>
                            </div>

                            <div className="flex items-center justify-between">
                                <label className="text-sm font-medium text-gray-300">
                                    Debug Mode
                                </label>
                                <button
                                    onClick={() => handleChange('debug', !config.debug)}
                                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${config.debug ? 'bg-purple-600' : 'bg-gray-700'
                                        }`}
                                >
                                    <span
                                        className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${config.debug ? 'translate-x-6' : 'translate-x-1'
                                            }`}
                                    />
                                </button>
                            </div>
                        </div>

                        <button
                            onClick={() => setIsOpen(false)}
                            className="w-full mt-6 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all font-medium"
                        >
                            Save Changes
                        </button>
                    </div>
                </div>
            )}
        </>
    );
}

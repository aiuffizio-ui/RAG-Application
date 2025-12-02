import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

class ApiService {
    constructor() {
        this.client = axios.create({
            baseURL: API_BASE_URL,
            headers: {
                'Content-Type': 'application/json',
            },
        });
    }

    setApiKey(apiKey) {
        if (apiKey) {
            this.client.defaults.headers.common['x-api-key'] = apiKey;
            localStorage.setItem('apiKey', apiKey);
        }
    }

    getApiKey() {
        return localStorage.getItem('apiKey') || '';
    }

    async query(queryText, topK = 8, maxTokens = 1024, stream = false) {
        if (stream) {
            return this.streamQuery(queryText, topK, maxTokens);
        }

        const response = await this.client.post('/query', {
            query: queryText,
            top_k: topK,
            max_tokens: maxTokens,
            stream: false,
        });

        return response.data;
    }

    async *streamQuery(queryText, topK = 8, maxTokens = 1024) {
        const response = await fetch(`${API_BASE_URL}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'x-api-key': this.getApiKey(),
            },
            body: JSON.stringify({
                query: queryText,
                top_k: topK,
                max_tokens: maxTokens,
                stream: true,
            }),
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value);
            const lines = chunk.split('\n').filter(line => line.trim());

            for (const line of lines) {
                try {
                    const data = JSON.parse(line);
                    yield data;
                } catch (e) {
                    console.error('Failed to parse chunk:', line);
                }
            }
        }
    }

    async ingest() {
        const response = await this.client.post('/ingest');
        return response.data;
    }

    async reindex() {
        const response = await this.client.post('/reindex');
        return response.data;
    }

    async health() {
        const response = await this.client.get('/health');
        return response.data;
    }

    async getMetadata(chunkId) {
        const response = await this.client.get(`/metadata/${chunkId}`);
        return response.data;
    }
}

export default new ApiService();

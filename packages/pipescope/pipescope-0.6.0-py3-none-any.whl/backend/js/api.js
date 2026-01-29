// PipeScope: Pipeline visualization for CPU microarchitecture traces
//
// Copyright (c) 2026 Microprocessor R&D Center (MPRC), Peking University
// SPDX-License-Identifier: MulanPSL-2.0
//
// Author: Chun Yang

// API request function
async function fetchJSON(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers,
            },
            ...options,
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

export const api = {
    // Health check
    async health() {
        return fetchJSON('/api/health');
    },

    // Get version information
    async version() {
        return fetchJSON('/api/version');
    },

    // Get configuration
    async getConfig() {
        return fetchJSON('/api/config');
    },

    // Get trace data
    async getTrace() {
        return fetchJSON('/api/trace');
    },
};

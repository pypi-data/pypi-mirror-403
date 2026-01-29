// PipeScope: Pipeline visualization for CPU microarchitecture traces
//
// Copyright (c) 2026 Microprocessor R&D Center (MPRC), Peking University
// SPDX-License-Identifier: MulanPSL-2.0
//
// Author: Chun Yang
//         Ziqing Lin

// Main application logic

import { api } from './api.js';
import { PipelineCanvas } from './canvas.js';
import { VerticalScrollbar, HorizontalScrollbar } from './scrollbar.js';

const { createApp } = Vue;

const app = createApp({
    template: `
        <div id="app">
            <header class="header">
                <h1>PipeScope <span class="version-badge" v-if="version">v{{ version }}</span></h1>
                <p>Pipeline Visualization for CPU Microarchitecture Traces</p>
            </header>
            <main class="main">
                <div class="toolbar">
                </div>
                <div class="canvas-container">
                    <div class="canvas-wrapper">
                        <canvas ref="canvas" class="canvas"></canvas>
                    </div>
                    <div class="vscrollbar-container">
                        <button class="scrollbar-button scrollbar-up" ref="scrollbarUp">▲</button>
                        <div class="scrollbar-track" ref="scrollbarTrackV">
                            <div class="scrollbar-area">
                                <div class="vscrollbar-thumb" ref="scrollbarThumbV"></div>
                            </div>
                        </div>
                        <button class="scrollbar-button scrollbar-down" ref="scrollbarDown">▼</button>
                    </div>
                </div>
                <div class="hscrollbar-container">
                    <button class="scrollbar-button scrollbar-left" ref="scrollbarLeft">◄</button>
                    <div class="scrollbar-track" ref="scrollbarTrackH">
                        <div class="scrollbar-area">
                            <div class="hscrollbar-thumb" ref="scrollbarThumbH"></div>
                        </div>
                    </div>
                    <button class="scrollbar-button scrollbar-right" ref="scrollbarRight">►</button>
                </div>
            </main>
        </div>
    `,
    data() {
        return {
            scale: 1,
            version: null,
            canvas: null,
            vScrollbar: null,
            hScrollbar: null,
        };
    },
    async mounted() {
        try {
            // Get version
            const versionInfo = await api.version();
            this.version = versionInfo.version;

            // Initialize canvas
            const config = await api.getConfig();
            this.canvas = new PipelineCanvas(this.$refs.canvas, config.canvasTheme);

            // Initialize scrollbars
            this.hScrollbar = new HorizontalScrollbar(
                this.$refs.canvas,
                this.canvas,
                this.$refs.scrollbarTrackH,
                this.$refs.scrollbarThumbH,
                this.$refs.scrollbarLeft,
                this.$refs.scrollbarRight
            );
            this.vScrollbar = new VerticalScrollbar(
                this.$refs.canvas,
                this.canvas,
                this.$refs.scrollbarTrackV,
                this.$refs.scrollbarThumbV,
                this.$refs.scrollbarUp,
                this.$refs.scrollbarDown,
                this.hScrollbar
            );

            this.checkHealth();
            this.loadTrace();
        } catch (error) {
            console.error('Failed to initialize:', error);
        }
    },
    methods: {
        async checkHealth() {
            try {
                const result = await api.health();
                console.log('Backend health:', result);
            } catch (error) {
                console.error('Failed to connect to backend:', error);
            }
        },
        async loadTrace() {
            try {
                const instructions = await api.getTrace();
                console.log('Loaded', instructions.length, 'instructions');
                if (this.canvas) {
                    this.canvas.setInstBuffer(instructions);

                    // Update ranges for scrollbars
                    if (this.vScrollbar) {
                        this.vScrollbar.setTotalInsts(Math.max(1, instructions.length));
                    }
                }
            } catch (error) {
                console.error('Failed to load trace:', error);
            }
        },
    },
});

app.mount('#app');

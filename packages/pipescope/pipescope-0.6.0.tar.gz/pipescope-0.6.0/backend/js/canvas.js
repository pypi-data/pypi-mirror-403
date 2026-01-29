// PipeScope: Pipeline visualization for CPU microarchitecture traces
//
// Copyright (c) 2026 Microprocessor R&D Center (MPRC), Peking University
// SPDX-License-Identifier: MulanPSL-2.0
//
// Author: Ziqing Lin
//         Chun Yang

// Canvas drawing module

export class PipelineCanvas {
    constructor(canvasElement, theme) {
        this.canvas = canvasElement;
        this.theme = theme;
        this.ctx = canvasElement.getContext('2d');

        // Instruction data buffer
        this.instBuffer = [];
        this.instBaseIndex = 0;

        // Viewport state
        this.topInstOffset = 0;  // First visible instruction offset in instBuffer
        this.leftCycle = 0;  // First visible cycle
        this.viewInsts = 0;  // Number of visible instruction rows
        this.viewCycles = 0;  // Number of visible cycles
        this.viewLeftCycleMin = 0;  // First cycle of visible instructions
        this.viewLeftCycleMax = 1;  // Last cycle of visible instructions

        // Layout parameters
        this.CYCLE_AXIS_H = 30;
        this.INST_PANEL_W = 180;
        this.PER_INST_H = 24;
        this.PER_CYCLE_W = 20;

        this.setupEventListeners();
        this.resizeCanvas();
    }

    setInstBuffer(insts, baseIndex = 0) {
        // Set instruction data and redraw
        this.instBuffer = insts || [];
        this.instBaseIndex = baseIndex;

        // Update viewport and redraw
        this.updateViewport();
        this.draw();
    }

    getViewInsts() {
        return this.viewInsts;
    }

    getViewCycles() {
        return this.viewCycles;
    }

    getTopInstIndex() {
        return this.instBaseIndex + this.topInstOffset;
    }

    setTopInstIndex(index) {
        if (index < this.instBaseIndex)
            return;
        if (index >= this.instBaseIndex + this.instBuffer.length)
            return;

        this.topInstOffset = index - this.instBaseIndex;
        // TODO load more instructions if needed

        this.updateViewport();
        this.draw();
    }

    updateViewport() {
        if (this.instBuffer.length === 0)
            return;

        // Get visible area size
        const rect = this.canvas.getBoundingClientRect();
        const height = rect.height - this.CYCLE_AXIS_H;
        const width = rect.width - this.INST_PANEL_W;

        // Update viewable instructions and cycles
        const maxInsts = this.instBuffer.length - this.topInstOffset;
        this.viewInsts = Math.min(Math.floor(height / this.PER_INST_H), maxInsts);
        this.viewCycles = Math.ceil(width / this.PER_CYCLE_W);

        // Update cycle range for visible instructions
        this.viewLeftCycleMin = this.instBuffer[this.topInstOffset].beginCycle - 1;
        const endCycle = this.instBuffer[this.topInstOffset + this.viewInsts - 1].endCycle;
        this.viewLeftCycleMax = Math.max(endCycle - this.viewCycles, this.viewLeftCycleMin + 1);

        // Adjust the left cycle position if out of bounds
        if (this.leftCycle < this.viewLeftCycleMin) {
            this.leftCycle = this.viewLeftCycleMin;
        } else if (this.leftCycle > this.viewLeftCycleMax) {
            this.leftCycle = this.viewLeftCycleMax;
        }
    }

    getLeftCycleRatio() {
        const range = this.viewLeftCycleMax - this.viewLeftCycleMin;
        const offset = this.leftCycle - this.viewLeftCycleMin;
        const ratio = Math.max(0, Math.min(offset / range, 1));

        return ratio;
    }

    setLeftCycleByRatio(ratio) {
        const range = this.viewLeftCycleMax - this.viewLeftCycleMin;
        const offset = Math.round(ratio * range);
        this.leftCycle = this.viewLeftCycleMin + offset;

        this.draw();
    }

    scrollLeftCycle(delta) {
        const newCycle = this.leftCycle + delta;

        if (newCycle < this.viewLeftCycleMin) {
            this.leftCycle = this.viewLeftCycleMin;
        } else if (newCycle > this.viewLeftCycleMax) {
            this.leftCycle = this.viewLeftCycleMax;
        } else {
            this.leftCycle = newCycle;
        }

        this.draw();
    }

    setupEventListeners() {
        window.addEventListener('resize', () => this.resizeCanvas());
    }

    resizeCanvas() {
        const rect = this.canvas.parentElement.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        this.canvas.width = rect.width * dpr;
        this.canvas.height = rect.height * dpr;
        this.canvas.style.width = `${rect.width}px`;
        this.canvas.style.height = `${rect.height}px`;
        this.ctx.scale(dpr, dpr);

        this.updateViewport();
        this.draw();
    }

    draw() {
        const rect = this.canvas.getBoundingClientRect();

        // Draw cycle axis at top
        this.drawCycleAxis(rect.width);

        // Draw instruction panel at left
        this.drawInstPanel(rect.height);

        // Draw pipeline area
        this.drawPipeline(rect.width, rect.height);
    }

    drawCycleAxis(width) {
        // Cycle axis background
        this.ctx.fillStyle = this.theme.background;
        this.ctx.fillRect(0, 0, width, this.CYCLE_AXIS_H);

        // Cycle axis border
        this.ctx.beginPath();
        this.ctx.moveTo(0, this.CYCLE_AXIS_H - 0.5);
        this.ctx.lineTo(width, this.CYCLE_AXIS_H - 0.5);
        this.ctx.strokeStyle = this.theme.border;
        this.ctx.stroke();

        // Clipping area for cycle axis labels
        this.ctx.save();
        this.ctx.beginPath();
        this.ctx.rect(this.INST_PANEL_W, 0, width - this.INST_PANEL_W, this.CYCLE_AXIS_H);
        this.ctx.clip();

        // Draw cycle labels (multiples of 5, starting from 5)
        this.ctx.font = `${this.theme.fontSizeAxis}px ${this.theme.fontFamily}`;
        this.ctx.textBaseline = 'middle';
        this.ctx.textAlign = 'left';
        this.ctx.fillStyle = this.theme.textLight;

        // Find first multiple of 5 >= beginCycle
        const endCycle = this.leftCycle + this.viewCycles;
        const firstLabel = Math.ceil(this.leftCycle / 5) * 5;
        for (let t = firstLabel; t <= endCycle; t += 5) {
            if (t > 0) {
                const x = this.INST_PANEL_W + (t - this.leftCycle) * this.PER_CYCLE_W;
                this.ctx.fillText(t.toString(), x, this.CYCLE_AXIS_H / 2);
            }
        }

        this.ctx.restore();
    }

    drawInstPanel(height) {
        // Instruction panel background
        this.ctx.fillStyle = this.theme.background;
        this.ctx.fillRect(0, this.CYCLE_AXIS_H, this.INST_PANEL_W, height - this.CYCLE_AXIS_H);

        // Instruction panel border
        this.ctx.beginPath();
        this.ctx.moveTo(this.INST_PANEL_W - 0.5, this.CYCLE_AXIS_H);
        this.ctx.lineTo(this.INST_PANEL_W - 0.5, height);
        this.ctx.strokeStyle = this.theme.border;
        this.ctx.stroke();

        // Draw instruction labels
        this.ctx.font = `${this.theme.fontSizeLabel}px ${this.theme.fontFamily}`;
        this.ctx.textBaseline = 'middle';
        this.ctx.fillStyle = this.theme.textDark;

        // Only draw visible rows
        for (let i = 0; i < this.viewInsts; i++) {
            const inst = this.instBuffer[this.topInstOffset + i];
            const y = this.CYCLE_AXIS_H + i * this.PER_INST_H;

            // SN
            this.ctx.textAlign = 'right';
            this.ctx.fillStyle = this.theme.textLight;
            this.ctx.fillText(`#${inst.seqNum}`, 60, y + this.PER_INST_H / 2);

            // PC
            this.ctx.textAlign = 'left';
            this.ctx.fillStyle = this.theme.textDark;
            const pcText = inst.pc || '0x0';
            this.ctx.fillText(pcText, 75, y + this.PER_INST_H / 2);
        }
    }

    drawPipeline(width, height) {
        // Clipping area for pipeline
        this.ctx.save();
        this.ctx.beginPath();
        this.ctx.rect(this.INST_PANEL_W, this.CYCLE_AXIS_H, width - this.INST_PANEL_W, height - this.CYCLE_AXIS_H);
        this.ctx.clip();

        // Clear background
        this.ctx.fillStyle = this.theme.pipelineBg;
        this.ctx.fillRect(this.INST_PANEL_W, this.CYCLE_AXIS_H, width - this.INST_PANEL_W, height - this.CYCLE_AXIS_H);

        // Transform for scrolling and offset
        this.ctx.translate(this.INST_PANEL_W - this.leftCycle * this.PER_CYCLE_W, this.CYCLE_AXIS_H);

        // Draw grid for visible range
        this.drawGrid();

        // Draw stage boxes for visible instructions
        this.drawInsts();

        this.ctx.restore();
    }

    drawGrid() {
        const end = this.leftCycle + this.viewCycles;
        const h = this.viewInsts * this.PER_INST_H;

        // Vertical grid lines (cycles)
        // Light grid lines
        this.ctx.strokeStyle = this.theme.gridLight;
        this.ctx.beginPath();
        for (let t = this.leftCycle; t <= end; t++) {
            if (t % 5 !== 0) {  // Skip multiples of 5
                const x = t * this.PER_CYCLE_W;
                this.ctx.moveTo(x, 0);
                this.ctx.lineTo(x, h);
            }
        }
        this.ctx.stroke();

        // Dark grid lines for multiples of 5
        this.ctx.strokeStyle = this.theme.gridDark;
        this.ctx.beginPath();
        for (let t = this.leftCycle; t <= end; t++) {
            if (t % 5 === 0) {
                const x = t * this.PER_CYCLE_W;
                this.ctx.moveTo(x, 0);
                this.ctx.lineTo(x, h);
            }
        }
        this.ctx.stroke();

        // Horizontal grid lines (instructions)
        this.ctx.strokeStyle = this.theme.gridLight;
        this.ctx.beginPath();
        for (let i = 0; i <= this.viewInsts; i++) {
            const y = i * this.PER_INST_H;
            this.ctx.moveTo(this.leftCycle * this.PER_CYCLE_W, y);
            this.ctx.lineTo(end * this.PER_CYCLE_W, y);
        }
        this.ctx.stroke();
    }

    drawInsts() {
        const endCycle = this.leftCycle + this.viewCycles;
        const h = this.PER_INST_H - 4;

        // Setup label text style
        this.ctx.font = `12px ${this.theme.fontFamily}`;
        this.ctx.textBaseline = 'middle';

        for (let i = 0; i < this.viewInsts; i++) {
            const inst = this.instBuffer[this.topInstOffset + i];
            const y = i * this.PER_INST_H;

            if (!inst.stageCycles || inst.stageCycles.length === 0) {
                continue;
            }

            // Draw PC at the beginning of the first stage
            const beginX = (inst.beginCycle - 1) * this.PER_CYCLE_W;
            this.ctx.textAlign = 'right';
            this.ctx.fillStyle = this.theme.textDark;
            this.ctx.fillText(inst.pc || '0x0', beginX, y + h / 2 + 2);

            // Draw each stage as a box
            let start = inst.beginCycle;
            for (let stage = 0; stage < inst.stageCycles.length; stage++) {
                // Determine stage end cycle
                let end;
                if (stage < inst.stageCycles.length - 1) {
                    // Next stage starts after this stage's duration
                    end = start + inst.stageCycles[stage + 1];
                } else {
                    // Last stage lasts 1 cycle
                    end = start + 1;
                }

                // Calculate box position and size
                const duration = end - start;
                const x = start * this.PER_CYCLE_W;
                const w = duration * this.PER_CYCLE_W;

                // Only draw if stage overlaps with visible cycle range
                if (end > this.leftCycle && start < endCycle) {
                    const color = this.theme.stageColors[stage % this.theme.stageColors.length];
                    this.ctx.fillStyle = color;
                    this.ctx.fillRect(x, y + 2, w - 1, h);

                    // Draw duration label for stages longer than 5 cycles
                    if (duration > 5) {
                        this.ctx.textAlign = 'left';
                        this.ctx.fillStyle = this.theme.textDark;
                        this.ctx.fillText(`×${duration}`, x + 4, y + h / 2 + 2);
                    }
                }

                // Next stage starts where this stage ends
                start = end;
            }
        }
    }
}

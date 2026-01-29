// PipeScope: Pipeline visualization for CPU microarchitecture traces
//
// Copyright (c) 2026 Microprocessor R&D Center (MPRC), Peking University
// SPDX-License-Identifier: MulanPSL-2.0
//
// Author: Chun Yang

// Scrollbars for pipeline canvas

export class VerticalScrollbar {
    constructor(canvasDOM, canvasObject, track, thumb, up, down, hScrollbar) {
        this.canvasDOM = canvasDOM;  // DOM element for event listeners
        this.canvas = canvasObject;  // PipelineCanvas object
        this.track = track;
        this.thumb = thumb;
        this.upButton = up;
        this.downButton = down;
        this.hScrollbar = hScrollbar;

        this.totalInsts = 0;

        // Drag state
        this.isDragging = false;
        this.dragStartY = 0;
        this.dragStartInstIndex = 0;

        this.setupEventListeners();
    }

    setTotalInsts(total) {
        this.totalInsts = total;
        this.updatePosition(this.canvas.getTopInstIndex());
    }

    setupEventListeners() {
        // Thumb drag
        this.thumb.addEventListener('mousedown', (e) => this.handleThumbDragStart(e));

        // Track click
        this.track.addEventListener('click', (e) => this.handleTrackClick(e));

        // Canvas wheel
        this.canvasDOM.addEventListener('wheel', (e) => this.handleWheel(e));

        // Keyboard events
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));

        // Up and down buttons
        this.upButton.addEventListener('click', () => this.handlePageUp());
        this.downButton.addEventListener('click', () => this.handlePageDown());
    }

    handleThumbDragStart(e) {
        e.preventDefault();
        this.isDragging = true;
        this.dragStartY = e.clientY;
        this.dragStartInstIndex = this.canvas.getTopInstIndex();

        document.addEventListener('mousemove', (moveE) => this.handleThumbDragMove(moveE));
        document.addEventListener('mouseup', () => this.handleThumbDragEnd());
    }

    handleThumbDragMove(e) {
        if (!this.isDragging) return;

        const deltaY = e.clientY - this.dragStartY;
        const trackHeight = this.track.clientHeight;
        const thumbHeight = this.thumb.clientHeight;
        const draggableHeight = trackHeight - thumbHeight;

        if (draggableHeight <= 0) return;

        const ratio = deltaY / draggableHeight;
        const delta = Math.round(ratio * this.totalInsts);
        const newInstIndex = this.dragStartInstIndex + delta;
        this.scrollToInstIndex(newInstIndex);
    }

    handleThumbDragEnd() {
        this.isDragging = false;
        document.removeEventListener('mousemove', (moveE) => this.handleThumbDragMove(moveE));
        document.removeEventListener('mouseup', () => this.handleThumbDragEnd());
    }

    handleTrackClick(e) {
        const rect = this.track.getBoundingClientRect();
        const clickY = e.clientY - rect.top;
        const trackHeight = rect.height;

        const ratio = clickY / trackHeight;
        const newInstIndex = Math.round(ratio * this.totalInsts);
        this.scrollToInstIndex(newInstIndex);
    }

    handleWheel(e) {
        // If Shift is pressed, let horizontal scrollbar handle it
        if (e.shiftKey)
            return;

        e.preventDefault();

        const delta = e.deltaY > 0 ? 3 : -3;
        const newInstIndex = this.canvas.getTopInstIndex() + delta;
        this.scrollToInstIndex(newInstIndex);
    }

    handleKeyDown(e) {
        if (e.key === 'PageUp') {
            e.preventDefault();
            this.handlePageUp();
        } else if (e.key === 'PageDown') {
            e.preventDefault();
            this.handlePageDown();
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            this.handleLineUp();
        } else if (e.key === 'ArrowDown') {
            e.preventDefault();
            this.handleLineDown();
        }
    }

    handleLineUp() {
        const newInstIndex = this.canvas.getTopInstIndex() -1;
        this.scrollToInstIndex(newInstIndex);
    }

    handleLineDown() {
        const newInstIndex = this.canvas.getTopInstIndex() + 1;
        this.scrollToInstIndex(newInstIndex);
    }

    handlePageUp() {
        const pageSize = this.canvas.getViewInsts() - 3;
        const delta = -Math.max(1, pageSize);
        const newInstIndex = this.canvas.getTopInstIndex() + delta;
        this.scrollToInstIndex(newInstIndex);
    }

    handlePageDown() {
        const pageSize = this.canvas.getViewInsts() - 3;
        const delta = Math.max(1, pageSize);
        const newInstIndex = this.canvas.getTopInstIndex() + delta;
        this.scrollToInstIndex(newInstIndex);
    }

    scrollToInstIndex(instIndex) {
        let clampedIndex = instIndex;
        if (instIndex < 0) {
            clampedIndex = 0;
        } else if (instIndex >= this.totalInsts) {
            clampedIndex = this.totalInsts - 1;
        }

        this.canvas.setTopInstIndex(clampedIndex);
        this.updatePosition(clampedIndex);

        // Also update horizontal scrollbar position
        const ratio = this.canvas.getLeftCycleRatio();
        this.hScrollbar.updatePosition(ratio);
    }

    // Update thumb position based on instruction index
    updatePosition(instIndex) {
        const trackHeight = this.track.clientHeight;
        const thumbHeight = this.thumb.clientHeight;
        const draggableHeight = trackHeight - thumbHeight;

        const ratio = instIndex / Math.max(1, this.totalInsts);
        const thumbTop = Math.max(0, Math.min(ratio * draggableHeight, draggableHeight));

        this.thumb.style.top = thumbTop + 'px';
    }
}

export class HorizontalScrollbar {
    constructor(canvasDOM, canvasObject, track, thumb, left, right) {
        this.canvasDOM = canvasDOM;  // DOM element for event listeners
        this.canvas = canvasObject;  // PipelineCanvas object
        this.track = track;
        this.thumb = thumb;
        this.leftButton = left;
        this.rightButton = right;

        // Drag state
        this.isDragging = false;
        this.dragStartX = 0;
        this.dragStartCycle = 0;

        this.setupEventListeners();
    }

    setupEventListeners() {
        // Thumb drag
        this.thumb.addEventListener('mousedown', (e) => this.handleThumbDragStart(e));

        // Track click
        this.track.addEventListener('click', (e) => this.handleTrackClick(e));

        // Canvas wheel with shift
        this.canvasDOM.addEventListener('wheel', (e) => this.handleWheel(e));

        // Keyboard events
        document.addEventListener('keydown', (e) => this.handleKeyDown(e));

        // Left and right buttons
        this.leftButton.addEventListener('click', () => this.handlePageLeft());
        this.rightButton.addEventListener('click', () => this.handlePageRight());
    }

    handleThumbDragStart(e) {
        e.preventDefault();
        this.isDragging = true;
        this.dragStartX = e.clientX;
        this.dragStartRatio = this.canvas.getLeftCycleRatio();

        document.addEventListener('mousemove', (moveE) => this.handleThumbDragMove(moveE));
        document.addEventListener('mouseup', () => this.handleThumbDragEnd());
    }

    handleThumbDragMove(e) {
        if (!this.isDragging) return;

        const deltaX = e.clientX - this.dragStartX;
        const trackWidth = this.track.clientWidth;
        const thumbWidth = this.thumb.clientWidth;
        const draggableWidth = trackWidth - thumbWidth;

        if (draggableWidth <= 0) return;

        const ratioDelta = deltaX / draggableWidth;
        const newRatio = Math.max(0, Math.min(this.dragStartRatio + ratioDelta, 1));
        this.scrollToRatio(newRatio);
    }

    handleThumbDragEnd() {
        this.isDragging = false;
        document.removeEventListener('mousemove', (moveE) => this.handleThumbDragMove(moveE));
        document.removeEventListener('mouseup', () => this.handleThumbDragEnd());
    }

    handleTrackClick(e) {
        const rect = this.track.getBoundingClientRect();
        const clickX = e.clientX - rect.left;
        const trackWidth = rect.width;

        const ratio = Math.max(0, Math.min(clickX / trackWidth, 1));
        this.scrollToRatio(ratio);
    }

    scrollToRatio(ratio) {
        this.canvas.setLeftCycleByRatio(ratio);
        this.updatePosition(ratio);
    }

    handleWheel(e) {
        // Only handle if Shift key is pressed
        if (!e.shiftKey)
            return;

        e.preventDefault();

        const delta = e.deltaY > 0 ? 5 : -5;
        this.canvas.scrollLeftCycle(delta);

        const ratio = this.canvas.getLeftCycleRatio();
        this.updatePosition(ratio);
    }

    handleKeyDown(e) {
        if (e.key === 'ArrowLeft') {
            e.preventDefault();
            this.handleLineLeft();
        } else if (e.key === 'ArrowRight') {
            e.preventDefault();
            this.handleLineRight();
        }
    }

    handleLineLeft() {
        this.canvas.scrollLeftCycle(-1);

        const ratio = this.canvas.getLeftCycleRatio();
        this.updatePosition(ratio);
    }

    handleLineRight() {
        this.canvas.scrollLeftCycle(1);

        const ratio = this.canvas.getLeftCycleRatio();
        this.updatePosition(ratio);
    }

    handlePageLeft() {
        const pageSize = Math.max(1, this.canvas.getViewCycles() - 5);
        this.canvas.scrollLeftCycle(-pageSize);

        const ratio = this.canvas.getLeftCycleRatio();
        this.updatePosition(ratio);
    }

    handlePageRight() {
        const pageSize = Math.max(1, this.canvas.getViewCycles() - 5);
        this.canvas.scrollLeftCycle(pageSize);

        const ratio = this.canvas.getLeftCycleRatio();
        this.updatePosition(ratio);
    }

    // Update thumb position based on ratio (0-1)
    updatePosition(ratio) {
        const trackWidth = this.track.clientWidth;
        const thumbWidth = this.thumb.clientWidth;
        const draggableWidth = trackWidth - thumbWidth;

        const thumbLeft = Math.max(0, Math.min(ratio * draggableWidth, draggableWidth));

        this.thumb.style.left = thumbLeft + 'px';
    }
}

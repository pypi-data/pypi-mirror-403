# PipeScope: Pipeline visualization for CPU microarchitecture traces
#
# Copyright (c) 2026 Microprocessor R&D Center (MPRC), Peking University
# SPDX-License-Identifier: MulanPSL-2.0
#
# Author: Chun Yang

"""Application configuration."""

from pathlib import Path
from dataclasses import dataclass, field
from pydantic_settings import BaseSettings


@dataclass
class CanvasTheme:
    """Canvas theme configuration."""

    # Color configuration
    background: str = "#f8f9fa"
    border: str = "#e1e4e8"
    text_dark: str = "#24292e"
    text_light: str = "#6a737d"
    grid_light: str = "#f0f0f0"
    grid_dark: str = "#d0d0d0"
    pipeline_bg: str = "#ffffff"
    stage_colors: list = field(
        default_factory=lambda: [
            "#6db3ff",
            "#9dd689",
            "#ffdb7d",
            "#ffb366",
            "#a8d8d8",
            "#ff99d9",
        ]
    )
    # Font configuration
    font_family: str = '"JetBrains Mono", Consolas, monospace'
    font_size_label: int = 12  # Instruction labels
    font_size_axis: int = 11  # Cycle axis labels

    def to_dict(self) -> dict:
        return {
            "background": self.background,
            "border": self.border,
            "textDark": self.text_dark,
            "textLight": self.text_light,
            "gridLight": self.grid_light,
            "gridDark": self.grid_dark,
            "pipelineBg": self.pipeline_bg,
            "stageColors": self.stage_colors,
            "fontFamily": self.font_family,
            "fontSizeLabel": self.font_size_label,
            "fontSizeAxis": self.font_size_axis,
        }


class Settings(BaseSettings):
    """Application settings."""

    # Server settings
    debug: bool = True
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = True

    # Trace file settings
    trace_file: Path

    class Config:
        """Pydantic config."""

        env_file = ".env"

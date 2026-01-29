# PipeScope: Pipeline visualization for CPU microarchitecture traces
#
# Copyright (c) 2026 Microprocessor R&D Center (MPRC), Peking University
# SPDX-License-Identifier: MulanPSL-2.0
#
# Author: Ziqing Lin
#         Chun Yang

"""Instruction record for CPU microarchitecture traces."""

from dataclasses import dataclass, field


@dataclass
class InstRec:
    """Instruction record data class."""

    seq_num: int
    pc: int
    begin_cycle: int
    stage_cycles: list[int] = field(default_factory=list)

    @property
    def end_cycle(self) -> int:
        return self.begin_cycle + sum(self.stage_cycles) + 1

    @classmethod
    def from_line(cls, line: str) -> "InstRec":
        parts = line.strip().split(" ")
        assert parts

        # Parse header (#SN:PC)
        header = parts[0]
        assert header[0] == "#" and ":" in header
        seq_num, pc = header[1:].split(":")

        # Parse stage cycles
        stage_cycles = []
        for p in parts[1:]:
            assert p.endswith(":0")  # start event only
            cycle = int(p.split(":")[0])
            stage_cycles.append(cycle)

        # Compute begin cycle
        assert stage_cycles
        begin = stage_cycles[0]
        stage_cycles[0] = 0

        return cls(int(seq_num), int(pc, 16), begin, stage_cycles)

    def to_dict(self) -> dict:
        return {
            "seqNum": self.seq_num,
            "pc": hex(self.pc),
            "beginCycle": self.begin_cycle,
            "endCycle": self.end_cycle,
            "stageCycles": self.stage_cycles,
        }

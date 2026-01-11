# Unified RTL Pipeline Controller with Formal Verification

> A formally verified pipeline controller for RISC-style processors with complete hazard detection, forwarding, and optimal scheduling

**Author:** Vulli Sharanya  
**Date:** November 2025

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Control Dependency Graph](#control-dependency-graph)
- [Scheduling Algorithms](#scheduling-algorithms)
- [Resource Binding](#resource-binding)
- [Verilog Implementation](#verilog-implementation)
- [Formal Verification](#formal-verification)
- [Usage](#usage)

---

## 🎯 Overview

This project develops a **unified pipeline controller** that manages all stage-level control signals centrally for pipelined processors. The controller applies High-Level Synthesis (HLS) principles for systematic scheduling and binding of control operations, and is formally verified using CTL/LTL temporal logic.

### Key Innovations

- **Centralized Control Architecture** - All pipeline stages managed from a single controller
- **Formal Verification** - Model-checked using NuSMV with CTL/LTL properties
- **Optimized Scheduling** - Force-Directed Scheduling (FDS) minimizes resource usage
- **Complete Hazard Handling** - RAW hazards, load-use stalls, forwarding, and flushing
- **Graph-Based Design** - Control Dependency Graph (CDG) ensures correct ordering

---

## ✨ Features

### Control Signals (23 Total)

**IF Stage:**
- `IF:PC_src`, `IF:PCWrite`, `IF:IF_ID_Write`, `IF:Flush_IF_ID`

**ID Stage:**
- `ID:RegWrite`, `ID:RegDst`, `ID:ImmSrc`, `ID:Bubble`, `ID:Stall`, `ID:ID_EX_Flush`

**EX Stage:**
- `EX:ALUOp`, `EX:ALUSrc`, `EX:Branch`, `EX:BranchZero`, `EX:BranchTaken`
- `EX:FwdA`, `EX:FwdB`, `EX:Jump`, `EX:TargetAddrReady`

**MEM Stage:**
- `MEM:MemRead`, `MEM:MemWrite`, `MEM:FwdC`

**WB Stage:**
- `WB:MemToReg`

### Hazard Detection & Resolution

- ✅ **Load-Use Hazards** - Automatic stall insertion
- ✅ **RAW Hazards** - EX and MEM stage forwarding
- ✅ **Branch Hazards** - Pipeline flushing on taken branches
- ✅ **Jump Hazards** - IF/ID stage flushing

---

## 📊 Control Dependency Graph

The CDG formally represents how pipeline control signals influence one another across stages. It enables:

- Correct control ordering and timing identification
- Cycle detection for rescheduling
- Topological sorting for deterministic control generation
- Multi-level logic optimization

### Adjacency List Structure

```python
adj_list = {
    "IF:PC_src": ["ID:RegWrite", "ID:RegDst", "EX:ALUOp", ...],
    "IF:PCWrite": ["IF:IF_ID_Write", "IF:Flush_IF_ID"],
    "ID:RegWrite": ["EX:FwdA", "EX:FwdB", "MEM:FwdC"],
    # ... (see full implementation in document)
}
```

### Visualization

The CDG is visualized as a layered graph with:
- **5 pipeline stages** (IF, ID, EX, MEM, WB)
- **23 control signal nodes**
- **Color-coded stages** for clarity
- **Directed edges** showing dependencies

---

## 🔧 Scheduling Algorithms

### ASAP (As Soon As Possible)

Schedules operations at the earliest possible cycle while respecting dependencies.

```
control_step(oi) = max(control_step(oj)) + 1
where oj is predecessor of oi
```

### ALAP (As Late As Possible)

Schedules operations at the latest cycle within constraints.

```
control_step(oi) = min(control_step(oj)) - 1
where oj is successor of oi
```

### FDS (Force-Directed Scheduling)

Balances operations across time steps to minimize resource conflicts.

**Key Metrics:**
- `iINTERVAL = [iASAP, iALAP]` - Flexible scheduling window
- `Pi,j = 1/iRANGE` - Probability of scheduling at step j
- `Ck,j = Σ Pi,j` - Resource demand at step j

### Critical Path

**Total Delay:** 8 steps

```
Instruction_Decode(0) → MemToReg(1) → RegWrite(2) → 
FwdA/FwdB(3) → ALUSrc(4) → ALUOp(5) → BranchZero(6) → 
BranchTaken(7) → PC_src/Flush_IF_ID/ID_EX_Flush(8)
```

---

## 🏗️ Resource Binding

### Hardware Modules

| Module | Type | Stage | Signals |
|--------|------|-------|---------|
| **InstructionDecoder** | Combinational | IF/ID | opcode, funct, rs, rt, rd |
| **ControlDecoder** | Combinational | ID | RegWrite, RegDst, ImmSrc, Branch, Jump |
| **ForwardingUnit** | Comparator Array | ID/EX | FwdA, FwdB, FwdC |
| **ALUController** | Combinational | EX | ALUOp, ALUSrc |
| **HazardUnit** | Comparator + Logic | ID | Bubble, PCWrite, IF_ID_Write |
| **BranchUnit** | Comparator + Logic | EX | BranchTaken, PC_src |
| **FlushController** | Combinational | IF/ID/EX | Flush_IF_ID, ID_EX_Flush |

---

## 💻 Verilog Implementation

### Optimized vs Unoptimized

| Metric | Unoptimized | Optimized | Improvement |
|--------|-------------|-----------|-------------|
| **Gate Count** | ~850 gates | ~420 gates | **50.6% reduction** |
| **Critical Path** | ~3.5 ns | ~1.8 ns | **48.6% faster** |
| **Max Frequency** | ~285 MHz | ~555 MHz | **94.7% increase** |

### Optimization Techniques

1. **Common Subexpression Elimination** - Reduced redundant comparisons
2. **Instruction Type Factorization** - Shared decode logic
3. **Logic Minimization** - Consolidated case statements
4. **Flattened Conditionals** - Reduced nesting depth
5. **Boolean Simplification** - Optimized branch logic
6. **Redundant Logic Removal** - Eliminated duplicate checks

### Module Interface

```verilog
module pipeline_controller (
    input wire clk, reset,
    
    // Instruction inputs
    input wire [31:0] IF_instruction, ID_instruction,
    input wire [5:0] ID_opcode, ID_funct,
    input wire [4:0] ID_rs, ID_rt, EX_rd, MEM_rd, WB_rd,
    
    // Pipeline register inputs
    input wire EX_RegWrite, MEM_RegWrite, WB_RegWrite,
    input wire EX_MemRead, MEM_MemRead, EX_MemToReg,
    
    // Branch/Jump inputs
    input wire Zero, branch_condition,
    
    // Control outputs (23 signals)
    output reg [1:0] RegDst, MemToReg, ForwardA, ForwardB, ForwardC,
    output reg [2:0] ALUOp,
    output reg ALUSrc, Branch, MemRead, MemWrite, RegWrite,
    output reg Jump, Stall, Bubble, BranchZero, BranchTaken,
    output reg PCWrite, IF_ID_Write, Flush_IF_ID, ID_EX_Flush,
    output reg [1:0] PC_src,
    output reg TargetAddrReady
);
```

---

## ✅ Formal Verification

### CTL/LTL Properties

All properties verified using **NuSMV model checker** with **ZERO counterexamples**.

#### Safety Properties (AG - Always Globally)

| ID | Property | Specification |
|----|----------|---------------|
| **S1** | No ERROR state | `AG(state ≠ ERROR)` |
| **S2** | Load-use causes stall | `AG(load_use_hazard → AX(Stall))` |
| **S3** | Stall freezes PC | `AG(Stall → ¬PCWrite)` |
| **S4** | Stall creates bubble | `AG(Stall → Bubble)` |
| **S5** | Stall/Flush exclusive | `AG(¬(Stall ∧ Flush))` |
| **S6** | ForwardA exclusive | `AG(¬(ForwardA=FWD_EX ∧ ForwardA=FWD_MEM))` |
| **S7** | ForwardB exclusive | `AG(¬(ForwardB=FWD_EX ∧ ForwardB=FWD_MEM))` |

#### Liveness Properties (F - Eventually)

| ID | Property | Specification |
|----|----------|---------------|
| **L1** | Stalls resolve | `G(Stall → F(¬Stall))` |
| **L2** | Flushes return to normal | `G(Flush → F(state=NORMAL))` |
| **L3** | PC makes progress | `G(F(PCWrite))` |
| **L4** | Stall reaches forwarding | `AG(STALL_LOAD → AF(FORWARD_MEM_STAGE))` |

#### Hazard Handling

| ID | Property | Specification |
|----|----------|---------------|
| **H1** | EX hazard forwards | `AG(FORWARD_EX_STAGE ∧ raw_hazard_ex → ForwardA=FWD_EX)` |
| **H2** | MEM hazard forwards | `AG(FORWARD_MEM_STAGE ∧ raw_hazard_mem → ForwardA=FWD_MEM)` |
| **H3** | Post-stall forwarding | `AG(STALL_LOAD → AX(FORWARD_MEM_STAGE))` |
| **H4** | Branch flushes | `AG(branch_taken ∧ is_branch → AX(FLUSH_BRANCH))` |

### FSM States

```
NORMAL → {FORWARD_EX_STAGE, FORWARD_MEM_STAGE, 
          STALL_LOAD, FLUSH_BRANCH, FLUSH_JUMP}
```

---

## 🚀 Usage

### 1. Generate Control Dependency Graph

```bash
python cdg_generator.py
```

**Outputs:**
- `CDG_Adjacency_Matrix.csv` - Adjacency matrix
- `CDG_Clean_Layered.png` - Visualization

### 2. Run FDS Scheduling

```bash
python fds_scheduler.py
```

**Outputs:**
- `Complete_Schedule.csv` - Full scheduling table
- `FDS_Schedule.txt` - Resource assignments
- `FDS_Schedule_Gantt.png` - Timeline visualization
- `Resource_Utilization.png` - Resource usage chart

### 3. Simulate Verilog Design

```bash
iverilog -o pipeline_sim pipeline_controller.v tb_pipeline_controller.v
vvp pipeline_sim
gtkwave waveform.vcd
```

### 4. Run Formal Verification

```bash
NuSMV pipeline_controller.smv
```

**Expected Output:**
```
-- specification AG (state != ERROR) is true
-- specification AG (load_use_hazard -> AX(Stall)) is true
...
*** All 25 properties verified successfully ***
```

---

## 🛠️ Requirements

### Software
- **Verilog Simulator:** Icarus Verilog / ModelSim / Vivado
- **Model Checker:** NuSMV 2.6+
- **Python:** 3.8+ (with numpy, pandas, matplotlib, networkx)
- **Waveform Viewer:** GTKWave

### Installation

```bash
# Install Python dependencies
pip install numpy pandas matplotlib networkx

# Install NuSMV (Ubuntu/Debian)
sudo apt-get install nusmv

# Install Icarus Verilog
sudo apt-get install iverilog gtkwave
```


## 👤 Author

**Vulli Sharanya**  
November 2025

---

## 🌟 Acknowledgments

- Formal verification techniques based on NuSMV model checker
- Scheduling algorithms adapted from HLS literature
- Graph visualization using NetworkX library

---

**⭐ Star this repository if you find it useful!**

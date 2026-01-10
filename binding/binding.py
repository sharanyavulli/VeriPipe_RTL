# mips_datapath_and_resources.py
# Requires: pip install graphviz
# Also require Graphviz system installed and on PATH (dot.exe)

from graphviz import Digraph
import json

# --------------------------
# Build Graphviz diagram
# --------------------------
dot = Digraph("MIPS_Pipeline", filename="mips_datapath", format="svg")
dot.attr(rankdir="LR", splines="ortho", fontsize="12", nodesep="0.6", ranksep="1.0")

# default node style
dot.attr("node", shape="box", style="filled,rounded", fillcolor="#f2f2f2", fontname="Helvetica")

# ---------- IF stage cluster ----------
with dot.subgraph(name="cluster_IF") as c:
    c.attr(label="IF", color="#b3d9ff")
    c.node("PC", "Program Counter\n(PC)", shape="box")
    c.node("PC4", "PC + 4", shape="circle", fillcolor="#fff2cc")
    c.node("IMEM", "Instruction\nMemory", shape="box")

dot.node("IF_ID", "IF/ID\nPipeline Register", shape="box", width="0.6", height="4.5", fillcolor="#ffffff")

# ---------- ID stage cluster ----------
with dot.subgraph(name="cluster_ID") as c:
    c.attr(label="ID", color="#d9f2d9")
    c.node("RegFile", "Register File\n(read ports & write port)", shape="box")
    c.node("SignExt", "Sign-Extend\n(immediate)", shape="box")
    c.node("MainCtrl", "Main Control\n(decoder)", shape="ellipse", fillcolor="#ffd1dc")
    c.node("Hazard", "Hazard\nDetection Unit", shape="ellipse", fillcolor="#fff2cc")
    c.node("STALL_NODE", "STALL\nControl Signal", shape="ellipse", fillcolor="#ffe6cc")

dot.node("ID_EX", "ID/EX\nPipeline Register", shape="box", width="0.6", height="4.5", fillcolor="#ffffff")

# ---------- EX stage cluster ----------
with dot.subgraph(name="cluster_EX") as c:
    c.attr(label="EX", color="#ffd9b3")
    c.node("RegDstMUX", "RegDst\nMux", shape="oval", fillcolor="#ffe6cc")
    c.node("ALUSrcMUX", "ALUSrc\nMux", shape="oval", fillcolor="#ffe6cc")
    c.node("ALU", "ALU", shape="box")
    c.node("ALUCtrl", "ALU Control\n(funct + ALUOp)", shape="ellipse", fillcolor="#ffd1dc")
    c.node("PCTarget", "PC Target\n(ShiftLeft2 + Add)", shape="box")
    c.node("PCSrcMUX", "PCSrc\nMux", shape="oval", fillcolor="#ffe6cc")

dot.node("EX_MEM", "EX/MEM\nPipeline Register", shape="box", width="0.6", height="4.5", fillcolor="#ffffff")

# ---------- MEM stage cluster ----------
with dot.subgraph(name="cluster_MEM") as c:
    c.attr(label="MEM", color="#ffe6f2")
    c.node("DMEM", "Data Memory", shape="box")
    c.node("FwdC_MUX", "FwdC\nMux (store data)", shape="oval", fillcolor="#ffe6cc")

dot.node("MEM_WB", "MEM/WB\nPipeline Register", shape="box", width="0.6", height="4.5", fillcolor="#ffffff")

# ---------- WB stage cluster ----------
with dot.subgraph(name="cluster_WB") as c:
    c.attr(label="WB", color="#e6e6ff")
    c.node("WBMux", "WB Mux\n( MemToReg )", shape="oval", fillcolor="#ffe6cc")

# ---------- Forwarding and other control units ----------
dot.node("ForwardUnit", "Forwarding\nUnit", shape="ellipse", fillcolor="#fff2cc")

# --------------------------
# Connections (wires)
# --------------------------

# IF stage wiring
dot.edge("PC", "IMEM", label="addr")
dot.edge("PC", "PC4", label="PC+4")
dot.edge("IMEM", "IF_ID", label="Instruction")
dot.edge("PC4", "IF_ID", label="PC+4")

# IF/ID → ID stage
dot.edge("IF_ID", "MainCtrl", label="opcode")
dot.edge("IF_ID", "RegFile", label="rs, rt (read indices)")
dot.edge("IF_ID", "SignExt", label="instr[15:0]")

# MainControl → ID/EX
dot.edge("MainCtrl", "ID_EX",
         label="RegWrite_cand\nRegDst_cand\nALUSrc_cand\nALUOp_cand\nMemRead_cand\nMemWrite_cand\nMemToReg_cand\nBranch_cand")

# RegFile outputs -> ID/EX
dot.edge("RegFile", "ID_EX", label="ReadData1\nReadData2\nrs, rt, rd")

# SignExt -> ID/EX
dot.edge("SignExt", "ID_EX", label="SignExtImm")

# Hazard inputs
dot.edge("IF_ID", "Hazard", label="rs, rt")
dot.edge("ID_EX", "Hazard", label="ID/EX.rt, ID/EX.MemRead")

# Hazard outputs
dot.edge("Hazard", "IF_ID", label="IF_ID_Write / Flush_IF_ID")
dot.edge("Hazard", "PC", label="PCWrite")
dot.edge("Hazard", "ID_EX", label="ID_EX_Flush (bubble)")

# NEW — Stall output
dot.edge("Hazard", "STALL_NODE", label="Stall (NEW)")
dot.edge("STALL_NODE", "ID_EX", label="Stall pipeline (freeze)")

# ID/EX -> EX
dot.edge("ID_EX", "RegDstMUX", label="rd, rt selection")
dot.edge("ID_EX", "ALUSrcMUX", label="regB vs imm")
dot.edge("ID_EX", "ALUCtrl", label="funct")
dot.edge("ALUCtrl", "ALU", label="ALUOp")
dot.edge("RegDstMUX", "EX_MEM", label="DestReg")
dot.edge("ALUSrcMUX", "ALU", label="ALU B input")
dot.edge("ID_EX", "ALU", label="ALU A input (ReadData1)")

# Forwarding unit
dot.edge("EX_MEM", "ForwardUnit", label="EX/MEM.RegWrite & Dest")
dot.edge("MEM_WB", "ForwardUnit", label="MEM/WB.RegWrite & Dest")
dot.edge("ForwardUnit", "RegDstMUX", label="(if needed)")
dot.edge("ForwardUnit", "ALUSrcMUX", label="forward selects")
dot.edge("ForwardUnit", "FwdC_MUX", label="FwdC select for store-data")
dot.edge("ForwardUnit", "ALU", label="FwdA/FwdB selects")

# ALU -> EX/MEM
dot.edge("ALU", "EX_MEM", label="ALUResult")

# Branch path
dot.edge("ID_EX", "PCTarget", label="PC+offset (from signext)")
dot.edge("PCTarget", "PCSrcMUX", label="TargetAddr")
dot.edge("PCSrcMUX", "PC", label="PC next")
dot.edge("ID_EX", "PCSrcMUX", label="Branch_cand")
dot.edge("ALU", "PCSrcMUX", label="Zero flag")

# EX/MEM -> MEM
dot.edge("EX_MEM", "FwdC_MUX", label="store-data in")
dot.edge("EX_MEM", "DMEM", label="Addr / control")
dot.edge("FwdC_MUX", "DMEM", label="WriteData")
dot.edge("EX_MEM", "MEM_WB", label="forward controls & ALUResult")

# MEM -> WB
dot.edge("DMEM", "MEM_WB", label="ReadData")
dot.edge("MEM_WB", "WBMux", label="MemToReg_cand, ALUResult")

# WB -> RegFile
dot.edge("WBMux", "RegFile", label="WriteBack (RegWrite)")

# Invisible spacing
dot.edge("IF_ID", "ID_EX", style="invis")
dot.edge("ID_EX", "EX_MEM", style="invis")
dot.edge("EX_MEM", "MEM_WB", style="invis")

# Render diagram
dot.render(cleanup=True)
print("Generated diagram: mips_datapath.svg")

# --------------------------
# Resource map (text output)
# --------------------------
resource_map = {
    "PC":                "PC_Unit",
    "PCSrcMUX":          "PC_MUX",
    "PCWrite":           "HazardUnit / MergeLogic",

    "IF_ID":             "PipelineLatch_IF_ID",
    "IF_ID_Write":       "HazardUnit",

    # NEW — stall
    "Stall":             "HazardUnit",

    "MainControl": {
        "RegWrite_cand": "MainControl",
        "RegDst_cand":   "MainControl",
        "ALUSrc_cand":   "MainControl",
        "ALUOp_cand":    "MainControl",
        "MemRead_cand":  "MainControl",
        "MemWrite_cand": "MainControl",
        "MemToReg_cand": "MainControl",
        "Branch_cand":   "MainControl"
    },

    "ID_EX":             "PipelineLatch_ID_EX",

    "RegDstMUX":         "RegDst_Mux",
    "ALUSrcMUX":         "ALUSrc_Mux",
    "ALUControl":        "ALU_Control",
    "ALU":               "ALU",
    "PCTarget":          "BranchAdder",
    "PCSrcMux":          "PC_MUX",
    "ForwardUnit":       "ForwardUnit",

    "EX_MEM":            "PipelineLatch_EX_MEM",

    "DataMemory":        "DataMemory",
    "FwdC_MUX":          "FwdC_Mux",

    "MEM_WB":            "PipelineLatch_MEM_WB",

    "WBMux":             "WB_Mux",
    "RegFile_Write":     "RegFile_WritePort",

    "HazardUnit":        "HazardUnit",
    "ForwardingUnit":    "ForwardUnit",
}

# Write map
with open("resource_map.txt", "w") as f:
    f.write("MIPS Pipeline Resource Map\n")
    f.write("==========================\n\n")
    json.dump(resource_map, f, indent=2)

print("Wrote resource_map.txt")

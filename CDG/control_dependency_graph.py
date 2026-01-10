adj_list = {
    # IF-stage: fetched instruction determines decode & downstream controls
    "IF:PC_src": [
        "ID:RegWrite", "ID:RegDst", "ID:ImmSrc", "ID:ID_EX_Flush", "ID:Bubble",
        "EX:ALUOp", "EX:ALUSrc", "EX:Branch", "EX:BranchZero",
        "MEM:MemRead", "MEM:MemWrite",
        "WB:MemToReg"
    ],

    # PC update controls whether IF/ID can be written or flushed this cycle
    "IF:PCWrite": [
        "IF:IF_ID_Write",
        "IF:Flush_IF_ID"
    ],

    # Writing IF/ID loads a new instruction into decode (affects all decode outputs)
    "IF:IF_ID_Write": [
        "ID:RegWrite", "ID:RegDst", "ID:ImmSrc", "ID:Bubble", "ID:ID_EX_Flush",
        "IF:Flush_IF_ID"
    ],

    # Flushing IF/ID clears decode outputs
    "IF:Flush_IF_ID": [
        "ID:RegWrite", "ID:RegDst", "ID:ImmSrc", "ID:Bubble", "ID:ID_EX_Flush"
    ],

    # ID-stage decode outputs used by forwarding / later stages
    "ID:RegWrite": [
        "EX:FwdA", "EX:FwdB", "MEM:FwdC"
    ],

    "ID:RegDst": [
        "EX:ALUSrc", "EX:ALUOp"
    ],

    # ImmSrc (I/S/B/J) is produced by decoding opcode; it drives immediate selection in EX
    "ID:ImmSrc": [
        "EX:ALUSrc"
    ],
    "ID:Stall": [
        "IF:PCWrite",       # freeze PC update
        "IF:IF_ID_Write",   # freeze IF/ID register
        "ID:Bubble"         # insert bubble in ID stage
    ],
    # Bubble (stall) cancels/holds several signals
    "ID:Bubble": [
        "IF:PCWrite", "IF:IF_ID_Write", "ID:ID_EX_Flush",
        "EX:ALUSrc", "EX:ALUOp"
    ],

    # Flushing ID/EX (killing instruction entering EX)
    "ID:ID_EX_Flush": [
        "EX:ALUSrc", "EX:ALUOp", "EX:Branch", "EX:BranchZero", "EX:BranchTaken"
    ],

    # Forwarding selects influence ALU input selection and ALU operation usage
    "EX:FwdA": [
        "EX:ALUSrc", "EX:ALUOp"
    ],
    "EX:FwdB": [
        "EX:ALUSrc", "EX:ALUOp"
    ],

    # ALUSrc selects immediate vs register; branch-zero depends on ALU result usage
    "EX:ALUSrc": [
        "EX:ALUOp", "EX:BranchZero"
    ],

    # ALUOp (decoded function) affects branch-zero interpretation (if any)
    "EX:ALUOp": [
        "EX:BranchZero"
    ],

    # Branch signals produce the final BranchTaken decision (computed in EX)
    "EX:Branch": [
        "EX:BranchTaken"
    ],
    "EX:BranchZero": [
        "EX:BranchTaken"
    ],

    # When branch decision is known, it redirects/fires flushes/PC update
    "EX:BranchTaken": [
        "IF:PC_src", "IF:PCWrite", "IF:Flush_IF_ID", "ID:ID_EX_Flush"
    ],

    # Target ready allows PC update/selection
    "EX:TargetAddrReady": [
        "IF:PC_src", "IF:PCWrite"
    ],

    # Jumps also redirect & flush decode
    "EX:Jump": [
        "IF:PC_src", "IF:Flush_IF_ID", "ID:ID_EX_Flush"
    ],

    # MEM-stage: loads cause forwarding and load-use stalls (next-cycle stall effects)
    # NOTE: the t+1 semantics should be time-indexed during scheduling (see notes below)
    "MEM:MemRead": [
        "EX:FwdA", "EX:FwdB", "MEM:FwdC",
        "ID:Bubble",        # (t+1) load-use stall: bubble inserted in the next cycle
        "IF:PCWrite",       # (t+1) PC update inhibited next cycle when stalling
        "IF:IF_ID_Write"    # (t+1) IF/ID write inhibited next cycle when stalling
    ],

    # Stores produce MEM writes but do not (in this design) drive other control signals
    "MEM:MemWrite": [
        # intentionally empty
    ],

    # Forward store-data from MEM to EX (for store data hazard)
    "MEM:FwdC": [
        "EX:FwdA", "EX:FwdB"
    ],

    # WB selection (MemToReg) affects register write semantics / forwarding
    "WB:MemToReg": [
        "ID:RegWrite", "EX:FwdA", "EX:FwdB"
    ]
}
import numpy as np
import pandas as pd

# ---- adjacency list defined above ----
adj = adj_list

# Collect all unique nodes
nodes = sorted(set(adj.keys()) | {v for values in adj.values() for v in values})

# Create index mapping
idx = {node: i for i, node in enumerate(nodes)}

# Create NxN matrix
N = len(nodes)
matrix = np.zeros((N, N), dtype=int)

# Fill matrix: edge u -> v means matrix[u][v] = 1
for u in adj:
    for v in adj[u]:
        matrix[idx[u], idx[v]] = 1

# Print the matrix
print("Adjacency Matrix:\n")
print(pd.DataFrame(matrix, index=nodes, columns=nodes))

# Save to CSV
pd.DataFrame(matrix, index=nodes, columns=nodes).to_csv("CDG_Adjacency_Matrix.csv")

# Save to TXT
with open("CDG_Adjacency_Matrix.txt", "w") as f:
    f.write(pd.DataFrame(matrix, index=nodes, columns=nodes).to_string())

print("\nFiles saved: CDG_Adjacency_Matrix.csv and CDG_Adjacency_Matrix.txt")
import networkx as nx
import matplotlib.pyplot as plt
import textwrap

# --------------------------
# Build graph from adjacency list
# --------------------------
G = nx.DiGraph()
for u in adj_list:
    for v in adj_list[u]:
        G.add_edge(u, v)

# --------------------------
# Assign each node to a pipeline stage column
# --------------------------
stage_x = {"IF": 0, "ID": 1, "EX": 2, "MEM": 3, "WB": 4}
y_count = {"IF": 0, "ID": 0, "EX": 0, "MEM": 0, "WB": 0}

pos = {}
node_colors = []

colors = {
    "IF": "#F4B183",
    "ID": "#A9D08E",
    "EX": "#FFD966",
    "MEM": "#9BC2E6",
    "WB": "#CDA0D9",
}

# Place nodes cleanly in layers
for node in sorted(G.nodes()):
    stage = node.split(":")[0]
    x = stage_x[stage]
    y = -y_count[stage] * 2.0 - 2    # shifted down to prevent graph top cutoff
    y_count[stage] += 1

    pos[node] = (x, y)
    node_colors.append(colors[stage])

# Wrap long labels
labels = {n: "\n".join(textwrap.wrap(n, width=18)) for n in G.nodes()}

# --------------------------
# DRAW CLEAN, GLITCH-FREE CDG
# --------------------------
plt.figure(figsize=(26, 32))

nx.draw_networkx_nodes(G, pos,
                       node_color=node_colors,
                       edgecolors="black",
                       node_size=4200)

nx.draw_networkx_edges(G, pos,
                       arrows=True,
                       arrowsize=16,
                       connectionstyle="arc3,rad=0.15",
                       width=1.1)

nx.draw_networkx_labels(G, pos,
                        labels,
                        font_size=9)

# --------------------------
# Draw Stage Titles (Moved FAR Above)
# --------------------------
for stage, x in stage_x.items():
    plt.text(x, 4.5, stage, fontsize=22, fontweight="bold", ha="center")

plt.title("Control Dependency Graph (Clean Layered View)", fontsize=28, pad=40)

plt.axis("off")
plt.tight_layout(rect=[0, 0, 1, 0.97])   # extra top padding → removes glitch
plt.savefig("CDG_Clean_Layered.png", dpi=330)
plt.show()

print("Clean CDG saved as CDG_Clean_Layered.png")
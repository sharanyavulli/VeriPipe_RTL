# ======================================================================
# CORRECTED PIPELINE CONTROL SIGNAL SCHEDULER WITH FDS ALGORITHM
# ======================================================================
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd

# ============================================================================
# CRITICAL FIX: Remove time indices - treat each signal as SINGLE operation
# ============================================================================
# Original mistake: Having PC_src(t), PC_src(t+3) as separate nodes
# Correction: Single PC_src node, dependencies show logical relationships

# ------------------------------------------------------------
# 1) CDG — Control Dependencies (CORRECTED - No Time Indices)
# ------------------------------------------------------------
edges = [
    # IF Stage signals
    ("Instruction_Decode", "RegWrite"),
    ("Instruction_Decode", "RegDst"),
    ("Instruction_Decode", "ImmSrc"),
    ("Instruction_Decode", "ALUOp"),
    ("Instruction_Decode", "ALUSrc"),
    ("Instruction_Decode", "Branch"),
    ("Instruction_Decode", "MemRead"),
    ("Instruction_Decode", "MemWrite"),
    ("Instruction_Decode", "MemToReg"),
    ("Instruction_Decode", "Jump"),
    
    # PCWrite and IF_ID_Write dependencies
    ("Bubble", "PCWrite"),
    ("Bubble", "IF_ID_Write"),
    ("PCWrite", "Flush_IF_ID"),

    # Stall signal dependencies (hazard detection)
    ("MemRead", "Stall"),     # Load-use → stall
    ("Stall", "PCWrite"),     # Stall freezes PC
    ("Stall", "IF_ID_Write"), # Stall freezes IF/ID
    ("Stall", "Bubble"),      # Stall also inserts bubble (if needed)

    # ID Stage dependencies
    ("RegWrite", "FwdA"),
    ("RegWrite", "FwdB"),
    ("RegWrite", "FwdC"),
    
    ("RegDst", "ALUSrc"),
    ("ImmSrc", "ALUSrc"),
    
    # Bubble generation (hazard detection)
    ("MemRead", "Bubble"),  # Load-use hazard detection
    ("Bubble", "ID_EX_Flush"),
    
    # EX Stage dependencies
    ("FwdA", "ALUSrc"),
    ("FwdB", "ALUSrc"),
    ("ALUSrc", "ALUOp"),
    ("ALUOp", "BranchZero"),
    
    ("Branch", "BranchZero"),
    ("BranchZero", "BranchTaken"),
    
    # Branch feedback to IF
    ("BranchTaken", "PC_src"),
    ("BranchTaken", "Flush_IF_ID"),
    ("BranchTaken", "ID_EX_Flush"),
    
    # Jump and target address dependencies
    ("Jump", "PC_src"),
    ("Jump", "Flush_IF_ID"),
    ("ALUOp", "TargetAddrReady"),  # Target address calculated in ALU
    ("TargetAddrReady", "PC_src"),  # Target ready before PC update
    
    # MEM Stage dependencies
    ("MemRead", "FwdC"),
    
    # WB Stage dependencies
    ("MemToReg", "RegWrite"),
]

# ------------------------------------------------------------
# 2) Build DAG
# ------------------------------------------------------------
G = nx.DiGraph()
G.add_edges_from(edges)

print(f"Total nodes (control signals): {G.number_of_nodes()}")
print(f"Total edges (dependencies): {G.number_of_edges()}")

# Check for cycles (should be acyclic for scheduling)
if not nx.is_directed_acyclic_graph(G):
    print("ERROR: Graph has cycles!")
    cycles = list(nx.simple_cycles(G))
    print(f"Cycles found: {cycles}")
else:
    print("✓ Graph is acyclic (valid for scheduling)")

# ------------------------------------------------------------
# 3) ASAP Scheduling (As-Soon-As-Possible)
# ------------------------------------------------------------
ASAP = {}
for node in nx.topological_sort(G):
    preds = list(G.predecessors(node))
    if not preds:
        ASAP[node] = 0  # Root nodes start at step 0
    else:
        ASAP[node] = max(ASAP[p] + 1 for p in preds)

# ------------------------------------------------------------
# 4) ALAP Scheduling (As-Late-As-Possible)
# ------------------------------------------------------------
max_asap = max(ASAP.values())
print(f"\nCritical path length (max ASAP): {max_asap} steps")

ALAP = {}
# Process in reverse topological order
for node in reversed(list(nx.topological_sort(G))):
    succs = list(G.successors(node))
    if not succs:
        ALAP[node] = max_asap  # Leaf nodes at latest time
    else:
        ALAP[node] = min(ALAP[s] - 1 for s in succs)

# ------------------------------------------------------------
# 5) Slack and Mobility
# ------------------------------------------------------------
SLACK = {n: ALAP[n] - ASAP[n] for n in G.nodes()}
MOBILITY = {n: ALAP[n] - ASAP[n] + 1 for n in G.nodes()}

print("\nCritical path signals (slack = 0):")
critical_signals = [n for n in G.nodes() if SLACK[n] == 0]
for sig in critical_signals:
    print(f"  {sig}: ASAP={ASAP[sig]}, ALAP={ALAP[sig]}")

# ------------------------------------------------------------
# 6) FDS (Force-Directed Scheduling)
# ------------------------------------------------------------
# Calculate probability distribution for each operation
Prob = {}
for n in G.nodes():
    Prob[n] = {}
    for t in range(max_asap + 1):
        if ASAP[n] <= t <= ALAP[n]:
            Prob[n][t] = 1.0 / MOBILITY[n]
        else:
            Prob[n][t] = 0.0

# Calculate distribution cost (forces) for each time step
Cost = {}
for t in range(max_asap + 1):
    Cost[t] = sum(Prob[n][t] for n in G.nodes())

print("\nDistribution cost per step:")
for t in sorted(Cost.keys()):
    print(f"  Step {t}: {Cost[t]:.2f} operations")

# FDS: Choose time step with minimum cost within valid interval
FDS_schedule = {}
for n in G.nodes():
    valid_steps = range(ASAP[n], ALAP[n] + 1)
    best_step = min(valid_steps, key=lambda t: Cost[t])
    FDS_schedule[n] = best_step

# ------------------------------------------------------------
# 7) Resource Type Classification
# ------------------------------------------------------------
resource_type = {
    "Instruction_Decode": "Decoder",
    "RegWrite": "Decoder",
    "RegDst": "Decoder",
    "ImmSrc": "Decoder",
    "ALUOp": "Decoder",
    "ALUSrc": "Decoder",
    "Branch": "Decoder",
    "MemRead": "Decoder",
    "MemWrite": "Decoder",
    "MemToReg": "Decoder",
    "Jump": "Decoder",
    "FwdA": "Comparator",
    "FwdB": "Comparator",
    "FwdC": "Comparator",
    "Bubble": "Logic",
    "Stall": "Logic",
    "ID_EX_Flush": "Logic",
    "Flush_IF_ID": "Logic",
    "PCWrite": "Logic",
    "IF_ID_Write": "Logic",
    "BranchZero": "Logic",
    "BranchTaken": "Logic",
    "PC_src": "Mux",
}

# ------------------------------------------------------------
# 8) Stage Assignment (for visualization)
# ------------------------------------------------------------
stage_assignment = {
    "Instruction_Decode": "IF",
    "PCWrite": "IF",
    "PC_src": "IF",
    "IF_ID_Write": "IF",
    "Flush_IF_ID": "IF",
    "RegWrite": "ID",
    "RegDst": "ID",
    "ImmSrc": "ID",
    "Bubble": "ID",
    "Stall": "ID",
    "ID_EX_Flush": "ID",
    "FwdA": "EX",
    "FwdB": "EX",
    "ALUSrc": "EX",
    "ALUOp": "EX",
    "Branch": "EX",
    "BranchZero": "EX",
    "BranchTaken": "EX",
    "Jump": "EX",
    "MemRead": "MEM",
    "MemWrite": "MEM",
    "FwdC": "MEM",
    "MemToReg": "WB",
}

# ------------------------------------------------------------
# 9) Create Comprehensive Output Table
# ------------------------------------------------------------
schedule_data = []
for node in sorted(G.nodes(), key=lambda n: (FDS_schedule[n], n)):
    schedule_data.append({
        'Signal': node,
        'Stage': stage_assignment.get(node, "?"),
        'ASAP': ASAP[node],
        'ALAP': ALAP[node],
        'Slack': SLACK[node],
        'Mobility': MOBILITY[node],
        'FDS_Step': FDS_schedule[node],
        'Resource': resource_type.get(node, "Unknown"),
        'Critical': 'YES' if SLACK[node] == 0 else 'NO'
    })

df = pd.DataFrame(schedule_data)

# ------------------------------------------------------------
# 10) Print Results
# ------------------------------------------------------------
print("\n" + "="*80)
print("COMPLETE SCHEDULING RESULTS")
print("="*80)
print(df.to_string(index=False))

# ------------------------------------------------------------
# 11) Save to Files
# ------------------------------------------------------------
# Save detailed table
df.to_csv("Complete_Schedule.csv", index=False)
print("\n✓ Saved: Complete_Schedule.csv")

# Save FDS schedule only
with open("FDS_Schedule.txt", "w") as f:
    f.write("="*60 + "\n")
    f.write("FDS SCHEDULING RESULTS\n")
    f.write("="*60 + "\n\n")
    f.write("Signal                          Step    Resource\n")
    f.write("-"*60 + "\n")
    for node in sorted(FDS_schedule.keys(), key=lambda n: (FDS_schedule[n], n)):
        step = FDS_schedule[node]
        res = resource_type.get(node, "?")
        f.write(f"{node:30s}  {step:4d}    {res}\n")
    
    f.write("\n" + "="*60 + "\n")
    f.write("CRITICAL PATH\n")
    f.write("="*60 + "\n")
    for sig in critical_signals:
        f.write(f"{sig:30s}  Step {ASAP[sig]}\n")
    
    f.write(f"\nTotal critical path delay: {max_asap} steps\n")

print("✓ Saved: FDS_Schedule.txt")

# Save ASAP/ALAP details
with open("ASAP_ALAP_Details.txt", "w") as f:
    f.write("="*60 + "\n")
    f.write("ASAP SCHEDULING\n")
    f.write("="*60 + "\n")
    for node in sorted(ASAP.keys(), key=lambda n: (ASAP[n], n)):
        f.write(f"{node:30s}: {ASAP[node]}\n")
    
    f.write("\n" + "="*60 + "\n")
    f.write("ALAP SCHEDULING\n")
    f.write("="*60 + "\n")
    for node in sorted(ALAP.keys(), key=lambda n: (ALAP[n], n)):
        f.write(f"{node:30s}: {ALAP[node]}\n")
    
    f.write("\n" + "="*60 + "\n")
    f.write("SLACK ANALYSIS\n")
    f.write("="*60 + "\n")
    for node in sorted(SLACK.keys(), key=lambda n: (SLACK[n], n)):
        slack = SLACK[node]
        crit = " [CRITICAL]" if slack == 0 else ""
        f.write(f"{node:30s}: {slack}{crit}\n")

print("✓ Saved: ASAP_ALAP_Details.txt")

# ------------------------------------------------------------
# 12) Visualizations
# ------------------------------------------------------------

# Visualization 1: Schedule Gantt Chart
fig, ax = plt.subplots(figsize=(14, 10))

stage_colors = {
    'IF': '#F4B183',
    'ID': '#A9D08E',
    'EX': '#FFD966',
    'MEM': '#9BC2E6',
    'WB': '#CDA0D9'
}

y_pos = 0
signal_positions = {}

for stage in ['IF', 'ID', 'EX', 'MEM', 'WB']:
    stage_signals = [s for s in sorted(G.nodes()) if stage_assignment.get(s) == stage]
    
    for sig in stage_signals:
        step = FDS_schedule[sig]
        ax.barh(y_pos, 1, left=step, height=0.8, 
               color=stage_colors[stage], edgecolor='black', linewidth=0.5)
        ax.text(step + 0.5, y_pos, sig, va='center', ha='center', fontsize=8)
        signal_positions[sig] = y_pos
        y_pos += 1
    
    y_pos += 0.5  # Space between stages

ax.set_yticks([])
ax.set_xlabel('Time Step', fontsize=12)
ax.set_title('FDS Schedule - Control Signal Generation Order', fontsize=14, fontweight='bold')
ax.set_xlim(-0.5, max_asap + 1.5)
ax.grid(axis='x', alpha=0.3)

# Add stage labels
y_pos = 0
for stage in ['IF', 'ID', 'EX', 'MEM', 'WB']:
    stage_signals = [s for s in sorted(G.nodes()) if stage_assignment.get(s) == stage]
    if stage_signals:
        mid_y = y_pos + len(stage_signals) / 2
        ax.text(-0.8, mid_y, stage, fontsize=11, fontweight='bold', va='center')
        y_pos += len(stage_signals) + 0.5

plt.tight_layout()
plt.savefig("FDS_Schedule_Gantt.png", dpi=300, bbox_inches='tight')
print("✓ Saved: FDS_Schedule_Gantt.png")
plt.close()

# Visualization 2: Dependency Graph with Scheduling
pos = nx.spring_layout(G, k=2, iterations=50, seed=42)

node_colors = [stage_colors.get(stage_assignment.get(n, 'IF'), '#CCCCCC') for n in G.nodes()]
node_labels = {n: f"{n}\n[{FDS_schedule[n]}]" for n in G.nodes()}

plt.figure(figsize=(16, 12))
nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=2000, 
                       edgecolors='black', linewidths=1.5)
nx.draw_networkx_edges(G, pos, arrows=True, arrowsize=15, 
                       edge_color='gray', width=1.5, 
                       connectionstyle='arc3,rad=0.1')
nx.draw_networkx_labels(G, pos, node_labels, font_size=7)

plt.title("Control Dependency Graph with FDS Schedule\n[Number] = Scheduled Step", 
         fontsize=14, fontweight='bold')
plt.axis('off')
plt.tight_layout()
plt.savefig("CDG_with_Schedule.png", dpi=300, bbox_inches='tight')
print("✓ Saved: CDG_with_Schedule.png")
plt.close()

# Visualization 3: Resource Utilization per Step
fig, ax = plt.subplots(figsize=(12, 6))

resource_usage = {}
for step in range(max_asap + 1):
    resource_usage[step] = {}
    for node, scheduled_step in FDS_schedule.items():
        if scheduled_step == step:
            res_type = resource_type.get(node, "Unknown")
            resource_usage[step][res_type] = resource_usage[step].get(res_type, 0) + 1

steps = sorted(resource_usage.keys())
resource_types = sorted(set(rt for step_res in resource_usage.values() for rt in step_res.keys()))

bottom = [0] * len(steps)
colors_res = {'Decoder': '#FF9999', 'Comparator': '#66B2FF', 'Logic': '#99FF99', 'Mux': '#FFCC99'}

for res_type in resource_types:
    values = [resource_usage[step].get(res_type, 0) for step in steps]
    ax.bar(steps, values, bottom=bottom, label=res_type, 
           color=colors_res.get(res_type, '#CCCCCC'), edgecolor='black', linewidth=0.5)
    bottom = [b + v for b, v in zip(bottom, values)]

ax.set_xlabel('Time Step', fontsize=12)
ax.set_ylabel('Number of Operations', fontsize=12)
ax.set_title('Resource Utilization per Time Step', fontsize=14, fontweight='bold')
ax.legend()
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig("Resource_Utilization.png", dpi=300, bbox_inches='tight')
print("✓ Saved: Resource_Utilization.png")
plt.close()

# ------------------------------------------------------------
# 13) Summary Statistics
# ------------------------------------------------------------
print("\n" + "="*80)
print("SUMMARY STATISTICS")
print("="*80)
print(f"Total control signals: {len(G.nodes())}")
print(f"Total dependencies: {len(G.edges())}")
print(f"Critical path length: {max_asap} steps")
print(f"Critical signals: {len(critical_signals)}")
print(f"Average mobility: {sum(MOBILITY.values()) / len(MOBILITY):.2f}")
print(f"Max step cost: {max(Cost.values()):.2f} operations")
print(f"Estimated delay: {max_asap * 0.3:.2f} ns (@ 0.3ns per step)")
print(f"Max frequency: {1 / (max_asap * 0.3e-9) / 1e6:.0f} MHz")

print("\n" + "="*80)
print("RESOURCE BREAKDOWN")
print("="*80)
resource_counts = {}
for res in resource_type.values():
    resource_counts[res] = resource_counts.get(res, 0) + 1
for res, count in sorted(resource_counts.items()):
    print(f"{res:15s}: {count} signals")

print("\n✅ All files generated successfully!")
print("="*80)
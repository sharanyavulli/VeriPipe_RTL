`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 18.11.2025 06:39:55
// Design Name: 
// Module Name: test_bench
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////

`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// COMPREHENSIVE TESTBENCH FOR OPTIMIZED PIPELINE CONTROLLER
// 
// Tests all control signals, hazard detection, forwarding, and branch logic
// Includes automatic checking with expected values
//////////////////////////////////////////////////////////////////////////////////

module tb_pipeline_controller;

    // ============================================================
    // Testbench Signals
    // ============================================================
    
    // Inputs
    reg clk;
    reg reset;
    reg [31:0] IF_instruction;
    reg [31:0] ID_instruction;
    reg [5:0] ID_opcode;
    reg [5:0] ID_funct;
    reg [4:0] ID_rs;
    reg [4:0] ID_rt;
    reg [4:0] EX_rd;
    reg [4:0] MEM_rd;
    reg [4:0] WB_rd;
    reg EX_RegWrite;
    reg MEM_RegWrite;
    reg WB_RegWrite;
    reg EX_MemRead;
    reg MEM_MemRead;
    reg EX_MemToReg;
    reg Zero;
    reg branch_condition;
    
    // Outputs
    wire [1:0] RegDst;
    wire [2:0] ALUOp;
    wire ALUSrc;
    wire Branch;
    wire MemRead;
    wire MemWrite;
    wire [1:0] MemToReg;
    wire RegWrite;
    wire Jump;
    wire [1:0] ImmSrc;
    wire [1:0] ForwardA;
    wire [1:0] ForwardB;
    wire [1:0] ForwardC;
    wire Stall;
    wire Bubble;
    wire BranchZero;
    wire BranchTaken;
    wire PCWrite;
    wire IF_ID_Write;
    wire Flush_IF_ID;
    wire ID_EX_Flush;
    wire [1:0] PC_src;
    wire TargetAddrReady;
    
    // Test tracking
    integer test_num;
    integer passed_tests;
    integer failed_tests;
    
    // ============================================================
    // DUT Instantiation
    // ============================================================
    
    pipeline_controller dut (
        .clk(clk),
        .reset(reset),
        .IF_instruction(IF_instruction),
        .ID_instruction(ID_instruction),
        .ID_opcode(ID_opcode),
        .ID_funct(ID_funct),
        .ID_rs(ID_rs),
        .ID_rt(ID_rt),
        .EX_rd(EX_rd),
        .MEM_rd(MEM_rd),
        .WB_rd(WB_rd),
        .EX_RegWrite(EX_RegWrite),
        .MEM_RegWrite(MEM_RegWrite),
        .WB_RegWrite(WB_RegWrite),
        .EX_MemRead(EX_MemRead),
        .MEM_MemRead(MEM_MemRead),
        .EX_MemToReg(EX_MemToReg),
        .Zero(Zero),
        .branch_condition(branch_condition),
        .RegDst(RegDst),
        .ALUOp(ALUOp),
        .ALUSrc(ALUSrc),
        .Branch(Branch),
        .MemRead(MemRead),
        .MemWrite(MemWrite),
        .MemToReg(MemToReg),
        .RegWrite(RegWrite),
        .Jump(Jump),
        .ImmSrc(ImmSrc),
        .ForwardA(ForwardA),
        .ForwardB(ForwardB),
        .ForwardC(ForwardC),
        .Stall(Stall),
        .Bubble(Bubble),
        .BranchZero(BranchZero),
        .BranchTaken(BranchTaken),
        .PCWrite(PCWrite),
        .IF_ID_Write(IF_ID_Write),
        .Flush_IF_ID(Flush_IF_ID),
        .ID_EX_Flush(ID_EX_Flush),
        .PC_src(PC_src),
        .TargetAddrReady(TargetAddrReady)
    );
    
    // ============================================================
    // Clock Generation
    // ============================================================
    
    initial begin
        clk = 0;
        forever #5 clk = ~clk;  // 10ns period
    end
    
    // ============================================================
    // Helper Tasks
    // ============================================================
    
    // Initialize all inputs
    task init_inputs;
        begin
            IF_instruction = 32'h00000000;
            ID_instruction = 32'h00000000;
            ID_opcode = 6'b000000;
            ID_funct = 6'b000000;
            ID_rs = 5'd0;
            ID_rt = 5'd0;
            EX_rd = 5'd0;
            MEM_rd = 5'd0;
            WB_rd = 5'd0;
            EX_RegWrite = 1'b0;
            MEM_RegWrite = 1'b0;
            WB_RegWrite = 1'b0;
            EX_MemRead = 1'b0;
            MEM_MemRead = 1'b0;
            EX_MemToReg = 1'b0;
            Zero = 1'b0;
            branch_condition = 1'b0;
        end
    endtask
    
    // Check a single bit signal
    task check_signal_1bit;
        input [100*8:1] signal_name;
        input expected;
        input actual;
        begin
            if (expected === actual) begin
                $display("    ? %s = %b (PASS)", signal_name, actual);
                passed_tests = passed_tests + 1;
            end else begin
                $display("    ? %s = %b, expected %b (FAIL)", signal_name, actual, expected);
                failed_tests = failed_tests + 1;
            end
        end
    endtask
    
    // Check a 2-bit signal
    task check_signal_2bit;
        input [100*8:1] signal_name;
        input [1:0] expected;
        input [1:0] actual;
        begin
            if (expected === actual) begin
                $display("    ? %s = %b (PASS)", signal_name, actual);
                passed_tests = passed_tests + 1;
            end else begin
                $display("    ? %s = %b, expected %b (FAIL)", signal_name, actual, expected);
                failed_tests = failed_tests + 1;
            end
        end
    endtask
    
    // Check a 3-bit signal
    task check_signal_3bit;
        input [100*8:1] signal_name;
        input [2:0] expected;
        input [2:0] actual;
        begin
            if (expected === actual) begin
                $display("    ? %s = %b (PASS)", signal_name, actual);
                passed_tests = passed_tests + 1;
            end else begin
                $display("    ? %s = %b, expected %b (FAIL)", signal_name, actual, expected);
                failed_tests = failed_tests + 1;
            end
        end
    endtask
    
    // Print test header
    task print_header;
        input [200*8:1] test_name;
        begin
            $display("\n========================================");
            $display("TEST %0d: %s", test_num, test_name);
            $display("========================================");
            test_num = test_num + 1;
        end
    endtask
    
    // ============================================================
    // Main Test Sequence
    // ============================================================
    
    initial begin
        // Initialize
        test_num = 1;
        passed_tests = 0;
        failed_tests = 0;
        
        $display("\n");
        $display("================================================================================");
        $display("        OPTIMIZED PIPELINE CONTROLLER TESTBENCH");
        $display("================================================================================");
        $display("Starting comprehensive verification...\n");
        
        // Reset sequence
        reset = 1;
        init_inputs();
        #20;
        reset = 0;
        #10;
        
        // ========================================
        // TEST 1: R-type ADD Instruction
        // ========================================
        print_header("R-type ADD: ADD r4, r6, r3");
        ID_opcode = 6'b000000;  // R-type
        ID_funct = 6'b100000;   // ADD
        ID_rs = 5'd6;
        ID_rt = 5'd3;
        #10;
        
        $display("  Expected Outputs:");
        $display("    RegWrite=1, RegDst=01, ALUSrc=0, MemRead=0, MemWrite=0");
        $display("    Branch=0, Jump=0, ALUOp=010");
        $display("  Actual Outputs:");
        check_signal_1bit("RegWrite", 1'b1, RegWrite);
        check_signal_2bit("RegDst", 2'b01, RegDst);
        check_signal_1bit("ALUSrc", 1'b0, ALUSrc);
        check_signal_1bit("MemRead", 1'b0, MemRead);
        check_signal_1bit("MemWrite", 1'b0, MemWrite);
        check_signal_1bit("Branch", 1'b0, Branch);
        check_signal_1bit("Jump", 1'b0, Jump);
        check_signal_3bit("ALUOp", 3'b010, ALUOp);
        
        // ========================================
        // TEST 2: R-type SUB Instruction
        // ========================================
        print_header("R-type SUB: SUB r5, r7, r2");
        ID_opcode = 6'b000000;
        ID_funct = 6'b100010;   // SUB
        ID_rs = 5'd7;
        ID_rt = 5'd2;
        #10;
        
        $display("  Expected: RegWrite=1, ALUOp=010 (R-type uses funct field)");
        check_signal_1bit("RegWrite", 1'b1, RegWrite);
        check_signal_2bit("RegDst", 2'b01, RegDst);
        check_signal_3bit("ALUOp", 3'b010, ALUOp);
        
        // ========================================
        // TEST 3: Load Word (LW)
        // ========================================
        print_header("Load Word: LW r5, 4(r6)");
        ID_opcode = 6'b100011;  // LW
        ID_funct = 6'b000000;
        ID_rs = 5'd6;
        ID_rt = 5'd5;
        #10;
        
        $display("  Expected Outputs:");
        $display("    RegWrite=1, RegDst=00, ALUSrc=1, MemRead=1, MemWrite=0");
        $display("    MemToReg=01, ImmSrc=00, ALUOp=000 (ADD for address calc)");
        check_signal_1bit("RegWrite", 1'b1, RegWrite);
        check_signal_2bit("RegDst", 2'b00, RegDst);
        check_signal_1bit("ALUSrc", 1'b1, ALUSrc);
        check_signal_1bit("MemRead", 1'b1, MemRead);
        check_signal_1bit("MemWrite", 1'b0, MemWrite);
        check_signal_2bit("MemToReg", 2'b01, MemToReg);
        check_signal_2bit("ImmSrc", 2'b00, ImmSrc);
        check_signal_3bit("ALUOp", 3'b000, ALUOp);
        
        // ========================================
        // TEST 4: Store Word (SW)
        // ========================================
        print_header("Store Word: SW r5, 8(r6)");
        ID_opcode = 6'b101011;  // SW
        ID_rs = 5'd6;
        ID_rt = 5'd5;
        #10;
        
        $display("  Expected Outputs:");
        $display("    RegWrite=0, ALUSrc=1, MemRead=0, MemWrite=1");
        $display("    ImmSrc=00, ALUOp=000");
        check_signal_1bit("RegWrite", 1'b0, RegWrite);
        check_signal_1bit("ALUSrc", 1'b1, ALUSrc);
        check_signal_1bit("MemRead", 1'b0, MemRead);
        check_signal_1bit("MemWrite", 1'b1, MemWrite);
        check_signal_2bit("ImmSrc", 2'b00, ImmSrc);
        check_signal_3bit("ALUOp", 3'b000, ALUOp);
        
        // ========================================
        // TEST 5: Branch Equal (BEQ) - Taken
        // ========================================
        print_header("Branch Equal: BEQ r6, r5, offset (TAKEN)");
        ID_opcode = 6'b000100;  // BEQ
        ID_rs = 5'd6;
        ID_rt = 5'd5;
        Zero = 1'b1;            // Branch condition met
        #10;
        
        $display("  Expected Outputs:");
        $display("    Branch=1, BranchZero=1, BranchTaken=1");
        $display("    Flush_IF_ID=1, ID_EX_Flush=1, PC_src=01");
        $display("    ImmSrc=10, ALUOp=001 (SUB for comparison)");
        check_signal_1bit("Branch", 1'b1, Branch);
        check_signal_1bit("BranchZero", 1'b1, BranchZero);
        check_signal_1bit("BranchTaken", 1'b1, BranchTaken);
        check_signal_1bit("Flush_IF_ID", 1'b1, Flush_IF_ID);
        check_signal_1bit("ID_EX_Flush", 1'b1, ID_EX_Flush);
        check_signal_2bit("PC_src", 2'b01, PC_src);
        check_signal_2bit("ImmSrc", 2'b10, ImmSrc);
        check_signal_3bit("ALUOp", 3'b001, ALUOp);
        
        // ========================================
        // TEST 6: Branch Equal (BEQ) - Not Taken
        // ========================================
        print_header("Branch Equal: BEQ r6, r5, offset (NOT TAKEN)");
        ID_opcode = 6'b000100;
        ID_rs = 5'd6;
        ID_rt = 5'd5;
        Zero = 1'b0;            // Branch condition not met
        #10;
        
        $display("  Expected Outputs:");
        $display("    Branch=1, BranchZero=0, BranchTaken=0");
        $display("    Flush_IF_ID=0, PC_src=00");
        check_signal_1bit("Branch", 1'b1, Branch);
        check_signal_1bit("BranchZero", 1'b0, BranchZero);
        check_signal_1bit("BranchTaken", 1'b0, BranchTaken);
        check_signal_1bit("Flush_IF_ID", 1'b0, Flush_IF_ID);
        check_signal_2bit("PC_src", 2'b00, PC_src);
        
        // ========================================
        // TEST 7: Branch Not Equal (BNE) - Taken
        // ========================================
        print_header("Branch Not Equal: BNE r6, r5, offset (TAKEN)");
        ID_opcode = 6'b000101;  // BNE
        ID_rs = 5'd6;
        ID_rt = 5'd5;
        Zero = 1'b0;            // Not equal (Zero=0 means BNE taken)
        #10;
        
        $display("  Expected Outputs:");
        $display("    Branch=1, BranchZero=1, BranchTaken=1");
        check_signal_1bit("Branch", 1'b1, Branch);
        check_signal_1bit("BranchZero", 1'b1, BranchZero);
        check_signal_1bit("BranchTaken", 1'b1, BranchTaken);
        
        // ========================================
        // TEST 8: Jump (J)
        // ========================================
        print_header("Jump: J target");
        ID_opcode = 6'b000010;  // J
        Zero = 1'b0;
        #10;
        
        $display("  Expected Outputs:");
        $display("    Jump=1, BranchTaken=1, RegWrite=0");
        $display("    Flush_IF_ID=1, PC_src=10, ImmSrc=11");
        check_signal_1bit("Jump", 1'b1, Jump);
        check_signal_1bit("BranchTaken", 1'b1, BranchTaken);
        check_signal_1bit("RegWrite", 1'b0, RegWrite);
        check_signal_1bit("Flush_IF_ID", 1'b1, Flush_IF_ID);
        check_signal_2bit("PC_src", 2'b10, PC_src);
        check_signal_2bit("ImmSrc", 2'b11, ImmSrc);
        
        // ========================================
        // TEST 9: Jump and Link (JAL)
        // ========================================
        print_header("Jump and Link: JAL target");
        ID_opcode = 6'b000011;  // JAL
        #10;
        
        $display("  Expected Outputs:");
        $display("    Jump=1, RegWrite=1, RegDst=10 (r31)");
        $display("    MemToReg=10 (PC+4), ImmSrc=11");
        check_signal_1bit("Jump", 1'b1, Jump);
        check_signal_1bit("RegWrite", 1'b1, RegWrite);
        check_signal_2bit("RegDst", 2'b10, RegDst);
        check_signal_2bit("MemToReg", 2'b10, MemToReg);
        check_signal_2bit("ImmSrc", 2'b11, ImmSrc);
        
        // ========================================
        // TEST 10: ADDI (I-type)
        // ========================================
        print_header("Add Immediate: ADDI r5, r6, 10");
        ID_opcode = 6'b001000;  // ADDI
        ID_rs = 5'd6;
        ID_rt = 5'd5;
        #10;
        
        $display("  Expected Outputs:");
        $display("    RegWrite=1, ALUSrc=1, RegDst=00");
        $display("    ImmSrc=00, ALUOp=000");
        check_signal_1bit("RegWrite", 1'b1, RegWrite);
        check_signal_1bit("ALUSrc", 1'b1, ALUSrc);
        check_signal_2bit("RegDst", 2'b00, RegDst);
        check_signal_2bit("ImmSrc", 2'b00, ImmSrc);
        check_signal_3bit("ALUOp", 3'b000, ALUOp);
        
        // ========================================
        // TEST 11: ANDI (Immediate AND)
        // ========================================
        print_header("AND Immediate: ANDI r5, r6, 0xFF");
        ID_opcode = 6'b001100;  // ANDI
        ID_rs = 5'd6;
        ID_rt = 5'd5;
        #10;
        
        $display("  Expected Outputs:");
        $display("    RegWrite=1, ALUSrc=1, ImmSrc=01 (zero-extend)");
        $display("    ALUOp=011 (AND)");
        check_signal_1bit("RegWrite", 1'b1, RegWrite);
        check_signal_1bit("ALUSrc", 1'b1, ALUSrc);
        check_signal_2bit("ImmSrc", 2'b01, ImmSrc);
        check_signal_3bit("ALUOp", 3'b011, ALUOp);
        
        // ========================================
        // TEST 12: EX-to-EX Forwarding (ForwardA)
        // ========================================
        print_header("EX-to-EX Forwarding: ForwardA");
        ID_opcode = 6'b000000;  // R-type
        ID_funct = 6'b100000;   // ADD
        ID_rs = 5'd6;
        ID_rt = 5'd3;
        EX_rd = 5'd6;           // Previous instr writes to r6
        EX_RegWrite = 1'b1;     // EX stage writing
        EX_MemRead = 1'b0;      // Not a load
        #10;
        
        $display("  Expected Outputs:");
        $display("    ForwardA=10 (forward from EX)");
        $display("    ForwardB=00 (no forwarding for r3)");
        check_signal_2bit("ForwardA", 2'b10, ForwardA);
        check_signal_2bit("ForwardB", 2'b00, ForwardB);
        
        // ========================================
        // TEST 13: MEM-to-EX Forwarding (ForwardA)
        // ========================================
        print_header("MEM-to-EX Forwarding: ForwardA");
        ID_rs = 5'd7;
        ID_rt = 5'd3;
        EX_rd = 5'd0;           // EX not writing to r7
        EX_RegWrite = 1'b0;
        MEM_rd = 5'd7;          // MEM stage writes to r7
        MEM_RegWrite = 1'b1;
        #10;
        
        $display("  Expected Outputs:");
        $display("    ForwardA=01 (forward from MEM)");
        $display("    ForwardB=00");
        check_signal_2bit("ForwardA", 2'b01, ForwardA);
        check_signal_2bit("ForwardB", 2'b00, ForwardB);
        
        // ========================================
        // TEST 14: ForwardB (EX stage)
        // ========================================
        print_header("EX-to-EX Forwarding: ForwardB");
        ID_rs = 5'd1;
        ID_rt = 5'd8;
        EX_rd = 5'd8;           // EX writes to r8
        EX_RegWrite = 1'b1;
        EX_MemRead = 1'b0;
        MEM_rd = 5'd0;
        MEM_RegWrite = 1'b0;
        #10;
        
        $display("  Expected Outputs:");
        $display("    ForwardA=00, ForwardB=10 (forward from EX)");
        check_signal_2bit("ForwardA", 2'b00, ForwardA);
        check_signal_2bit("ForwardB", 2'b10, ForwardB);
        
        // ========================================
        // TEST 15: Load-Use Hazard (Stall)
        // ========================================
        print_header("Load-Use Hazard: Stall Pipeline");
        ID_opcode = 6'b000000;
        ID_funct = 6'b100000;
        ID_rs = 5'd6;
        ID_rt = 5'd3;
        EX_rd = 5'd6;           // Load in EX writes to r6
        EX_MemRead = 1'b1;      // It's a LOAD
        EX_RegWrite = 1'b1;
        #10;
        
        $display("  Expected Outputs:");
        $display("    Stall=1, Bubble=1 (load-use hazard detected)");
        $display("    PCWrite=0, IF_ID_Write=0 (freeze pipeline)");
        $display("    ID_EX_Flush=1 (insert bubble)");
        check_signal_1bit("Stall", 1'b1, Stall);
        check_signal_1bit("Bubble", 1'b1, Bubble);
        check_signal_1bit("PCWrite", 1'b0, PCWrite);
        check_signal_1bit("IF_ID_Write", 1'b0, IF_ID_Write);
        check_signal_1bit("ID_EX_Flush", 1'b1, ID_EX_Flush);
        
        // ========================================
        // TEST 16: No Hazard (Normal Operation)
        // ========================================
        print_header("No Hazard: Normal Pipeline Flow");
        init_inputs();
        ID_opcode = 6'b000000;
        ID_funct = 6'b100000;
        ID_rs = 5'd6;
        ID_rt = 5'd3;
        EX_rd = 5'd10;          // No conflict
        EX_RegWrite = 1'b0;
        EX_MemRead = 1'b0;
        #10;
        
        $display("  Expected Outputs:");
        $display("    Stall=0, Bubble=0 (no hazard)");
        $display("    PCWrite=1, IF_ID_Write=1 (pipeline advancing)");
        $display("    ForwardA=00, ForwardB=00 (no forwarding needed)");
        check_signal_1bit("Stall", 1'b0, Stall);
        check_signal_1bit("Bubble", 1'b0, Bubble);
        check_signal_1bit("PCWrite", 1'b1, PCWrite);
        check_signal_1bit("IF_ID_Write", 1'b1, IF_ID_Write);
        check_signal_2bit("ForwardA", 2'b00, ForwardA);
        check_signal_2bit("ForwardB", 2'b00, ForwardB);
        
        // ========================================
        // TEST 17: Branch Comparator Forwarding (ForwardC)
        // ========================================
        print_header("Branch Comparator Forwarding: ForwardC");
        ID_opcode = 6'b000100;  // BEQ
        ID_rs = 5'd6;
        ID_rt = 5'd5;
        EX_rd = 5'd6;           // EX writes to r6 (used in branch)
        EX_RegWrite = 1'b1;
        EX_MemRead = 1'b0;
        Zero = 1'b0;
        #10;
        
        $display("  Expected Outputs:");
        $display("    ForwardC=10 (forward to comparator from EX)");
        $display("    Branch=1");
        check_signal_2bit("ForwardC", 2'b10, ForwardC);
        check_signal_1bit("Branch", 1'b1, Branch);
        
        // ========================================
        // TEST 18: TargetAddrReady for Branch
        // ========================================
        print_header("Target Address Ready: Branch");
        ID_opcode = 6'b000100;  // BEQ
        #10;
        
        $display("  Expected Outputs:");
        $display("    TargetAddrReady=1 (branch target computed)");
        check_signal_1bit("TargetAddrReady", 1'b1, TargetAddrReady);
        
        // ========================================
        // TEST 19: TargetAddrReady for Jump
        // ========================================
        print_header("Target Address Ready: Jump");
        ID_opcode = 6'b000010;  // J
        #10;
        
        $display("  Expected Outputs:");
        $display("    TargetAddrReady=1 (jump target ready)");
        check_signal_1bit("TargetAddrReady", 1'b1, TargetAddrReady);
        
        // ========================================
        // TEST 20: Jump Register (JR) via funct
        // ========================================
        print_header("Jump Register: JR r31");
        ID_opcode = 6'b000000;  // R-type
        ID_funct = 6'b001000;   // JR
        ID_rs = 5'd31;
        #10;
        
        $display("  Expected Outputs:");
        $display("    Jump=1, RegWrite=0 (JR doesn't write)");
        $display("    BranchTaken=1 (acts like jump)");
        check_signal_1bit("Jump", 1'b1, Jump);
        check_signal_1bit("RegWrite", 1'b0, RegWrite);
        check_signal_1bit("BranchTaken", 1'b1, BranchTaken);
        
        // ========================================
        // Final Results
        // ========================================
        #50;
        
        $display("\n");
        $display("================================================================================");
        $display("                          TEST RESULTS SUMMARY");
        $display("================================================================================");
        $display("Total Checks:    %0d", passed_tests + failed_tests);
        $display("Passed:          %0d", passed_tests);
        $display("Failed:          %0d", failed_tests);
        $display("Pass Rate:       %.2f%%", (passed_tests * 100.0) / (passed_tests + failed_tests));
        $display("================================================================================");
        
        if (failed_tests == 0) begin
            $display("\n? ? ?  ALL TESTS PASSED!  ? ? ?\n");
        end else begin
            $display("\n? SOME TESTS FAILED - Review output above\n");
        end
        
        $display("================================================================================\n");
        
        $finish;
    end
    
    // ============================================================
    // Waveform Dumping
    // ============================================================
    
    initial begin
        $dumpfile("pipeline_controller_tb.vcd");
        $dumpvars(0, tb_pipeline_controller);
    end
    
    // ============================================================
    // Timeout Watchdog
    // ============================================================
    
    initial begin
        #50000;
        $display("\n[ERROR] Testbench timeout after 50us!");
        $finish;
    end

endmodule
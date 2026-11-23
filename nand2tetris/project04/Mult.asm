// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/4/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)
// The algorithm is based on repetitive addition.

//// Replace this comment with your code.


@R2
M=0 //setup r2
(LOOP)

@R1 //first load data with r1 and check whether it is greater than 0
D=M
@END
D;JLE

@R0
D=M        // D = R0 again
@R2
M=D+M      // R2 = R2 + R0

@R1
M=M-1
D=M


@LOOP
D;JGT

(END)
@END
0;JMP


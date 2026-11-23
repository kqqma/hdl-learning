// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/4/Fill.asm

// Runs an infinite loop that listens to the keyboard input. 
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel. When no key is pressed, 
// the screen should be cleared.

//// Replace this comment with your code.
(MAIN)
//keyboard address and load
@KBD
D=M
//check if white
@WHITE
D;JEQ

//black
@color //register color
M=-1 //give color -1 for black
//jump to start, which is loop
@START
0;JMP

(WHITE)
@color
M=0
@START
0;JMP

(START)

@SCREEN
D=A
@addr
M=D

(FILL)
@color
D=M
@addr
A=M
M=D
@addr
M=M+1

@addr
D=M
@KBD
D=D-A
@MAIN
D;JEQ
@FILL
0;JMP









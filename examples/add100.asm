STR $i, 1
STR $sum, 0

LOOP:
    STR A, $i
    MOV D, M

    STR A, 100
    SUB D, D, A

    JGT D, $END

    STR A, $i
    MOV D, M

    STR A, $sum
    ADD M, D, M

    INC $i

    JMP $LOOP

END:
    JMP $END

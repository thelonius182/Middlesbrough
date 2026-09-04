def tijdtekst(uur, minuut):
    volgend_uur = (uur + 1) % 24

    if minuut == 0:
        return f"Het is {uur} uur."

    if minuut == 15:
        return f"Het is kwart over {uur}."

    if minuut == 30:
        return f"Het is half {volgend_uur}."

    if minuut == 45:
        return f"Het is kwart voor {volgend_uur}."

    if minuut < 15:
        return f"Het is {minuut} over {uur}."

    if minuut < 30:
        return f"Het is {30 - minuut} voor half {volgend_uur}."

    if minuut < 45:
        return f"Het is {minuut - 30} over half {volgend_uur}."

    return f"Het is {60 - minuut} voor {volgend_uur}."


for uur, minuut in [
    (5, 0),
    (5, 7),
    (5, 15),
    (5, 25),
    (5, 30),
    (5, 37),
    (5, 45),
    (5, 53),
]:
    print(f"{uur:02d}:{minuut:02d}  ->  {tijdtekst(uur, minuut)}")

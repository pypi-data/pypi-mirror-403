def is_even(number: int) -> bool:
    if number < 0:
        raise ValueError("Negative numbers are not allowed")
    else:
        if str(number)[-1] in ['0', '2', '4', '6', '8']:
            return True
        else:
            return False
    raise ValueError("ho- how?")
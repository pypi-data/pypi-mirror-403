
def fin_format(number) -> str:
    number = round(number, 2)
    return "{:,.2f}".format(number)


def percentage(new_value: float, original_value: float):
    pct = 100 * (new_value - original_value) / original_value
    return round(pct, 2)

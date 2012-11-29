def format_amount(amount):
    """
    Format the amount to respond to the plateform needs, which is a undivisible version of the amount.

    c.g. if amount = $50.24 
         then format_amount = 5024
    """
    return int(amount * 100)
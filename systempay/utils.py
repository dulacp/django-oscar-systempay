def format_amount(amount):
    """
    Format the amount to respond to the plateform needs, which is a undivisible version of the amount.

    c.g. if amount = $50.24 
         then format_amount = 5024
    """
    return int(amount * 100)

def printable_form_errors(form):
    return u' / '.join([u"%s: %s" % (f.name, '. '.join(f.errors)) for f in form])

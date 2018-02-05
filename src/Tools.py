import sys

def eprint(*args, **kwargs):
    """
    Standard Python3's standard print() function, but on STDERR
    :param args:
    :param kwargs:
    :return:
    """
    return print(*args, **kwargs, file=sys.stderr)

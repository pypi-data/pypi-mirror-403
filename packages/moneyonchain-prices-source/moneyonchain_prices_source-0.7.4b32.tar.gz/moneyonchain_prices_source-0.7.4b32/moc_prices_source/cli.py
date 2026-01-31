import click, shutil,sys
from tabulate import tabulate



cli = click
option = click.option
argument = click.argument
BadParameter = click.BadParameter
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


class Output():
    def clean(self):
        self.histo = []
    def __init__(self, print=None):
        self.print = print
        self.clean()
    def __call__(self, *args):
        if self.print is not None:
            self.print(*args)
        if args:
            self.histo.extend([str(a) for a in args])
        else:
            self.histo.append('')
    def __str__(self):
        return '\n'.join([str(h) for h in self.histo])


def command_group(command_group_=None, name=None, **kargs):
    f = command_group_.group if command_group_ else cli.group
    kargs['context_settings'] = CONTEXT_SETTINGS
    kargs['name'] = name
    return f(**kargs)


def command(command_=None, name=None, **kargs):
    f = command_.command if command_ else cli.command
    kargs['context_settings'] = CONTEXT_SETTINGS
    kargs['name'] = name
    return f(**kargs)


def trim(s, len_=30, end=' [...]'):
    assert len(end)<=len_
    out = str(s)
    if len(out)>len_:
        out = out[:(len_-len(end))] + end
    return out 


def print_list(items):
    if not items:
        return
    
    items = list(map(str, items))
    items.sort()
    
    width = shutil.get_terminal_size().columns
    col_width = max(len(s) for s in items) + 2
    cols = max(1, width // col_width)

    for i, s in enumerate(items):
        print(s.ljust(col_width), end="")
        if (i + 1) % cols == 0:
            print()
    print()

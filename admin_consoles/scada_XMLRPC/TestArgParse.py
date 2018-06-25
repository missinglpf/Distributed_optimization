import argparse
import shlex


class ArgumentParserError(Exception): pass


class CommandParser(argparse.ArgumentParser):
	def __init__(self, custom_cmd, description):
		super(CommandParser, self).__init__(prog=custom_cmd, description=description)

	def error(self, message):
		raise ArgumentParserError(message)

def test():
    parts = shlex.split('plot --help')
    if parts[0] == "plot":
        plot_parser = CommandParser(description='The plot command', custom_cmd='plot')
        plot_parser.add_argument("agent", help="the name of the agent to be ploted")
        plot_parser.add_argument("var", help="variable to be plotted [1 - xopt][2 - beta][3 - nu][4 - z]",
                                 type = int)
        plot_parser.add_argument("idx", help="index of the variable to be plotted", type=int)
        try:
            args = plot_parser.parse_args(parts[1:])
        except ArgumentParserError as ape:
            print('error: %s\n' % ape.message)
        except Exception as ex:
            print('error: %s\n' % ex.message)

test()

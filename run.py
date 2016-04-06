import brawlbracket
import argparse

parser = argparse.ArgumentParser(description='Run the BrawlBracket server.')
parser.add_argument('-d', '--debug', dest='debugMode', action='store_true',
                   help='run in debug mode')
parser.set_defaults(debugMode=False)
args = parser.parse_args();

brawlbracket.runWebServer(args.debugMode)
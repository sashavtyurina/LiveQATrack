import sys
import re

def check(from_file, to_file):
    with open(from_file) as f:
        with open(to_file, 'w') as to:
            for l in f:
                match_obj = re.search('<\w*>(.*)<\/\w*>', l)
                if match_obj:
                    if '/' in match_obj.group(1):
                        print(l)
                    else:
                        to.write(l)
                else:
                    to.write(l)

from_file = sys.argv[1]
to_tile = sys.argv[2]
check(from_file, to_tile)

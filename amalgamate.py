#!/usr/bin/env python
"""A package-based, source code amalgamater."""
import os
import sys

def main(pkgs):
    # Read the packages to merge
    lines = []
    import_lines = []
    for pkg in pkgs:
        print('Amalgamating ' + pkg)
        f = open(pkg, 'r')
        for line in f.readlines():
            line = line.rstrip()
            if line.startswith('import ') or line.startswith('from '):
                if not line in import_lines:
                    import_lines.append(line)
            else:
                lines.append(line)
        f.close()
    # remove imports from the packages that we merge
    for pkg in pkgs:
        from_pkg = 'from ' + pkg[:-3]
        to_remove = []
        for line in import_lines:
            if line.startswith(from_pkg):
                to_remove.append(line)
        for line in to_remove:
            import_lines.remove(line)
    # output
    out = open('__amalgam__.py', 'w')
    out.write('#!/usr/bin/env python\n')
    out.write('"""Generated file. Amalgated from: {0}"""\n\n'.format(', '.join(pkgs)))
    for line in import_lines:
        out.write(line + '\n')
    for line in lines:
        out.write(line + '\n')
    out.close()


if __name__ == '__main__':
    main(sys.argv[1:])

#!/usr/bin/python3

"""db2html converts any FSDB file into an html table.
WARNING: very little escaping is done -- watch out for mallicious input files.
Note: for any html that is more complex, you might use pdbjinja instead.
"""

import argparse
import sys
import pyfsdb

def parse_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description=__doc__,
                                     epilog="Exmaple Usage: pdb2html -c col1 col2 -- input.fsdb")

    parser.add_argument("-c", "--columns", type=str, nargs="*",
                        help="Column names to include; will use all if not specified")

    parser.add_argument("input_file", type=argparse.FileType('r'),
                        nargs='?', default=sys.stdin,
                        help="The input FSDB file")

    parser.add_argument("output_file", type=argparse.FileType('w'),
                        nargs='?', default=sys.stdout,
                        help="The output file to print latex table data to")

    args = parser.parse_args()
    return args

def latex_escape(value):
    return str(value).replace("\\","\\\\").replace("_", "\\_").replace("&","\\&")

def main():
    args = parse_args()

    inh = pyfsdb.Fsdb(file_handle = args.input_file)
    outh = args.output_file

    columns = args.columns
    if not columns:
        columns = inh.column_names

    # write out the header info
    outh.write("<table>\n")
    outh.write("  <tr><th>" + "</th><th>".join(columns) + "</th></tr>\n")

    # write out the body
    for row in inh:
        outh.write("  <tr><td>")
        outh.write("</td><td>".join(map(lambda x: latex_escape(x), row)))
        outh.write("</td></tr>\n")

    # and close the table
    outh.write("</table>\n")

if __name__ == "__main__":
    main()

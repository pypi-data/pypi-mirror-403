import argparse
from geoexpress import encode, decode
from geoexpress.core.info import info_raw
from geoexpress.core.utilities import locking_code


def main():
    parser = argparse.ArgumentParser("geoexpress")
    sub = parser.add_subparsers(dest="cmd")

    enc = sub.add_parser("encode")
    enc.add_argument("input")
    enc.add_argument("output")
    enc.add_argument("--cr", type=int)
    enc.add_argument("--of")
    enc.add_argument("--lossless", action="store_true")

    dec = sub.add_parser("decode")
    dec.add_argument("input")
    dec.add_argument("output")

    inf = sub.add_parser("info")
    inf.add_argument("path")

    sub.add_parser("license")

    args = parser.parse_args()

    if args.cmd == "encode":
        opts = {}
        if args.cr:
            opts["cr"] = args.cr
        if args.of:
            opts["of"] = args.of
        if args.lossless:
            opts["lossless"] = True

        encode(args.input, args.output, opts)

    elif args.cmd == "decode":
        decode(args.input, args.output)

    elif args.cmd == "info":
        print(info_raw(args.path))

    elif args.cmd == "license":
        print(locking_code())

    else:
        parser.print_help()

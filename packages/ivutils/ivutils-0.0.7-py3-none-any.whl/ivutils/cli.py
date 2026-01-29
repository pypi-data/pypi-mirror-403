import argparse
from ivutils.parsers import parser_img as img_parser
from ivutils.parsers import parser_vid as vid_parser


def run():
    parser = argparse.ArgumentParser(description="CLI tool for Image / Video processing tasks")

    # Create the base subparser handler
    module_subparsers = parser.add_subparsers(dest='module', help='Select a module', required=True)

    # --- Setup modules ---
    img_parser.get_parser(module_subparsers)
    vid_parser.get_parser(module_subparsers)

    args = parser.parse_args()

    # Process arguments
    if args.module == "img":
        img_parser.process_parser(args)
    elif args.module == "vid":
        vid_parser.process_parser(args)

if __name__ == "__main__":
    run()
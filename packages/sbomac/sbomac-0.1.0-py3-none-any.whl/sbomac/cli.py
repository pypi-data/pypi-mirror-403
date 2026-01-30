# Copyright (C) 2026 Anthony Harrison
# SPDX-License-Identifier: Apache-2.0

import argparse
import sys
import textwrap
from collections import ChainMap

from sbomac.parse import SBOMascode
from sbomac.version import VERSION

# CLI processing


def main(argv=None):

    argv = argv or sys.argv
    app_name = "sbomac"
    parser = argparse.ArgumentParser(
        prog=app_name,
        description=textwrap.dedent("""
            SBOMac generates a Software Bill of Materials for the items
            specified in a simple YAML file. Different types of SBOMs can
            be generated based on the content.
            """),
    )
    input_group = parser.add_argument_group("Input")
    input_group.add_argument(
        "-i",
        "--input-file",
        action="store",
        default="",
        help="identity of sbom definition file",
    )
    input_group.add_argument(
        "--name",
        action="store",
        help="specify name of system",
    )

    output_group = parser.add_argument_group("Output")
    output_group.add_argument(
        "-d",
        "--debug",
        action="store_true",
        default=False,
        help="add debug information",
    )
    output_group.add_argument(
        "--sbom",
        action="store",
        default="spdx",
        choices=["spdx", "cyclonedx"],
        help="specify type of sbom to generate (default: spdx)",
    )
    output_group.add_argument(
        "--format",
        action="store",
        default="tag",
        choices=["tag", "json", "yaml"],
        help="specify format of software bill of materials (sbom) (default: tag)",
    )
    output_group.add_argument(
        "--type",
        action="store",
        default="design",
        choices=["design", "source"],
        help="specify type of software bill of materials (sbom) to create (default: design)",
    )

    output_group.add_argument(
        "-o",
        "--output-file",
        action="store",
        default="",
        help="output filename (default: output to stdout)",
    )

    parser.add_argument("-V", "--version", action="version", version=VERSION)

    defaults = {
        "input_file": "",
        "output_file": "",
        "sbom": "spdx",
        "debug": False,
        "format": "tag",
        "type": "design",
        "name": "",
    }

    raw_args = parser.parse_args(argv[1:])
    args = {key: value for key, value in vars(raw_args).items() if value}
    args = ChainMap(args, defaults)

    # Validate CLI parameters

    input_file = args["input_file"]

    # Ensure format is aligned with type of SBOM
    bom_format = args["format"]
    if args["sbom"] == "cyclonedx":
        # Only JSON format valid for CycloneDX
        if bom_format != "json":
            bom_format = "json"

    if args["debug"]:
        print("Input file", input_file)
        print("SBOM format:", bom_format)
        print("Format:", bom_format)
        print("Output file:", args["output_file"])
        print("SBOM Type:", args["type"])
        print("Name", args["name"])

    if len(input_file) == 0:
        print("[ERROR] Nothing to process")
        return -1

    if args["name"] == "":
        print("[ERROR] Must specify name of system")
        return -1

    # Create SBOM file..

    sbom = SBOMascode(args["name"], debug=args["debug"])
    # Ingest data
    sbom.load(input_file)
    # Create relevent metadata
    sbom.set_sbom_format(args["sbom"], bom_format)
    # set lifecycle
    sbom.set_lifecycle(args["type"])
    # Author?
    # Tool?
    # Generate
    sbom.generate(args["output_file"])

    return 0


if __name__ == "__main__":
    sys.exit(main())

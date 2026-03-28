#!/usr/bin/env python

import re
import sys
import shutil
import os
import textwrap
import argparse

try:
    from core import TargetType, classify_target, get_runner, is_private_ip
    from core.logging_setup import configure_logging
    from core.reporter import write_reports
except ModuleNotFoundError:  # Imported as part of the datasploit package
    from .core import TargetType, classify_target, get_runner, is_private_ip
    from .core.logging_setup import configure_logging
    from .core.reporter import write_reports


def main():
    desc = r"""
   ____/ /____ _ / /_ ____ _ _____ ____   / /____   (_)/ /_
  / __  // __ `// __// __ `// ___// __ \ / // __ \ / // __/
 / /_/ // /_/ // /_ / /_/ /(__  )/ /_/ // // /_/ // // /_
 \__,_/ \__,_/ \__/ \__,_//____// .___//_/ \____//_/ \__/
                               /_/

            Open Source Assistant for #OSINT
                www.datasploit.info

    """
    desc = desc.replace("\\\\", "\\")
    epilog = """              Connect at Social Media: @datasploit
                """
    print(textwrap.dedent(desc))
    print(textwrap.dedent(epilog))

    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(desc),
        epilog=epilog,
    )
    parser.add_argument("-i", "--input", help="Provide Input", dest="single_target")
    parser.add_argument("-f", "--file", help="Provide Input", dest="file_target")
    parser.add_argument("-a", "--active", help="Run Active Scan attacks", dest="active", action="store_false")
    parser.add_argument("-q", "--quiet", help="Run scans in automated manner accepting default answers", dest="quiet", action="store_false")
    parser.add_argument(
        "-o", "--output",
        help="Output format: text | json | html | all  (default: none)",
        dest="output",
        choices=["text", "json", "html", "all"],
        default=None,
    )
    parser.add_argument(
        "-v", "--verbose",
        help="Enable verbose/debug logging",
        dest="verbose",
        action="store_true",
        default=False,
    )

    # Ensure config file exists before any imports touch it
    ds_dir = os.path.dirname(os.path.realpath(__file__))
    config_candidates = ["config.ini", "config.py"]
    config_paths = [os.path.join(ds_dir, name) for name in config_candidates]
    config_template_candidates = [
        os.path.join(ds_dir, "config.template.ini"),
        os.path.join(ds_dir, "config_sample.py"),
    ]

    config_file_path = next((path for path in config_paths if os.path.exists(path)), None)
    if config_file_path is None:
        print("[+] Looks like a new setup, setting up the config file.")
        template_path = next((path for path in config_template_candidates if os.path.exists(path)), None)
        if not template_path:
            raise FileNotFoundError("No configuration template found. Expected config.template.ini.")
        config_file_path = os.path.join(ds_dir, "config.ini")
        shutil.copyfile(template_path, config_file_path)
        print(
            "[+] A config file is added please follow guide at "
            "https://datasploit.github.io/datasploit/apiGeneration/ "
            "to fill API Keys for better results"
        )

    x = parser.parse_args()
    configure_logging(verbose=x.verbose)

    active = x.active
    quiet = x.quiet
    single_input = x.single_target
    file_input = x.file_target
    output = x.output

    if not (single_input or file_input):
        print("\nSingle target or file input required to run\n")
        parser.print_help()
        sys.exit()

    if single_input:
        try:
            auto_select_target(single_input, output)
        except KeyboardInterrupt:
            print("\nCtrl+C called Quiting")

    if file_input:
        try:
            if os.path.isfile(file_input):
                print("File Input: %s" % file_input)
                with open(file_input, "r") as f:
                    for target in f:
                        auto_select_target(target.rstrip(), output)
                print("\nDone processing %s" % file_input)
            else:
                print("%s is not a readable file" % file_input)
                print("Exiting...")
        except KeyboardInterrupt:
            print("\nCtrl+C called Quiting")


def auto_select_target(target, output=None):
    """Determine the target type, run collectors, and optionally write reports."""
    print("Target: %s" % target)

    if is_private_ip(target):
        print("Internal IP detected. Skipping target.")
        return

    target_type = classify_target(target)
    messages = {
        TargetType.IP:       "Looks like an IP, running IP collectors...",
        TargetType.DOMAIN:   "Looks like a DOMAIN, running domain collectors...",
        TargetType.EMAIL:    "Looks like an EMAIL, running email collectors...",
        TargetType.USERNAME: "Nothing matched; treating input as USERNAME...",
    }
    print(messages[target_type] + "\n")

    runner = get_runner()
    results = runner.run(target_type, target, output)

    if output:
        write_reports(results, target, output)


if __name__ == "__main__":
    main()

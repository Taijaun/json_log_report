import argparse
import csv
import logging
import json

# Counters to compute
# total_lines, valid_lines, skipped_lines, levels dict, services dict, actions dict (top 3)

def build_parser():
    
    parser = argparse.ArgumentParser(
        description="Cleans up a jsonl file and calculates metrics"
    )

    parser.add_argument(
        "input_file",
        nargs="?",
        default="app.jsonl",
        help="Path to input .jsonl file (default app.jsonl)"

    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on the first invalid entry instead of skipping it."
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test mode that disables writing to a csv, prints results directly to CLI."
    )

    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Path to output CSV file (default <input>_report.csv)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug-level logging."
    )

    return parser
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

def output_filename_for(input_file: str) -> str:
    base = input_file.rsplit(".", 1)[0]
    return base + "_report.csv"


def main():

    parser = build_parser()
    args = parser.parse_args()

    logging.basicConfig(
        level = logging.DEBUG if args.verbose else logging.INFO,
        format = "%(levelname)s: %(message)s"
    )

    input_file = args.input_file
    output_file = args.output if args.output else output_filename_for(input_file)

    total_lines = 0
    valid_lines = 0
    skipped_lines = 0

    levels = {"info": 0, "warn": 0, "error": 0}
    valid_levels = set(levels)

    actions = {}
    services = {}

    required_keys = ["timestamp", "level", "service", "action"]

    try:
        with open(input_file, "r") as file:

            for lineno, line in enumerate(file, start=1):
                if not line.strip():
                    continue

                total_lines += 1

                try:
                    obj = json.loads(line)

                    if not isinstance(obj, dict):
                        if args.strict:
                            logging.error(
                                "Line %d: invalid format (expected json format). Content=%r",
                                lineno,
                                line
                            )
                            raise SystemExit(1)
                        else:
                            logging.warning(
                                "Line %d: invalid format (expected json format). Content=%r",
                                lineno,
                                line
                            )
                            skipped_lines += 1
                            continue

                    # Check for correct keys
                    missing_keys = []

                    for key in required_keys:
                        if key not in obj.keys():
                            missing_keys.append(key)

                    if missing_keys:
                        if args.strict:
                            logging.error(
                                "Line %d: missing required keys=%s. Content=%r",
                                lineno,
                                missing_keys,
                                line
                            )
                            raise SystemExit(1)
                        else:
                            logging.warning(
                                "Line %d: missing required keys=%s. Skipping line. Content=%r",
                                lineno,
                                missing_keys,
                                line
                            )
                            skipped_lines += 1
                            continue

                    # type/empty validation

                    invalid_fields = []

                    for key in required_keys:
                        value = obj.get(key)

                        if not isinstance(value, str):
                            invalid_fields.append(key)
                            continue

                        clean = value.strip()
                        if not clean:
                            invalid_fields.append(key)
                            continue


                        if key == "level":
                            if clean.lower() not in valid_levels:
                                invalid_fields.append(key)
                                continue

                    if invalid_fields:
                        if args.strict:
                            logging.error(
                                "Line %d: invalid fields=%s. Content=%r",
                                lineno,
                                invalid_fields,
                                line
                            )
                            raise SystemExit(1)
                        else:
                            logging.warning(
                                "Line %d: invalid fields=%s, Skipping line. Content=%r",
                                lineno,
                                invalid_fields,
                                line
                            )
                            skipped_lines += 1
                            continue

                    level = obj["level"].strip().lower()
                    service = obj["service"].strip().lower()
                    action = obj["action"].strip().lower()

                    logging.debug("Line %d: level=%s service=%s action=%s", lineno, service, action)

                    # Deal with level metric
                    if level not in valid_levels:
                        if args.strict:
                            logging.error(
                                "Line %d: invalid level metric (expected info, warn, error). Content=%r",
                                lineno,
                                line
                                )
                            raise SystemExit(1)
                        else:
                            logging.warning(
                                "Line %d: invalid level metric (expected info, warn, level). Content=%r",
                                lineno,
                                line
                                )
                            skipped_lines += 1
                            continue


                    levels[level] += 1

                    if action not in actions:
                        actions[action] = 0

                    actions[action] += 1

                    if service not in services:
                        services[service] = 0
 
                    services[service] += 1

                        

                    valid_lines += 1
                

                except json.JSONDecodeError:
                    if args.strict:
                        logging.error(
                            "Line %d: invalid JSON. Content=%r",
                            lineno,
                            line
                        )
                        raise SystemExit(1)
                    else:
                        logging.warning(
                            "Line %d: invalid JSON. Skipping. Content=%r",
                            lineno,
                            line
                        )
                        skipped_lines += 1
                        continue
                

    except FileNotFoundError:
        logging.error("File not found: %s", input)
        raise SystemExit(1)
    
    if not actions:
        logging.error("No valid action data found.")
        raise SystemExit(1)

    if not services:
        logging.error("No valid service data found.")
        raise SystemExit(1)
    
    sorted_actions = sorted(
        actions.items(),
        key=lambda pair: (-pair[1], pair[0])
    )

    top_actions = sorted_actions[:3]

    if args.dry_run:
        logging.info("--- Dry Run ---")
        logging.info("Lines skipped: %d", skipped_lines)
        logging.info("Valid lines: %d", valid_lines)
        logging.info("Total lines: %d", total_lines)

        logging.info("--- levels ---")
        for level, total in levels.items():
            logging.info("%s: %d", level, total)

        logging.info("--- Services ---")
        for service, total in services.items():
            logging.info("%s: %d", service, total)

        logging.info("--- Top Actions ---")
        for action, total, in top_actions:
            logging.info("%s: %d", action, total)
        return
    
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow(["category", "total"])
        writer.writerow(["lines skipped", skipped_lines])
        writer.writerow(["valid lines", valid_lines])
        writer.writerow(["total lines", total_lines])

        writer.writerow(["---levels---", ""])
        for level, total in levels.items():
            writer.writerow([level, total])

        writer.writerow(["---services---", ""])
        for service, total in services.items():
            writer.writerow([service, total])

        writer.writerow(["---top_actions---", ""])
        for action, total in top_actions:
            writer.writerow([action, total])

        logging.info("Wrote report: %s", output_file)



if __name__ == "__main__":
    main()

    
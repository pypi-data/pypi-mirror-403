import argparse


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="schedint",
        description="Jodrell Bank pulsar observing schedule editor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    group = parser.add_argument_group("General options")

    group.add_argument(
        "--version",
        help="Show version info",
        required=False,
        action="store_true"
    )

    group.add_argument(
        "--export-yaml-template",
        help="Write out yaml template to submit new override request",
        required=False,
        action="store_true"
    )

    group = parser.add_argument_group("Read Overrides")

    group.add_argument(
        "--export-all",
        help="Export full list of overrides",
        required=False,
        action="store_true"
    )

    group.add_argument(
        "--export-by-user",
        help="Export full list of overrides requested by a user",
        required=False,
        default=None,
        type=str
    )

    group.add_argument(
        "--export-by-source",
        help="Export full list of overrides for a specific source",
        required=False,
        default=None,
        type=str
    )

    group.add_argument(
        "--export-by-id",
        help="Export override by id",
        required=False,
        default=None,
        type=str
    )

    group.add_argument(
        "--export-all-active",
        help="Export full list of active overrides",
        required=False,
        action="store_true"
    )

    group.add_argument(
        "--export-all-expired",
        help="Export full list of expired overrides",
        required=False,
        action="store_true"
    )

    group.add_argument(
        "--export-all-between-dates",
        help="Export full list of expired overrides",
        required=False,
        default=None,
        type=list
    )

    group = parser.add_argument_group("Submit new override")

    group.add_argument(
        "--source",
        help="Name of source to be overriden",
        required=False,
        default=None,
        type=str
    )

    group.add_argument(
        "--start-time",
        help="Time at which override becomes active (def=now)",
        required=False,
        type=str
    )

    group.add_argument(
        "--end-time",
        help="Time at which override expires",
        required=False,
        type=str
    )

    group.add_argument(
        "--set-cadence",
        help="New cadence (days)",
        required=False,
        type=int
    )

    group.add_argument(
        "--set-tobs",
        help="New integration time",
        required=False,
        type=int
    )

    group.add_argument(
        "--set-stars",
        help="New priority tier in stars",
        required=False,
        type=int
    )

    group.add_argument(
        "--reason",
        help="Reason for submission",
        required=False,
        type=str
    )

    group.add_argument(
        "--submit-file",
        help="Submit submission in yaml format",
        required=False,
        type=str
    )

    group = parser.add_argument_group("Delete existing override")

    group.add_argument(
        "--delete-by-id",
        help="id of override to remove",
        required=False,
        type=str
    )

    args = parser.parse_args()

    if args:
        pass

    parser.print_help()
    return 0

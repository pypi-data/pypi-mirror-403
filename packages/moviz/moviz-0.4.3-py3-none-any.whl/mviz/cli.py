import argparse
import sys

from .ice_tools.utils import cli_echo, cli_info, cli_hz, cli_record, cli_play


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="mtopic", description="mtopic command line interface")
    subparsers = parser.add_subparsers(dest="command", metavar="{echo,info,hz,record,play}")

    # echo
    p_echo = subparsers.add_parser("echo", help="Print messages on a topic")
    p_echo.add_argument("topic", help="Topic name")
    p_echo.add_argument("--type", default="auto", help="Message type (or 'auto') in mviz.ice_tools.msgs, e.g. G1State")
    p_echo.add_argument("--once", action="store_true", help="Print only the first message and exit")
    p_echo.add_argument("--limit", type=int, default=0, help="Maximum number of messages to print (0 = unlimited)")
    p_echo.add_argument("--rate", type=float, default=0.0, help="Throttle printing to N messages per second (0 = no throttle)")
    p_echo.add_argument("--filter", default=None, help="Regex to filter message text")
    p_echo.add_argument("--timeout", type=float, default=0.0, help="Timeout in seconds waiting for first message (0 = no timeout)")
    p_echo.add_argument("--namespace", default="", help="Optional namespace/prefix for the topic")
    p_echo.set_defaults(func=cli_echo.run)

    # info
    p_info = subparsers.add_parser("info", help="Show topic metadata and discovery info")
    p_info.add_argument("topic", help="Topic name")
    p_info.add_argument("--type", default="auto", help="Message type (or 'auto') in mviz.ice_tools.msgs, e.g. G1State")
    p_info.add_argument("--namespace", default="", help="Optional namespace/prefix for the topic")
    p_info.add_argument("--timeout", type=float, default=1.0, help="Discovery timeout seconds")
    p_info.set_defaults(func=cli_info.run)

    # hz
    p_hz = subparsers.add_parser("hz", help="Measure topic message frequency")
    p_hz.add_argument("topic", help="Topic name")
    p_hz.add_argument("--type", default="auto", help="Message type (or 'auto') in mviz.ice_tools.msgs, e.g. G1State")
    p_hz.add_argument("--window", type=float, default=5.0, help="Sliding window seconds for rate calculation")
    p_hz.add_argument("--warmup", type=int, default=3, help="Number of initial messages to skip for warmup")
    p_hz.add_argument("--report-every", type=float, default=1.0, help="Reporting interval seconds")
    p_hz.add_argument("--namespace", default="", help="Optional namespace/prefix for the topic")
    p_hz.add_argument("--timeout", type=float, default=0.0, help="Timeout in seconds waiting for first message (0 = no timeout)")
    p_hz.set_defaults(func=cli_hz.run)

    # record
    p_record = subparsers.add_parser("record", help="Record messages from topics to a .mbag file")
    p_record.add_argument("topics", nargs="*", help="Topic names to record (or use --all)")
    p_record.add_argument("--all", "-a", action="store_true", help="Record all available topics")
    p_record.add_argument("--output", "-o", help="Output file path (default: timestamped .mbag file)")
    p_record.add_argument("--namespace", default="", help="Optional namespace/prefix for topics")
    p_record.add_argument("--duration", "-d", type=float, default=0.0, help="Maximum recording duration in seconds (0 = unlimited)")
    p_record.add_argument("--limit", "-l", type=int, default=0, help="Maximum number of messages per topic (0 = unlimited)")
    p_record.set_defaults(func=cli_record.run)

    # play
    p_play = subparsers.add_parser("play", help="Play back messages from a .mbag file")
    p_play.add_argument("bagfile", help="Path to .mbag file")
    p_play.add_argument("--rate", "-r", type=float, default=1.0, help="Playback rate multiplier (default 1.0)")
    p_play.add_argument("--loop", action="store_true", help="Loop playback continuously")
    p_play.add_argument("--topics", nargs="*", help="Filter specific topics to play")
    p_play.set_defaults(func=cli_play.run)

    return parser


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    if not argv:
        parser.print_help()
        return 0
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 2
    try:
        return int(args.func(args) or 0)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())



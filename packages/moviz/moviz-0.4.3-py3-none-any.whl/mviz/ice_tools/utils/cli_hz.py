import sys
import time
from collections import deque

import iceoryx2 as iox2

from .subscription import (
    build_service_name,
    create_node,
    create_subscriber,
    resolve_message_type,
    detect_and_subscribe,
)


def run(args) -> int:
    node = create_node()
    service_name = build_service_name(args.namespace, args.topic)
    if getattr(args, "type", "auto") == "auto":
        try:
            msg_type_name, subscriber = detect_and_subscribe(node, service_name)
            print(f"[auto] detected type: {msg_type_name}")
        except Exception as exc:  # noqa: BLE001
            print(f"Failed to auto-detect message type: {exc}", file=sys.stderr)
            return 2
    else:
        msg_type_name: str = args.type
        message_type = resolve_message_type(msg_type_name)
        _, subscriber = create_subscriber(node, service_name, message_type)

    timestamps = deque()
    last_report = time.monotonic()
    received = 0
    first_message_deadline = (time.monotonic() + args.timeout) if args.timeout and args.timeout > 0 else None
    cycle_time = iox2.Duration.from_micros(10000)

    try:
        while True:
            try:
                node.wait(cycle_time)
            except iox2.NodeWaitFailure:
                return 130

            # drain any available samples
            while True:
                sample = subscriber.receive()
                if sample is None:
                    break
                now = time.monotonic()
                received += 1
                if received <= args.warmup:
                    continue
                timestamps.append(now)

            # keep only samples within the sliding window
            now = time.monotonic()
            cutoff = now - args.window
            while timestamps and timestamps[0] < cutoff:
                timestamps.popleft()

            # report even if no new messages arrived
            if now - last_report >= args.report_every:
                if len(timestamps) >= 2:
                    dt = timestamps[-1] - timestamps[0]
                    hz = (len(timestamps) - 1) / dt if dt > 0 else 0.0
                    print(f"average rate: {hz:.2f} Hz over {dt:.2f}s ({len(timestamps)} msgs)")
                elif len(timestamps) == 1:
                    # only one message -> cannot compute rate, but still provide feedback
                    print("average rate: 0.00 Hz (only 1 msg in window)")
                else:
                    print("average rate: 0.00 Hz (no messages)")
                last_report = now

            # handle timeout for first message if configured
            if first_message_deadline is not None and received == 0 and time.monotonic() > first_message_deadline:
                print("Timeout waiting for first message", file=sys.stderr)
                return 2
    except KeyboardInterrupt:
        return 130




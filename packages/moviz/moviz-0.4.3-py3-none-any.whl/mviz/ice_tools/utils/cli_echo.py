import sys
import time
from typing import Optional

import iceoryx2 as iox2

from .subscription import (
    build_service_name,
    create_node,
    create_subscriber,
    matches_filter,
    receive_samples,
    resolve_message_type,
    sample_to_string,
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

    printed = 0
    min_interval = (1.0 / args.rate) if args.rate and args.rate > 0 else 0.0
    last_print = 0.0

    try:
        for sample in receive_samples(subscriber, node, args.timeout):
            text = sample_to_string(sample)
            if not matches_filter(text, args.filter):
                continue
            now = time.monotonic()
            if min_interval and (now - last_print) < min_interval:
                continue
            print(text)
            last_print = now
            printed += 1
            if args.once or (args.limit and printed >= args.limit):
                break
        return 0
    except TimeoutError:
        print("Timeout waiting for first message", file=sys.stderr)
        return 2
    except iox2.NodeWaitFailure:
        return 130
    except KeyboardInterrupt:
        return 130




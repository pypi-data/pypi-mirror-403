import sys
import iceoryx2 as iox2
from .subscription import (
    build_service_name,
    create_node,
    resolve_message_type,
    detect_and_subscribe,
)


def run(args) -> int:
    service_name = build_service_name(args.namespace, args.topic)
    try:
        node = create_node()
        if getattr(args, "type", "auto") == "auto":
            msg_type_name, _subscriber = detect_and_subscribe(node, service_name)
        else:
            msg_type_name = args.type
            message_type = resolve_message_type(msg_type_name)
            _ = node.service_builder(service_name).publish_subscribe(message_type).open_or_create()
        print(f"Topic: {service_name.to_string()}")
        print(f"Type: {msg_type_name}")
        print("Transport: iceoryx2 (IPC)")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to query topic info: {exc}", file=sys.stderr)
        return 2
    except iox2.NodeWaitFailure:
        return 130
    except KeyboardInterrupt:
        return 130




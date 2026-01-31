import importlib
import re
import time
from typing import Generator, Optional, Tuple, Type

import iceoryx2 as iox2


def resolve_message_type(type_name: str):
    msgs_module = importlib.import_module("mviz.ice_tools.msgs")
    try:
        return getattr(msgs_module, type_name)
    except AttributeError as exc:
        raise SystemExit(f"Unknown message type: {type_name}") from exc


def build_service_name(namespace: str, topic: str) -> iox2.ServiceName:
    path = f"/{namespace.strip('/')}/{topic.strip('/')}" if namespace else f"/{topic.strip('/')}"
    return iox2.ServiceName.new(path)


def create_node() -> iox2.Node:
    iox2.set_log_level_from_env_or(iox2.LogLevel.Warn)
    return iox2.NodeBuilder.new().create(iox2.ServiceType.Ipc)


def create_subscriber(node: iox2.Node, service_name: iox2.ServiceName, message_type) -> Tuple[iox2.Node, any]:
    service = node.service_builder(service_name).publish_subscribe(message_type).open_or_create()
    subscriber = service.subscriber_builder().create()
    return node, subscriber


def receive_samples(
    subscriber,
    node: iox2.Node,
    first_message_timeout: float = 0.0,
):
    start = time.monotonic()
    cycle_time = iox2.Duration.from_micros(1000)
    first_received = False
    while True:
        node.wait(cycle_time)
        while True:
            sample = subscriber.receive()
            if sample is None:
                break
            first_received = True
            yield sample
        if not first_received and first_message_timeout > 0.0:
            if time.monotonic() - start > first_message_timeout:
                raise TimeoutError("No messages received within timeout")


def sample_to_string(sample, include_timestamp: bool = True) -> str:
    payload = sample.payload().contents
    msg_str = str(payload)
    if include_timestamp:
        timestamp_str = None
        if hasattr(payload, "header") and hasattr(payload.header, "stamp"):
            stamp = payload.header.stamp
            timestamp_str = f"[{stamp.sec}.{stamp.nanosec:09d}] "
        else:
            timestamp = time.time()
            sec = int(timestamp)
            nanosec = int((timestamp - sec) * 1e9)
            timestamp_str = f"[recv: {sec}.{nanosec:09d}] "
        return timestamp_str + msg_str
    return msg_str


def matches_filter(text: str, pattern: Optional[str]) -> bool:
    if not pattern:
        return True
    try:
        return re.search(pattern, text) is not None
    except re.error:
        return True


def list_available_message_types():
    msgs_module = importlib.import_module("mviz.ice_tools.msgs")
    names = getattr(msgs_module, "__all__", [])
    result = []
    for name in names:
        try:
            result.append((name, getattr(msgs_module, name)))
        except AttributeError:
            continue
    return result


def detect_and_subscribe(node: iox2.Node, service_name: iox2.ServiceName):
    last_exc: Optional[Exception] = None
    for name, msg_type in list_available_message_types():
        try:
            _node, subscriber = create_subscriber(node, service_name, msg_type)
            return name, subscriber
        except Exception as exc:  # noqa: BLE001
            last_exc = exc
            continue
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("No message types available for detection")



import gzip
import pickle
import sys
import time
from collections import defaultdict
from typing import Dict, List, Tuple, Any

import iceoryx2 as iox2

from .subscription import (
    build_service_name,
    create_node,
    create_subscriber,
    detect_and_subscribe,
    list_available_message_types,
)


def serialize_sample(sample) -> Dict[str, Any]:
    payload = sample.payload().contents
    
    # Convert ctypes.Structure to dictionary
    if hasattr(payload, '_fields_'):
        data = {}
        for field_name, _ in payload._fields_:
            value = getattr(payload, field_name)
            if hasattr(value, '_fields_'):  # Nested structure
                data[field_name] = serialize_sample_value(value)
            else:
                data[field_name] = value
        return data
    else:
        # For simple types, return as-is
        return payload


def serialize_sample_value(value) -> Dict[str, Any]:
    if hasattr(value, '_fields_'):
        data = {}
        for field_name, _ in value._fields_:
            nested_value = getattr(value, field_name)
            data[field_name] = serialize_sample_value(nested_value)
        return data
    else:
        return value


def list_all_topics(node: iox2.Node, namespace: str = "") -> List[Tuple[str, str]]:
    topics = []
    available_types = list_available_message_types()
    
    # try common topic names with different message types
    common_topics = ["state", "pose", "quat", "joints", "imu", "camera", "depth"]
    
    for topic in common_topics:
        service_name = build_service_name(namespace, topic)
        for type_name, msg_type in available_types:
            try:
                _, subscriber = create_subscriber(node, service_name, msg_type)
                topics.append((topic, type_name))
                break  # found working type for this topic
            except Exception:
                continue
    
    return topics


def run(args) -> int:
    node = create_node()
    
    # determine topics to record
    if args.all:
        print("Discovering available topics...")
        topics_to_record = list_all_topics(node, args.namespace)
        if not topics_to_record:
            print("No topics found to record", file=sys.stderr)
            return 2
        print(f"Found {len(topics_to_record)} topics: {[t[0] for t in topics_to_record]}")
    else:
        if not args.topics:
            print("No topics specified. Use --all to record all topics or specify topic names.", file=sys.stderr)
            return 2
        topics_to_record = [(topic, "auto") for topic in args.topics]
    
    # create subscribers for all topics
    subscribers = {}
    topic_metadata = {}
    
    for topic, msg_type_name in topics_to_record:
        service_name = build_service_name(args.namespace, topic)
        
        if msg_type_name == "auto":
            try:
                detected_type, subscriber = detect_and_subscribe(node, service_name)
                print(f"[{topic}] auto-detected type: {detected_type}")
                topic_metadata[topic] = detected_type
            except Exception as exc:
                print(f"Failed to auto-detect message type for topic '{topic}': {exc}", file=sys.stderr)
                continue
        else:
            try:
                from .subscription import resolve_message_type
                message_type = resolve_message_type(msg_type_name)
                _, subscriber = create_subscriber(node, service_name, message_type)
                topic_metadata[topic] = msg_type_name
            except Exception as exc:
                print(f"Failed to create subscriber for topic '{topic}': {exc}", file=sys.stderr)
                continue
        
        subscribers[topic] = subscriber
    
    if not subscribers:
        print("No valid subscribers created", file=sys.stderr)
        return 2
    
    # prepare output file
    if not args.output:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        args.output = f"recording_{timestamp}.mbag"
    
    print(f"Recording to: {args.output}")
    print(f"Topics: {list(subscribers.keys())}")
    print("Press Ctrl+C to stop recording...")
    
    # recording data structure
    messages = []
    message_counts = defaultdict(int)
    start_time = time.time()
    last_progress_time = start_time
    
    try:
        cycle_time = iox2.Duration.from_micros(1000)  # 1ms cycle
        
        while True:
            node.wait(cycle_time)
            
            # Check for messages from all subscribers
            for topic, subscriber in subscribers.items():
                while True:
                    sample = subscriber.receive()
                    if sample is None:
                        break
                    
                    # Check limits
                    if args.limit > 0 and message_counts[topic] >= args.limit:
                        continue
                    
                    # Record message
                    timestamp = time.time()
                    serialized_data = serialize_sample(sample)
                    messages.append((timestamp, topic, topic_metadata[topic], serialized_data))
                    message_counts[topic] += 1
            
            # Check duration limit
            if args.duration > 0 and (time.time() - start_time) >= args.duration:
                print(f"\nDuration limit ({args.duration}s) reached")
                break
            
            # Progress reporting
            now = time.time()
            if now - last_progress_time >= 1.0:  # Report every second
                total_messages = sum(message_counts.values())
                duration = now - start_time
                print(f"\rMessages: {total_messages} | Duration: {duration:.1f}s | Topics: {dict(message_counts)}", end="", flush=True)
                last_progress_time = now
    
    except KeyboardInterrupt:
        print(f"\nRecording stopped by user")
    except iox2.NodeWaitFailure:
        print(f"\nNode wait failure")
    
    # Save recorded data (always try to save, even after exceptions)
    if messages:
        print(f"\nSaving {len(messages)} messages to {args.output}...")
        
        bag_data = {
            "version": "1.0",
            "metadata": {
                "created": start_time,
                "topics": topic_metadata,
                "message_counts": dict(message_counts),
                "duration": time.time() - start_time
            },
            "messages": messages
        }
        
        try:
            with gzip.open(args.output, 'wb') as f:
                pickle.dump(bag_data, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            print(f"Successfully saved {len(messages)} messages to {args.output}")
            print(f"Topics recorded: {list(topic_metadata.keys())}")
            print(f"Message counts: {dict(message_counts)}")
            return 0
            
        except Exception as exc:
            print(f"Failed to save recording: {exc}", file=sys.stderr)
            return 1
    else:
        print("No messages recorded")
        return 0



import gzip
import pickle
import sys
import time
from typing import Dict, List, Tuple, Any

import iceoryx2 as iox2

from .subscription import (
    build_service_name,
    create_node,
    resolve_message_type,
)


def deserialize_sample(data: Dict[str, Any], msg_type_name: str):
    from .subscription import resolve_message_type
    
    message_type = resolve_message_type(msg_type_name)
    
    # create instance of the message type
    instance = message_type()
    
    # fill in the fields
    for field_name, value in data.items():
        if hasattr(instance, field_name):
            if isinstance(value, dict) and hasattr(getattr(instance, field_name), '_fields_'):
                # nested structure - recursively deserialize
                nested_instance = deserialize_sample(value, getattr(instance, field_name).__class__.__name__)
                setattr(instance, field_name, nested_instance)
            else:
                setattr(instance, field_name, value)
    
    return instance


def run(args) -> int:
    # load the bag file
    try:
        with gzip.open(args.bagfile, 'rb') as f:
            bag_data = pickle.load(f)
    except Exception as exc:
        print(f"Failed to load bag file '{args.bagfile}': {exc}", file=sys.stderr)
        return 2
    
    if bag_data.get("version") != "1.0":
        print(f"Unsupported bag version: {bag_data.get('version')}", file=sys.stderr)
        return 2
    
    metadata = bag_data.get("metadata", {})
    messages = bag_data.get("messages", [])
    
    if not messages:
        print("No messages found in bag file", file=sys.stderr)
        return 2
    
    print(f"Loaded bag file: {args.bagfile}")
    print(f"Topics: {list(metadata.get('topics', {}).keys())}")
    print(f"Total messages: {len(messages)}")
    print(f"Duration: {metadata.get('duration', 0):.2f}s")
    
    # Filter topics if specified
    if args.topics:
        filtered_messages = []
        for timestamp, topic, msg_type, data in messages:
            if topic in args.topics:
                filtered_messages.append((timestamp, topic, msg_type, data))
        messages = filtered_messages
        print(f"Filtered to topics: {args.topics}")
        print(f"Filtered messages: {len(messages)}")
    
    if not messages:
        print("No messages match the topic filter", file=sys.stderr)
        return 2
    
    # create node and publishers
    node = create_node()
    publishers = {}
    
    # group messages by topic to create publishers
    topics_to_publish = set(msg[1] for msg in messages)
    
    for topic in topics_to_publish:
        # find the message type for this topic
        msg_type_name = metadata.get("topics", {}).get(topic)
        if not msg_type_name:
            print(f"Unknown message type for topic '{topic}'", file=sys.stderr)
            continue
        
        try:
            message_type = resolve_message_type(msg_type_name)
            service_name = build_service_name("", topic)  # Use empty namespace for playback
            service = node.service_builder(service_name).publish_subscribe(message_type).open_or_create()
            publisher = service.publisher_builder().create()
            publishers[topic] = publisher
            print(f"Created publisher for topic '{topic}' (type: {msg_type_name})")
        except Exception as exc:
            print(f"Failed to create publisher for topic '{topic}': {exc}", file=sys.stderr)
            continue
    
    if not publishers:
        print("No publishers created", file=sys.stderr)
        return 2
    
    # sort messages by timestamp
    messages.sort(key=lambda x: x[0])
    
    print(f"\nStarting playback...")
    print(f"Rate: {args.rate}x")
    print(f"Loop: {'Yes' if args.loop else 'No'}")
    print("Press Ctrl+C to stop playback...")
    
    try:
        start_time = time.time()
        last_timestamp = None
        message_count = 0
        
        while True:
            for timestamp, topic, msg_type, data in messages:
                if topic not in publishers:
                    continue
                
                # calculate sleep time based on rate
                if last_timestamp is not None:
                    time_diff = (timestamp - last_timestamp) / args.rate
                    if time_diff > 0:
                        time.sleep(time_diff)
                
                # deserialize and publish message
                try:
                    sample_data = deserialize_sample(data, msg_type)
                    publisher = publishers[topic]
                    
                    # use the correct iceoryx2 publisher api
                    sample = publisher.loan_uninit()
                    sample = sample.write_payload(sample_data)
                    sample.send()
                    
                    message_count += 1
                    
                    if message_count % 100 == 0:
                        elapsed = time.time() - start_time
                        print(f"\rPublished: {message_count}/{len(messages)} | Elapsed: {elapsed:.1f}s", end="", flush=True)
                
                except Exception as exc:
                    print(f"\nFailed to publish message {message_count}: {exc}", file=sys.stderr)
                    continue
                
                last_timestamp = timestamp
            
            if not args.loop:
                break
            
            print(f"\nLooping playback... ({message_count} messages)")
            last_timestamp = None
            message_count = 0
            start_time = time.time()
    
    except KeyboardInterrupt:
        print(f"\nPlayback stopped by user")
    except iox2.NodeWaitFailure:
        print(f"\nNode wait failure")
        return 130
    
    print(f"\nPlayback completed. Published {message_count} messages.")
    return 0



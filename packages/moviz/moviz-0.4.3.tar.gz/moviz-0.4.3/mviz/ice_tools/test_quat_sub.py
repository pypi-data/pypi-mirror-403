import iceoryx2 as iox2
from mviz.ice_tools.msgs import G1Quat


def main() -> None:
    iox2.set_log_level_from_env_or(iox2.LogLevel.Info)
    node = iox2.NodeBuilder.new().create(iox2.ServiceType.Ipc)
    service = (
        node.service_builder(iox2.ServiceName.new("/mviz/quat"))
        .publish_subscribe(G1Quat)
        .open_or_create()
    )
    subscriber = service.subscriber_builder().create()
    print("Subscriber ready to receive /mviz/quat data!")

    cycle_time = iox2.Duration.from_micros(100)
    try:
        while True:
            node.wait(cycle_time)
            while True:
                sample = subscriber.receive()
                if sample is None:
                    break
                payload = sample.payload().contents
                print("received:", payload)
    except iox2.NodeWaitFailure:
        print("exit")


if __name__ == "__main__":
    main()



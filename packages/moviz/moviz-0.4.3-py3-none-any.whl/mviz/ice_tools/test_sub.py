import iceoryx2 as iox2
from mviz.ice_tools.msgs import G1State

cycle_time = iox2.Duration.from_micros(1)

iox2.set_log_level_from_env_or(iox2.LogLevel.Info)
node = iox2.NodeBuilder.new().create(iox2.ServiceType.Ipc)

service = (
    node.service_builder(iox2.ServiceName.new("/mviz/state"))
    .publish_subscribe(G1State)
    .open_or_create()
)

subscriber = service.subscriber_builder().create()

print("Subscriber ready to receive data!")

try:
    while True:
        node.wait(cycle_time)
        while True:
            sample = subscriber.receive()
            if sample is not None:
                payload = sample.payload().contents
                print("received:", payload)
            else:
                break

except iox2.NodeWaitFailure:
    print("exit")
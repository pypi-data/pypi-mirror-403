import time
import math

import iceoryx2 as iox2
from mviz.ice_tools.msgs import G1Quat, Quaternion


def build_quat(counter: int) -> G1Quat:
    phase = counter * 0.05
    def q_from_yaw(yaw: float) -> Quaternion:
        half = 0.5 * yaw
        s = math.sin(half)
        c = math.cos(half)
        return Quaternion(qx=0.0, qy=0.0, qz=s, qw=c)

    gq = G1Quat()
    for field_name, _ in gq._fields_:
        setattr(gq, field_name, q_from_yaw(phase))
    return gq


def main() -> None:
    iox2.set_log_level_from_env_or(iox2.LogLevel.Info)
    node = iox2.NodeBuilder.new().create(iox2.ServiceType.Ipc)
    service = (
        node.service_builder(iox2.ServiceName.new("/mviz/quat"))
        .publish_subscribe(G1Quat)
        .open_or_create()
    )
    publisher = service.publisher_builder().create()

    counter = 0
    try:
        while True:
            counter += 1
            sample = publisher.loan_uninit()
            sample = sample.write_payload(build_quat(counter))
            sample.send()
            time.sleep(0.01)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()



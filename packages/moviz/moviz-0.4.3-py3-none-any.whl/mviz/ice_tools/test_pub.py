import math

import iceoryx2 as iox2
from mviz.ice_tools.msgs import G1State, Kpose

cycle_time = iox2.Duration.from_secs_f64(0.01)

iox2.set_log_level_from_env_or(iox2.LogLevel.Info)
node = iox2.NodeBuilder.new().create(iox2.ServiceType.Ipc)

service = (
    node.service_builder(iox2.ServiceName.new("/mviz/msg"))
    .publish_subscribe(G1State)
    .open_or_create()
)

publisher = service.publisher_builder().create()


def build_state(counter: int) -> G1State:
    phase = counter * 0.1
    root_pose = Kpose(
        x=0.1 * math.sin(phase),
        y=0.0,
        z=0.9,
        qx=0.0,
        qy=0.0,
        qz=0.0,
        qw=1.0,
    )

    state = G1State(root_joint=root_pose)
    swing = math.sin(phase)
    bend = math.sin(phase * 0.5)

    state.left_hip_pitch_joint = 0.4 * swing
    state.right_hip_pitch_joint = -0.4 * swing
    state.left_knee_joint = 0.8 * bend
    state.right_knee_joint = 0.8 * bend
    state.left_shoulder_pitch_joint = 0.3 * swing
    state.right_shoulder_pitch_joint = 0.3 * swing
    state.waist_yaw_joint = 0.2 * bend

    return state

COUNTER = 0
try:
    while True:
        COUNTER += 1
        node.wait(cycle_time)
        sample = publisher.loan_uninit()
        sample = sample.write_payload(build_state(COUNTER))
        sample.send()
        print("Send sample", COUNTER, "...")

except iox2.NodeWaitFailure:
    print("exit")
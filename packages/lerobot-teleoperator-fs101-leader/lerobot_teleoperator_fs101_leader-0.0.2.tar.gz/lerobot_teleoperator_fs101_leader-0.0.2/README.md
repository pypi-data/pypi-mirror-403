# LeRobot + teleop Integration

## Getting Started

```bash
pip install lerobot_teleoperator_fs101_leader

lerobot-teleoperate \
    --robot.type=lerobot_robot_fs101_follower \
    --robot.port=/dev/ttyUSB1 \
    --robot.id=my_awesome_fs101_follower_arm \
    --teleop.type=lerobot_teleoperator_fs101_leader \
    --teleop.port=/dev/ttyUSB0 \
    --teleop.id=my_awesome_fs101_leader_arm
```

# RobotPy QuestNav

Python implementation of questnav-lib for FRC robots.

## Installation

```powershell
pip install .
```

## Usage

```python
from questnav import QuestNav, PoseFrame
from wpimath.geometry import Pose2d, Rotation2d, Pose3d

questnav = QuestNav()

initial_pose = Pose2d(1.0, 2.0, Rotation2d.fromDegrees(90))
questnav.set_pose(Pose3d(initial_pose))

questnav.command_periodic()
frames = questnav.get_all_unread_pose_frames()
```

## Requirements

- `protobuf`
- RobotPy environment providing `ntcore` and `wpimath`


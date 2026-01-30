from argparse import ArgumentParser

from pitechcar.car import PiTechCar, ControlMode


CONTROL_MODES = ("left_only", "right_only", "mixed")

def main() -> None:
    parser = ArgumentParser(description="PiTechCar joystick control configuration")

    parser.add_argument(
        "--control",
        choices=CONTROL_MODES,
        default="mixed",
        help=(
            "Joystick control mode: "
            "'left_only' and 'right_only' use one joystick for both speed and steering. "
            "'mixed' uses the left vertical axis for speed and the right horizontal axis "
            "for steering angle."
        ),
    )

    args = parser.parse_args()

    car = PiTechCar(control_mode=ControlMode(args.control))
    car.run()

if __name__ == "__main__":
    main()

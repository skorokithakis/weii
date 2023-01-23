import argparse
import re
import statistics
import subprocess
import sys
import time
from typing import List
from typing import Optional

import evdev
from evdev import ecodes


TERSE = False


def debug(message: str, force: bool = False) -> None:
    if force or not TERSE:
        print(message)


def get_board_device() -> Optional[evdev.InputDevice]:
    """Return the Wii Balance Board device."""
    devices = [
        path
        for path in evdev.list_devices()
        if evdev.InputDevice(path).name == "Nintendo Wii Remote Balance Board"
    ]
    if not devices:
        return None

    board = evdev.InputDevice(
        devices[0],
    )
    return board


def get_raw_measurement(device: evdev.InputDevice) -> float:
    """Read one measurement from the board."""
    data = [None] * 4
    while True:
        event = device.read_one()
        if event is None:
            continue

        # Measurements are in decigrams, so we convert them to kilograms here.
        if event.code == ecodes.ABS_HAT1X:
            # Top left.
            data[0] = event.value / 100
        elif event.code == ecodes.ABS_HAT0X:
            # Top right.
            data[1] = event.value / 100
        elif event.code == ecodes.ABS_HAT0Y:
            # Bottom left.
            data[2] = event.value / 100
        elif event.code == ecodes.ABS_HAT1Y:
            # Bottom right.
            data[3] = event.value / 100
        elif event.code == ecodes.BTN_A:
            sys.exit("ERROR: User pressed board button while measuring, aborting.")
        elif event.code == ecodes.SYN_DROPPED:
            pass
        elif event.code == ecodes.SYN_REPORT and event.value == 3:
            pass
        elif event.code == ecodes.SYN_REPORT and event.value == 0:
            if None in data:
                # This measurement failed to read one of the sensors, try again.
                data = [None] * 4
                continue
            else:
                return sum(data)  # type: ignore
        else:
            debug(f"ERROR: Got unexpected event: {evdev.categorize(event)}")


def read_data(device: evdev.InputDevice, samples: int, threshold: float) -> List[float]:
    """
    Read weight data from the board.

    samples - The number of samples we ideally want to collect, if the user doesn't
              cancel.
    threshold - The weight (in kilos) to cross before starting to consider measurements
                valid.
    """
    data: List[float] = []
    while True:
        measurement = get_raw_measurement(device)
        if len(data) and measurement < threshold:
            # The user stepped off the board.
            debug("User stepped off.")
            break
        if len(data) == 0 and measurement < threshold:
            # This measurement is too light and measurement hasn't yet started, ignore.
            continue
        data.append(measurement)
        if len(data) == 1:
            debug("\aMeasurement started, please wait...")
        if len(data) > samples:
            # We have enough samples now.
            break
    device.close()
    return data


def measure_weight(
    adjust: float,
    disconnect_address: str,
    command: Optional[str],
    terse: bool,
    fake: bool = False,
) -> float:
    """Perform one weight measurement."""
    if disconnect_address and not re.match(
        r"^([0-9a-f]{2}[:]){5}([0-9a-f]{2})$", disconnect_address, re.IGNORECASE
    ):
        sys.exit("ERROR: Invalid device address to disconnect specified.")

    debug("Waiting for balance board...")
    while not fake:
        board = get_board_device()
        if board:
            break
        time.sleep(0.5)
    debug("\aBalance board found, please step on.")

    if fake:
        weight_data = [85.2] * 200
    else:
        weight_data = read_data(board, 200, threshold=20)

    final_weight = statistics.median(weight_data)
    final_weight += adjust

    if terse:
        debug(f"{final_weight:.1f}", force=True)
    else:
        debug(f"\aDone, weight: {final_weight:.1f}.")

    if disconnect_address:
        debug("Disconnecting...")
        subprocess.run(
            ["/usr/bin/env", "bluetoothctl", "disconnect", disconnect_address],
            capture_output=True,
        )

    if command:
        subprocess.run(command.replace("{weight}", f"{final_weight:.1f}"), shell=True)

    return final_weight


def cli():
    parser = argparse.ArgumentParser(
        description="Measure weight using a Wii Balance Board."
    )
    parser.add_argument(
        "-a",
        "--adjust",
        help="adjust the final weight by some value (e.g. to match some other scale,"
        " or to account for clothing)",
        type=float,
        default=0,
    )
    parser.add_argument(
        "-c",
        "--command",
        help="the command to run when done (use `{weight}` to pass the weight "
        "to the command",
        type=str,
        metavar="ADDRESS",
        default="",
    )
    parser.add_argument(
        "-d",
        "--disconnect-when-done",
        help="disconnect the board when done, so it turns off",
        type=str,
        metavar="ADDRESS",
        default="",
    )
    parser.add_argument(
        "-w",
        "--weight-only",
        action="store_true",
        help="only print the final weight",
    )

    args = parser.parse_args()

    if args.weight_only:
        global TERSE
        TERSE = True

    measure_weight(
        args.adjust,
        args.disconnect_when_done,
        command=args.command,
        terse=args.weight_only,
    )


if __name__ == "__main__":
    cli()

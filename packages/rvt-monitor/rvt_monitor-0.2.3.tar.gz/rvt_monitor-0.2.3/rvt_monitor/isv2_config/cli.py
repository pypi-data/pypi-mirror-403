"""ISV2 Motor Configuration CLI."""

import argparse
import sys

from .protocol import ISV2Client, ISV2Error


def cmd_read(client: ISV2Client, args) -> int:
    """Read register(s)."""
    try:
        addr = int(args.reg_addr, 0)  # Support hex (0x...) and decimal
        count = args.count

        values = client.read(addr, count)

        print(f"Address 0x{addr:04X} ({count} register{'s' if count > 1 else ''}):")
        for i, val in enumerate(values):
            reg_addr = addr + i
            print(f"  0x{reg_addr:04X}: 0x{val:04X} ({val})")

        return 0
    except ISV2Error as e:
        print(f"Error: {e}")
        return 1


def cmd_write(client: ISV2Client, args) -> int:
    """Write to register."""
    try:
        addr = int(args.reg_addr, 0)
        value = int(args.value, 0)

        if args.bits == 32:
            success = client.write32(addr, value)
        else:
            success = client.write16(addr, value)

        if success:
            print(f"Written 0x{value:0{args.bits//4}X} to 0x{addr:04X}")

            # Verify if requested
            if args.verify:
                count = 2 if args.bits == 32 else 1
                verify = client.read(addr, count)
                if args.bits == 32:
                    read_val = (verify[0] << 16) | verify[1]
                else:
                    read_val = verify[0]

                if read_val == value:
                    print(f"Verified: OK")
                else:
                    print(f"Verified: MISMATCH (read 0x{read_val:0{args.bits//4}X})")
                    return 1

        return 0
    except ISV2Error as e:
        print(f"Error: {e}")
        return 1


def cmd_status(client: ISV2Client, args) -> int:
    """Read motor status."""
    try:
        status = client.read_status()

        print("ISV2 Motor Status")
        print("-" * 30)
        print(f"Alarm Code: 0x{status['alarm_code']:03X}")
        print(f"Alarm:      {status['alarm_text']}")

        return 0
    except ISV2Error as e:
        print(f"Error: {e}")
        return 1


def cmd_params(client: ISV2Client, args) -> int:
    """Read parameters."""
    try:
        results = client.read_all_params()

        print("ISV2 Parameters")
        print("-" * 60)
        print(f"{'Param':<10} {'Description':<18} {'Value':>6}  {'Setting':<20}")
        print("-" * 60)

        for p in results:
            if "error" in p:
                print(f"{p['name']:<10} ERROR: {p['error']}")
            else:
                print(f"{p['name']:<10} {p['description']:<18} {p['value']:>6}  {p['mapped']:<20}")

        return 0
    except ISV2Error as e:
        print(f"Error: {e}")
        return 1


def cmd_save(client: ISV2Client, args) -> int:
    """Save parameters to EEPROM."""
    try:
        if args.dry_run:
            print("Dry-run: Would save parameters to EEPROM")
            return 0

        success = client.save()
        if success:
            print("Parameters saved to EEPROM")
        return 0
    except ISV2Error as e:
        print(f"Error: {e}")
        return 1


def cmd_baudrate(client: ISV2Client, args) -> int:
    """Read or set baud rate."""
    try:
        if args.set_value is not None:
            # Set baud rate
            if args.dry_run:
                print(f"Dry-run: Would set baud rate to value {args.set_value}")
                return 0

            success = client.set_baudrate(args.set_value)
            if success:
                baudrate = client.BAUD_RATES.get(args.set_value, "unknown")
                print(f"Baud rate set to {baudrate} (value: {args.set_value})")
                print("Save to motor and reconnect with new baud rate.")
            return 0
        else:
            # Read baud rate
            result = client.read_baudrate()
            baudrate = result["baudrate"] or "unknown"
            print(f"Current baud rate: {baudrate} bps (value: {result['value']})")
            return 0
    except ISV2Error as e:
        print(f"Error: {e}")
        return 1


def cmd_factory_reset(client: ISV2Client, args) -> int:
    """Factory reset."""
    try:
        if args.dry_run:
            print("Dry-run: Would perform factory reset")
            return 0

        if not args.force:
            print("WARNING: Factory reset will restore ALL parameters to defaults.")
            print("Use --force to confirm.")
            return 1

        success = client.factory_reset()
        if success:
            print("Factory reset completed. Power cycle the motor.")
        return 0
    except ISV2Error as e:
        print(f"Error: {e}")
        return 1


def cmd_serve(args) -> int:
    """Start web server."""
    from .server import run_server
    import webbrowser
    import threading

    host = args.host
    port = args.web_port

    url = f"http://{host}:{port}"
    print(f"Starting ISV2 Config server at {url}")

    # Open browser after short delay
    def open_browser():
        import time
        time.sleep(1)
        webbrowser.open(url)

    threading.Thread(target=open_browser, daemon=True).start()

    run_server(host=host, port=port)
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="isv2-config",
        description="ISV2-RS2 Motor Configuration Tool",
    )

    # Global options
    parser.add_argument(
        "-p", "--port",
        help="Serial port (e.g., COM6, /dev/ttyUSB0)",
    )
    parser.add_argument(
        "-a", "--address",
        type=lambda x: int(x, 0),
        default=0x11,
        help="Device address (default: 0x11)",
    )
    parser.add_argument(
        "-b", "--baudrate",
        type=int,
        default=38400,
        help="Baud rate (default: 38400)",
    )
    parser.add_argument(
        "-t", "--timeout",
        type=float,
        default=0.2,
        help="Timeout in seconds (default: 0.2)",
    )
    parser.add_argument(
        "-r", "--retries",
        type=int,
        default=3,
        help="Number of retries (default: 3)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output (show packets)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry-run mode (no actual writes)",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Web server host address (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--web-port",
        type=int,
        default=8001,
        help="Web server port (default: 8001)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # read command
    read_parser = subparsers.add_parser("read", help="Read register(s)")
    read_parser.add_argument("reg_addr", help="Register address (hex or decimal)")
    read_parser.add_argument("count", type=int, nargs="?", default=1, help="Number of registers")

    # write command
    write_parser = subparsers.add_parser("write", help="Write to register")
    write_parser.add_argument("reg_addr", help="Register address (hex or decimal)")
    write_parser.add_argument("value", help="Value to write (hex or decimal)")
    write_parser.add_argument("--bits", type=int, choices=[16, 32], default=16, help="Value size")
    write_parser.add_argument("--verify", action="store_true", help="Verify after write")

    # status command
    subparsers.add_parser("status", help="Read motor status")

    # params command
    subparsers.add_parser("params", help="Read all parameters (Pr0.01, Pr5.29-31)")

    # save command
    subparsers.add_parser("save", help="Save parameters to EEPROM")

    # baudrate command
    baudrate_parser = subparsers.add_parser("baudrate", help="Read or set baud rate")
    baudrate_parser.add_argument(
        "--set", "-s",
        type=int,
        choices=[0, 1, 2, 3, 4, 5, 6],
        dest="set_value",
        help="Set baud rate: 0=2400, 1=4800, 2=9600, 3=19200, 4=38400, 5=57600, 6=115200",
    )

    # factory-reset command
    reset_parser = subparsers.add_parser("factory-reset", help="Factory reset (restore defaults)")
    reset_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Confirm factory reset",
    )

    args = parser.parse_args()

    # Default: start web server if no command specified
    if not args.command:
        return cmd_serve(args)

    # Other commands require serial port
    if not args.port:
        print("Error: --port is required for this command")
        return 1

    # Connect and execute command
    try:
        with ISV2Client(
            port=args.port,
            device_addr=args.address,
            baudrate=args.baudrate,
            timeout=args.timeout,
            retries=args.retries,
            verbose=args.verbose,
        ) as client:
            if args.command == "read":
                return cmd_read(client, args)
            elif args.command == "write":
                if args.dry_run:
                    print(f"Dry-run: Would write to 0x{int(args.reg_addr, 0):04X}")
                    return 0
                return cmd_write(client, args)
            elif args.command == "status":
                return cmd_status(client, args)
            elif args.command == "params":
                return cmd_params(client, args)
            elif args.command == "save":
                return cmd_save(client, args)
            elif args.command == "baudrate":
                return cmd_baudrate(client, args)
            elif args.command == "factory-reset":
                return cmd_factory_reset(client, args)

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

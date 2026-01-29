import click
import socket
import platform


if platform.system() == "Windows":
    SOCKET_FAMILY = socket.AF_INET
    SOCKET_ADDR = ("127.0.0.1", 7154)
else:
    SOCKET_FAMILY = socket.AF_UNIX
    SOCKET_ADDR = "\x00/tmp/telepointer-socket"



def send_msg(*msgs):
    try:
        with socket.socket(family=SOCKET_FAMILY) as client:
            client.connect(SOCKET_ADDR)
            for msg in msgs:
                encoded = bytearray(msg, "utf-8")
                client.send(encoded)
            client.recv(1)
            client.close()
    except ConnectionRefusedError:
        print("Could not connect to telepointer. Is it currently running?")
    except:
        print("An unknown error occured.")


@click.group()
def cli():
    pass


@cli.command(None, short_help="start cursor control")
def start():
    send_msg("STRT")


@cli.command(None, short_help="stop cursor control")
def stop():
    send_msg("STOP")


@cli.command(None, short_help="calibrate current face landmarker processor")
def calibrate():
    send_msg("CALI")


@cli.group("click", short_help="trigger a mouse click")
def mouse_click():
    pass

@mouse_click.command("left", short_help="trigger a left mouse click")
def mouse_click_left():
    send_msg("CLCK", "LEFT")

@mouse_click.command("right", short_help="trigger a right mouse click")
def mouse_click_right():
    send_msg("CLCK", "RGHT")

@cli.group(None, short_help="hold down a mouse button")
def press():
    pass

@press.command("left", short_help="hold down left mouse button")
def press_left():
    send_msg("PUSH", "LEFT")

@press.command("right", short_help="hold down right mouse button")
def press_right():
    send_msg("PUSH", "RGHT")

@cli.group(None, short_help="release a mouse button")
def lift():
    pass

@lift.command("left", short_help="release left mouse button")
def lift_left():
    send_msg("LIFT", "LEFT")

@lift.command("right", short_help="release right mouse button")
def lift_left():
    send_msg("LIFT", "RGHT")

@cli.command(None, short_help="tell telepointer to exit")
def quit():
    send_msg("QUIT")

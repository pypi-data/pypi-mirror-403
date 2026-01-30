import sys
from commandly.commands.hello import hello_command
from commandly.commands.version import version_command
from commandly.commands.doctor import doctor_command

def main():
    if len(sys.argv) < 2:
        print("Usage: commandly <command>")
        print("Commands: hello, version, doctor")
        return

    command = sys.argv[1]

    if command == "hello":
        hello_command()
    elif command == "version":
        version_command()
    elif command == "doctor":
        doctor_command()
    else:
        print("Unknown command")
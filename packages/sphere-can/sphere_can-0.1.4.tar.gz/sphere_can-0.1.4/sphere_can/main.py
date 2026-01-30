import typer
from sphere_can.readcan import readcan
from sphere_can.sendcan import sendcan
from sphere_can.status import status
from sphere_can.setup import setup
from sphere_can.stop import stop

app = typer.Typer(help="SPHERE CAN command-line interface")

app.command()(readcan)
app.command()(sendcan)
app.command()(status)
app.command()(stop)
app.add_typer(setup, name="setup")

def main():
    app()

if __name__ == "__main__":
    main()

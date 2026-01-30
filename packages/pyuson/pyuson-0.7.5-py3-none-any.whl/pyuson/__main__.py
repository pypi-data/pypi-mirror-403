"""Run the GUI when using pyuson as a module.

Usage : `python -m pyuson`
"""


def main():
    """Run GUI."""
    from . import gui

    print("Running GUI...")
    gui.run()


if __name__ == "__main__":
    main()

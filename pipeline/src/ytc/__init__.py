# The CLI is imported on call so a light install (the Atlas publisher in CI) can import ytc.atlas.publish without
# the studio's heavy dependencies.
def main():
    from .cli import main as cli_main

    return cli_main()


__all__ = ["main"]

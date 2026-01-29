def greet(name: str = "World") -> str:
    """Return a greeting message."""
    return f"Hello, {name}!"


def main():
    """Main entry point."""
    print(greet())


if __name__ == "__main__":
    main()

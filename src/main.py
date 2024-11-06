from service import Service  # type: ignore


def main() -> None:
    try:
        service = Service()
        service.start_change_stream()
    except KeyboardInterrupt:
        print("Service interrupted by user.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if service:
            service.shutdown()


if __name__ == "__main__":
    main()

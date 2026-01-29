def main():
    print("Hello from sysadmin3!")

    # import configure_logging  # type:ignore
    import mrodent_lib  # type:ignore

    print(f'dir(mrodent_lib) {dir(mrodent_lib)}')

    import mrodent_lib.configure_logging
    print(f'dir(mrodent_lib.configure_logging) {dir(mrodent_lib.configure_logging)}')

    mrodent_lib.configure_logging.configure_logging('PPP')

    import mrodent_lib.library_main
    mrodent_lib.library_main.other_instance_running()


if __name__ == "__main__":
    main()

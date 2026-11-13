import multiprocessing

from papyrus_agent.main import main

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()

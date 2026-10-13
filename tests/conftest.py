pytest_plugins = ["pykern.pytest_plugin"]


def pytest_configure(config):
    # RF-Track otherwise takes every core, and pykern may run test files in
    # parallel processes.
    import RF_Track as rft

    rft.cvar.number_of_threads = 1

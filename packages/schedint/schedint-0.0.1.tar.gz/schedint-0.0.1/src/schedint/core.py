class InterruptRequest:
    def __init__(self, pulsar: str):
        self.pulsar = pulsar


def always_ok() -> bool:
    return True

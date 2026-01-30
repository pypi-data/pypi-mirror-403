from typing import Protocol


class MessageProtocol(Protocol):

    def value(self):
        pass

    def properties(self) -> dict:
        pass

    def message(self):
        pass

    def raw(self):
        pass

    def offset(self):
        pass

    def partition(self):
        pass

    def topic(self):
        pass
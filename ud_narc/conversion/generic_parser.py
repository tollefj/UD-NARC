from abc import ABC, abstractmethod

class GenericParser(ABC):
    FROM_FILE = None
    TO_FILE = None

    def __init__(self, file_path):
        self.file_path = file_path

    @abstractmethod
    def parse(self):
        raise NotImplementedError

    @abstractmethod
    def write(self, file_path):
        raise NotImplementedError
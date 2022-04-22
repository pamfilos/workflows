from typing import IO


class IRepository:
    def find_all(self):
        raise NotImplementedError

    def find_by_id(self, id: str):
        raise NotImplementedError

    def save(self, filename: str, obj: IO):
        raise NotImplementedError

    def delete_all(self):
        raise NotImplementedError

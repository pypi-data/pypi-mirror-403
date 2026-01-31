import secretstorage


class KeyringBytes:
    """
    Простая обёртка над Secret Service.
    Хранит bytes, ключ — str.
    """

    def __init__(self, service: str):
        self.service = service
        self.bus = secretstorage.dbus_init()
        self.collection = secretstorage.get_default_collection(self.bus)
        if self.collection.is_locked():
            self.collection.unlock()

    def set(self, key: str, data: bytes) -> None:
        if not isinstance(key, str):
            raise TypeError("key must be str")
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("data must be bytes")

        self.collection.create_item(
            label=f"{self.service}:{key}",
            attributes={
                "service": self.service,
                "key": key,
            },
            secret=data,
            replace=True,
        )

    def get(self, key: str) -> bytes | None:
        if not isinstance(key, str):
            raise TypeError("key must be str")

        items = list(self.collection.search_items({
            "service": self.service,
            "key": key,
        }))

        if not items:
            return None

        item = items[0]
        if item.is_locked():
            item.unlock()

        return item.get_secret()

    def delete(self, key: str) -> bool:
        items = list(self.collection.search_items({
            "service": self.service,
            "key": key,
        }))
        if not items:
            return False
        for item in items:
            item.delete()
        return True

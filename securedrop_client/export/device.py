from tempfile import TemporaryDirectory

class ConnectedDevice():

    __create_key = object()  # Used to ensure the create method is used to construct instances

    @classmethod
    def create(cls, temp_dir: Optional[TemporaryDirectory] = None) -> Optional[ConnectedDevice]:
        """Creates a ConnectedDevice if a USB device is indeed connected, else None."""

        if temp_dir is None:
            temp_dir = TemporaryDirectory()



        # Assuming that temp_dir needs to be known
        device = ConnectedDevice(cls.__create_key, value)

        return None

    def __init__(self, create_key, value):
        assert(create_key == ConnectedDevice.__create_key), \
            "ConnectedDevice objects must be created using ConnectedDevice.create"
        self.value = value
        
class EncryptedDevice() -> None:
    def __init__(self):
        pass


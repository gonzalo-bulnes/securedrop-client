class Item:
    def transcript(self) -> str:
        """A transcription of the item."""
        raise NotImplementedError

    def metadata(self) -> str:
        """Some context about the item."""
        raise NotImplementedError

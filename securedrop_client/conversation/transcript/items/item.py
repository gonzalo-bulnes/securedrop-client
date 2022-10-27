class Item:
    @property
    def transcript(self) -> str:
        """A transcription of the conversation item."""
        raise NotImplementedError  # pragma: nocover

    @property
    def context(self) -> str:
        """Some context about the conversation item."""
        raise NotImplementedError  # pragma: nocover

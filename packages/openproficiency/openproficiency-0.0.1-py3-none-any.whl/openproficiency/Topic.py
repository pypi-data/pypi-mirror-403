"""Topic module for OpenProficiency library."""

from typing import List, Union


class Topic:

    # Initializers
    def __init__(
        self,
        # Required
        id: str,
        # Optional
        description: str = "",
        subtopics: List[Union[str, "Topic"]] = [],
        pretopics: List[Union[str, "Topic"]] = []
    ):
        # Required
        self.id = id

        # Optional
        self.description = description
        self.subtopics: List[str] = []
        self.pretopics: List[str] = []

        # Process initial subtopics and pretopics
        self.add_subtopics(subtopics)
        self.add_pretopics(pretopics)

    # Methods
    def add_subtopic(self, subtopic: Union[str, "Topic"]) -> None:
        """
        Add a subtopic to this topic.
        Supports a string ID or another Topic instance.
        """
        # Support direct string
        if isinstance(subtopic, str):
            self.subtopics.append(subtopic)

        # Support Topic object
        elif isinstance(subtopic, Topic):
            self.subtopics.append(subtopic.id)

        else:
            raise ValueError(
                "Subtopic must be a string or a dictionary with an 'id' key.")

    def add_subtopics(self, subtopics: List[Union[str, "Topic"]]) -> None:
        """
        Add multiple subtopics to this topic.
        Supports a list of string IDs or Topic instances.
        """
        for subtopic in subtopics:
            self.add_subtopic(subtopic)

    def add_pretopic(self, pretopic: Union[str, "Topic"]) -> None:
        """
        Add a pretopic to this topic.
        Supports a string ID or a dictionary with an 'id' key.
        """
        # Support direct string
        if isinstance(pretopic, str):
            self.pretopics.append(pretopic)

        # Support Topic object
        elif isinstance(pretopic, Topic):
            self.pretopics.append(pretopic.id)
        else:
            raise ValueError(
                "Pretopic must be a string or a dictionary with an 'id' key.")

    def add_pretopics(self, pretopics: List[Union[str, "Topic"]]) -> None:
        """
        Add multiple pretopics to this topic.
        Supports a list of string IDs or Topic instances.
        """
        for pretopic in pretopics:
            self.add_pretopic(pretopic)

    # Debugging
    def __repr__(self) -> str:
        """String representation of Topic."""
        return f"Topic(id='{self.id}', description='{self.description}')"

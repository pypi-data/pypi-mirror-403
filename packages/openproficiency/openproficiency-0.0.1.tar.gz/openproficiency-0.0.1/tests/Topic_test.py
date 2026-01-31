from openproficiency import Topic


class TestTopic:

    # Initializers
    def test_init_required_params(self):
        """Create a topic with requied fields only"""

        # Arrange
        id = "git-commit"

        # Act
        topic = Topic(id=id)

        # Assert
        assert topic.id == id

        # Assert - default values
        assert topic.description == ""
        assert topic.subtopics == []
        assert topic.pretopics == []

    def test_init_optional_params(self):
        """Test creating a topic with subtopics."""

        # Arrange
        id = "git-commit"
        description = "Saving changes to the Git history"
        subtopics = ["git-branch", "git-merge"]
        pretopics = ["cli"]

        # Act
        topic = Topic(
            id=id,
            description=description,
            subtopics=subtopics,
            pretopics=pretopics
        )

        # Assert
        assert topic.description == description
        assert len(topic.subtopics) == 2
        assert len(topic.pretopics) == 1

    # Methods

    def test_add_subtopic_string(self):
        """Test adding a subtopic as a string."""

        # Arrange
        topic = Topic(id="git")
        subtopic_id = "git-commit"

        # Act
        topic.add_subtopic(subtopic_id)

        # Assert
        assert subtopic_id in topic.subtopics

    def test_add_subtopic_topic(self):
        """Test adding a subtopic as a Topic instance."""

        # Arrange
        topic = Topic(id="git")
        subtopic = Topic(
            id="git-commit",
            description="Saving changes to the Git history"
        )

        # Act
        topic.add_subtopic(subtopic)

        # Assert
        assert subtopic.id in topic.subtopics

    def test_add_subtopics_mixed(self):
        """Test adding multiple subtopics as a mix of strings and Topic instances."""

        # Arrange
        topic = Topic(id="git")
        subtopic1 = "git-commit"
        subtopic2 = Topic(
            id="git-branch",
            description="Managing branches in Git"
        )
        subtopics = [subtopic1, subtopic2]

        # Act
        topic.add_subtopics(subtopics)

        # Assert
        assert subtopic1 in topic.subtopics
        assert subtopic2.id in topic.subtopics

    def test_add_pretopic_string(self):
        """Test adding a pretopic as a string."""

        # Arrange
        topic = Topic(id="git")
        pretopic_id = "version-control"

        # Act
        topic.add_pretopic(pretopic_id)

        # Assert
        assert pretopic_id in topic.pretopics

    def test_add_pretopic_topic(self):
        """Test adding a pretopic as a Topic instance."""

        # Arrange
        topic = Topic(id="git")
        pretopic = Topic(
            id="version-control",
            description="Managing changes to code over time"
        )

        # Act
        topic.add_pretopic(pretopic)

        # Assert
        assert pretopic.id in topic.pretopics

    def test_add_pretopics_mixed(self):
        """Test adding multiple pretopics as a mix of strings and Topic instances."""

        # Arrange
        topic = Topic(id="git")
        pretopic1 = "version-control"
        pretopic2 = Topic(
            id="software-development",
            description="The process of creating software"
        )
        pretopics = [pretopic1, pretopic2]

        # Act
        topic.add_pretopics(pretopics)

        # Assert
        assert pretopic1 in topic.pretopics
        assert pretopic2.id in topic.pretopics

    # Debugging
    def test_topic_repr(self):
        """Check string representation of a Topic"""

        # Arrange
        topic = Topic(id="git", description="Git version control")

        # Act
        repr_str = repr(topic)

        # Assert
        assert "git" in repr_str
        assert "Git version control" in repr_str
        assert "Topic" in repr_str

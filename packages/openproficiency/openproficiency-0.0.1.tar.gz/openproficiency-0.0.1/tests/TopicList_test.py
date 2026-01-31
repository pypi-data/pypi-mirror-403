"""Tests for the TopicList class."""

import json
from openproficiency import Topic, TopicList


class TestTopicList:

    # Initializers
    def test_init_required_params(self):
        """Create a topic list with required."""

        # Arrange
        owner = "github"
        name = "github"

        # Act
        topic_list = TopicList(
            owner=owner,
            name=name
        )

        # Assert
        assert topic_list.owner == owner
        assert topic_list.name == name
        assert topic_list.topics == {}
        assert topic_list.dependencies == {}

    def test_init_optional_params(self):
        """Create a topic list with optional details."""

        # Arrange
        owner = "github"
        name = "github"
        description = "Features of the GitHub platform"

        # Act
        topic_list = TopicList(
            owner=owner,
            name=name,
            description=description
        )

        # Assert
        assert topic_list.owner == owner
        assert topic_list.name == name
        assert topic_list.description == description

    # Methods
    def test_add_topic_string(self):
        """Add a new topic using a string ID."""

        # Arrange
        topic_list = TopicList(
            owner="github",
            name="git"
        )
        topic_id = "git-commit"

        # Act
        topic_list.add_topic(topic_id)

        # Assert
        assert "git-commit" in topic_list.topics
        assert isinstance(topic_list.topics["git-commit"], Topic)

    def test_add_topic_topic(self):
        """Add a new topic using a Topic instance."""

        # Arrange
        topic_list = TopicList(
            owner="github",
            name="git"
        )
        topic1 = Topic(
            id="git-commit",
            description="Storing changes to the Git history"
        )

        # Act
        topic_list.add_topic(topic1)

        # Assert
        assert "git-commit" in topic_list.topics
        assert topic_list.topics["git-commit"] == topic1

    def test_get_topic(self):
        """Test retrieving a topic that exists in the list."""

        # Arrange
        topic_list = TopicList(
            owner="github",
            name="git"
        )
        topic = Topic(id="git-commit")
        topic_list.topics[topic.id] = topic

        # Act
        retrieved = topic_list.get_topic("git-commit")

        # Assert
        assert retrieved is not None
        assert retrieved.id == "git-commit"

    def test_get_topic_nonexistent(self):
        """Test retrieving a topic that does not exist in the list."""

        # Arrange
        topic_list = TopicList(
            owner="github",
            name="git"
        )
        topic = Topic(id="git-commit")
        topic_list.topics[topic.id] = topic

        # Act
        retrieved = topic_list.get_topic("nonexistent")

        # Assert
        assert retrieved is None

    # Properties
    def test_full_name(self):
        """Test getting the full name of the topic list."""

        # Arrange
        owner = "github"
        name = "git"
        topic_list = TopicList(
            owner=owner,
            name=name
        )

        # Act
        full_name = topic_list.full_name

        # Assert
        assert full_name == "github/git"

    # Methods - Class
    def test_load_from_json_basic_info(self):
        """Load a list with only list info."""

        # Arrange
        json_data = """
        {
            "owner": "github",
            "name": "github-features",
            "description": "Features of the GitHub platform"
        }
        """

        # Act
        topic_list = TopicList.from_json(json_data)

        # Assert - list details
        assert topic_list.owner == "github"
        assert topic_list.name == "github-features"
        assert topic_list.description == "Features of the GitHub platform"

    def test_load_from_json_simple(self):
        """Load a list with only top-level topics."""

        # Arrange
        json_data = """
        {
            "owner": "github",
            "name": "github-features",
            "description": "Features of the GitHub platform",
            "topics": {
                "actions": {
                    "description": "Storing changes to the Git history"
                },
                "repositories": {
                    "description": "Versioning code with Git repositories"
                }
            }
        }
        """

        # Act
        topic_list = TopicList.from_json(json_data)

        # Assert - topics
        assert "actions" in topic_list.topics
        assert topic_list.topics["actions"].description == "Storing changes to the Git history"

        assert "repositories" in topic_list.topics
        assert topic_list.topics["repositories"].description == "Versioning code with Git repositories"

    def test_load_from_json_subtopics(self):
        """Load a list with subtopics."""

        # Arrange
        json_data = """
        {
            "owner": "github",
            "name": "github-features",
            "description": "Features of the GitHub platform",
            "topics": {

                "git-branch": {
                    "description": "Parallel versions of work",
                    "pretopic": ["git-commit"]
                },
                
                "actions": {
                    "description": "Storing changes to the Git history",
                    "subtopics": ["git-branch"]
                },

                "repositories": {
                    "description": "Versioning code with Git repositories",
                    "subtopics": [
                        "commit-history",
                        "pull-request",
                        "fork"
                    ]
                }
            }
        }
        """

        # Act
        topic_list = TopicList.from_json(json_data)

        # Assert - topics
        assert "actions" in topic_list.topics
        assert "git-branch" in topic_list.topics
        assert topic_list.topics["git-branch"].description == "Parallel versions of work"

        assert "repositories" in topic_list.topics
        assert "commit-history" in topic_list.topics
        assert "pull-request" in topic_list.topics
        assert "fork" in topic_list.topics

    def test_load_from_json_subsubtopics(self):
        """Load a list with multiple layers of subtopics."""

        # Arrange
        json_data = """
        {
            "owner": "github",
            "name": "github",
            "description": "Features of the GitHub platform",
            "topics": {
                
                "repositories": {
                    "description": "Versioning code with Git repositories",
                    "subtopics": [
                        "commit-history",
                        { 
                            "id": "community-files",
                            "description": "Essential files for repository community health",
                            "subtopics": [
                                "code-of-conduct-file",
                                "codeowners-file",
                                "contributing-file",
                                "license-file",
                                "readme-file"
                            ]
                        },
                        "pull-request",
                        "fork"
                    ]
                }
            }
        }
        """

        # Act
        topic_list = TopicList.from_json(json_data)

        # Assert
        assert "community-files" in topic_list.topics
        assert topic_list.topics["community-files"].description == "Essential files for repository community health"
        assert "code-of-conduct-file" in topic_list.topics
        assert "codeowners-file" in topic_list.topics
        assert "contributing-file" in topic_list.topics
        assert "license-file" in topic_list.topics
        assert "readme-file" in topic_list.topics

    def test_load_from_json_pretopics(self):
        """Load a list with subtopics."""

        # Arrange
        json_data = """
        {
            "owner": "github",
            "name": "github-features",
            "description": "Features of the GitHub platform",
            "topics": {
                
                "actions": {
                    "description": "Storing changes to the Git history",
                    "pretopics": ["yaml"]
                },

                "git-commit": {
                    "description": "Saving changes to the Git history"
                },

                "repositories": {
                    "description": "Versioning code with Git repositories",
                    "pretopics": [
                        "git-commit",
                        "git-push",
                        "git-pull"
                    ]
                }
            }
        }
        """

        # Act
        topic_list = TopicList.from_json(json_data)

        # Assert - topics
        assert "actions" in topic_list.topics
        assert topic_list.topics["yaml"].description == "Storing changes to the Git history"
        assert "yaml" in topic_list.topics

        assert "repositories" in topic_list.topics
        assert topic_list.topics["repositories"].description == "Versioning code with Git repositories"
        assert "git-commit" in topic_list.topics
        assert "git-push" in topic_list.topics
        assert "git-pull" in topic_list.topics

    def test_load_from_json_prepretopics(self):
        """Load a list with multiple layers of pretopics."""

        # Arrange
        json_data = """
        {
            "owner": "github",
            "name": "github-features",
            "description": "Features of the GitHub platform",
            "topics": {
                
                "repositories": {
                    "description": "Versioning code with Git repositories",
                    "pretopics": [
                        "git-commit",
                        { 
                            "id": "git-merge",
                            "description": "Essential files for repository community health",
                            "pretopics": [
                                "git1",
                                "git2",
                                "git3"
                            ]
                        },
                        "git-pull"
                    ]
                }
            }
        }
        """

        # Act
        topic_list = TopicList.from_json(json_data)

        # Assert - topics
        assert "repositories" in topic_list.topics
        assert "git-commit" in topic_list.topics
        assert topic_list.topics["git-commit"].description == "Versioning code with Git repositories"

        assert "git-merge" in topic_list.topics
        assert topic_list.topics["git-merge"].description == "Essential files for repository community health"
        assert "git1" in topic_list.topics
        assert "git2" in topic_list.topics
        assert "git3" in topic_list.topics

        assert "git-pull" in topic_list.topics
        assert topic_list.topics["git-pull"].description == "Versioning code with Git repositories"

    def test_to_json_simple(self):
        """Exporting a simple TopicList to JSON."""

        # Arrange
        topic_list = TopicList(
            owner="github",
            name="github-features",
            description="Features of the GitHub platform",
        )
        topic1 = Topic(id="actions", description="Storing changes to the Git history")
        topic1.add_subtopic("automation")
        topic1.add_pretopic("yaml")

        topic2 = Topic(id="repositories", description="Versioning code with Git repositories")
        topic2.add_subtopic("git-clone")
        topic2.add_pretopic("git-push")

        topic_list.add_topic(topic1)
        topic_list.add_topic(topic2)

        # Act
        json_data = topic_list.to_json()
        data = json.loads(json_data)

        # Assert - List Info
        assert data["owner"] == "github"
        assert data["name"] == "github-features"
        assert data["description"] == "Features of the GitHub platform"

        # Assert - Topic 1
        assert "actions" in data["topics"]
        assert data["topics"]["actions"]["description"] == "Storing changes to the Git history"
        assert "automation" in data["topics"]["actions"]["subtopics"]
        assert "yaml" in data["topics"]["actions"]["pretopics"]

        # Assert - Topic 2
        assert "repositories" in data["topics"]
        assert data["topics"]["repositories"]["description"] == "Versioning code with Git repositories"
        assert "git-clone" in data["topics"]["repositories"]["subtopics"]
        assert "git-push" in data["topics"]["repositories"]["pretopics"]

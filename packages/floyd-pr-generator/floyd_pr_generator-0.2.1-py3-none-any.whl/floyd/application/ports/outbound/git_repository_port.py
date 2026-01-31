from abc import ABC, abstractmethod


class GitRepositoryPort(ABC):

    @abstractmethod
    def is_git_repo(self) -> bool:
        ...

    @abstractmethod
    def branch_exists(self, branch_name: str) -> bool:
        ...

    @abstractmethod
    def get_current_branch(self) -> str:
        ...

    @abstractmethod
    def get_commits(self, base_branch: str) -> str:
        ...

    @abstractmethod
    def get_diff(self, base_branch: str) -> str:
        ...

    @abstractmethod
    def get_diff_stat(self, base_branch: str) -> str:
        ...

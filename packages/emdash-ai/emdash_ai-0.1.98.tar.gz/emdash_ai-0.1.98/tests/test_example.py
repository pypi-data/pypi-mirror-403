"""Example Python file for testing EmDash."""

import os
import sys
from pathlib import Path


class BaseModel:
    """Base model class."""

    def __init__(self, name: str):
        self.name = name

    def save(self):
        """Save the model."""
        print(f"Saving {self.name}")


class User(BaseModel):
    """User model."""

    def __init__(self, name: str, email: str):
        super().__init__(name)
        self.email = email

    def send_email(self, message: str):
        """Send an email to the user."""
        print(f"Sending email to {self.email}: {message}")
        self.log_action("email_sent")

    def log_action(self, action: str):
        """Log a user action."""
        print(f"User {self.name} performed: {action}")


def create_user(name: str, email: str) -> User:
    """Create a new user."""
    user = User(name, email)
    user.save()
    return user


def main():
    """Main entry point."""
    user = create_user("Alice", "alice@example.com")
    user.send_email("Hello World!")


if __name__ == "__main__":
    main()

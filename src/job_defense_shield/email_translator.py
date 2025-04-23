"""Class to replace the tags in user-written email files."""

import os
from typing import Dict


class EmailTranslator:

    def __init__(self,
                 base_path: str,
                 template_file: str,
                 tags: Dict[str, str]) -> None:
        self.base_path = base_path
        self.template_file = template_file
        self.tags = tags
        self.lines = []
        self._read_template_file()

    def _read_template_file(self) -> None:
        """Method to read email file."""
        email_file_abs = os.path.join(self.base_path, self.template_file)
        try:
            with open(email_file_abs, "r", encoding="utf-8") as fp:
                self.lines = fp.readlines()
        except FileNotFoundError:
            print(f"Error: File not found at {email_file_abs}")
            raise
        except IOError:
            print(f"Error: Could not read file at {email_file_abs}")
            raise
        except Exception as e:
            print(f"Error: Could not read {email_file_abs} ({e})")
            raise

    def replace_tags(self) -> str:
        """Replace tags like <TABLE> with the actual values computed in
           create_emails()."""
        for key, value in self.tags.items():
            for i in range(len(self.lines)):
                self.lines[i] = self.lines[i].replace(key, value)
        return "".join(self.lines)

from abc import ABC, abstractmethod
from typing import Optional

import pandas as pd


class BaseConverter(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the provider."""
        pass

    @property
    def instructions(self) -> Optional[str]:
        """Instructions for the user on how to obtain/format the file."""
        return None

    @property
    @abstractmethod
    def input_data_types(self) -> list[dict]:
        """
        Returns a list of dictionaries describing the expected input columns.
        Each dictionary should have: 'field_name', 'field_type', 'description', 'example'.
        """
        pass

    @abstractmethod
    def detect(self, input_path: str) -> bool:
        """Check if the file belongs to this provider."""
        pass

    @abstractmethod
    def _convert(self, input_path: str, config_path: Optional[str] = None) -> pd.DataFrame:
        """Internal transformation logic to be implemented by subclasses."""
        pass

    def convert(self, input_path: str, config_path: Optional[str] = None) -> pd.DataFrame:
        """
        Convert the file to Portfolio Performance format.
        This base method handles common post-processing like adding the broker prefix to notes.
        """
        df = self._convert(input_path, config_path)
        
        # Standardize 'Note' column
        if 'Note' not in df.columns:
            df['Note'] = ""
            
        # Add broker prefix to notes
        prefix = f"{self.name} - "
        
        def add_prefix(note):
            note_str = str(note) if pd.notna(note) else ""
            if note_str.startswith(prefix):
                 return note_str
            return f"{prefix}{note_str}"

        df['Note'] = df['Note'].apply(add_prefix)
        
        return df

# OMNIMIND Data Package
# Data loading, preprocessing, and synthetic data generation

from .dataprep import (
    RawTextDataLoader,
    TextPreprocessor,
    TextChunk,
    create_training_dataset,
)

from .synthetic import (
    SyntheticDataGenerator,
    QAPairGenerator,
    InstructionGenerator,
    SyntheticConfig,
    generate_qa_pairs,
)

from .documents import (
    DocumentLoader,
    Document,
    create_document_dataset,
)

__all__ = [
    # Data Prep
    "RawTextDataLoader",
    "TextPreprocessor",
    "TextChunk",
    "create_training_dataset",
    
    # Synthetic
    "SyntheticDataGenerator",
    "QAPairGenerator",
    "InstructionGenerator",
    "SyntheticConfig",
    "generate_qa_pairs",
    
    # Documents
    "DocumentLoader",
    "Document",
    "create_document_dataset",
]

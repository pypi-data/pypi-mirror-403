from pydantic import BaseModel, Field

class FileAnalysis(BaseModel):
    """Analysis of an individual source code file."""
    file_path: str = Field(description="The relative path to the file.")
    summary: str = Field(description="A concise 1-2 sentence description of what this file does.")
    key_definitions: list[str] = Field(description="List of main classes or functions exported.")
    dependencies: list[str] = Field(description="Key external libraries or local modules imported.")

class BatchSummary(BaseModel):
    """The output of the first prompt: a summary of a group of files."""
    theme: str = Field(description="The general purpose of this batch (e.g., 'Database Utilities').")
    analyses: list[FileAnalysis] = Field(description="Individual analysis for each file in the batch.")
    logic_flow: str = Field(description="How these files interact or depend on each other.")



class Feature(BaseModel):
    title: str = Field(description="Feature name with an emoji")
    description_bullets: list[str] = Field(description="Bullet points explaining the feature.")

class READMEStructure(BaseModel):
    project_name: str
    tagline: str = Field(description="A catchy one-sentence value proposition.")
    detailed_description: str = Field(description="Comprehensive overview of the project.")
    tech_stack: list[str] = Field(
        description="List of Tech Stacks Used"
    )
    features: list[Feature] = Field(description="Core features with titles and bullet points.")
    installation_steps: list[str] = Field(description="Inferred installation commands.")
    environment_variables: list[str] = Field(description="List of .env keys required.")
    usage_example: str = Field(description="A code snippet showing how to use the tool.")
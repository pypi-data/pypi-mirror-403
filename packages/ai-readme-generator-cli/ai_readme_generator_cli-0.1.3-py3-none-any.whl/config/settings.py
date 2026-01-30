from pydantic import BaseModel

from pydantic_settings import BaseSettings

from config.analyzer_config import AnalyzerConfigFile

class LoggerSettings(BaseModel):
    level: str = 'DEBUG'

class AnalyzerConfig(BaseModel):
    config: AnalyzerConfigFile = AnalyzerConfigFile()


class Settings(BaseSettings):
    app_name: str = 'Code-Analyzer'
    logger: LoggerSettings = LoggerSettings()
    analyzer_config: AnalyzerConfig = AnalyzerConfig()

    class config:
        env_file = '.env'



settings: Settings = Settings()
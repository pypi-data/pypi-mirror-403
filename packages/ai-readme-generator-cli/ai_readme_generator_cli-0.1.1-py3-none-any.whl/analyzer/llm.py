import os
from pathlib import Path
import json
from langchain_openai import ChatOpenAI
from langchain_google_genai import GoogleGenerativeAI
from langchain_anthropic import ChatAnthropic

from config.logger import logger


def initialize_llm():
    try:

        project_root = Path.cwd()

        config_dir = project_root / "config"
        config_file = config_dir / "analyzer.json"

        if  not os.path.exists(config_file):
            logger.error('Config file analyzer.json do not exist!!! Run init first.')
            raise FileNotFoundError('Config file analyzer.json do not exist!!! Run init first.')

        with open(config_file, 'r', encoding='utf-8') as f:
            content = json.load(f)
            llm_content = content.get('llm', '')
            model_provider = llm_content.get('model_provider', '')
            llm_model = llm_content.get('model', '')
            llm_key = llm_content.get('key', '')
            llm_temperature = llm_content.get('temperature', 0.7)

        if llm_model == '' or llm_key == '':
            logger.error('Model or key missing')
            raise Exception('Model or key missing analyzer.json')

        if model_provider.lower() == 'openai':
            return ChatOpenAI(
                model = llm_model,
                api_key=llm_key,
                temperature = llm_temperature
            )

        elif model_provider.lower() == 'google':
            return GoogleGenerativeAI(
                model = llm_model,
                google_api_key = llm_key,
                temperature = llm_temperature
            )

        elif model_provider.lower() == 'anthropic':
            return ChatAnthropic(
                model_name = llm_model,
                api_key=llm_key,
                temperature=llm_temperature,
                timeout = None,
                stop = None
            )

        else:
            logger.error('Model Provided is not yet supported')
            raise Exception('Model Provided is not yet supported')




    except Exception as e:
        logger.error(f"Error occured in initializing llm {e}")
        raise Exception(f"Error occured in initializing llm {e}")



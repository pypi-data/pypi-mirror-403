from typing import cast
import os
import json
from pathlib import Path
import tiktoken

from config.logger import logger
from analyzer.files import get_all_files_paths, get_content_of_file
from analyzer.llm import initialize_llm
from config.prompts import mapper_prompt, aggregator_prompt
from config.schemas import BatchSummary, READMEStructure


def get_batches(file_object):

    try:
        project_root = Path.cwd()
        config_dir = project_root / "config"
        config_file = config_dir / "analyzer.json"

        batch_limit = 100000

        if not os.path.exists(config_file):
            logger.error('Config file analyzer.json do not exist!!! Run init first.')
            raise FileNotFoundError('Config file analyzer.json do not exist!!! Run init first.')

        with open(config_file, 'r', encoding='utf-8') as f:
            content_json  = json.load(f)
            llm_content = content_json.get('llm', '')
            llm_model = llm_content.get('model', 'gpt-4o-mini')
            batch_limit = llm_content.get('batch_limit', '')
        encoding = tiktoken.encoding_for_model(llm_model) 

        batches= []
        current_batch_tokens = 0
        current_batch_text = ''

        for file_path, content in file_object.items():
            if not content: continue
            file_text = f"\nFILE: {file_path}\nCONTENT:\n{content}\n"
            file_tokens = len(encoding.encode(file_text))


            if file_tokens > batch_limit:
                if current_batch_text:
                    batches.append(current_batch_text)
                    current_batch_text = ""
                    current_batch_tokens = 0
                logger.info(f"File {file_path} is too large. Splitting into multiple batches.")
                file_chunks = handle_oversized_file(file_path, content, batch_limit, encoding)
                batches.extend(file_chunks)
                continue


            if current_batch_tokens + file_tokens < batch_limit:
                current_batch_text += file_text
                current_batch_tokens += file_tokens


            else:
                
                if current_batch_text:
                    batches.append(current_batch_text)
                current_batch_text = file_text
                current_batch_tokens = file_tokens

        if current_batch_text:
            batches.append(current_batch_text)

        return batches

        
    except Exception as e:
        logger.error(f'Error creating batches: {e}')
        raise Exception(f'Error creating batches for analyzing code: {e}')
        


def handle_oversized_file(file_path: str, content: str, limit: int, encoding):

    chunks = []
    lines = content.split('\n')
    current_chunk = f"FILE (Continued): {file_path}\n"
    current_tokens = len(encoding.encode(current_chunk))

    for line in lines:
        line_tokens = len(encoding.encode(line + '\n'))
        
        if line_tokens > limit:
            line = line[:limit * 2] # Emergency truncation
            line_tokens = len(encoding.encode(line))

        if current_tokens + line_tokens < limit:
            current_chunk += line + '\n'
            current_tokens += line_tokens
        else:
            chunks.append(current_chunk)
            current_chunk = f"FILE (Continued): {file_path}\n" + line + '\n'
            current_tokens = len(encoding.encode(current_chunk))

    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks

    

def format_as_markdown(data: READMEStructure) -> str:
    """Helper to turn the Pydantic object into a professional README.md."""
    
    # 1. Format Tech Stack (Category: Value)
    tech_stack_md = "\n".join([f"- {tech}" for tech in data.tech_stack])
    
    # 2. Format Features: Heading (Title) + Bullets
    features_md = ""
    for feature in data.features:
        # feature is now an object with .title and .description_bullets
        bullets = "\n".join([f"- {b}" for b in feature.description_bullets])
        features_md += f"### {feature.title}\n{bullets}\n\n"
    
    # 3. Format Environment Variables with dummy values
    env_vars_md = "\n".join([f"{var}=your_{var.lower()}_here" for var in data.environment_variables])
    
    # 4. Clean up installation and usage
    install_commands = "\n".join(data.installation_steps)
    
    usage = data.usage_example.strip()
    if not usage.startswith("```"):
        usage = f"```python\n{usage}\n```"
    
    # 5. Build the Final Markdown
    markdown = f"""# {data.project_name}
    
> {data.tagline}

---

## 📖 Overview
{data.detailed_description}

## ✨ Features
{features_md}

## 🏗️ Tech Stack
{tech_stack_md}

## 🚀 Getting Started

### Prerequisites
Ensure you have the necessary environment variables set up. Create a `.env` file and add:
```bash
{env_vars_md}
```

### Installation
```bash
{install_commands}
```

## 💡 Usage Example
{usage}

## 🤝 Contributing
Pull requests are welcome! For larger changes, please open an issue to discuss ideas first.

## 📜 License
MIT License — free to use, modify, and distribute.

Generated with ❤️ by your AI-README-Generator
"""

    return markdown


def analyze_code():
    try:
        llm = initialize_llm()
        all_files = get_all_files_paths()
        file_object = {}
        for file in all_files:
            content = get_content_of_file(file)
            file_object[file] = content

        batches = get_batches(file_object)


        analysis_chain = mapper_prompt | llm.with_structured_output(BatchSummary)
        readme_chain = aggregator_prompt | llm.with_structured_output(READMEStructure)

        all_summaries = []
        logger.info(f'analyzing {len(batches)} batches')

        for i, batch_content in enumerate(batches):
            summary = analysis_chain.invoke({"code_batch": batch_content})
            summary = cast(BatchSummary, summary)
            all_summaries.append(summary.model_dump_json())
            logger.info(f"Batch {i+1} analyzed.")

        logger.info("Synthesizing final README...")
        result = readme_chain.invoke({"summaries": "\n".join(all_summaries)})


        final_data = cast(READMEStructure, result)


        readme_content = format_as_markdown(final_data)

        return readme_content


    except Exception as e:
        logger.error(f"Error analyzing and code and generating README.md: {e}")
        raise Exception(f"Error analyzing and code and generating README.md: {e}")






        
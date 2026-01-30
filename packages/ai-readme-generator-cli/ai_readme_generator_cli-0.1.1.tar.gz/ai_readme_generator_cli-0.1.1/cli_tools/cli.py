import json
import os
import sys
import argparse
from pathlib import Path
from config.settings import settings
from config.logger import logger
from analyzer.analyze import analyze_code


def initialize_analyze_code():

    try:
        project_root = Path.cwd()
        config_dir = project_root / "config"
        config_file = config_dir / "analyzer.json"
        config_dir.mkdir(exist_ok=True)

        if config_file.exists():
            logger.info("file already exists")
            overwrite = input(
                "analyzer.json already exists under config folder. Overwrite? [y/N]: "
            )
            if overwrite.lower() != "y":
                logger.info("file is not overwritten")
                return

        logger.info("writing file analyzer.json with default content")

        analyzer_config = settings.analyzer_config.config 

        with open(config_file, "w", encoding="utf-8") as f:
            logger.info('Writing file analyzer.json with default dict')
            json.dump(
                analyzer_config.model_dump(), 
                f,
                indent=4
            )
        logger.info('Initializing done')
        return
    except Exception as e:
        logger.error(f"Error in initializing module: {e}")
        raise Exception(f"Error in initializing module: {e}")



    

def generate_readme():
    try:
        readme_content = analyze_code()
        if readme_content is None:
            logger.error("Failed to generate README content.")
            return

        if os.path.exists('README.md'):
            answer = input("README.md exists. Overwrite? [y/N]: ")
            if answer.lower() != 'y':
                logger.info('User did not permit to overwrite README.md')
                return


        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(readme_content)

            
        return
    except Exception as e:
        logger.error(f'Error in Generating Readme {e}')
        raise Exception(f'Error in Generating Readme {e}')




def main():
    parser = argparse.ArgumentParser(description="AI README Generator CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: init
    subparsers.add_parser("init", help="Initialize the analyzer configuration file")

    # Command: generate
    generate_parser = subparsers.add_parser("generate", help="Analyze code and generate README.md")
    generate_parser.add_argument("--provider", type=str, help="Override default LLM provider")

    args = parser.parse_args()

    # Wrap the execution logic in a try-except block
    try:
        if args.command == "init":
            initialize_analyze_code()
            logger.info("Successfully initialized configuration.")
        
        elif args.command == "generate":
            logger.info("Analyzing codebase and generating README...")
            generate_readme()
            logger.info("README.md generated successfully!")
        
        else:
            parser.print_help()

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(1)

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


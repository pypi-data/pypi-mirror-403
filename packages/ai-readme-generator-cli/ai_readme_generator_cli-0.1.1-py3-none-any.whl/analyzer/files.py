import glob
import json
from operator import truediv
from pathlib import Path
import os
from shutil import ReadError
from config.logger import logger



def get_all_files_paths():

    try:
        project_root = Path.cwd()


        config_dir = project_root / "config"
        config_file = config_dir / "analyzer.json"

        if not os.path.exists(config_file):
            logger.error('Config file analyzer.json do not exist!!! Run init first.')
            raise FileNotFoundError('Config file analyzer.json do not exist!!! Run init first.')



        with open(config_file, 'r', encoding='utf-8') as f:
            content_json  = json.load(f)
            global_ignore = set(content_json.get('global_ignore', []))
            ignore_dirs = set(content_json.get('ignore_dirs', []))
            ignore_files = set(content_json.get('ignore_files', []))
            ignore_extensions = set(content_json.get('ignore_extensions', []))
            include_files = set(content_json.get('include_files', []))
            include_dirs =  set(content_json.get('include_dirs', []))
            # update lists
            logger.info("initialized variables with default values")



        all_files = []


        for root, dirs, files in os.walk(project_root):
            root_path = Path(root)
            root_rel = root_path.relative_to(project_root).as_posix()


            pruned_dirs = []

            for d in dirs:
                dir_rel = f"{root_rel}/{d}" if root_rel != "." else d

                if dir_rel in include_dirs or any(idir.startswith(f"{dir_rel}/") for idir in include_dirs):
                    pruned_dirs.append(d)
                    continue

                if d in global_ignore:
                    continue

                if d in ignore_dirs or dir_rel in ignore_dirs:
                    continue

                pruned_dirs.append(d)

            dirs[:] = pruned_dirs
            
            for f in files:
                if f in global_ignore:
                    continue
                full_path = root_path / f
                rel_path =full_path.relative_to(project_root)
                rel_posix = rel_path.as_posix()

                if (rel_posix in include_files 
                    or f in include_files 
                    or any(rel_posix.startswith(f"{idir}/") for idir in include_dirs)):
                    all_files.append(rel_path)
                    continue
                
                if f in global_ignore:
                    continue


                if rel_posix in ignore_files or f in ignore_files:
                    continue

                if rel_path.suffix in ignore_extensions:
                    continue

                all_files.append(rel_path)

        logger.info(f'Total Files for analyze: {len(all_files)}')

        return all_files

    except Exception as e:
        logger.error(f" Error getting files paths: {e}")
        raise Exception(f"Error in get_all_files_paths: {e}")



def get_content_of_file(file):
    try:

        project_root = Path.cwd()
        full_path = project_root / file
        content = full_path.read_text(encoding = 'utf-8')
        return content
    
    except Exception as e:
        logger.error(f'Error occured in reading {file}:  {e}')
        raise ReadError(f"Error in reading file: {e}")

    
    
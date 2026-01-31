import logging
import os
import uuid
import zipfile

from pathlib import Path
from typing import Union, List

from xgse.sandbox.sandbox_base import SkillSandbox, SkillSandboxResult


class E2BSkillSandbox(SkillSandbox):
    def __init__(self,
                 host_work_dir:str,
                 sandbox_work_dir:str,
                 timeout: int = 300
                 ):

        from e2b_code_interpreter import Sandbox as E2BSandbox

        self.host_work_dir = host_work_dir
        self.sandbox_work_dir = sandbox_work_dir

        self.sandbox: E2BSandbox = E2BSandbox.create(timeout=timeout)
        self.sandbox.files.make_dir(path=sandbox_work_dir)

        sandbox_results_dir = str(Path(sandbox_work_dir) / 'results')
        self.sandbox.files.make_dir(path=sandbox_results_dir)

        self.code_context = self.sandbox.create_code_context(cwd=sandbox_work_dir ,language='python')

        logging.info(f"🛠️ E2BSkillSandBox init: Create sandbox id='{self.sandbox.sandbox_id}' , workspace='{sandbox_work_dir}'")


    def destroy(self):
        try:
            if self.sandbox:
                self.sandbox.kill()
                logging.info(f"E2BSkillSandBox destroy: Kill sandbox id='{self.sandbox.sandbox_id}'")
        except Exception as e:
            logging.error(f"E2BSkillSandBox destroy: Error {e}")


    def upload_file(self,
                    file_name: str,
                    local_file_path: str = "",
                    sandbox_file_path: str = ""
                    ):
        try:
            local_file_path = Path(self.host_work_dir) / local_file_path.lstrip("/")
            sandbox_file_path = Path(self.sandbox_work_dir) / sandbox_file_path.lstrip("/")

            local_full_path = str(local_file_path / file_name)
            sandbox_full_path = str(sandbox_file_path / file_name)

            file_size = os.path.getsize(local_full_path)
            logging.info(f"E2BSkillSandBox upload_file: Begin upload '{local_full_path}' {file_size} bytes"
                         f" to sandbox '{sandbox_full_path}'")

            with open(local_full_path, "rb") as file:
                self.sandbox.files.write(sandbox_full_path, file)
            logging.info(f"E2BSkillSandBox upload_file: Upload '{local_full_path}' to sandbox '{sandbox_full_path}' completed")
        except Exception as e:
            logging.error(f"E2BSkillSandBox upload_file: Error {e}")
            raise e


    def download_file(self,
                      file_name: str,
                      sandbox_file_path: str = "",
                      local_file_path: str = ""
                      ):
        try:
            sandbox_file_path = Path(self.sandbox_work_dir) / sandbox_file_path.lstrip("/")
            local_file_path = Path(self.host_work_dir) / local_file_path.lstrip("/")

            sandbox_full_path = str(sandbox_file_path / file_name)
            local_full_path = str(local_file_path / file_name)

            logging.info(f"E2BSkillSandBox download_file: Begin download '{sandbox_full_path}' to local '{local_full_path}'")

            # Ensure local directory exists
            os.makedirs(local_file_path, exist_ok=True)

            # Read file from sandbox
            file_content = self.sandbox.files.read(path=sandbox_full_path, format='bytes')
            with open(local_full_path, "wb") as f:
                f.write(file_content)

            file_size = os.path.getsize(local_full_path)
            logging.info(f"E2BSkillSandBox download_file: Download '{sandbox_full_path}' to local '{local_full_path}' {file_size} bytes completed")
        except Exception as e:
            logging.error(f"E2BSkillSandBox download_file: Error {e}")
            raise e


    def download_results(self,
                         local_file_path: str = "results"
                         ):
        try:
            sandbox_results_dir = Path(self.sandbox_work_dir) / 'results'
            local_results_dir = Path(self.host_work_dir) / local_file_path.lstrip("/")

            logging.info(f"E2BSkillSandBox download_results: Begin download sandbox '{sandbox_results_dir}' to local '{local_results_dir}'")

            # Ensure local directory exists
            os.makedirs(local_results_dir, exist_ok=True)

            # Create a zip file in sandbox containing the results directory
            zip_file_name = f"results_temp_{uuid.uuid4()}.zip"
            sandbox_zip_path = str(Path(self.sandbox_work_dir) / zip_file_name)

            # Command to create a zip of results directory in sandbox
            zip_command = f"cd {self.sandbox_work_dir} && zip -r -q '{zip_file_name}' results/"
            zip_result = self.sandbox.commands.run(zip_command)

            if zip_result.exit_code != 0:
                raise RuntimeError(f"Failed to create zip file in sandbox: {zip_result.stderr}")

            logging.info(f"E2BSkillSandBox download_results: Created zip file in sandbox '{sandbox_zip_path}'")

            # Download the zip file from sandbox
            local_zip_path = Path(self.host_work_dir) / zip_file_name
            self.download_file(file_name=zip_file_name)

            # Extract the zip file to local results directory
            logging.info(f"E2BSkillSandBox download_results: Extracting zip to '{local_results_dir}'")
            with zipfile.ZipFile(local_zip_path, 'r') as zip_ref:
                zip_ref.extractall(local_results_dir.parent)

            # Clean up the zip file in sandbox
            rm_command = f"rm '{sandbox_zip_path}'"
            self.sandbox.commands.run(rm_command)

            # Clean up the local zip file
            if local_zip_path.exists():
                os.unlink(local_zip_path)

            # Count downloaded files
            downloaded_files = []
            if local_results_dir.exists():
                for root, dirs, files in os.walk(local_results_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, Path(self.host_work_dir))
                        downloaded_files.append(rel_path)
                        file_size = os.path.getsize(file_path)

            logging.info(f"E2BSkillSandBox download_results: Downloaded {len(downloaded_files)} files from sandbox to local '{local_results_dir}'")
            logging.info(f"E2BSkillSandBox download_results: Download completed successfully")

        except Exception as e:
            logging.error(f"E2BSkillSandBox download_results: Error {e}")
            raise e


    def upload_work_dir(self):
        self.upload_dir(local_dir_path="", sandbox_dir_path="")


    def upload_dir(self,
                   local_dir_path: str,
                   sandbox_dir_path: str,
                   ):
        zip_file_path = None
        try:
            local_dir_path = Path(self.host_work_dir) / local_dir_path.lstrip("/")
            sandbox_dir_path = Path(self.sandbox_work_dir) / sandbox_dir_path.lstrip("/")
            logging.info(f"E2BSkillSandBox upload_dir: Begin upload local '{local_dir_path}' to sandbox '{sandbox_dir_path}'")

            zip_file_name = f"skills_temp_{uuid.uuid4()}.zip"
            zip_temp_file_path = Path(self.host_work_dir).parent / zip_file_name

            with zipfile.ZipFile(zip_temp_file_path, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as zip_file:
                for root, dirs, files in os.walk(local_dir_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_file = os.path.relpath(path=file_path, start=local_dir_path)
                        zip_file.write(file_path, arc_file)
            logging.info(f"E2BSkillSandBox upload_dir: Compress dir '{local_dir_path}' to '{zip_temp_file_path}' completed")

            zip_file_path = Path(self.host_work_dir) / zip_file_name
            os.rename(zip_temp_file_path, zip_file_path)
            self.upload_file(file_name=zip_file_name)

            sandbox_zip_path = str(Path(sandbox_dir_path) / zip_file_name)
            unzip_command = f"unzip -o -q '{sandbox_zip_path}' -d '{sandbox_dir_path}'"
            self.sandbox.commands.run(unzip_command)
            logging.info(f"E2BSkillSandBox upload_dir: Sandbox unzip '{sandbox_zip_path}' to '{sandbox_zip_path}' completed")
                
            rm_command = f"rm '{sandbox_zip_path}'"
            self.sandbox.commands.run(rm_command)
            
            logging.info(f"E2BSkillSandBox upload_dir: Upload local '{local_dir_path}' to sandbox '{sandbox_dir_path}' succeed")
        except Exception as e:
            logging.error(f"E2BSkillSandBox upload_dir: Error {e}")
            raise e
        finally:
            if os.path.exists(zip_file_path):
                os.unlink(zip_file_path)


    def install_requirements(self, requirements: list[str] | None):
        if requirements is None or len(requirements) == 0:
            logging.warning("E2BSkillSandBox install_requirements: requirements is empty !")
            return

        requirements_file = Path(self.sandbox_work_dir) / f"{uuid.uuid4()}/requirements.txt"
        self.sandbox.files.write(str(requirements_file), '\n'.join(requirements))

        logging.info("-" * 10 + f"E2BSkillSandBox[{self.sandbox.sandbox_id}]: PIP INSTALL BEGIN" + "-" * 10)

        result_requirements = self.sandbox.commands.run(f'pip install -r {requirements_file}')

        logging.info("\n" + result_requirements.stdout)
        logging.info("-" * 10 + f"E2BSkillSandBox[{self.sandbox.sandbox_id}]: PIP INSTALL END" + "-" * 10)


    def run_code(self,
                 python_code: Union[str, List[str]],
                 requirements: List[str] = None
                 ) -> List[SkillSandboxResult]:
        from e2b.exceptions import SandboxException
        results = []

        self.install_requirements(requirements)

        if isinstance(python_code, str):
            python_code = [python_code]

        logging.info("-" * 10 + f"E2BSkillSandBox[{self.sandbox.sandbox_id}]: RUN CODE" + "-" * 10)
        for code in python_code:
            logging.info("\n" + code)

            code_result = self.sandbox.run_code(code=code, context=self.code_context)
            success  = True if code_result.error is None else False
            if success:
                output = code_result.text
                if output is None and hasattr(code_result, 'logs'):
                    output = code_result.logs.stdout
            else:
                output = code_result.error.value
            results.append({
                'output': output,
                'success': success
            })

            logging.info(f"E2BSkillSandBox run_code: result='{output}'")
            if not success:
                # raise Exception for keeping up with 'exec_command' function
                raise SandboxException(f"E2BSkillSandBox run_code: Error {output}")

        return results


    def exec_command(self,
                     shell_command: Union[str, List[str]],
                     requirements: List[str] = None
                     ) -> List[SkillSandboxResult]:
        results = []

        self.install_requirements(requirements)

        if isinstance(shell_command, str):
            shell_command = [shell_command]

        logging.info("-" * 10 + f"E2BSkillSandBox[{self.sandbox.sandbox_id}]: EXEC COMMAND" + "-" * 10)
        for command in shell_command:
            logging.info(command)

            shell_result =  self.sandbox.commands.run(command)
            success  = True if shell_result.exit_code == 0 else False
            output = shell_result.stdout if success else shell_result.stderr
            results.append({
                'output': output,
                'success': success
            })

            logging.info(f"E2BSkillSandBox exec_command: result='{output}'")

        return results


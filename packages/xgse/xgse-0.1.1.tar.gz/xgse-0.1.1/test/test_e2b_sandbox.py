from pathlib import Path

from xgse.sandbox.e2b_sandbox import E2BSkillSandbox
from xgse.sandbox.sandbox_base import SkillSandbox

if __name__ == '__main__':
    from xgse.utils.setup_env import setup_logging

    setup_logging()

    def main():
        run_path = Path(__file__).parent.resolve()
        project_path = run_path.parents[0]
        skill_work_dir = str(project_path / 'skill_workspace')
        skill_sandbox = E2BSkillSandbox(host_work_dir=skill_work_dir,
                                        sandbox_work_dir="/skill_workspace",
                                        timeout=300)

        try:
            skill_sandbox.upload_work_dir()

            skill_sandbox.download_file(file_name="Nature_paper.pdf", local_file_path="results")

            test_run_code2(skill_sandbox)

            test_exec_command(skill_sandbox)

            skill_sandbox.download_results()
        finally:
            pass
            #skill_sandbox.destroy()


    def test_exec_command(skill_sandbox: SkillSandbox):
        commands = ["pwd", "mv /skill_workspace/new.pdf /skill_workspace/results/"]
        results = skill_sandbox.exec_command(commands)
        print(f"Sandbox exec_command: {results}")


    def test_run_code1(skill_sandbox: SkillSandbox):
        code = """
from typing import Annotated, Optional
from pydantic import Field
def getHostFaultCause(
    faultCode: Annotated[str, Field(description="Fault Code")],
    severity: Annotated[int, Field(default=2, description="Fault Level，1-5，default: 1")]
    ):
    print(f"getHostFaultCause: faultCode={faultCode}, severity={severity}")
    faultCause = ""
    if (faultCode == 'F02'):
        faultCause = "Host Disk Fault，Change Disk"
    else:
        faultCause = f"Unknown Fault，FaultCode'{faultCode}'"        
    return faultCause

getHostFaultCause('F02', 2)    
    """
        requirements = ["pydantic", "typing"]
        results = skill_sandbox.run_code(python_code=code, requirements=requirements)

        print(f"Sandbox run getHostFaultCause result is {results}")


    def test_run_code2(skill_sandbox: SkillSandbox):
        code ="""
import os
import pypdf
from pypdf import PdfReader, PdfWriter

# Step 1: Verify existence of PDF files
file1 = 'Nature_paper.pdf'
file2 = 'OLYMPIC_MEDAL_TABLE_zh.pdf'
if not os.path.exists(file1):
    raise FileNotFoundError(f"{file1} not found in the working directory.")
if not os.path.exists(file2):
    raise FileNotFoundError(f"{file2} not found in the working directory.")

# Step 2: Read each PDF file using PdfReader
reader1 = PdfReader(file1)
reader2 = PdfReader(file2)

# Step 3: Add all pages from each PDF into a PdfWriter instance
writer = PdfWriter()
for page in reader1.pages:
    writer.add_page(page)
for page in reader2.pages:
    writer.add_page(page)

# Step 4: Write merged content to new.pdf
output_file = 'new.pdf'
with open(output_file, 'wb') as f:
    writer.write(f)

# Step 5: Confirm output file contains all expected pages
output_reader = PdfReader(output_file)
expected_pages = len(reader1.pages) + len(reader2.pages)
actual_pages = len(output_reader.pages)
if expected_pages != actual_pages:
    raise Exception(f"Expected {expected_pages} pages, but found {actual_pages} pages in the output file.")
print(f"PDF files merged successfully. Output file: {output_file}")        
        """
        requirements = ["pypdf"]
        results = skill_sandbox.run_code(python_code=code, requirements=requirements)

        print(f"Sandbox run merge pdf  result is {results}")


    main()
DEFAULT_PLAN = """

"""

DEFAULT_TASKS = """

"""

DEFAULT_IMPLEMENTATION = """

"""


PROMPT_SKILL_PLAN = """
According to the user's request:\n {query}\n,
analyze the following skill content and breakdown the necessary steps to complete the task step by step, considering any dependencies or prerequisites that may be required.
According to following sections: `SKILL_MD_CONTEXT`, `REFERENCE_CONTEXT`, `SCRIPT_CONTEXT` and `RESOURCE_CONTEXT`, you **MUST** identify the most relevant **FILES** (if any) and outline a detailed plan to accomplish the user's request.
{skill_md_context} {reference_context} {script_context} {resource_context}
\n\nThe format of your response:\n
<QUERY>
... The user's original query ...
</QUERY>


<PLAN>
... The concise and clear step-by-step plan to accomplish the user's request ...
</PLAN>


<SCRIPTS>
... The most relevant SCRIPTS (if any) in JSON format ...
</SCRIPTS>


<REFERENCES>
... The most relevant REFERENCES (if any) in JSON format ...
</REFERENCES>


<RESOURCES>
... The most relevant RESOURCES (if any) in JSON format ...
</RESOURCES>

"""


PROMPT_SKILL_TASKS = """
According to `SKILL PLAN CONTEXT`:\n\n{skill_plan_context}\n\n
Provide a concise and precise TODO-LIST of implementations required to execute the plan, **MUST** be as concise as possible.
Each task should be specific, actionable, and clearly defined to ensure successful completion of the overall plan.
The format of your response: \n
<QUERY>
... The user's original query ...
</QUERY>


<TASKS>
... A concise and clear TODO-LIST of implementations required to execute the plan ...
</TASKS>

"""


SCRIPTS_IMPLEMENTATION_FORMAT = """[
    {
        "script": "<script_path_1>",
        "parameters": {
            "param1": "value1",
            "param2": "value2"
        }
    },
    {
        "function": "import pypdf\nfrom pypdf import PdfReader, PdfWriter\nimport os\n\n# Step 1: Read both PDFs\nreader1 = PdfReader('file1.pdf')\nreader2 = PdfReader('file2.pdf')\n\n# Step 2: Create a PdfWriter and add all pages\nwriter = PdfWriter()\nfor page in reader1.pages:\n    writer.add_page(page)\nfor page in reader2.pages:\n    writer.add_page(page)\n\n# Step 3: Ensure results directory exists\nos.makedirs('results', exist_ok=True)\n\n# Step 4: Write merged PDF to results directory\nwith open('results/merged.pdf', 'wb') as output_file:\n    writer.write(output_file)"
    }
]"""

PROMPT_TASKS_IMPLEMENTATION = """
According to relevant content of `SCRIPTS`, `REFERENCES` and `RESOURCES`:\n\n{script_contents}\n\n{reference_contents}\n\n{resource_contents}\n\n

**WORKING DIRECTORY:** All file paths should be relative to: `{work_dir}`\n

You **MUST** strictly implement the todo-list in `SKILL_TASKS_CONTEXT` step by step:\n\n{skill_tasks_context}\n\n

**CRITICAL INSTRUCTIONS FOR IMPLEMENTATION CHOICE:**

1. **Scenario-1 (Execute Existing Scripts)**: Only use the "script" key for scripts that **ACTUALLY EXIST** in the provided `SCRIPT_CONTEXT` above. Do NOT invent or hallucinate script names.
   Format:
   <IMPLEMENTATION>
   {scripts_implementation_format}
   </IMPLEMENTATION>

2. **Scenario-2 (Inline Python Code)**: If no appropriate script exists in `SCRIPT_CONTEXT` for the task, use the "function" key with inline Python code. This is the preferred approach for simple operations or when scripts are unavailable.
   Format:
   <IMPLEMENTATION>
   ```json
   [
       {{
           "function": "import pypdf\n# Your inline Python code here..."
       }}
   ]
   ```
   IMPORTANT: When using the "function" key, include all import statements at the top of the code. The system will automatically extract and install the required packages.
   </IMPLEMENTATION>

3. **Scenario-3 (No Script Execution Needed)**: For HTML, JavaScript code generation, or other non-Python outputs, provide the final answer directly.
   Format:
   <IMPLEMENTATION>
   ```html
   ```
   or
   ```javascript
   ```
   </IMPLEMENTATION>

4. **Scenario-4 (Unable to Execute)**: If you cannot complete the task, explain why.
   Format:
   <IMPLEMENTATION>
   ... The reason why unable to execute ...
   </IMPLEMENTATION>

**IMPORTANT:**
- Check `SCRIPT_CONTEXT` carefully before using the "script" key
- If the required script is NOT listed in `SCRIPT_CONTEXT`, use "function" key with inline Python code instead
- Do NOT make up script names or assume scripts exist
- When using "function" key with inline code, all file paths should be relative to the working directory: `{work_dir}`
- When using "function" key, include all import statements at the top - the system will automatically detect and install required packages
- **CRITICAL: ALL OUTPUT FILES MUST BE WRITTEN TO THE "results/" DIRECTORY**
  - For inline code: Use `os.makedirs('results', exist_ok=True)` to ensure the results directory exists, then write all output files to `results/` (e.g., `results/output.pdf`, `results/data.json`)
  - For scripts: Pass output file paths with the `results/` prefix in parameters (e.g., `"output": "results/filled_form.pdf"`)
  - After execution, all result files will be located in the `{work_dir}/results/` directory
- Be concise and direct in your response

"""


PROMPT_SKILL_FINAL_SUMMARY = """
Given the comprehensive context:\n\n{comprehensive_context}\n\n
Provide a concise summary of the entire process, highlighting key actions taken, decisions made, and the final outcome achieved.
Ensure the summary is clear and informative.
"""

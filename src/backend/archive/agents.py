from google.adk.agents import Agent, SequentialAgent
from src.backend.prompts import PROMPT_FILE_SELECTOR, PROMPT_REPORT_SYNTHESIZER
from src.backend.utils.file_utils import get_file_contents, save_selected_files, fetch_all_content, list_files

MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash-lite-001"

content_fetcher_agent = Agent(
    model=MODEL_GEMINI_2_0_FLASH,
    name="Content_Fetcher",
    description="Fetches the content of all selected files.",
    instruction="You must immediately call the `fetch_all_content` tool.",
    tools=[fetch_all_content],
)

report_synthesizer_agent = Agent(
    model=MODEL_GEMINI_2_0_FLASH,
    name="Report_Synthesizer",
    description="Synthesizes all file contents into a final report.",
    instruction=PROMPT_REPORT_SYNTHESIZER,
    output_key="analysis_results"
)

analysis_pipeline = SequentialAgent(
    name="Analysis_Pipeline",
    sub_agents=[file_selector_agent, content_fetcher_agent, report_synthesizer_agent]
)

root_agent = Agent(
    model=MODEL_GEMINI_2_0_FLASH,
    name="Root_Agent",
    description="Manages the repository analysis workflow.",
    instruction="""Immediately start the Analysis_Pipeline to handle the request.""",
    sub_agents=[analysis_pipeline],
)
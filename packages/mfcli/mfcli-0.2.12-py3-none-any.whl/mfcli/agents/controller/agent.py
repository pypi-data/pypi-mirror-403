from pathlib import Path

from google.adk.agents import Agent

from mfcli.agents.controller.tools import query_knowledgebase, list_projects
from mfcli.agents.tools.general import load_agent_config
from mfcli.pipeline.pipeline import run

config_path = Path(__file__).parent / "config.yaml"
config = load_agent_config(config_path)

root_agent = Agent(
    name=config.name,
    model=config.model,
    description=config.description,
    instruction=config.instructions,
    tools=[run, query_knowledgebase, list_projects],
    output_key="pipeline_run_output"
)

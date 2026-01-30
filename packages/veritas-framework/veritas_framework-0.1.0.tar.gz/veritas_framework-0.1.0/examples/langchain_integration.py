"""
Example: Integrating Veritas with LangChain

This example shows how to use Veritas to enforce trust on LangChain tool calls.
"""

from typing import Any
from langchain.agents import initialize_agent, Tool
from langchain_openai import ChatOpenAI
from veritas import TrustContext, EvidenceType

# 1. Initialize Veritas Context
ctx = TrustContext(agent_id="langchain-agent", strict_mode=True)

# 2. Define a "Trust-Aware" Tool
def search_database(query: str) -> str:
    # Simulate a search
    result = f"Found data for {query}"
    
    # Capture evidence
    ctx.add_evidence(
        claim=f"Database search for {query}",
        evidence_type=EvidenceType.COMMAND_OUTPUT,
        content=result,
        verifiable_command=f"db-query --q {query}"
    )
    return result

tools = [
    Tool(
        name="Search",
        func=search_database,
        description="Search the database for information"
    )
]

# 3. Initialize LangChain Agent
llm = ChatOpenAI(model="gpt-4", temperature=0)
agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True)

# 4. Run with Trust Monitoring
def run_with_trust(prompt: str):
    print(f"Running task: {prompt}")
    ctx.record_action("execute", f"Processing prompt: {prompt}")
    
    try:
        response = agent.run(prompt)
        
        # Veritas check: Did we get enough evidence?
        report = ctx.get_audit_trail()
        evidence_count = len(ctx.evidence)
        
        print(f"\nResponse: {response}")
        print(f"Veritas Evidence Captured: {evidence_count}")
        print("Audit Trail Summary:")
        for action in report:
            print(f"- {action['description']}")
            
    except Exception as e:
        ctx.record_action("error", str(e), is_failure=True)
        print(f"Task Failed: {e}")

if __name__ == "__main__":
    run_with_trust("Search the database for LegalBERT and summarize it.")

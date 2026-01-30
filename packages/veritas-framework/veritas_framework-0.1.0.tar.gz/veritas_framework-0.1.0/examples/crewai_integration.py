"""
Example: Integrating Veritas with CrewAI

This example demonstrates using Veritas to enforce workflow gates between 
different agents in a Crew.
"""

from crewai import Agent, Task, Crew, Process
from veritas import TrustContext, EvidenceType
from veritas.layers.gates import WorkflowGate, GateRequirement, TaskStatus

# 1. Setup Veritas Workflow Gate
# This gate requires a 'test_results' artifact before allowing transition to DONE
qa_gate = WorkflowGate(
    name="qa_verification",
    from_status=TaskStatus.DOING,
    to_status=TaskStatus.DONE,
    requirements=[
        GateRequirement(
            name="test_proof",
            evidence_type=EvidenceType.TEST_RESULTS,
            required=True
        )
    ]
)

# 2. Define Agents with Veritas Hooks
class VeritasAgent(Agent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trust_ctx = TrustContext(agent_id=self.role)

def create_crew():
    # Research Agent
    researcher = VeritasAgent(
        role='Researcher',
        goal='Analyze the current state of AI trust',
        backstory='Expert in AI governance and reliability.',
        allow_delegation=False
    )

    # QA Agent
    tester = VeritasAgent(
        role='QA_Specialist',
        goal='Verify the claims made by the researcher',
        backstory='Specialized in verification and evidence collection.',
        allow_delegation=False
    )

    # 3. Define Tasks
    task1 = Task(
        description="Write a report on AI trust benchmarks.",
        agent=researcher
    )

    task2 = Task(
        description="Verify the benchmarks and provide evidence.",
        agent=tester
    )

    # 4. Orchestrate with Crew
    crew = Crew(
        agents=[researcher, tester],
        tasks=[task1, task2],
        process=Process.sequential
    )

    return crew, researcher.trust_ctx, tester.trust_ctx

if __name__ == "__main__":
    crew, ctx1, ctx2 = create_crew()
    result = crew.kickoff()
    
    print("######################")
    print(f"Crew Result: {result}")
    print("######################")
    print(f"Researcher Actions: {len(ctx1.get_audit_trail())}")
    print(f"Tester Evidence: {len(ctx2.evidence)}")

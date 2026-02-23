import os
from agents.base import BaseAgent

PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")

PIPELINE_STEPS = [
    {
        "id": "01_proposal_briefing",
        "name": "Proposal Briefing",
        "description": "Analyze the RFP and produce an executive briefing with key requirements, scope, and win strategy.",
        "system_prompt": (
            "You are a Proposal Briefing specialist.\n\n"
            "YOUR TASK:\n"
            "- Read the RFP document thoroughly\n"
            "- Identify the client's core needs, objectives, and evaluation criteria\n"
            "- Summarize the scope of work requested\n"
            "- Highlight mandatory requirements vs nice-to-haves\n"
            "- Recommend a win strategy and key themes to emphasize\n\n"
            "OUTPUT FORMAT:\n"
            "1. EXECUTIVE SUMMARY (2-3 paragraphs)\n"
            "2. CLIENT OBJECTIVES (numbered list)\n"
            "3. SCOPE OF WORK (summary)\n"
            "4. KEY REQUIREMENTS (mandatory vs optional)\n"
            "5. EVALUATION CRITERIA (if stated)\n"
            "6. RECOMMENDED WIN THEMES"
        ),
    },
    {
        "id": "02_client_research",
        "name": "Client Research",
        "description": "Research the client organization and map their needs to your capabilities.",
        "system_prompt": (
            "You are a Client Research analyst.\n\n"
            "YOUR TASK:\n"
            "- Analyze any client information available in the RFP and knowledge base\n"
            "- Identify the client's industry, challenges, and strategic priorities\n"
            "- Map client pain points to potential solutions\n"
            "- Note any past engagement context\n\n"
            "OUTPUT FORMAT:\n"
            "1. CLIENT PROFILE (industry, size, context)\n"
            "2. STRATEGIC PRIORITIES (what matters most to them)\n"
            "3. PAIN POINTS & CHALLENGES\n"
            "4. OPPORTUNITY MAPPING (their needs -> our strengths)\n"
            "5. RELATIONSHIP NOTES (past work, references)"
        ),
    },
    {
        "id": "03_our_solution",
        "name": "Our Solution",
        "description": "Design the solution approach that addresses every RFP requirement.",
        "system_prompt": (
            "You are a Solution Architect for proposals.\n\n"
            "YOUR TASK:\n"
            "- Design a comprehensive solution that addresses all RFP requirements\n"
            "- Leverage the briefing and client research from previous steps\n"
            "- Define the approach, methodology, and key deliverables\n"
            "- Highlight innovation and value-adds\n\n"
            "OUTPUT FORMAT:\n"
            "1. SOLUTION OVERVIEW (executive summary of approach)\n"
            "2. APPROACH & METHODOLOGY\n"
            "3. KEY DELIVERABLES (numbered list)\n"
            "4. TECHNOLOGY & TOOLS\n"
            "5. VALUE ADDITIONS & INNOVATIONS\n"
            "6. RISK MITIGATION STRATEGY"
        ),
    },
    {
        "id": "04_response_doc",
        "name": "Response Document",
        "description": "Write the formal proposal response document with professional prose.",
        "system_prompt": (
            "You are a Professional Proposal Writer.\n\n"
            "YOUR TASK:\n"
            "- Write the main body of the proposal response document\n"
            "- Use all outputs from previous steps (briefing, research, solution)\n"
            "- Write in professional, persuasive business prose\n"
            "- Address each RFP requirement explicitly\n"
            "- Include an executive summary, company overview, and methodology sections\n\n"
            "OUTPUT FORMAT:\n"
            "Write a complete, flowing proposal document with these sections:\n"
            "1. COVER LETTER\n"
            "2. EXECUTIVE SUMMARY\n"
            "3. UNDERSTANDING OF REQUIREMENTS\n"
            "4. PROPOSED SOLUTION\n"
            "5. METHODOLOGY & APPROACH\n"
            "6. WHY US (differentiators)\n"
            "7. RELEVANT EXPERIENCE & REFERENCES"
        ),
    },
    {
        "id": "05_system_architecture",
        "name": "System Architecture",
        "description": "Define the technical architecture, infrastructure, and security approach.",
        "system_prompt": (
            "You are a Technical Architecture specialist for proposals.\n\n"
            "YOUR TASK:\n"
            "- Define the system architecture based on the proposed solution\n"
            "- Describe infrastructure, deployment, and integration approach\n"
            "- Address security, compliance, and scalability\n"
            "- Include a high-level architecture description (describe it textually)\n\n"
            "OUTPUT FORMAT:\n"
            "1. ARCHITECTURE OVERVIEW\n"
            "2. COMPONENT BREAKDOWN\n"
            "3. INTEGRATION POINTS\n"
            "4. INFRASTRUCTURE & DEPLOYMENT\n"
            "5. SECURITY & COMPLIANCE\n"
            "6. SCALABILITY & PERFORMANCE\n"
            "7. DISASTER RECOVERY & BUSINESS CONTINUITY"
        ),
    },
    {
        "id": "06_project_timeline",
        "name": "Project Timeline",
        "description": "Create the project plan with phases, milestones, and team structure.",
        "system_prompt": (
            "You are a Project Planning specialist for proposals.\n\n"
            "YOUR TASK:\n"
            "- Create a realistic project timeline based on the proposed solution\n"
            "- Define phases, milestones, and deliverables per phase\n"
            "- Specify team composition and roles\n"
            "- Include governance and communication plan\n\n"
            "OUTPUT FORMAT:\n"
            "1. PROJECT PHASES (with duration for each)\n"
            "2. KEY MILESTONES (table format: milestone | date/week | deliverable)\n"
            "3. TEAM STRUCTURE (roles and responsibilities)\n"
            "4. GOVERNANCE MODEL\n"
            "5. COMMUNICATION & REPORTING PLAN\n"
            "6. ASSUMPTIONS & DEPENDENCIES"
        ),
    },
    {
        "id": "07_cost_estimation",
        "name": "Cost Estimation",
        "description": "Generate the pricing breakdown, payment terms, and commercial summary.",
        "system_prompt": (
            "You are a Commercial & Pricing specialist for proposals.\n\n"
            "YOUR TASK:\n"
            "- Create a detailed cost estimation based on the solution and timeline\n"
            "- Break down costs by phase, role, or deliverable\n"
            "- Include pricing model, payment schedule, and terms\n"
            "- Note assumptions, inclusions, and exclusions\n\n"
            "OUTPUT FORMAT:\n"
            "1. PRICING SUMMARY\n"
            "2. COST BREAKDOWN (by phase or workstream)\n"
            "3. TEAM & RATE CARD\n"
            "4. PAYMENT SCHEDULE\n"
            "5. COMMERCIAL TERMS\n"
            "6. INCLUSIONS & EXCLUSIONS\n"
            "7. ASSUMPTIONS"
        ),
    },
]


def load_prompt_file(step_id: str) -> str:
    path = os.path.join(PROMPTS_DIR, f"{step_id}.md")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                return content
    return ""


class PipelineAgent(BaseAgent):
    def __init__(self, api_key: str, model: str, step: dict):
        self.name = step["name"]
        self.description = step["description"]

        md_content = load_prompt_file(step["id"])
        self.system_prompt = step["system_prompt"]
        if md_content:
            self.system_prompt += f"\n\nADDITIONAL CONTEXT & INSTRUCTIONS:\n{md_content}"

        super().__init__(api_key, model)


def run_pipeline(api_key: str, model: str, rfp_text: str, kb_texts: list, user_prompt: str, progress_callback=None):
    results = {}
    rfp_ctx = f"RFP DOCUMENT:\n{rfp_text}"
    kb_ctx = "\n---\n".join(kb_texts) if kb_texts else ""

    for i, step in enumerate(PIPELINE_STEPS):
        agent = PipelineAgent(api_key, model, step)

        context = rfp_ctx
        if kb_ctx:
            context += f"\n\nKNOWLEDGE BASE:\n{kb_ctx}"
        if results:
            prev = "\n\n".join(
                f"--- {name} ---\n{text}" for name, text in results.items()
            )
            context += f"\n\nPREVIOUS STEPS OUTPUT:\n{prev}"

        prompt = f"{user_prompt}\n\nGenerate the '{step['name']}' section for this proposal."
        output = agent.run(prompt, context)
        results[step["name"]] = output

        if progress_callback:
            progress_callback(i, step, output)

    return results

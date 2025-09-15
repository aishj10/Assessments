# backend/app/prompts.py
from textwrap import dedent
from typing import Dict

def qualification_prompt(lead: Dict, scoring_weights: Dict = None) -> str:
    weights = scoring_weights or {
        "company_size": 1,
        "industry_fit": 2,
        "funding": 1,
        "decision_maker": 2,
        "tech_stack": 1,
        "revenue": 1
    }
    
    # Create detailed scoring criteria based on weights
    criteria_explanation = []
    for criterion, weight in weights.items():
        if criterion == "company_size":
            criteria_explanation.append(f"- Company Size (weight: {weight}): Evaluate based on employee count - larger companies may have more budget and decision-making complexity")
        elif criterion == "industry_fit":
            criteria_explanation.append(f"- Industry Fit (weight: {weight}): Assess alignment with target industries - tech, SaaS, finance typically score higher")
        elif criterion == "funding":
            criteria_explanation.append(f"- Recent Funding (weight: {weight}): Consider recent funding rounds - well-funded companies have budget for new solutions")
        elif criterion == "decision_maker":
            criteria_explanation.append(f"- Decision Maker (weight: {weight}): Evaluate title/role - C-level, VP, Director roles indicate decision-making authority")
        elif criterion == "tech_stack":
            criteria_explanation.append(f"- Tech Stack (weight: {weight}): Assess technology alignment - modern tech stacks indicate innovation readiness")
        elif criterion == "revenue":
            criteria_explanation.append(f"- Revenue (weight: {weight}): Consider annual revenue - higher revenue suggests budget availability")
    
    criteria_text = "\n    ".join(criteria_explanation)
    
    return dedent(f"""
    You are a sales qualification assistant. Evaluate this lead using the following weighted criteria:

    {criteria_text}

    Scoring Weights: {weights}

    Lead Information:
    {lead}

    Instructions:
    1. Score each criterion from 0-10 based on the lead's information
    2. Apply the weights to calculate weighted scores
    3. Sum weighted scores and normalize to 0-100 scale
    4. Provide a clear justification for the overall score
    5. Include detailed breakdown showing individual criterion scores

    Return strictly valid JSON:
    {{
      "score": <int 0-100>,
      "justification": "<string explaining the overall score>",
      "breakdown": {{
        "company_size": {{"score": <0-10>, "weighted_score": <float>, "reason": "<string>"}},
        "industry_fit": {{"score": <0-10>, "weighted_score": <float>, "reason": "<string>"}},
        "funding": {{"score": <0-10>, "weighted_score": <float>, "reason": "<string>"}},
        "decision_maker": {{"score": <0-10>, "weighted_score": <float>, "reason": "<string>"}},
        "tech_stack": {{"score": <0-10>, "weighted_score": <float>, "reason": "<string>"}},
        "revenue": {{"score": <0-10>, "weighted_score": <float>, "reason": "<string>"}}
      }}
    }}
    """).strip()

def outreach_prompt(lead: Dict, tone: str="professional", goal: str="book a 30-min discovery call") -> str:
    return dedent(f"""
    You are an SDR writing a cold outreach email tailored to the lead below.
    Use the lead/company metadata to personalize subject and first paragraph.
    Keep it short (subject + 3 short paragraphs), end with a clear CTA to {goal}.
    Output JSON:
    {{
      "subject": "<subject line>",
      "body": "<email body in plain text>",
      "tags": ["<tag1>", "<tag2>"]
    }}

    Lead:
    {lead}

    Tone: {tone}
    """).strip()

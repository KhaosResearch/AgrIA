import json
from pathlib import Path

SKILL_DIR = Path(__file__).parent.resolve()


def generate_llm_payload():
    with open(SKILL_DIR / "analysis_results.json", "r") as f:
        analysis = json.load(f)

    with open(SKILL_DIR / "satellite_prompts.json", "r") as f:
        prompts = json.load(f)

    # Dynamically build summary context based on analysis results
    if analysis["image_type"] == "agricultural":
        content = (
            f"Agricultural layout detected with {analysis['vegetation_percentage']}% vegetative coverage. "
            f"Inferred phenological stage: '{analysis['phenological_stage']}'. "
            f"Structural edge density score: {analysis['edge_density']}."
        )
    else:
        content = (
            f"Urban layout detected with building/structural complexity variance score of "
            f"{analysis['building_structural_variance']} and edge density of {analysis['edge_density']}."
        )

    llm_input = {
        "system_instructions": prompts["system_instructions"],
        "analysis_metrics": analysis,
        "derived_summary": content,
        "user_prompts": prompts["prompt_text"],
    }

    return llm_input


if __name__ == "__main__":
    payload = generate_llm_payload()
    print(json.dumps(payload, indent=2, ensure_ascii=False))

---
name: satellite-image-analysis
version: 1.1.0
description: "Analyze crop and urban satellite imagery based on actual image patterns with edge detection, pattern recognition, and phenological state inference"
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [image-analysis, satellite-imagery, agriculture, urban-analysis, edge-detection, land-use-mapping, phenology]
    category: geospatial-analysis
    related_skills: [systematic-debugging, test-driven-development, urban-planning-analysis]
---

# Satellite Image Analysis - Crop and Urban Landscapes

This skill provides precise analysis of satellite imagery for both agricultural and urban landscapes. It combines edge detection, color analysis, and pattern recognition to extract structural details and infer crop phenological stages ("crops not present", "crops growing", etc.) for text-only LLMs.

## Tool Execution & File Integration

To process an image, execute the Python assets in the following sequence:

1. **Run Feature Extraction**:
   Execute `satellite_analyzer.py` with the path to the target satellite image. This generates `analysis_results.json` containing spatial metrics.
   ```bash
   python satellite_analyzer.py <image_path>
   ```

2. **Format & Inject Context**:
   Execute `satellite_image_integration.py` to merge `analysis_results.json` with system prompts from `satellite_prompts.json`.
   ```bash
   python satellite_image_integration.py
   ```

---

## Observed Patterns & Phenological Inferences

### Agricultural Satellite Imagery:
- **Field boundaries**: Geometric distributions with clear edges.
- **Grassland & Crops**: Uniform green patches representing active growth.
- **Phenology Rules**:
  - High green channel intensity $\rightarrow$ **"Crops growing / Active canopy"**
  - High color variance / Low green channel $\rightarrow$ **"Crops not present / Bare soil / Till period"**
  - Mixed textures $\rightarrow$ **"Harvested / Transition stage"**
- **Pathway systems**: Clear delineation lanes between fields.

### Urban Satellite Imagery:
- **Building clusters**: Dense rectangular structures in organized blocks.
- **Infrastructure**: Stadiums, paved roads, and recreational zones.
- **Layout patterns**: Grid-based organization with urban-rural transitions.
- **Green spaces**: Trees and vegetative plots interspersed between structures.

---

## Integration with LLM Prompts

System Instruction (`satellite_prompts.json`):
> "Describe satellite images: Detail parcel boundaries, zones, textures, and features in 60 words. Classify as agricultural or urban. Note geometric patterns, grasslands, buildings, landscape composition, and crop phenological state."

### Output Constraints & Requirements
When generating the final description from the Python output payload:
1. **Length**: Strictly 60 words or fewer. Do not include any additional commentary or explanations.
2. **Classification**: Identify as either Agricultural or Urban.
3. **Features**: Note visible structures, geometric patterns, and boundary definitions.
4. **Phenology**: Infer crop status if an agricultural scene is detected.

---

## Output Generation Guidelines

Using the JSON payload returned from the integration step, compose the final narrative.

CRITICAL DIRECTIVES:
- Return ONLY the exact 50-60 word description block.
- DO NOT include headers (e.g., "**Descripción:**"), bullet points, word counts, or verification metrics.
- DO NOT include post-response commentary, explanations, or meta-analysis (e.g., "This description meets...", "The analysis used...").
- Output standard prose paragraphs directly.
- If Spanish and English are mixed in the user message, respond in Spanish. Otherwise, respond in English.

### Output Format Specification:
[Classification: Agricultural or Urban]. [50-60 word narrative detailing boundaries, structures/features, and phenological stage].

---

## Sample Output Examples

**Agricultural Image (~54 words):**
> Classification: Agricultural. Geo-distributed parcels feature rectangular pastures and quadriculated crop fields separated by clear pathway systems. Dominant green spectral signatures indicate active canopy development with crops growing across primary sectors. Darker contrasting areas highlight unplanted bare soil along field margins, showing heterogeneous vegetation patterns.

**Urban Image (~50 words):**
> Classification: Urban. Dense rectangular building clusters are organized in a clear grid-planned layout. The area features prominent paved infrastructure, integrated green spaces, and a central sports stadium. Visible urban-rural transition zones demarcate residential blocks from surrounding vegetative buffers.
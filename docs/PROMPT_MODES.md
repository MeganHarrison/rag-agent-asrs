# FM Global 8-34 ASRS Agent - Prompt Modes

The FM Global 8-34 ASRS Expert Agent now supports two distinct conversation modes, each optimized for different use cases:

## 1. Expert Q&A Mode (`prompt_mode="expert"`)

### Overview
Direct, concise responses with immediate access to FM Global database. Best for users who:
- Know their specific requirements
- Need quick answers to technical questions
- Want immediate figure/table references
- Seek cost optimization suggestions

### Key Features
- **Instant Lookups**: Direct figure and table identification
- **Precise Citations**: Always includes "Per Figure X and Table Y..."
- **Cost Focus**: Proactive optimization recommendations
- **Technical Depth**: Machine-readable claims and specifications

### Example Interaction
```
User: "I have a shuttle ASRS with 8ft deep racks and closed-top containers. What figures and tables apply?"

Agent: "Per Figure 12 and Table 14, your shuttle ASRS with 8ft rack depth requires:
- Horizontal spacing: 5ft maximum (can reduce sprinkler count by 50%)
- Closed-top containers eliminate in-rack sprinkler requirements
- Applicable protection scheme: Wet pipe ceiling-only
- Cost optimization: Consider reducing to 6ft depth to eliminate vertical barriers..."
```

### Best Use Cases
- Quick compliance checks
- Specific technical questions
- Cost estimation requests
- Figure/table lookups

## 2. Guided Design Process Mode (`prompt_mode="guided"`)

### Overview
Step-by-step requirements gathering for complete system design. Best for users who:
- Are new to FM Global 8-34 requirements
- Need comprehensive design guidance
- Want to ensure nothing is missed
- Prefer structured decision-making

### Key Features
- **Progressive Questions**: One decision at a time
- **Educational Context**: Explains impact of each choice
- **Systematic Approach**: Follows 5-step design process
- **Complete Documentation**: Comprehensive final specification

### Design Process Steps
1. **ASRS System Identification**
   - Shuttle vs Mini-Load vs Other
   - Explains protection implications

2. **Container/Storage Configuration**
   - Closed-top vs Open-top
   - Impact on protection levels

3. **Physical Dimensions**
   - Rack depth, spacing, height
   - Shows sprinkler count impact

4. **Protection Scheme Requirements**
   - Tables and figures selection
   - Special conditions identification

5. **Design Output & Specifications**
   - Complete requirements list
   - Installation guidelines
   - Compliance summary

### Example Interaction
```
User: "I need help designing a sprinkler system for my ASRS warehouse"

Agent: "I'll guide you through the FM Global 8-34 design process step by step.

**Step 1: ASRS System Identification**
What type of ASRS system are you designing?

• **Shuttle ASRS** - Horizontal loading with shuttle devices, typically 20-120ft high
• **Mini-Load ASRS** - Automated tote/carton handling, 8-40ft high
• **Other/Unsure** - Describe your system and I'll help identify it

Each type has different protection requirements. Shuttle systems typically need ceiling + selective in-rack, while mini-load often requires closer sprinkler spacing..."
```

### Best Use Cases
- New project design
- Complex multi-variable systems
- Training and education
- Comprehensive documentation needs

## API Integration

### Using Prompt Modes via API

#### Python Example
```python
from rag_agent.core.fm_global_agent import get_fm_global_agent
from rag_agent.core.dependencies import AgentDependencies

# Expert Mode
expert_agent = get_fm_global_agent(mode="expert")
result = await expert_agent.run("What tables apply to shuttle ASRS?", deps=deps)

# Guided Mode
guided_agent = get_fm_global_agent(mode="guided")
result = await guided_agent.run("Help me design my ASRS sprinklers", deps=deps)
```

#### REST API Example
```json
POST /chat

{
  "query": "Your question here",
  "prompt_mode": "expert",  // or "guided"
  "asrs_topic": "fire_protection",
  "conversation_history": []
}
```

### CLI Usage

When starting the CLI, you'll be prompted to select a mode:

```bash
$ python fm_global_cli.py

Select conversation mode:
1. Expert Mode - Direct Q&A with instant answers
2. Guided Mode - Step-by-step design process
3. Standard Mode - Comprehensive consulting approach

Enter mode (1/2/3): 1
✓ Expert Q&A Mode activated
```

You can switch modes anytime using the `mode` command.

## Mode Selection Guidelines

### Choose Expert Mode When:
- ✅ You have specific technical questions
- ✅ You know your ASRS configuration details
- ✅ You need quick figure/table references
- ✅ You want cost optimization suggestions
- ✅ You're experienced with FM Global requirements

### Choose Guided Mode When:
- ✅ You're starting a new design project
- ✅ You're unfamiliar with FM Global 8-34
- ✅ You want comprehensive coverage
- ✅ You need educational context
- ✅ You prefer structured decision-making

## Configuration

### Environment Variable
Set default mode in `.env`:
```bash
FM_GLOBAL_PROMPT_MODE=expert  # or "guided"
```

### Runtime Selection
Override at runtime:
```python
from rag_agent.core.fm_global_prompts import PROMPT_MODE
PROMPT_MODE = "guided"  # Changes default for session
```

## Technical Implementation

Both modes:
- Access the same FM Global database
- Use identical search tools and functions
- Maintain conversation history
- Support streaming responses
- Provide table/figure references

The difference is purely in the conversational approach and response structure.

## Future Enhancements

Planned improvements:
- **Adaptive Mode**: Automatically switches based on query complexity
- **Hybrid Mode**: Combines expert answers with guided follow-ups
- **Profile Mode**: Remembers user preferences and expertise level
- **Training Mode**: Interactive tutorials with examples
## Project Overview

This project develops an AI-powered system for automating FM Global 8-34 ASRS (Automated Storage and Retrieval Systems) sprinkler design and compliance. The system transforms the complex 119-page FM Global document into an intelligent RAG (Retrieval-Augmented Generation) agent that can:

1. **Expert AI Chat** - Answer questions and identify exact tables/figures for requirements
2. **Dynamic Form Generation** - Guide users through requirement identification
3. **Interactive Documentation** - Transform the PDF into navigable content
4. **Lead Generation** - Qualify prospects and generate ballpark quotes

## Business Context

**Client**: Alleato - ASRS sprinkler design and construction for large warehouses
**Problem**: FM Global 8-34 PDF is poorly designed, time-consuming, and error-prone
**Opportunity**: Streamline process, reduce human error, generate significant cost savings
**Market**: 3PL and integrator companies needing ASRS sprinkler compliance

## Data Architecture

### Core Database Tables

#### 1. Figures Database (`fm_global_figures_rows.csv`)
- **32 figures** systematically categorized
- **Navigation & System Diagrams** (Figures 1-3)
- **Shuttle ASRS Layouts** (Figures 4-25) - Closed/open-top arrangements
- **Mini-Load ASRS** (Figures 26-45) - Various depth configurations

**Key Fields:**
```
- figure_number: Primary identifier
- title: Descriptive name
- normalized_summary: AI-optimized description
- figure_type: Category (Navigation, System Diagram, Sprinkler Layout)
- asrs_type: Shuttle, Mini-Load, All
- container_type: Closed-Top, Open-Top, null
- max_depth_ft/max_depth_m: Physical dimensions
- max_spacing_ft/max_spacing_m: Sprinkler spacing
- machine_readable_claims: JSON with programmatic data
- search_keywords: Array of searchable terms
```

#### 2. Tables Database (`fm_global_tables_rows.csv`) 
- **36 tables** with detailed requirements
- **Branch line calculations** with equations
- **Protection schemes** by ASRS type and commodity
- **Design parameters** with conditions and exceptions

**Key Fields:**
```
- table_number: Primary identifier  
- asrs_type: System compatibility
- protection_scheme: Wet, dry, ceiling-only, in-rack
- commodity_types: Materials covered
- ceiling_height_min/max_ft: Height constraints
- sprinkler_specifications: JSON with K-factors, orientations
- design_parameters: JSON with calculation rules
- special_conditions: Exceptions and requirements
```

#### 3. Vector Embeddings (`fm_table_vectors_rows.csv`)
- **80 vectorized chunks** for semantic search
- **OpenAI text-embedding-3-small** model
- **Content summaries** optimized for RAG retrieval
- **Metadata** for filtering and context

#### 4. Cost Factors (`fm_cost_factors_rows.csv`)
- **Component pricing** (pipes, sprinklers, etc.)
- **Regional adjustments** for accurate estimates
- **Complexity multipliers** for non-standard installations

### Machine-Readable Claims Structure

Each figure includes JSON for programmatic use:
```json
{
  \"max_rack_depth\": 3,
  \"max_spacing\": 2.5,
  \"sprinkler_count\": 8,
  \"numbering\": \"1-8\", 
  \"container_type\": \"Closed-Top\",
  \"requires_flue_spaces\": true,
  \"protection_level\": \"Standard\",
  \"applicable_commodities\": [\"Class 1-4\", \"Cartoned Plastics\"]
}
```

## Key ASRS Concepts

### System Types
1. **Shuttle ASRS** - Horizontal loading mechanism with shuttle devices
2. **Mini-Load ASRS** - Smaller systems with angle iron supports
3. **Top-Loading ASRS** - Vertical loading configurations

### Container Classifications
- **Closed-Top** - Fully enclosed containers (less protection needed)
- **Open-Top** - Open containers (more protection required)
- **Uncartoned** - Direct product storage (highest protection)

### Protection Schemes
- **Wet Systems** - Water-filled pipes (most common)
- **Dry Systems** - Air-filled pipes for freezing environments
- **Ceiling-Only** - Sprinklers at ceiling level only
- **In-Rack (IRAS)** - Additional sprinklers within racks
- **Combined** - Ceiling + in-rack protection

### Critical Dimensions
- **Rack Depth** - Front-to-back dimension (affects sprinkler count)
- **Spacing** - Distance between sprinklers (affects coverage)
- **Ceiling Height** - Impacts pressure requirements
- **Aisle Width** - Affects protection patterns

## Cost Optimization Strategies

### Automatic Identification Opportunities
1. **Spacing Optimization** - \"Increase spacing from 2.5ft to 5ft = 50% fewer sprinklers\"
2. **Rack Depth Reduction** - \"Reduce depth by 1ft = eliminate vertical barriers\"
3. **Container Type Changes** - \"Switch to closed-top = reduced protection requirements\"
4. **Protection Scheme Selection** - \"Ceiling-only vs. in-rack cost comparison\"

### Lead Qualification Metrics
- **High-Value Configurations** - Complex arrangements requiring extensive protection
- **Non-Standard Applications** - Outside typical guidelines (higher margins)
- **Large Square Footage** - Significant sprinkler quantities

## RAG Implementation Guidelines

### Query Processing Strategy
1. **Intent Classification** - Question type (requirement lookup, cost estimate, compliance check)
2. **Entity Extraction** - ASRS type, dimensions, commodities, conditions
3. **Multi-Modal Retrieval** - Combine figure, table, and text searches
4. **Validation Logic** - Cross-reference requirements across sources

### Search Optimization
```sql
-- Example: Find applicable figures
SELECT * FROM fm_global_figures 
WHERE asrs_type IN ('Shuttle', 'All')
  AND container_type = 'Closed-Top'
  AND max_depth_ft >= 6.0
  AND max_spacing_ft >= 4.0;

-- Example: Get protection requirements  
SELECT * FROM fm_global_tables
WHERE commodity_types LIKE '%Cartoned Plastics%'
  AND asrs_type = 'Mini-Load'
  AND protection_scheme = 'wet';
```

### Response Generation Patterns
1. **Requirement Answers** - \"Based on Figure 12 and Table 8...\"
2. **Cost Estimates** - \"Estimated X sprinklers at $Y each...\"
3. **Compliance Guidance** - \"Must meet conditions in Section...\"
4. **Optimization Suggestions** - \"Consider these alternatives to reduce cost...\"

## Form Generation Logic

### Progressive Disclosure Questions
1. **ASRS Type** - Shuttle, Mini-Load, Top-Loading
2. **System Type** - Wet, Dry, Pre-action
3. **Storage Configuration** - Height, depth, spacing
4. **Commodity Types** - Class 1-4, Plastics, etc.
5. **Environmental Factors** - Ceiling height, temperature
6. **Special Conditions** - Seismic, corrosion, etc.

### Dynamic Field Generation
```javascript
// Example: Generate fields based on ASRS type
if (asrsType === 'Shuttle') {
  showFields(['containerType', 'rackDepth', 'aisleWidth']);
} else if (asrsType === 'Mini-Load') {
  showFields(['toteSize', 'verticalSpacing', 'horizontalSpacing']);
}
```

## Compliance Validation Rules

### Critical Requirements
1. **Minimum Clearances** - 4\" between storage and sprinkler deflectors
2. **Spacing Limits** - Maximum distances per commodity type
3. **Pressure Requirements** - Based on height and K-factor
4. **Installation Standards** - Per NFPA and FM guidelines

### Validation Chains
```
User Input → Dimension Validation → Commodity Compatibility → 
Protection Scheme Selection → Sprinkler Calculation → 
Pressure Requirements → Code Compliance Check
```

## Integration Architecture

### API Endpoints
- `POST /analyze-requirements` - Process ASRS configuration
- `GET /figures/{id}` - Retrieve specific figure details  
- `GET /tables/{id}` - Get table requirements
- `POST /estimate-cost` - Calculate material costs
- `POST /generate-quote` - Create formal proposal

### Database Schema Notes
- All tables use UUID primary keys
- Vector embeddings stored as arrays
- JSON fields for complex structured data
- Temporal fields for versioning and updates

## Success Metrics

### Technical KPIs
- **Query Response Time** < 2 seconds
- **Accuracy Rate** > 95% for requirement identification
- **Cost Estimate Variance** < 10% from actual

### Business KPIs  
- **Lead Qualification Rate** - % of forms resulting in qualified leads
- **Quote Generation Time** - Minutes vs. hours previously
- **Cost Optimization Value** - $ saved per project through recommendations

## Development Priorities

### Phase 1 - MVP RAG Agent
1. Core question-answering capability
2. Figure and table retrieval
3. Basic cost estimation
4. Simple form generation

### Phase 2 - Advanced Features
1. Complex requirement validation
2. Multi-scenario cost optimization
3. Interactive documentation site
4. Lead qualification scoring

### Phase 3 - Enterprise Integration
1. CRM webhooks for lead processing
2. PDF quote generation
3. Project management integration
4. Advanced analytics dashboard

## Domain Expertise Notes

### Common User Intents
- \"What figures apply to my shuttle ASRS with 8ft deep racks?\"
- \"How many sprinklers do I need for 50,000 sq ft warehouse?\"
- \"What's the difference between wet and dry system costs?\"
- \"Does my configuration meet FM Global requirements?\"

### Technical Edge Cases
- **Mixed Commodity Storage** - Different protection zones
- **Seismic Considerations** - Additional bracing requirements  
- **Temperature Extremes** - Dry system vs. glycol solutions
- **High-Piled Storage** - >20ft rack heights
- **Specialized Products** - Aerosols, flammable liquids

### Regulatory Context
- **FM Global** - Insurance-driven standards (most restrictive)
- **NFPA 13** - Base fire protection standard
- **Local AHJs** - Authority Having Jurisdiction variations
- **International Codes** - Regional adaptations needed

This comprehensive guide provides Claude Code with the complete context needed to develop an expert-level FM Global 8-34 ASRS RAG agent that can serve Alleato's business objectives while maintaining technical accuracy and compliance.`
}
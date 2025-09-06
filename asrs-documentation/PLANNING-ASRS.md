# FM Global 8-34 ASRS Sprinkler System - Complete Solution

## OVERVIEW

In the files, I've uploaded the FM global 8–34 code requirements for a ASRS sprinkler systems. Alleato provides ASRS sprinkler design and construction for large warehouses.

In order to pass inspection, it's essential that all requirements are met from the ASRS documentation. However, this PDF is so poorly designed. It takes forever to try to figure out the nuances, and there are so many opportunities for human error.

The goal is to streamline, simplify, and heavily leverage AI with this process to ultimately bottom line profit.

I'd like you to review this PDF in extreme detail and act as an expert in automated warehouse storage and retrieval systems and FM global 8–34 code requirements so that you know exactly what data we need to know in order to identify the design requirements.

We will use this knowledge to ultimately create the following:

1. AI Chat that serves as an expert in ASRS and FM-Global 8-34. The agent will be able to answer questions, identify the exact tables and figures that need to be referenced, design the asrs system, and help with coming up with innovative ideas to modify the design in order to generate significant savings.

2. Front end form that ask the user the necessary questions in order to identify the requirements.

3. Documentation site to transform the FM-Global pdf into an easy to navigate interactive version.

## FEATURE:
Build a comprehensive AI-powered platform for FM Global 8-34 ASRS (Automated Storage and Retrieval System) sprinkler design compliance, optimization, and lead generation. The system must streamline the complex process of navigating FM Global requirements while creating significant cost optimization opportunities and automating quote generation and asrs sprinkler design for Alleato's ASRS sprinkler design and construction business.

### Core Components Required:

#### 1. AI Expert Chat System
- **RAG-powered AI assistant** that serves as an expert in ASRS systems and FM Global 8-34 code requirements
- **Precise figure/table identification** - Must identify exact tables (1-20+) and figures (1-47+) for any given configuration
- **Design validation** - Ensures all FM Global requirements are met for inspection compliance
- **Innovative modification suggestions** - Proposes design changes that significantly reduce costs while maintaining compliance

#### 2. Dynamic Requirements Form
- **Multi-step wizard** that collects necessary information to determine requirements
- **Smart conditionals** - Shows/hides fields based on ASRS type, container configuration, protection scheme
- **Real-time validation** - Validates inputs against FM Global constraints as user types
- **Progress indicators** - Clear progression through the complex requirements gathering process
- **Automatic table/figure selection** - Uses collected data to identify applicable requirements

#### 3. Interactive Documentation Site
- **Searchable, filterable interface** replacing the poorly-designed 119-page PDF
- **Visual navigation** starting with Figure 1 decision tree
- **Linked references** between figures and tables with instant access
- **Machine-readable claims** displayed alongside human-readable content
- **Mobile-responsive design** for field use during inspections

### Technical Architecture Required:

#### Database Structure (Already Provided):
- **32 Figures** with machine-readable claims, normalized summaries, and metadata
- **46 Tables** with detailed specifications, design parameters, and conditions  
- **Vector embeddings** for semantic search capabilities
- **Cost factors** for automated pricing calculations
- **Cross-references** between figures, tables, and requirements

#### Key Data Structures:
```json
{
  "asrs_types": ["Shuttle", "Mini-Load", "Top-Loading"],
  "container_types": ["Closed-Top", "Open-Top", "Mixed"],
  "protection_schemes": ["In-Rack with Ceiling", "Ceiling Only", "In-Rack Only"],
  "max_depths": [3, 6, 8, 12], // feet
  "max_spacings": [2.0, 2.5, 4.0, 5.0], // feet
  "ceiling_heights": [20, 30, 40, 45], // feet ranges
  "sprinkler_specifications": {
    "k_factors": [11.2, 14.0, 16.8],
    "orientations": ["Upright", "Pendent", "Sidewall"],
    "temperature_ratings": ["155°F", "212°F", "286°F"]
  }
}
```

#### Required Calculations:
- **Sprinkler quantity calculations** based on rack dimensions and spacing
- **Hydraulic design area** determinations from applicable tables
- **Cost estimations** using base costs and complexity multipliers
- **Optimization scenarios** comparing different configuration options

## EXAMPLES:
Refer to the uploaded CSV files in the examples/ folder:

### Database Schema Examples:
- **`fm_global_figures_rows.csv`** - Complete figure database with machine-readable claims
- **`fm_global_tables_rows.csv`** - Comprehensive table specifications with design parameters  
- **`fm_cost_factors_rows.csv`** - Cost calculation factors for quote generation
- **`fm_table_vectors_rows.csv`** - Vector embeddings for semantic search

### Key Patterns to Follow:
- **Machine-readable claims structure** from figures database for programmatic use
- **Nested JSON specifications** in tables database for complex requirements
- **Search keyword optimization** for RAG system effectiveness
- **Cost multiplier patterns** for regional and complexity adjustments

### Critical Data Examples:
- **Figure 1**: Navigation decision tree for entire FM Global 8-34 standard
- **Figures 4-13**: Shuttle ASRS closed-top arrangements (depths 3-12 ft, spacings 2.5-5 ft)
- **Figures 14-25**: Shuttle ASRS open-top arrangements with specific sprinkler numbering
- **Figures 26-45**: Mini-Load ASRS horizontal IRAS layouts for various configurations
- **Tables 14-20**: Core shuttle ASRS specifications with detailed design parameters

## DOCUMENTATION:

### FM Global 8-34 Standard Requirements:
- **ASRS Type Classification**: Shuttle, Mini-Load, Top-Loading systems
- **Container Configuration Impact**: Closed-top vs Open-top requirements differ significantly
- **Protection Scheme Selection**: In-rack with ceiling, ceiling-only, in-rack only
- **Spacing Optimization**: 2.5 ft vs 4-5 ft spacing can reduce sprinkler count by 50%+
- **Depth Limitations**: 3 ft depth avoids vertical barriers, 6+ ft requires complex arrangements

### Critical Navigation Flow:
1. **ASRS Type Identification** → Determines applicable figure range
2. **Container Type Selection** → Closed-top (Figures 4-13) vs Open-top (Figures 14-25)
3. **Dimension Constraints** → Rack depth and spacing determine specific figure
4. **Table Cross-Reference** → Figure references specific requirement tables
5. **Sprinkler Specification** → Tables provide exact K-factors, orientations, temperatures

### Cost Optimization Opportunities:
- **Spacing Increases**: 2.5 ft → 4 ft spacing = ~35% sprinkler reduction
- **Container Type Changes**: Closed-top containers reduce protection complexity
- **Rack Depth Optimization**: Limiting to 3 ft eliminates vertical barrier requirements
- **Protection Scheme Selection**: Ceiling-only systems significantly reduce in-rack infrastructure

### RAG System Requirements:
- **Semantic search** across normalized summaries for natural language queries
- **Exact matching** on technical specifications using machine-readable claims
- **Cross-reference resolution** between figures and tables automatically
- **Context-aware responses** understanding ASRS domain-specific terminology

## OTHER CONSIDERATIONS:

### Critical Implementation Details:

#### Human Error Prevention:
- **The original FM Global PDF is extremely poorly designed** - requires extensive cross-referencing
- **Complex figure numbering systems** (1-8, 1a-8a, etc.) must be handled programmatically
- **Multiple requirement layers** - figures reference tables which reference other tables
- **Regional code variations** may require different interpretations

#### Cost Optimization Engine Requirements:
- **Automatic scenario generation** - "What if we change container type?"
- **Savings quantification** - "Changing spacing saves $47,000 in sprinklers"
- **Compliance validation** - Ensure all optimizations maintain FM Global compliance
- **ROI calculations** - Factor installation labor, material costs, and timeline impacts

#### Form Logic Complexity:
- **Conditional field display** based on previous selections
- **Real-time requirement updates** as users change inputs  
- **Progress indicators** showing completion status through complex workflow
- **Validation messaging** explaining why certain combinations are invalid

#### Performance Requirements:
- **Sub-second query response** for RAG system searches
- **Real-time form validation** without perceived lag
- **Instant quote generation** for configurations under 100 sprinklers
- **PDF generation** must complete within 10 seconds for complex quotes

#### Mobile Considerations:
- **Field inspector access** - Must work on tablets/phones during site visits
- **Offline capability** - Core requirements checking without internet
- **Photo integration** - Allow site photos to be attached to quotes/assessments
- **GPS integration** - Automatic location stamping for site visits

#### Integration Requirements:
- **Supabase backend** with vector search capabilities for RAG system
- **PDF generation** for professional quotes and specification documents  
- **Email automation** for quote delivery and follow-up sequences
- **Analytics tracking** for lead conversion and optimization effectiveness

### Success Metrics:
- **Quote Generation Speed**: From 4+ hours manual process to under 5 minutes automated
- **Error Reduction**: Eliminate human cross-reference errors that cause inspection failures
- **Cost Optimization Impact**: Average 15-30% cost reduction through automated optimization suggestions
- **Lead Conversion**: Improve lead qualification and conversion rates through instant, professional quotes
- **User Adoption**: System must be intuitive enough for non-experts to use effectively

### Common Pitfalls to Avoid:
- **Over-simplifying the requirements logic** - FM Global has numerous edge cases and exceptions
- **Ignoring cross-references** - Figures and tables are heavily interconnected
- **Static forms** - Requirements are highly conditional and must update dynamically
- **Poor mobile experience** - Field use is critical for inspections and site visits
- **Inadequate cost modeling** - Regional variations and complexity multipliers are essential

# ASRS Sprinkler System Data Requirements Analysis
## FM Global 8-34 Comprehensive Review

### 1. ASRS System Classification Parameters

#### 1.1 Primary ASRS Type Classification
**Critical Decision Point #1**
- **Horizontal-Loading ASRS (HL-ASRS)**
  - Mini-load type: Uses angle irons/guides for support
  - Shuttle type: Uses slats/mesh shelving without vertical guides
- **Top-Loading ASRS (TL-ASRS)**: Robots access containers from above on grid
- **Vertically Enclosed ASRS**: Lift or carousel type systems

#### 1.2 Container Classification
**Critical Decision Point #2**
- **Material Composition**:
  - Noncombustible (metal)
  - Combustible cellulosic (cardboard)
  - Unexpanded plastic
  - Expanded plastic (NOT covered - outside scope)
  
- **Container Configuration**:
  - Closed-top vs Open-top
  - Solid-walled vs Non-solid-walled
  - Solid-bottom vs Non-solid-bottom (gridded bottoms NOT covered)

### 2. Critical Dimensional Parameters

#### 2.1 Rack/Storage Configuration
- **Rack row depth**: Horizontal length perpendicular to loading aisle
- **Tier height**: 9-18 inches typical for HL-ASRS
- **Storage height**: Maximum height above floor
- **Ceiling height**: Critical for sprinkler selection
- **Aisle width**: Minimum requirements vary (3-8 ft)

#### 2.2 Rack Structure Details (Mini-load Specific)
- **Rack upright spacing**: Typically 18-24 inches horizontally
- **Rack upright dimensions**: 2-3 inches wide x 3 inches deep
- **Transverse flue space width**: Minimum 3 inches
- **Longitudinal flue space**: 3-24 inches (>24 inches = aisle)
- **Horizontal distance between transverse flue spaces**

#### 2.3 Container/Tray Dimensions
- **Small container**: Max 18" height, typically 16"x24"x15"
- **Small tray**: Lip â‰¤1.25" height, typically 16"x24"

### 3. Commodity Classification Requirements

#### 3.1 FM Global Commodity Classes
- **Class 1**: Noncombustible products in noncombustible packaging
- **Class 2**: Noncombustible products in combustible packaging
- **Class 3**: Combustible products (wood, paper, natural fibers)
- **Class 4**: Class 1-3 with limited plastic content
- **Plastics**: 
  - Cartoned unexpanded
  - Uncartoned unexpanded
  - Cartoned expanded
  - Uncartoned expanded

#### 3.2 Special Hazards (Require Separate Guidelines)
- Ignitable liquids â†’ See DS 7-29
- Aerosols â†’ See DS 7-31
- Lithium-ion batteries â†’ See DS 7-112

### 4. Sprinkler System Design Parameters

#### 4.1 Ceiling Sprinkler Requirements
- **System Type**: Wet, Dry, Preaction, Antifreeze
- **Sprinkler Temperature Rating**: 160Â°F, 280Â°F, etc.
- **Response Type**: Quick-response vs Standard-response
- **Coverage Type**: Standard vs Extended-coverage
- **Orientation**: Pendent vs Upright
- **K-Factor Options**: K11.2, K14.0, K16.8, K22.4, K25.2, K28.0, K33.6

#### 4.2 In-Rack Sprinkler Requirements (IRAS)
- **Vertical spacing between levels**
- **Horizontal spacing requirements**
- **Face sprinkler requirements**
- **K-factor specifications** (typically K8.0)
- **Water delivery time**: Max 40 seconds for dry systems

#### 4.3 Hydraulic Design Parameters
- **Design area of operation**: Number of sprinklers
- **Minimum pressure requirements**: 7-80 psi range
- **Hose demand**: 250-500 gpm
- **Water supply duration**: 60-120 minutes

### 5. Critical Design Decision Trees

#### 5.1 Protection Scheme Selection
1. **Ceiling-only protection** (when allowed)
2. **Ceiling + In-rack sprinklers** (most common for combustibles)
3. **Modular in-rack design** (prevents vertical fire spread)

#### 5.2 Key Dimensional Thresholds
- Storage height â‰¤20 ft: Different requirements
- Storage height >20 ft: Enhanced protection
- Storage height >55 ft: Maximum for many configurations
- Rack row depth â‰¤3 ft vs â‰¤6 ft vs >6 ft
- Ceiling height impacts sprinkler selection

### 6. Cost Optimization Opportunities

#### 6.1 Container Material Changes
- **Noncombustible containers**: Eliminate in-rack sprinklers
- **Closed-top vs open-top**: Significant protection differences
- **Solid-walled vs non-solid**: Changes fire spread characteristics

#### 6.2 Dimensional Modifications
- **Aisle width adjustments**: 
  - <6 ft may require higher pressures
  - â‰¥8 ft allows more options
- **Transverse flue spacing**:
  - Proper spacing improves water penetration
  - Reduces sprinkler requirements
- **Storage height optimization**:
  - Stay under critical thresholds (20 ft, 25 ft, etc.)
  - Avoid triggering enhanced protection

#### 6.3 System Type Trade-offs
- **Wet vs Dry systems**: Different sprinkler counts/pressures
- **Quick-response vs Standard**: Performance differences
- **K-factor selection**: Balance flow vs pressure

### 7. Required Input Data for Form System

#### 7.1 Facility Information
- [ ] Building construction type
- [ ] Ceiling height
- [ ] Floor drainage capacity
- [ ] Available water supply (pressure/flow)

#### 7.2 ASRS System Configuration
- [ ] ASRS type (HL-mini-load, HL-shuttle, TL, Vertically enclosed)
- [ ] Overall storage dimensions (L x W x H)
- [ ] Number of storage levels/tiers
- [ ] Aisle configuration and widths

#### 7.3 Rack Structure Details
- [ ] Rack row depth
- [ ] Rack upright spacing
- [ ] Tier heights
- [ ] Transverse flue space width
- [ ] Longitudinal flue space width
- [ ] Support type (angle irons vs slats)

#### 7.4 Container/Product Information
- [ ] Container material (metal, cardboard, plastic type)
- [ ] Container configuration (closed/open-top, solid/non-solid walls)
- [ ] Container dimensions
- [ ] Commodity classification
- [ ] Special hazards present

#### 7.5 Environmental Conditions
- [ ] Ambient temperature (freezer, cooler, ambient)
- [ ] Ventilation/airflow conditions
- [ ] Seismic zone considerations

### 8. Validation Requirements

#### 8.1 Code Compliance Checks
- Minimum clearances (3 ft to ceiling sprinklers)
- Maximum storage heights for configuration
- Required fire detection systems
- Small hose station requirements
- Emergency shutdown procedures

#### 8.2 System Performance Validation
- Water delivery times (<20 sec wet, <40 sec dry)
- Hydraulic balance between ceiling and in-rack
- Design area coverage
- Obstruction compliance

### 9. Automated Recommendation Engine Logic

#### 9.1 Cost Optimization Algorithm
```
IF (open-top combustible containers) THEN
  EVALUATE: Changing to closed-top â†’ Eliminate in-rack sprinklers
  SAVINGS: $X based on sprinkler density reduction

IF (rack row depth > 6 ft) THEN
  EVALUATE: Reducing to â‰¤6 ft â†’ Lower pressure requirements
  SAVINGS: $Y based on pump/pipe sizing

IF (storage height = 21 ft) THEN
  EVALUATE: Reducing to â‰¤20 ft â†’ Avoid enhanced protection
  SAVINGS: $Z based on sprinkler count reduction
```

#### 9.2 Risk-Based Recommendations
- Identify borderline configurations
- Calculate incremental costs for safety margins
- Provide tiered options (minimum, recommended, premium)

### 10. Documentation Output Requirements

#### 10.1 Design Specification Report
- Complete sprinkler system layout
- Hydraulic calculations
- Equipment specifications
- Installation guidelines

#### 10.2 Compliance Checklist
- FM Global 8-34 requirement verification
- Local code compliance
- Insurance requirements
- Testing/commissioning procedures

#### 10.3 Cost Analysis
- Initial installation costs
- Potential optimization savings
- Maintenance requirements
- Insurance premium impacts

---

## Next Steps for Implementation

### Phase 1: Data Collection Form Development
- Create intelligent form with conditional logic
- Implement validation rules
- Build help text/tooltips for each field

### Phase 2: Calculation Engine
- Develop table lookup algorithms
- Implement interpolation for intermediate values
- Create optimization suggestion generator

### Phase 3: Documentation System
- Convert PDF to searchable web format
- Create interactive decision trees
- Build visual aids and diagrams

### Phase 4: Testing & Validation
- Test against known designs
- Validate with FM Global requirements
- User acceptance testing
- Compliance verification
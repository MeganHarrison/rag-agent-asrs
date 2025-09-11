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

### Phase 3: Documentation System
- Convert PDF to searchable web format
- Create interactive decision trees
- Build visual aids and diagrams

### Phase 4: Testing & Validation
- Test against known designs
- Validate with FM Global requirements
- User acceptance testing
- Compliance verification

### Future Implementation
- Optimization and cost saver
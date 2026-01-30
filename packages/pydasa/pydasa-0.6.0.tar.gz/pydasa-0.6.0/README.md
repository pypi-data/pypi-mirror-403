# PyDASA

Library to solve software architecture and physical problems with dimensionless analysis and the Pi-Theorem

## Epic User Story

**As a** researcher, engineer, or software architect analyzing complex systems,

**I want** a comprehensive dimensional analysis library implementing the Buckingham Pi theorem,

**So that** I can systematically discover dimensionless relationships, validate models, and understand system behavior across physical, computational, and software architecture domains.

### Core Capabilities

#### Dimensional Framework Management
- **Manage fundamental dimensions** beyond traditional physical units (L, M, T) .to include computational (T, S, N) and software architecture domains (T, D, E, C, A).
- **Switch between frameworks** for different problem domains.

#### Parameter and Variable Management
- **Define dimensional parameters** with complete specifications:
   - Symbolic representation (name, LaTeX symbol).
   - Dimensional formula (e.g., "L*T^-1" for velocity).
   - Numerical ranges (min, max, mean, step)
   - Classification (input, output, control).
   - Statistical distributions and dependencies.

#### Unit System Integration
- **Handle measurements** across unit systems (imperial, metric, custom).
- **Convert between units** while maintaining dimensional consistency.
- **Relate measurements** to dimensional parameters.

#### Dimensionless Coefficient Discovery
- **Generate dimensionless numbers** using the Buckingham Pi theorem:
   1. **Build relevance list:** Identify mutually independent parameters influencing the phenomenon.
   2. **Construct dimensional matrix:** Arrange FDUs (rows) and variables (columns) into core and residual matrices.
   3. **Transform to identity matrix:** Apply linear transformations to the core matrix.
   4. **Generate Pi coefficients:** Combine residual and unity matrices to produce dimensionless groups.
- **Classify coefficients** by repeating vs. non-repeating parameters.
- **Manage metadata:** names, symbols, formulas, and parameter relationships.

#### Analysis and Simulation
- **Verify similitude principles** for model scaling and validation.
- **Calculate coefficient ranges** and parameter influence.
- **Run Monte Carlo simulations** to quantify uncertainty propagation.
- **Perform sensitivity analysis** to identify dominant parameters.
- **Generate behavioral data** for dimensionless relationships.

#### Data Export and Visualization Integration
- **Export data formats** compatible with pandas, matplotlib, seaborn.
- **Structure results** for integration with visualization libraries.
- **Provide standardized outputs** for dimensionless charts and parameter influence plots.

## Emoji

1. TODO 📋
2. WORKING 🔶👨‍💻
3. DONE ✅
4. WARNING ⚠️

## Development Status

### ✅ Completed

- **Src:** Merged buckingham→dimensional, split config, moved parameter to elements, renamed datastruct→structs and handlers→workflows
- **Imports:** Fixed 7 files (analysis, workflows, dimensional modules) to use new paths
- **Code Quality:** Fixed syntax errors, enhanced Enum validation, fixed frozen dataclass issues
- **Tests:** Updated test_basic.py and test_setup.py, all 16 core tests passing, structure aligned with src
- **Decorator Migration:** 100\% complete - all core classes migrated to decorator-based validation (463+ tests passing)
   - Elements: Variable, Coefficient, Basic, Fundamental, Measurement, Parameter
   - Workflows: SensitivityAnalysis (21/21 tests ✓), MonteCarloSimulation (14/14 tests ✓), AnalysisEngine (27/27 tests ✓)
   - **Validation System:** Enhanced @validate_emptiness to handle dictionaries, lists, and all collections (not just strings)
   - **Package Configuration (v0.3.2):**
   - Added package-data to include JSON config files in distribution
   - Exposed `__version__` attribute in main module (7/7 package tests passing)
   - Configured semantic versioning for 0.x releases (major_on_zero=false)
   - Updated CHANGELOG.md with recent changes
   - **Dimensional Analysis Fix:**
   - Fixed empty dimensional columns bug in CUSTOM framework variables
   - Added validation in Matrix.create_matrix() to detect missing dimensions
   - Fixed 5 test files (test_phenomena.py, test_scenario.py, test_simulation.py, test_practical.py, test_influence.py)
   - All variables now properly initialize with schema and parse dimensions (130/130 tests passing)
   - **Documentation Structure:**
   - Integrated public folder subpages into main index.rst
   - Reorganized navigation: Getting Started, User Guide, Design & Architecture, API Reference, Examples, Development, Project
   - Documentation builds successfully with Sphinx

### 🔶 In Progress

- Implementing Solver() class in workflows/phenomena.py
- Incremental testing and validation

### 📋 Pending

- **context/**: Unit conversion system (conversion.py, system.py, units.py)
- **structs/**: Complete test coverage for lists, tables, tools modules
- **Tests**: Coverage for context, structs modules
- **Docs**: Fill in stub content for documentation pages (basics.rst, architecture.rst, requirements.rst, etc.)

## Src Path Structure

1. **pydasa**
   1. **analysis:** analysis and simulation modules, pending recheck📋!!!.

      1. scenario.py: contains the DimSensitivity class for understanding variance in the coefficients. ✅
      2. simulation.py: monte carlo simulator for one coefficient (MonteCarloSim class). ✅

      ---
   2. **context:** unit conversion and measurement context (future scope)

      1. conversion.py: unit conversion handler for the solver. 📋
      2. system.py: system of units management. 📋
      3. units.py: unit definitions and operations. 📋

      ---
   3. **core:** shared and core capabilities.

      1. basic.py: contains Foundation, SymBasis, IdxBasis classes, shared capabilities for entities with validation. ✅
      2. constants.py: contains predefined dimensional frameworks (PHYSICAL, COMPUTATION, SOFTWARE) and FDU definitions. ✅
      3. io.py: contains all the input/output functions for saving/loading data of the analysis. ✅
      4. setup.py: contains global configuration (Framework, VarCardinality, CoefCardinality, AnaliticMode enums) and PyDASAConfig singleton. ✅
      5. **cfg/**: configuration files folder
         1. default.json: default framework configurations. ✅

      ---
   4. **dimensional:** dimensional analysis core, pending recheck📋!!!.

      1. buckingham.py: contains the Coefficient class to represent dimensionless numbers (formerly vashchy.py). ✅
      2. framework.py: contains the DimSchema class to manage and control FDUs in the solving process. UPDATING CODE NOW🔶👨‍💻!!!.
      3. fundamental.py: contains Dimension class for Buckingham Pi-theorem specific operations. ✅
      4. model.py: contains the DimMatrix class to solve the dimensional matrix. ✅

      ---
   5. **elements:** parameter and variable management with specification classes. ✅

      1. parameter.py: contains Parameter class for dimensional parameter analysis with decorator-based validation. ✅
      2. **specs/**: specification classes for different aspects of parameters
         1. conceptual.py: contains conceptual specifications (category, schema). ✅
         2. numerical.py: contains numerical specifications (min, max, mean, dev, ranges). ✅
         3. statistical.py: contains statistical specifications (distributions, dependencies). ✅
         4. symbolic.py: contains symbolic specifications (dimensions, units, expressions). ✅

      ---
   6. **structs:** data structures and utilities, pending extensive tests📋!!!.

      1. **lists**

         1. arlt.py: arraylist implementation. ✅
         2. dllt.py: double linked list implementation. 📋
         3. ndlt.py: node list for double and single linked lists. ✅
         4. sllt.py: single linked list implementation. ✅
      2. **tables**

         1. htme.py: entry used in the separate chaining hashtable. ✅
         2. scht.py: separate chaining hashtable implementation. ✅
      3. **tools**

         1. hashing.py: hashing utilities for data structures. ✅
         2. math.py: mathematical utilities for dimensional analysis. ✅
         3. memory.py: memory management utilities. ✅
      4. **types**

         1. functions.py: function type definitions and utilities. ✅
         2. generics.py: generic type definitions and type aliases. ✅

      ---
   7. **workflows:** analysis workflow handlers (formerly tasks). ✅

      1. influence.py: contains the SensitivityAnalysis class (formerly SensitivityHandler) for understanding variance in the coefficients. ✅
      2. phenomena.py: has the main Solver() class of the project. IMPORTANT📋!!!
      3. practical.py: contains the MonteCarloSimulation class (formerly MonteCarloHandler) to control all the Monte Carlo simulations. ✅

      ---
   8. **serialization:** parsing and serialization utilities. ✅

      1. parser.py: contains LaTeX and formula parsing functions for better representation (formerly utils/latex.py). ✅

      ---
   9. **validations:** validation decorators, patterns, and error handling. ✅

      1. decorators.py: contains all validation decorators (@validate_type, @validate_emptiness, @validate_choices, @validate_range, @validate_index, @validate_pattern, @validate_custom). Fully implemented with enhanced @validate_emptiness supporting strings, dicts, lists, and all collections. ✅
      2. error.py: contains the generic error_handler() function and inspect_var() for all components. ✅
      3. patterns.py: contains regex patterns for validation and parsing (formerly utils/patterns.py). ✅

      ---

## Tests Path Structure

1. **pydasa**
   1. **analysis:** shared analytic capabilities, pending updates📋!!!.

      1. test_scenario.py: tests for sensitivity analysis of the Coefficients (DimSensitivity class). ✅
      2. test_simulation.py: tests for the Monte Carlo simulator for one coefficient (MonteCarloSim class). ✅

      ---
   2. **context:** shared unit of measure and system capabilities.

      1. test_conversion.py: tests for unit conversion handler. 📋
      2. test_system.py: tests for system of units management. 📋
      3. test_units.py: tests for unit definitions and operations. 📋

      ---
   3. **core:** shared and core capabilities

      1. test_basic.py: tests for the Foundation, SymBasis, IdxBasis classes. ✅
      2. test_constants.py: tests for predefined dimensional frameworks and FDU definitions. ✅
      3. test_io.py: tests for all the input/output functions for saving/loading data. ✅
      4. test_setup.py: tests for global configuration and PyDASAConfig singleton. ✅

      ---
   4. **data:** test fixtures and sample data

      1. test_data.py: contains test data for all PyDASA tests (fixtures and samples). ✅

      ---
   5. **dimensional:** main dimensiona analysis capabilities, pending updates📋!!!.

      1. test_buckingham.py: tests for the Coefficient class. ✅
      2. test_framework.py: tests for the DimSchema class to manage and control FDUs. 🔶👨‍💻
      3. test_fundamental.py: tests for the Dimension class. ✅
      4. test_model.py: tests for the DimMatrix class to solve the dimensional matrix. ✅

      ---
   6. **elements:** parameter and variable tests with specification tests. ✅

      1. test_parameter.py: tests for the Parameter class. ✅
      2. **specs/**: specification class tests
         1. test_conceptual.py: tests for conceptual specifications. ✅
         2. test_numerical.py: tests for numerical specifications. ✅
         3. test_statistical.py: tests for statistical specifications. ✅
         4. test_symbolic.py: tests for symbolic specifications. ✅

      ---
   7. **structs:** data structures tests, fundamental for unit of measure and conversions. 📋

      1. **lists**

         1. test_arlt.py: tests for the arraylist. 📋
         2. test_dllt.py: tests for the double linked list. 📋
         3. test_ndlt.py: tests for the node list for double and single linked. 📋
         4. test_sllt.py: tests for the single linked list. 📋
      2. **tables**

         1. test_htme.py: tests for the entry useful for the separate chaining hashtable. 📋
         2. test_scht.py: tests for the separate chaining hashtable. 📋
      3. **tools**

         1. test_hashing.py: tests for hashing utilities. 📋
         2. test_math.py: tests for mathematical utilities. 📋
         3. test_memory.py: tests for memory management utilities. 📋
      4. **types**

         1. test_functions.py: tests for function type definitions. 📋
         2. test_generics.py: tests for generic type definitions and type aliases. 📋

      ---
   8. **workflows** (formerly tasks)

      1. test_influence.py: tests for the SensitivityAnalysis class (formerly SensitivityHandler) for understanding variance in the coefficients. All 21 tests passing. ✅
      2. test_phenomena.py: tests for the main Solver() class of the project. 📋
      3. test_practical.py: tests for the MonteCarloSimulation class (formerly MonteCarloHandler) to control all the Monte Carlo simulations. All 14 tests passing. ✅

      ---
   9. **serialization:** parsing and serialization tests. ✅

      1. test_parser.py: tests for LaTeX and formula parsing functions (formerly test_latex.py). ✅

      ---
   10. **validations:** validation decorators, patterns, and error handling tests. ✅

       1. test_decorators.py: tests for all validation decorators (@validate_type, @validate_pattern, @validate_choices, etc.). ✅
       2. test_error.py: tests for the generic error_handler() function and inspect_var() for all components. ✅
       3. test_patterns.py: tests for regex patterns for validation and parsing. ✅

       ---

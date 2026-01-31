  Summary of the 6-Step A11y Audit Workflow

  Step 1: Structural Analysis & Discovery
  - Identify UI framework (React, Vue, Angular)
  - Locate component files and map page structure
  - Detect CSS framework (Tailwind, Bootstrap, custom)
  - Create component inventory for analysis

  Step 2: ARIA Labels & Attributes
  - Check for missing aria-label or aria-labelledby on interactive elements
  - Verify role attributes are used correctly
  - Validate aria-describedby, aria-hidden, aria-live regions
  - Check stateful ARIA attributes (expanded, selected, checked)
  - Validate landmark roles

  Step 3: Keyboard Navigation
  - Verify all interactive elements are keyboard accessible
  - Check logical tab order
  - Detect keyboard traps
  - Verify modal focus trapping
  - Check for tabindex misuse (avoid positive values)
  - Verify dropdown/menu keyboard controls

  Step 4: Focus Management
  - Check focus management during content changes (SPA navigation)
  - Verify focus returns to trigger element after modal close
  - Check focus indicators are visible
  - Verify focus moves to newly revealed content
  - Check for focus loss during async operations

  Step 5: Visual Accessibility & Color Contrast
  - Check text color contrast (WCAG AA: 4.5:1 normal text, 3:1 large text)
  - Verify interactive element contrast (buttons, links: 3:1)
  - Tailwind-specific checks: text-gray-400, text-gray-500 contrast issues
  - Check focus indicators have sufficient contrast
  - Verify disabled state contrast
  - Check for information conveyed by color alone

  Step 6: Semantic HTML & WCAG Compliance
  - Check for semantic HTML5 elements (header, nav, main, footer)
  - Verify heading hierarchy (no skipped levels)
  - Check button vs. anchor usage
  - Verify form structure (fieldset/legend)
  - Check image alt text
  - Verify WCAG 2.1 Level AA compliance

  The plan includes a complete data model, sample report structure (A11Y-AUDIT.MD), and integration with the existing
  workflow infrastructure. It requires no new external dependencies and leverages all the existing WorkflowTool
  patterns.

──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
 Ready to code?

 Here is Claude's plan:
╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌
 UI Accessibility Audit Tool - Implementation Plan

 Created: 2026-01-13
 Based on: specs/006-security-audit (security audit tool pattern)

 Summary

 Create an a11y_audit MCP tool that performs comprehensive UI accessibility audits following the same multi-step
 workflow pattern as the security audit tool. The tool will guide users through a 6-step analysis covering ARIA
 labels, keyboard navigation, focus management, color contrast, and semantic HTML to ensure WCAG 2.1/2.2 compliance.

 Architecture Overview

 The accessibility audit tool will extend the existing WorkflowTool base class, mirroring the successful architecture
  of the security audit tool:

 Tool (Protocol)
     ↓
 WorkflowTool (ABC)
     ↓
 AccessibilityAuditTool (NEW)

 Key Pattern: The same deferred API execution pattern will be used - external LLM analysis (if needed) only occurs at
  workflow completion, not on each step.

 6-Step Accessibility Audit Workflow

 Step 1: Structural Analysis & Discovery

 Domain: STRUCTURE
 Focus: Component identification, page structure, UI framework detection

 Required Actions:
 - Identify UI framework (React, Vue, Angular, vanilla HTML)
 - Locate component files (tsx, jsx, vue, html templates)
 - Map page structure and navigation hierarchy
 - Identify interactive elements (buttons, forms, modals, dialogs)
 - Detect CSS framework (Tailwind, Bootstrap, custom CSS)

 Expected Findings:
 - Application type and framework
 - Component inventory
 - Entry points for deeper analysis

 ---
 Step 2: ARIA Labels & Attributes

 Domain: ARIA_LABELS
 Focus: Missing or incorrect ARIA labels, roles, states, properties

 Required Actions:
 - Check for missing aria-label or aria-labelledby on interactive elements
 - Verify role attributes are used correctly (button, navigation, dialog, etc.)
 - Validate aria-describedby for form fields and complex controls
 - Check aria-hidden usage (should not hide focusable elements)
 - Verify aria-live regions for dynamic content
 - Check aria-expanded, aria-selected, aria-checked for stateful components
 - Validate landmark roles (main, navigation, complementary, contentinfo)

 Common Issues to Detect:
 - Icons/buttons without labels
 - Form inputs without labels or aria-label
 - Custom dropdowns/selects missing ARIA attributes
 - Modal dialogs without role="dialog" and aria-modal="true"
 - Incorrect ARIA attribute values

 ---
 Step 3: Keyboard Navigation

 Domain: KEYBOARD_NAV
 Focus: Keyboard navigation issues, tab order, keyboard traps

 Required Actions:
 - Verify all interactive elements are keyboard accessible (tab-reachable)
 - Check logical tab order (matches visual flow)
 - Detect keyboard traps (focus cannot escape a component)
 - Verify keyboard shortcuts don't conflict with browser/screen reader shortcuts
 - Check for tabindex misuse (avoid positive values)
 - Verify skip links for navigation
 - Check modal focus trapping (focus should stay within modal)
 - Verify dropdown/menu keyboard controls (arrow keys, Enter, Escape)

 Common Issues to Detect:
 - Div/span elements with onClick but no keyboard handler
 - Missing tabindex="0" on custom interactive elements
 - Positive tabindex values (anti-pattern)
 - No keyboard way to close modals/dialogs
 - Missing focus indicators (outline removed without replacement)

 ---
 Step 4: Focus Management

 Domain: FOCUS_MANAGEMENT
 Focus: Focus loss, modal dialogs, dynamic content focus handling

 Required Actions:
 - Check focus is managed when content changes (SPA navigation)
 - Verify focus returns to trigger element after modal close
 - Check focus moves to newly revealed content (accordion, tabs)
 - Verify focus indicator visibility (CSS outline or custom styles)
 - Check for focus loss during async operations
 - Verify autofocus usage is appropriate (not overused)
 - Check focus is programmatically managed for dynamic insertions

 Common Issues to Detect:
 - Focus lost on page navigation (SPA)
 - No focus indicator (outline: none without replacement)
 - Focus not returned after modal close
 - Focus not moved to error messages after form submission
 - Invisible focus indicators (color contrast too low)

 ---
 Step 5: Visual Accessibility & Color Contrast

 Domain: COLOR_CONTRAST
 Focus: Color contrast issues, especially in Tailwind CSS / CSS

 Required Actions:
 - Check text color contrast against background (WCAG AA: 4.5:1 for normal text, 3:1 for large text)
 - Verify interactive element contrast (buttons, links, form controls: 3:1)
 - Check Tailwind color utilities (text-gray-400 on bg-gray-100 may fail)
 - Verify focus indicators have sufficient contrast (3:1 minimum)
 - Check icon-only buttons have adequate visual distinction
 - Verify disabled state contrast (should still be perceivable)
 - Check for information conveyed by color alone (needs text/icon alternative)

 Common Issues to Detect:
 - Low contrast text (common in Tailwind: text-gray-400, text-gray-500)
 - Placeholder text too light
 - Link color insufficient contrast
 - Disabled inputs invisible (too light)
 - Focus indicators with low contrast
 - CSS with hardcoded color values that fail contrast

 Tailwind-Specific Checks:
 - text-gray-400 on bg-white (fails AA)
 - text-blue-400 on bg-white (may fail AA)
 - Custom color configurations in tailwind.config.js

 ---
 Step 6: Semantic HTML & WCAG Compliance

 Domain: SEMANTIC_HTML
 Focus: Proper HTML5 elements, overall WCAG 2.1/2.2 compliance

 Required Actions:
 - Check for semantic HTML5 elements (header, nav, main, footer, article, section)
 - Verify heading hierarchy (h1 → h2 → h3, no skipped levels)
 - Check for div/span overuse (should use semantic elements instead)
 - Verify button vs. anchor usage (buttons for actions, anchors for navigation)
 - Check form structure (fieldset/legend for grouped inputs)
 - Verify list markup for lists (ul/ol, not div/span)
 - Check image alt text (decorative: alt="", informative: descriptive alt)
 - Verify language attribute on html tag
 - Check for WCAG 2.1 Level AA compliance gaps

 Common Issues to Detect:
 - Divs used instead of buttons/links
 - Clickable spans instead of buttons
 - Skipped heading levels (h1 → h3)
 - Missing main landmark
 - Images without alt attributes
 - Forms without labels
 - Lists not marked up as lists

 ---
 Data Model

 AccessibilityFinding

 @dataclass
 class AccessibilityFinding:
     severity: AccessibilitySeverity      # CRITICAL, HIGH, MEDIUM, LOW, INFO
     wcag_criterion: str                  # e.g., "1.1.1", "2.1.1", "4.1.2"
     category: str                        # e.g., "ARIA", "Keyboard", "Contrast"
     description: str
     affected_files: list[str]
     affected_elements: list[str]         # CSS selectors or component names
     remediation: str
     wcag_level: str                      # "A", "AA", "AAA"

 AccessibilitySeverity (Enum)

 - CRITICAL: Blocks users from accessing core functionality (e.g., no keyboard navigation, missing form labels)
 - HIGH: Significantly impacts accessibility (e.g., low contrast, missing ARIA labels)
 - MEDIUM: Moderate impact (e.g., suboptimal tab order, minor semantic HTML issues)
 - LOW: Minor issues (e.g., missing skip links, non-critical ARIA attributes)
 - INFO: Best practice recommendations

 AccessibilityStepDomain (Enum)

 - STRUCTURE (Step 1)
 - ARIA_LABELS (Step 2)
 - KEYBOARD_NAV (Step 3)
 - FOCUS_MANAGEMENT (Step 4)
 - COLOR_CONTRAST (Step 5)
 - SEMANTIC_HTML (Step 6)

 A11yReport

 @dataclass
 class A11yReport:
     executive_summary: str
     findings_by_severity: dict[AccessibilitySeverity, list[AccessibilityFinding]]
     findings_by_wcag: dict[str, list[AccessibilityFinding]]  # Grouped by WCAG criterion
     files_examined: list[str]
     total_violations: int
     severity_counts: dict[AccessibilitySeverity, int]
     wcag_compliance_level: str           # "A", "AA", "AAA", or "Non-compliant"
     recommendations: list[str]
     expert_analysis: str | None          # LLM analysis if triggered

 Technical Implementation

 File Structure

 tools/
 └── a11y_audit/              # NEW
     ├── __init__.py
     ├── tool.py              # AccessibilityAuditTool (extends WorkflowTool)
     ├── finding.py           # AccessibilityFinding dataclass
     ├── severity.py          # AccessibilitySeverity enum
     ├── domains.py           # AccessibilityStepDomain enum
     ├── guidance.py          # Step-specific guidance
     ├── report.py            # A11Y-AUDIT.MD generator
     └── wcag.py              # WCAG criterion mappings

 tests/
 ├── unit/tools/a11y_audit/
 │   ├── test_tool.py
 │   ├── test_guidance.py
 │   ├── test_report.py
 │   └── test_wcag.py
 └── integration/
     └── test_a11y_audit_workflow.py

 Key Classes

 AccessibilityAuditTool (extends WorkflowTool):
 - name: "a11y_audit"
 - description: "Perform comprehensive UI accessibility audit with WCAG 2.1/2.2 compliance"
 - execute(): Maps a11y-specific parameters (accessibility_findings, contrast_issues, etc.)
 - get_required_actions(): Returns domain-specific actions per step
 - _generate_guidance(): Uses AccessibilityAuditGuidance
 - process_step(): Parses AccessibilityFinding data
 - _handle_completion(): Generates A11Y-AUDIT.MD
 - should_call_expert_analysis(): Returns true if critical/high findings exist AND confidence != "certain"
 - prepare_expert_analysis_context(): Formats findings for LLM validation

 AccessibilityAuditGuidance:
 - get_step_guidance(step_number) -> StepGuidance: Returns step-specific required_actions and next_steps
 - Includes mandatory pause instruction to prevent immediate tool re-calls

 A11yReportGenerator:
 - generate_report(consolidated_findings) -> A11yReport: Aggregates findings
 - to_markdown(report) -> str: Converts to markdown format
 - Groups findings by severity AND by WCAG criterion

 Report Structure (A11Y-AUDIT.MD)

 # UI Accessibility Audit Report

 **Generated**: 2026-01-13 10:00:00
 **Tool**: optix-mcp-server a11y_audit
 **WCAG Compliance Level**: AA (Target)

 ## Executive Summary

 | Metric | Count |
 |--------|-------|
 | Total Violations | 12 |
 | Critical | 2 |
 | High | 5 |
 | Medium | 3 |
 | Low | 2 |
 | WCAG Level A Compliance | 🔴 Non-compliant |
 | WCAG Level AA Compliance | 🔴 Non-compliant |

 **Risk Assessment**: Application has critical accessibility barriers that prevent keyboard-only and screen reader
 users from accessing core functionality.

 ## Findings by Severity

 ### CRITICAL Severity

 #### 1. Missing Keyboard Navigation on Primary CTA
 **WCAG**: 2.1.1 Keyboard (Level A)
 **Category**: Keyboard Navigation
 **Description**: Main "Submit Order" button is implemented as a div with onClick handler, making it inaccessible to
 keyboard users.
 **Affected Files**: `src/components/CheckoutForm.tsx`
 **Affected Elements**: `.submit-button` (line 45)
 **Remediation**: Replace div with a button element or add tabindex="0" and onKeyDown handler for Enter/Space keys.

 ---

 ### HIGH Severity

 #### 2. Insufficient Color Contrast on Body Text
 **WCAG**: 1.4.3 Contrast (Minimum) (Level AA)
 **Category**: Color Contrast
 **Description**: Body text uses text-gray-400 on bg-white, resulting in 3.2:1 contrast ratio (fails 4.5:1 minimum).
 **Affected Files**: `src/styles/globals.css`, `src/components/ProductCard.tsx`
 **Affected Elements**: `.product-description`, `.body-text`
 **Remediation**: Use text-gray-700 or darker (7:1 ratio) for body text. Update Tailwind config if needed.

 ---

 ## Findings by WCAG Criterion

 ### 1.1.1 Non-text Content (Level A)
 - Missing alt text on product images (HIGH)
 - Decorative icons not marked as aria-hidden (LOW)

 ### 1.4.3 Contrast (Minimum) (Level AA)
 - Body text contrast failure (HIGH)
 - Link color insufficient contrast (HIGH)

 ### 2.1.1 Keyboard (Level A)
 - Custom dropdown not keyboard accessible (CRITICAL)
 - Modal close button div instead of button (CRITICAL)

 ### 4.1.2 Name, Role, Value (Level A)
 - Missing aria-label on icon buttons (HIGH)
 - Custom checkbox without role and aria-checked (HIGH)

 ## Files Examined

 - src/components/CheckoutForm.tsx
 - src/components/ProductCard.tsx
 - src/components/Navigation.tsx
 - src/components/Modal.tsx
 - src/styles/globals.css
 - tailwind.config.js

 ## Recommendations (Priority Order)

 1. **IMMEDIATE** (Critical): Convert all clickable divs/spans to button elements or add proper keyboard handlers
 2. **IMMEDIATE** (Critical): Add aria-label to all icon-only buttons
 3. **HIGH PRIORITY**: Fix color contrast violations (update Tailwind theme)
 4. **HIGH PRIORITY**: Add focus indicators to all interactive elements
 5. **MEDIUM PRIORITY**: Implement skip links for main navigation
 6. **MEDIUM PRIORITY**: Fix heading hierarchy (ensure no skipped levels)
 7. **LOW PRIORITY**: Add landmark roles to major page sections

 ## WCAG 2.1 Compliance Summary

 | Level | Status | Notes |
 |-------|--------|-------|
 | Level A | 🔴 Non-compliant | 5 Level A violations (2.1.1, 4.1.2) |
 | Level AA | 🔴 Non-compliant | 8 Level AA violations (1.4.3 contrast) |
 | Level AAA | ⚪ Not assessed | Fix A/AA first |

 ---

 *Auto-generated by optix-mcp-server a11y_audit tool*
 *For questions or issues, see documentation*

 Integration with Existing Infrastructure

 Workflow Base Class Integration

 The tool will use the existing WorkflowTool infrastructure:
 - ✅ WorkflowStateManager (singleton state management)
 - ✅ WorkflowRequest/WorkflowResponse (request/response models)
 - ✅ ConsolidatedFindings (finding accumulation with new a11y helper methods)
 - ✅ StepGuidance (step-specific guidance structure)
 - ✅ ConfidenceLevel (confidence tracking)

 New Helper Methods for ConsolidatedFindings

 # Add to tools/workflow/findings.py
 def get_findings_by_wcag(self) -> dict[str, list[dict]]:
     """Group accessibility findings by WCAG criterion."""

 def get_wcag_compliance_level(self) -> str:
     """Determine highest WCAG compliance level achieved."""

 MCP Server Registration

 # In server.py
 from tools.a11y_audit import AccessibilityAuditTool

 a11y_audit_tool = AccessibilityAuditTool()

 @mcp.tool()
 async def a11y_audit(
     step_number: int,
     continuation_id: str | None = None,
     next_step_required: bool = True,
     files_examined: list[str] = [],
     accessibility_findings: list[dict] = [],
     confidence: str = "exploring"
 ) -> dict:
     """
     Perform step-by-step UI accessibility audit.

     Returns structured guidance for accessibility analysis including
     ARIA labels, keyboard navigation, focus management, color contrast,
     and semantic HTML checks.
     """
     return a11y_audit_tool.execute(
         step_number=step_number,
         continuation_id=continuation_id,
         next_step_required=next_step_required,
         files_examined=files_examined,
         findings=accessibility_findings,
         confidence=confidence
     )

 Verification Plan

 End-to-End Test Scenario

 1. User calls a11y_audit with step_number: 1 → Receives structural analysis guidance
 2. User examines React components → Reports framework (React) and component files
 3. Tool returns step 2 guidance → ARIA label focus
 4. User examines ARIA attributes → Reports 3 missing aria-label findings
 5. Steps 3-6 continue similarly → Each step accumulates findings
 6. User calls step 6 with next_step_required: false → Tool generates A11Y-AUDIT.MD

 Critical Files to Test

 - React component with missing ARIA labels
 - Tailwind CSS with low contrast colors
 - Custom button implemented as div
 - Modal dialog without focus trap
 - Form without proper labels

 Success Criteria

 - ✅ Complete 6-step workflow without errors
 - ✅ Findings grouped by severity (CRITICAL → HIGH → MEDIUM → LOW)
 - ✅ Findings grouped by WCAG criterion
 - ✅ WCAG compliance level accurately determined
 - ✅ Report includes actionable remediation steps
 - ✅ Tailwind-specific color contrast issues detected

 Implementation Phases

 Phase 1: Foundation (MVP)

 - Create AccessibilityFinding, AccessibilitySeverity, AccessibilityStepDomain
 - Create AccessibilityAuditTool extending WorkflowTool
 - Implement basic 6-step guidance
 - Implement A11yReportGenerator
 - Register tool in server.py

 Phase 2: Guidance & Domain Logic

 - Implement detailed step-by-step guidance for all 6 domains
 - Add WCAG criterion mapping (wcag.py)
 - Enhance report with WCAG compliance summary

 Phase 3: Testing & Polish

 - Unit tests for all components
 - Integration test for full workflow
 - Update CLAUDE.md with a11y_audit tool
 - Create quickstart.md example

 Key Differences from Security Audit
 ┌──────────────────┬──────────────────────────┬────────────────────────────────────────────────────┐
 │      Aspect      │      Security Audit      │                     A11y Audit                     │
 ├──────────────────┼──────────────────────────┼────────────────────────────────────────────────────┤
 │ Domain           │ Security vulnerabilities │ Accessibility barriers                             │
 ├──────────────────┼──────────────────────────┼────────────────────────────────────────────────────┤
 │ Primary Standard │ OWASP Top 10             │ WCAG 2.1/2.2                                       │
 ├──────────────────┼──────────────────────────┼────────────────────────────────────────────────────┤
 │ Finding Entity   │ SecurityFinding          │ AccessibilityFinding                               │
 ├──────────────────┼──────────────────────────┼────────────────────────────────────────────────────┤
 │ Severity Focus   │ Exploit risk             │ User impact (can't access vs. difficult to access) │
 ├──────────────────┼──────────────────────────┼────────────────────────────────────────────────────┤
 │ Step 5 Focus     │ Dependencies/config      │ Color contrast/visual                              │
 ├──────────────────┼──────────────────────────┼────────────────────────────────────────────────────┤
 │ Report Grouping  │ By severity              │ By severity AND WCAG criterion                     │
 ├──────────────────┼──────────────────────────┼────────────────────────────────────────────────────┤
 │ Tool Name        │ security_audit           │ a11y_audit                                         │
 ├──────────────────┼──────────────────────────┼────────────────────────────────────────────────────┤
 │ Report File      │ AUDIT.MD                 │ A11Y-AUDIT.MD                                      │
 └──────────────────┴──────────────────────────┴────────────────────────────────────────────────────┘
 WCAG Criterion Reference

 Quick reference for common WCAG violations:
 ┌────────┬────────────────────────┬───────┬─────────────────────────────────────────────────┐
 │ WCAG # │          Name          │ Level │                  Common Issues                  │
 ├────────┼────────────────────────┼───────┼─────────────────────────────────────────────────┤
 │ 1.1.1  │ Non-text Content       │ A     │ Missing alt text                                │
 ├────────┼────────────────────────┼───────┼─────────────────────────────────────────────────┤
 │ 1.3.1  │ Info and Relationships │ A     │ Improper heading hierarchy, missing form labels │
 ├────────┼────────────────────────┼───────┼─────────────────────────────────────────────────┤
 │ 1.4.3  │ Contrast (Minimum)     │ AA    │ Text contrast < 4.5:1                           │
 ├────────┼────────────────────────┼───────┼─────────────────────────────────────────────────┤
 │ 2.1.1  │ Keyboard               │ A     │ Not keyboard accessible                         │
 ├────────┼────────────────────────┼───────┼─────────────────────────────────────────────────┤
 │ 2.4.3  │ Focus Order            │ A     │ Illogical tab order                             │
 ├────────┼────────────────────────┼───────┼─────────────────────────────────────────────────┤
 │ 2.4.7  │ Focus Visible          │ AA    │ No visible focus indicator                      │
 ├────────┼────────────────────────┼───────┼─────────────────────────────────────────────────┤
 │ 4.1.2  │ Name, Role, Value      │ A     │ Missing ARIA labels/roles                       │
 └────────┴────────────────────────┴───────┴─────────────────────────────────────────────────┘
 Dependencies

 No new external dependencies required - uses existing:
 - mcp[cli]>=1.25.0 (FastMCP)
 - Python 3.13.11 standard library (dataclasses, abc, uuid)
 - pytest>=7.0 for testing

 Timeline Estimate

 This is a straightforward extension of the existing security audit pattern:
 - Foundation setup: ~3 hours
 - 6-step guidance implementation: ~4 hours
 - Report generation: ~2 hours
 - Testing: ~3 hours
 - Total: ~12 hours (1.5 days)

 Next Steps

 1. ✅ Complete this plan
 2. Create spec.md in new feature branch (007-a11y-audit)
 3. Implement foundation (Phase 1)
 4. Implement guidance (Phase 2)
 5. Testing & validation (Phase 3)
 6. Update documentation

 ---
 Plan Status: Ready for review and approval
 Blockers: None - all infrastructure exists
 Risk Level: Low (proven pattern from security audit)
"""Step-specific accessibility audit guidance."""

from tools.a11y_audit.domains import AccessibilityStepDomain
from tools.workflow.guidance import StepGuidance

TOTAL_STEPS = 6


def get_step_guidance(step_number: int) -> StepGuidance:
    """Get guidance for a specific audit step.

    Args:
        step_number: Step number (1-6)

    Returns:
        StepGuidance with required actions and next steps
    """
    domain = AccessibilityStepDomain.from_step_number(step_number)

    guidance_map = {
        1: _get_structural_analysis_guidance,
        2: _get_aria_labels_guidance,
        3: _get_keyboard_navigation_guidance,
        4: _get_focus_management_guidance,
        5: _get_color_contrast_guidance,
        6: _get_semantic_html_guidance,
    }

    guidance_func = guidance_map.get(step_number, _get_structural_analysis_guidance)
    return guidance_func(domain)


def _get_structural_analysis_guidance(domain: AccessibilityStepDomain) -> StepGuidance:
    """Guidance for Step 1: Structural Analysis & Discovery."""
    return StepGuidance(
        required_actions=[
            "Identify UI framework (React, Vue, Angular, vanilla HTML)",
            "Locate UI component files (tsx, jsx, vue, html templates)",
            "Map page structure and navigation hierarchy",
            "Identify interactive elements (buttons, forms, modals, dialogs)",
            "Detect CSS framework (Tailwind, Bootstrap, custom CSS)",
        ],
        suggestions=[
            "Look for package.json to identify framework",
            "Use grep/rg to find component patterns",
            "Check for tailwind.config.js or Bootstrap imports",
        ],
        next_step_focus="ARIA Labels & Attributes",
        confidence_guidance="Explore the codebase structure to identify key files and patterns",
    )


def _get_aria_labels_guidance(domain: AccessibilityStepDomain) -> StepGuidance:
    """Guidance for Step 2: ARIA Labels & Attributes."""
    return StepGuidance(
        required_actions=[
            "Check for missing aria-label or aria-labelledby on interactive elements",
            "Verify role attributes are used correctly (button, navigation, dialog)",
            "Validate aria-describedby for form fields and complex controls",
            "Check aria-hidden usage (should not hide focusable elements)",
            "Verify aria-live regions for dynamic content",
            "Check aria-expanded, aria-selected, aria-checked for stateful components",
            "Validate landmark roles (main, navigation, complementary, contentinfo)",
        ],
        suggestions=[
            "Search for icon-only buttons without aria-label",
            "Check form inputs for labels or aria-label",
            "Look for custom dropdowns/selects missing ARIA attributes",
            "Verify modal dialogs have role='dialog' and aria-modal='true'",
        ],
        next_step_focus="Keyboard Navigation",
        confidence_guidance="Examine ARIA attributes systematically across all interactive components",
    )


def _get_keyboard_navigation_guidance(
    domain: AccessibilityStepDomain,
) -> StepGuidance:
    """Guidance for Step 3: Keyboard Navigation."""
    return StepGuidance(
        required_actions=[
            "Verify all interactive elements are keyboard accessible (tab-reachable)",
            "Check logical tab order (matches visual flow)",
            "Detect keyboard traps (focus cannot escape a component)",
            "Verify keyboard shortcuts don't conflict with browser/screen reader shortcuts",
            "Check for tabindex misuse (avoid positive values)",
            "Verify skip links for navigation",
            "Check modal focus trapping (focus should stay within modal)",
            "Verify dropdown/menu keyboard controls (arrow keys, Enter, Escape)",
        ],
        suggestions=[
            "Search for <div onClick> or <span onClick> without keyboard handlers",
            "Look for positive tabindex values (anti-pattern)",
            "Check custom interactive components for tabindex=0",
            "Verify onKeyDown handlers for clickable non-button elements",
        ],
        next_step_focus="Focus Management",
        confidence_guidance="Test keyboard navigation systematically through all interactive paths",
    )


def _get_focus_management_guidance(domain: AccessibilityStepDomain) -> StepGuidance:
    """Guidance for Step 4: Focus Management."""
    return StepGuidance(
        required_actions=[
            "Check focus is managed when content changes (SPA navigation)",
            "Verify focus returns to trigger element after modal close",
            "Check focus moves to newly revealed content (accordion, tabs)",
            "Verify focus indicator visibility (CSS outline or custom styles)",
            "Check for focus loss during async operations",
            "Verify autofocus usage is appropriate (not overused)",
            "Check focus is programmatically managed for dynamic insertions",
        ],
        suggestions=[
            "Search for outline:none without custom focus indicators",
            "Check modal close handlers for focus restoration",
            "Look for useRef/ref usage for focus management",
            "Verify focus moves to error messages after form submission",
        ],
        next_step_focus="Visual Accessibility & Color Contrast",
        confidence_guidance="Trace focus flow through dynamic content changes and modals",
    )


def _get_color_contrast_guidance(domain: AccessibilityStepDomain) -> StepGuidance:
    """Guidance for Step 5: Color Contrast."""
    return StepGuidance(
        required_actions=[
            "Check text color contrast against background (WCAG AA: 4.5:1 for normal text)",
            "Verify interactive element contrast (buttons, links: 3:1 minimum)",
            "Check Tailwind color utilities (text-gray-400 on bg-gray-100 may fail)",
            "Verify focus indicators have sufficient contrast (3:1 minimum)",
            "Check icon-only buttons have adequate visual distinction",
            "Verify disabled state contrast (should still be perceivable)",
            "Check for information conveyed by color alone (needs text/icon alternative)",
        ],
        suggestions=[
            "Search for text-gray-400, text-gray-500 (likely fails on white)",
            "Check text-blue-400, text-yellow-300 on light backgrounds",
            "Use browser DevTools accessibility checker for precise ratios",
            "Recommend text-gray-600+ for body text on light backgrounds",
        ],
        next_step_focus="Semantic HTML & WCAG Compliance",
        confidence_guidance="Identify common color contrast patterns and flag known failures",
    )


def _get_semantic_html_guidance(domain: AccessibilityStepDomain) -> StepGuidance:
    """Guidance for Step 6: Semantic HTML & WCAG Compliance."""
    return StepGuidance(
        required_actions=[
            "Check for semantic HTML5 elements (header, nav, main, footer, article)",
            "Verify heading hierarchy (h1 → h2 → h3, no skipped levels)",
            "Check for div/span overuse (should use semantic elements)",
            "Verify button vs. anchor usage (buttons for actions, anchors for navigation)",
            "Check form structure (fieldset/legend for grouped inputs)",
            "Verify list markup for lists (ul/ol, not div/span)",
            "Check image alt text (decorative: alt='', informative: descriptive alt)",
            "Verify language attribute on html tag",
            "Check for WCAG 2.1 Level AA compliance gaps",
        ],
        suggestions=[
            "Search for divs used as buttons/links",
            "Check heading level progression (h1, h2, h3)",
            "Verify main landmark exists",
            "Look for images without alt attributes",
        ],
        next_step_focus="Audit Complete",
        confidence_guidance="Perform final WCAG compliance check across all criteria",
    )

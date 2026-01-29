# ZERO-G CODE REVIEW PROTOCOL

Review the following code against the **Nexus Zero-G Standard**.

## Review Criteria

1.  **Structural Integrity (SOLID & DRY):**
    *   Are responsibilities clearly defined?
    *   Is code repeated unnecessarily?
    *   Can usage be simplified?

2.  **Type Safety & Robustness:**
    *   Are Type Hints used everywhere (Python `typing`, TS interfaces)?
    *   Are `Any` types avoided unless absolutely necessary?
    *   Are edge cases and errors handled gracefully (no bare `except` or silent failures)?

3.  **Modern Standards:**
    *   Does the code use the latest stable features of the language/library?
    *   Are deprecated patterns avoided?

4.  **Security:**
    *   Are inputs validated?
    *   Are secrets exposed?
    *   Are there obviously unsafe operations?

5.  **Performance:**
    *   Are there redundant computations?
    *   Is I/O blocked unnecessarily?

## Output Format

Provide your feedback in the following structure:

### 🔍 Critical Issues (Must Fix)
*   [Line X]: Description of the issue.

### ⚠️ Improvements (Should Fix)
*   [Line Y]: Suggestion for better style/performance.

### ✅ Best Practices (Keep/Praise)
*   Good usage of [Pattern/Library].

### 🛠️ Refactored Snippet (If Applicable)
```language
# Optimized verification code here
```

## Code to Review
{code}

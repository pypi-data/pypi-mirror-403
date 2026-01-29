# ZERO-G CODE GENERATION PROTOCOL

Generate code based on the requirements below, strictly adhering to **Nexus** standards.

## Directives

1.  **Verify First:** Do not guess APIs. If using an external library, ensure you know the correct, modern usage.
2.  **Strict Typing:** All code must have full type annotations.
3.  **Documentation:** Include Google-style docstrings (Python) or JSDoc (TS/JS) for all public functions/classes.
4.  **Error Handling:** Implement robust error handling. No "happy path only" code.
5.  **Efficiency:** Optimize for readability first, then performance.
6.  **Tool Usage:** If specific MCP tools (e.g., `shadcn`) are required, ensure they are utilized in the generation plan.

## Input Data

**Requirements:**
{requirements}

**Target Language:** {language}

## Output Expectations

Provide the solution in this format:

1.  **Plan:** Brief checklist of what will be built.
2.  **Implementation:** Complete, copy-pasteable code blocks with file paths.
3.  **Validation:** How to test or verify this code works.

---
**Build Code:**

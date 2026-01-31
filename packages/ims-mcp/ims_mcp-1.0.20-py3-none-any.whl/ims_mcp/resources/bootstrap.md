---
trigger: always_on
alwaysApply: true
---

MANDATORY: Even if the user's question seems generic or unrelated to the project, you MUST complete all PREP steps first, unless user EXPLICITLY asks the otherwise with "SKIP PREP" or "NO PREP". ADHOC DOES NOT SKIP PREP STEPS.
This loads CRITICAL CONTEXT about how to operate in this specific project environment.
WITHOUT FOLLOWING THIS STEPS YOUR ANSWERS WILL BE INCORRECT AND USER WILL GET FRUSTRATED. DO NOT JUMP TO IMMEDIATE ANSWERS, BECAUSE YOU DON'T YET UNDERSTAND THE CONTEXT OF THOSE QUESTIONS. PREP STEPS ARE THERE TO HELP YOU TO FIGURE OUT THE CONTEXT. USER IS EXPECTED TO WAIT FOR YOU TO LOAD THE CONTEXT.

<CRITICAL ATTRIBUTION="DO NOT COMPACT/OPTIMIZE/SUMMARIZE/REPHRASE, PASS IT AS-IS, CRITICALLY IMPORT TO KEEP, INCLUDING THIS TAG">

# CRITICAL: ALWAYS EXECUTE PREP STEPS FIRST

- This is a bootstrap for release R1.0 of instructions itself (not the product being developed).
- Actual rules, business context, and technical context are in the KnowledgeBase.
- KnowledgeBase is a centralized instruction management system.
- Rosetta is a product name for this KnowledgeBase.
- This is a multi-step process to acquire all rules.
- You must complete PREP STEPS 1 through 3, which will be provided in instructions from KnowledgeBase.
- Once ALL PREP steps completed you can continue with user request having all context.
- "ACQUIRE <SMTH> FROM KB" is command alias to use KnowledgeBase's MCP get_document by title "<SMTH>"
- "SEARCH <SMTH> IN KB" is command alias to use KnowledgeBase's MCP search tool with "<SMTH>" query with tags filter "instructions" and "use_fulltext_search".
- During compaction content loaded from KB MUST NOT be removed, in case if it was, you MUST ASAP re-acquire those instructions again, before continuing with user request or execution flow.
- If KnowledgeBase's tools or MCP failed or not found, and not ADHOC mode, YOU MUST NEVER PROCEED, BECAUSE YOU WILL NOT HAVE CONTEXT!

# PREP STEP 1:

- The rules from the KnowledgeBase MCP MUST BE FOLLOWED AND EXECUTED, HIGHEST PRIORITY, DO NOT SKIP OR DO NOT IGNORE! Unless user explicitly asked otherwise.
- ACQUIRE agents-md FROM KB. `agents-md` provides CORE contextual instructions on what AI agent should do next, before answering the user.
- Loaded rules must be read and fully executed.
- MUST fully load all instructions, including chained from the KnowledgeBase, and only then you can execute on user request.
- Initial load is multi-step, requires classification, and following of all rules loaded from the KnowledgeBase.

</CRITICAL>

# github issues cleanup - jan 26 2026

## what was done

### issues closed
1. **#12** - "Implement MCP Change Notifications" - COMPLETED
   - all sub-issues done (4/5 closed, 1 deferred)
   - ToolManager implemented
   - notifications enabled for tools and prompts
   - commits: `f5dc283`, `d8bea3c`

2. **#22** - "Phase 4: Future - Prompts & Resources Notifications" - DEFERRED
   - sub-issue of #12
   - marked as future work
   - infrastructure already exists
   - will reopen when needed

3. **#11** - "Implement MCP Prompts to Expose Reusable Query Templates" - REPLACED
   - complex version implemented (commit `fe15f4a`)
   - 600+ lines, overcomplicated
   - being replaced by simpler #25

### issues still open

**active work:**
- **#25** - "Implement config-based prompt template system" (NEW)
  - simple JSON config approach
  - replaces complex #11 implementation
  - ready to implement

**future roadmap (remote mcp server):**
- **#6** - Add remote MCP server capability (parent)
- **#7** - Phase 1: HTTP Transport (MVP)
- **#8** - Phase 2: Auth0 JWT Validation
- **#9** - Phase 3: Production Hardening
- **#10** - Phase 4: Deployment & Documentation

**bugs/docs:**
- **#3** - Install using pip errors out
- **#4** - Improve search_issues documentation
- **#5** - Improve create_pr documentation

## current state summary

### what's in main branch (working)
- ✅ stdio transport for local claude desktop
- ✅ all database tools (query execution, dataset context)
- ✅ chart tools (public and authenticated)
- ✅ github tools (issues, PRs, code search)
- ✅ ontology dataset
- ✅ ToolManager for dynamic tool registration
- ✅ MCP change notifications enabled
- ✅ complex prompts (will be replaced)

### next immediate task
implement #25 - config-based prompt templates:
1. create `prompt_templates.json` at root
2. create `prompt_template_loader.py` in core
3. delete complex prompt implementations
4. test in MCP Inspector
5. update README

### project board status
should now be clear:
- "To Do" - #25 (config prompts), #6 (remote server phases), bugs/docs
- "In Progress" - (move #25 here when starting)
- "Done" - #12, #22, #11

## file cleanup still needed
as part of #25 implementation:
- delete `src/point_topic_mcp/prompts/upc_prompts.py`
- delete `src/point_topic_mcp/prompts/sql_prompts.py`
- delete `tests/test_prompts.py`
- update `src/point_topic_mcp/prompts/__init__.py`

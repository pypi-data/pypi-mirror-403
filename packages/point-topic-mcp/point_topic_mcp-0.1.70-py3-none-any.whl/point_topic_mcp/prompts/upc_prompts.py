"""MCP prompts for UPC data analysis.

Provides reusable prompts for analyzing UK broadband coverage, take-up, and forecast data.
"""


def answer_upc_client_email_question(emails: str) -> str:
    """Help Point Topic analysts answer client questions about UPC data.
    
    **INTERNAL USE ONLY** - For Point Topic employees responding to client emails.
    
    This prompt helps you investigate client questions about data totals, dataset definitions,
    or confusion about numbers in their deliverables. It provides both analysis and a 
    copy-pasteable email response.
    
    Args:
        emails: The email thread or question from the client
    
    Returns:
        A prompt with context and instructions for investigating and answering the question
    """
    return f"""You are helping a Point Topic analyst respond to a client email about UK broadband data.

**THIS IS INTERNAL USE ONLY** - You're assisting the Point Topic employee, not directly responding to the client.

# CLIENT QUESTION/EMAIL THREAD
{emails}

# YOUR TASK
Investigate the client's question thoroughly, then provide:
1. Your full analysis (SQL queries, findings, exploration)
2. A draft email response ready to copy/paste to the client

# AVAILABLE TOOLS & RESOURCES

1. **Point Topic MCP Server** - Use these tools to query data:
   - `assemble_dataset_context` - Get schema and documentation for datasets (upc, upc_take_up, upc_forecast, tariffs, ontology)
   - `execute_query` - Run SQL queries against Snowflake
   - `get_dataset_status` - Check latest data availability dates
   
2. **GitHub Tools** - Access client deliverables:
   - Client SQL files are in: `UPC_Client/models/client/[client_name]/`
   - Use `read_file` to view their specific queries
   - Use `search_code` to find relevant models

3. **Common Data Gotchas**:
   - **Premises vs Subscribers**: UPC shows *availability* (premises), NOT subscriber counts. Use `upc_take_up` for modeled subscriber estimates
   - **Reported vs Calendar dates**: Check if client expects `reported_at` date (data snapshot) vs `calendar_date` (time series)
   - **LA boundaries**: Local Authority codes may change over time - use latest ONS codes
   - **Operator footprints**: Virgin Media O2, Openreach, CityFibre etc. are *operators* not ISPs
   - **FTTP vs FTTC**: Be clear about technology types - full fiber (FTTP/FTTH) vs fiber-to-cabinet (FTTC/VDSL)
   - **Take-up is modeled**: Not actual subscriber data, but algorithmic distribution of reported ISP totals

# INVESTIGATION STEPS

1. **Understand the question**: What is the client actually asking?
2. **Check their SQL**: Look at their client deliverables to see what they're receiving
3. **Query the data**: Use Point Topic MCP to verify numbers and reproduce their results
4. **Document everything**: Save all SQL queries and results - never make statements without backing them up with actual data

# OUTPUT FORMAT

Structure your response in two clear sections:

## ANALYSIS (For Point Topic Analyst)

Show all your investigation work:
- SQL queries you ran (with full query text)
- Results/counts from those queries
- What you found in their client SQL files
- Any CSVs or data exports that explain the numbers
- Your conclusions about what's happening

Always back up statements with actual SQL and results. Never speculate.

## DRAFT EMAIL RESPONSE (Ready to Copy/Paste)

Provide a complete email response:
- Brief and direct
- Bullet points for key information
- Professional but friendly tone

The email should:
- Answer their question clearly
- Reference specific numbers/data where relevant
- Clarify any confusion (e.g., premises vs subscribers)
- Be helpful and informative

Now investigate and respond to the client's question."""



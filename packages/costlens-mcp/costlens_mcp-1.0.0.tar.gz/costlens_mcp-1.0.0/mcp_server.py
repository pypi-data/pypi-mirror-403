"""CostLens MCP Server - FinOps for BigQuery.

A Model Context Protocol server that provides cost estimation, query optimization,
and safe execution for BigQuery queries.
"""
import asyncio
import sys
import os
import argparse
from typing import Any, Optional
from dataclasses import asdict

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from mcp.server.fastmcp import FastMCP

# Service Imports
from services.sql_parser import parse_sql
from services.cost_calculator import calculator
from services.optimizer import optimizer
from services.bigquery_client import get_bigquery_client, BigQueryClient, DryRunResult

# Global configuration
CONFIG = {
    "project_id": None,
    "location": "US",
    "key_file": None,
    "datasets_filter": [],
    "allow_execute": False,
    "max_cost_usd": 1.0,  # Default $1 limit
}

# Initialize FastMCP Server
mcp = FastMCP("CostLens FinOps")

def get_client():
    """Get configured BigQuery client."""
    return get_bigquery_client(
        project_id=CONFIG["project_id"],
        location=CONFIG["location"],
        key_file=CONFIG["key_file"]
    )


# =============================================================================
# TOOL: estimate_query_cost
# =============================================================================
@mcp.tool()
async def estimate_query_cost(sql: str) -> str:
    """
    Estimate the cost of a BigQuery SQL query before execution.
    Uses BigQuery's native dry-run for precise estimation when connected.
    
    Args:
        sql: The SQL query to analyze.
        
    Returns:
        Cost estimate, bytes scanned, and optimization suggestions.
    """
    try:
        client = get_client()
        
        # 1. Try BigQuery dry-run first (precise)
        if isinstance(client, BigQueryClient):
            dry_run = client.dry_run_query(sql)
            
            if dry_run.is_valid:
                # Get optimizations from our analyzer
                parsed = parse_sql(sql)
                optimizations = optimizer.analyze(parsed, [], sql)
                
                response = f"""
💰 **Precise Cost Estimate** (via BigQuery dry-run)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Bytes to scan: **{dry_run.total_bytes_human}**
💵 Estimated cost: **${dry_run.estimated_cost_usd:.4f}**

🔍 **Optimizations**:
"""
                if not optimizations:
                    response += "✅ No issues found. Query looks optimized."
                else:
                    for opt in optimizations:
                        severity_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}
                        response += f"- {severity_icon.get(opt.severity, '⚪')} [{opt.severity.upper()}] {opt.title}\n"
                        response += f"  {opt.message}\n"
                        if opt.code_suggestion:
                            response += f"  💡 `{opt.code_suggestion}`\n"
                
                return response
            else:
                return f"❌ Query validation failed: {dry_run.error_message}"
        
        # 2. Fallback to static analysis (approximate)
        parsed = parse_sql(sql)
        tables_info = []
        
        for table_data in parsed.tables:
            full_name = table_data["full_name"]
            info = client.get_table_info(full_name)
            if info:
                info.columns_used = parsed.columns_by_table.get(full_name, [])
                tables_info.append(info)
        
        total_bytes = sum(t.size_bytes or 0 for t in tables_info)
        cost_result = calculator.calculate(total_bytes)
        optimizations = optimizer.analyze(parsed, tables_info, sql)
        
        response = f"""
💰 **Approximate Cost Estimate** (simulation mode)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 Estimated bytes: **{cost_result.bytes_human}**
💵 Estimated cost: **${cost_result.cost_usd:.4f}**
🏷️ Tier: **{cost_result.tier.upper()}**

⚠️ _Connect to BigQuery for precise estimation (--project, --key-file)_

🔍 **Optimizations**:
"""
        if not optimizations:
            response += "✅ No issues found."
        else:
            for opt in optimizations:
                response += f"- [{opt.severity.upper()}] {opt.title}: {opt.message}\n"
        
        return response

    except Exception as e:
        return f"❌ Error: {str(e)}"


# =============================================================================
# TOOL: list_tables
# =============================================================================
@mcp.tool()
async def list_tables(dataset: str | None = None) -> str:
    """
    List all tables in BigQuery with size information.
    
    Args:
        dataset: Optional dataset name to filter. If not provided, lists all datasets.
        
    Returns:
        List of tables with sizes and partitioning info.
    """
    try:
        client = get_client()
        
        if not isinstance(client, BigQueryClient):
            return "❌ Connect to BigQuery to list tables. Provide --project and --key-file."
        
        dataset_filter = [dataset] if dataset else CONFIG["datasets_filter"] or None
        tables = client.list_tables(dataset_filter)
        
        if not tables:
            return "📭 No tables found."
        
        response = f"📋 **Tables** ({len(tables)} found)\n"
        response += "━" * 50 + "\n"
        
        # Sort by size descending
        tables_sorted = sorted(tables, key=lambda t: t.get("size_bytes", 0), reverse=True)
        
        for table in tables_sorted:
            if "error" in table:
                response += f"❌ {table['name']}: {table['error']}\n"
            else:
                partition_icon = "📅" if table.get("is_partitioned") else ""
                cluster_icon = "📊" if table.get("is_clustered") else ""
                response += f"• **{table['name']}** — {table['size_human']} {partition_icon}{cluster_icon}\n"
                response += f"  Rows: {table.get('num_rows', 'N/A'):,}\n"
        
        return response
        
    except Exception as e:
        return f"❌ Error listing tables: {str(e)}"


# =============================================================================
# TOOL: describe_table
# =============================================================================
@mcp.tool()
async def describe_table(table_name: str) -> str:
    """
    Get detailed schema and metadata for a BigQuery table.
    
    Args:
        table_name: Table name (dataset.table or project.dataset.table)
        
    Returns:
        Schema, partitioning, clustering, and size information.
    """
    try:
        client = get_client()
        
        if not isinstance(client, BigQueryClient):
            return "❌ Connect to BigQuery to describe tables. Provide --project and --key-file."
        
        info = client.describe_table(table_name)
        
        response = f"""
📋 **{info['full_name']}**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **Size**: {info['size_human']} ({info.get('num_rows', 0):,} rows)
📅 **Created**: {info.get('created', 'N/A')}
🔄 **Modified**: {info.get('modified', 'N/A')}
"""
        
        if info.get('partitioning'):
            response += f"📅 **Partitioned**: {info['partitioning']['type']} on `{info['partitioning']['field']}`\n"
        
        if info.get('clustering'):
            response += f"📊 **Clustered**: {', '.join(info['clustering'])}\n"
        
        response += "\n**Schema**:\n"
        for col in info.get('schema', []):
            mode_icon = "🔑" if col['mode'] == 'REQUIRED' else ""
            response += f"  • `{col['name']}` ({col['type']}) {mode_icon}\n"
        
        return response
        
    except Exception as e:
        return f"❌ Error describing table: {str(e)}"


# =============================================================================
# TOOL: execute_query (COST-GATED)
# =============================================================================
@mcp.tool()
async def execute_query(sql: str, max_cost: float | None = None) -> str:
    """
    Execute a BigQuery SQL query with cost protection.
    
    SAFETY: Query is dry-run first. Execution only proceeds if:
    1. Estimated cost is under the limit (default $1.00)
    2. The --allow-execute flag was provided at server start
    
    Args:
        sql: SQL query to execute
        max_cost: Maximum allowed cost in USD (defaults to server config)
        
    Returns:
        Query results or rejection message if cost exceeded.
    """
    try:
        if not CONFIG["allow_execute"]:
            return """
❌ **Query execution is disabled**

The server was started without the `--allow-execute` flag.
CostLens is in estimation-only mode for safety.

To enable execution, restart with:
```
python mcp_server.py --allow-execute --project YOUR_PROJECT
```
"""
        
        client = get_client()
        
        if not isinstance(client, BigQueryClient):
            return "❌ Connect to BigQuery to execute queries. Provide --project and --key-file."
        
        cost_limit = max_cost or CONFIG["max_cost_usd"]
        
        # Dry-run first
        dry_run = client.dry_run_query(sql)
        
        if not dry_run.is_valid:
            return f"❌ Query validation failed: {dry_run.error_message}"
        
        if dry_run.estimated_cost_usd > cost_limit:
            return f"""
🛑 **Query Blocked - Cost Limit Exceeded**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💵 Estimated cost: **${dry_run.estimated_cost_usd:.4f}**
🚫 Your limit: **${cost_limit:.4f}**
📊 Would scan: **{dry_run.total_bytes_human}**

To proceed, either:
1. Optimize the query to reduce scanned bytes
2. Increase the limit: `execute_query(sql, max_cost={dry_run.estimated_cost_usd + 0.1})`
"""
        
        # Execute with cost gate
        result = client.execute_query(sql, max_cost_usd=cost_limit)
        
        # Format results
        response = f"""
✅ **Query Executed Successfully**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Rows returned: **{result.total_rows}**
💵 Actual cost: **${result.cost_usd:.4f}**

**Results** (first 10 rows):
"""
        
        for i, row in enumerate(result.rows[:10]):
            response += f"{i+1}. {row}\n"
        
        if result.total_rows > 10:
            response += f"\n... and {result.total_rows - 10} more rows"
        
        return response
        
    except ValueError as e:
        return f"🛑 **Blocked**: {str(e)}"
    except Exception as e:
        return f"❌ Error executing query: {str(e)}"


# =============================================================================
# TOOL: get_optimizations (structured)
# =============================================================================
@mcp.tool()
async def get_optimizations(sql: str) -> list[dict[str, Any]]:
    """
    Get structured optimization suggestions for a SQL query.
    Useful for programmatic processing by agents.
    
    Args:
        sql: SQL query to analyze
        
    Returns:
        List of optimization objects with severity, title, message, suggestion.
    """
    try:
        parsed = parse_sql(sql)
        optimizations = optimizer.analyze(parsed, [], sql)
        return [
            {
                "severity": opt.severity,
                "title": opt.title,
                "message": opt.message,
                "code_suggestion": opt.code_suggestion,
                "estimated_savings": opt.estimated_savings,
            }
            for opt in optimizations
        ]
    except Exception as e:
        return [{"error": str(e)}]


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description='CostLens MCP Server - FinOps for BigQuery',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Estimation only (safe mode)
  python mcp_server.py --project my-project --key-file key.json
  
  # With execution enabled
  python mcp_server.py --project my-project --key-file key.json --allow-execute
  
  # With cost limit
  python mcp_server.py --project my-project --allow-execute --max-cost 5.0
"""
    )
    
    parser.add_argument('--project', help='BigQuery project ID', required=False)
    parser.add_argument('--location', help='BigQuery location (default: US)', default='US')
    parser.add_argument('--key-file', help='Service account key file path', required=False)
    parser.add_argument('--dataset', help='Filter to specific dataset(s)', action='append')
    parser.add_argument('--allow-execute', help='Enable query execution', action='store_true')
    parser.add_argument('--max-cost', help='Max cost limit in USD (default: 1.0)', type=float, default=1.0)
    
    args = parser.parse_args()
    
    # Update global config
    CONFIG["project_id"] = args.project or os.environ.get('BIGQUERY_PROJECT')
    CONFIG["location"] = args.location or os.environ.get('BIGQUERY_LOCATION', 'US')
    CONFIG["key_file"] = args.key_file or os.environ.get('BIGQUERY_KEY_FILE')
    CONFIG["datasets_filter"] = args.dataset or []
    CONFIG["allow_execute"] = args.allow_execute
    CONFIG["max_cost_usd"] = args.max_cost
    
    # Env var fallback for datasets
    if not CONFIG["datasets_filter"] and 'BIGQUERY_DATASETS' in os.environ:
        CONFIG["datasets_filter"] = [
            d.strip() for d in os.environ['BIGQUERY_DATASETS'].split(',') if d.strip()
        ]
    
    # Run MCP server
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

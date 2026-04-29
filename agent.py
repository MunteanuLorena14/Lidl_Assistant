from dotenv import load_dotenv
from database import get_all_products, get_database_schema, get_inventory_stats, execute_sql_batch
import os
import re

load_dotenv()

_client = None


def get_llm_client():
    global _client
    if _client is not None:
        return _client

    # Lazy import so that local utilities/tests can run without the dependency.
    from google import genai  # type: ignore

    _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client

def build_system_prompt():
    schema = get_database_schema()
    products = get_all_products()
    stats = get_inventory_stats()

    products_list = "\n".join([
        f"  - ID {p['id']}: {p['nume']} | Category: {p['categorie']} | Price: {p['pret']} RON | Stock: {p['stoc']}"
        for p in products
    ])

    system_prompt = f"""
You are an AI Store Manager for a Lidl retail store in Romania.
You have full access to the store's SQLite inventory database.

DATABASE SCHEMA:
{schema}

CURRENT INVENTORY:
{products_list}

INVENTORY STATS:
- Total products: {stats['total_products']}
- Total inventory value: {stats['total_inventory_value']} RON

YOUR CAPABILITIES:
- Query the database (SELECT)
- Update stock levels (UPDATE)
- Add new products (INSERT)
- Remove products (DELETE)

INSTRUCTIONS:
1. When the user asks you to perform database operations, respond with SQL commands wrapped in ```sql ... ``` blocks.
2. You may return multiple SQL statements (separate blocks OR semicolon-separated inside a block). Assume the runtime executes one statement at a time.
3. After SQL, add a brief human summary.
4. Do NOT add recommendations or planning unless the user explicitly asks for them.
5. If the user asks you to "plan", "recommend", "forecast", "next bulk-buy", etc., you ARE allowed to include a short plan.
6. Keep the human summary concise (1-3 sentences). If a plan is requested, use up to 6 bullets under a "Plan:" heading.

EXAMPLE:
User: "I sold 10 units of Lapte Zuzu today."
You:
```sql
UPDATE produse SET stoc = stoc - 10 WHERE id = 1
```
Stock for Lapte Zuzu 1L updated: 150 → 140 units.
"""
    return system_prompt.strip()


def extract_sql_blocks(text):
    pattern = r"```sql\s*(.*?)\s*```"
    matches = re.findall(pattern, text, re.DOTALL)
    return matches


def split_sql_statements(sql_block: str):
    """
    Split a SQL block into individual statements.

    sqlite3 cursor.execute() accepts only one statement at a time, but LLMs
    often return multiple statements inside a single ```sql``` block.

    This is a minimal splitter that respects quoted strings.
    """
    statements = []
    current = []
    in_single_quote = False
    in_double_quote = False

    i = 0
    while i < len(sql_block):
        ch = sql_block[i]

        if ch == "'" and not in_double_quote:
            # Handle escaped single-quote in SQL strings: ''
            if in_single_quote and i + 1 < len(sql_block) and sql_block[i + 1] == "'":
                current.append("''")
                i += 2
                continue
            in_single_quote = not in_single_quote
            current.append(ch)
            i += 1
            continue

        if ch == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            current.append(ch)
            i += 1
            continue

        if ch == ";" and not in_single_quote and not in_double_quote:
            stmt = "".join(current).strip()
            if stmt:
                statements.append(stmt)
            current = []
            i += 1
            continue

        current.append(ch)
        i += 1

    tail = "".join(current).strip()
    if tail:
        statements.append(tail)

    return statements


def validate_sql(sql):
    sql_upper = sql.upper().strip()

    dangerous = ["DROP TABLE", "DROP DATABASE", "TRUNCATE", "ALTER TABLE"]
    for keyword in dangerous:
        if keyword in sql_upper:
            return False, f"Dangerous operation not allowed: {keyword}"

    if "DELETE" in sql_upper and "WHERE" not in sql_upper:
        return False, "DELETE without WHERE clause is not allowed"

    if sql_upper.startswith("UPDATE") and "WHERE" not in sql_upper:
        return False, "UPDATE without WHERE clause is not allowed"

    return True, "OK"


def execute_agent_sql(sql_blocks):
    results = []

    for sql in sql_blocks:
        statements = split_sql_statements(sql)
        allowed = []
        for statement in statements:
            is_valid, message = validate_sql(statement)
            if not is_valid:
                results.append(f"BLOCKED: {message}\nSQL: {statement}")
            else:
                allowed.append(statement)

        if not allowed:
            continue

        batch_result = execute_sql_batch(allowed)

        if "error" in batch_result:
            results.append(f"ERROR executing SQL batch (rolled back):\nError: {batch_result['error']}")
            continue

        for statement, result in zip(allowed, batch_result["results"]):
            if isinstance(result, dict) and "affected_rows" in result:
                results.append(f"SUCCESS: {result['affected_rows']} row(s) affected.\nSQL: {statement}")
            else:
                results.append(f"QUERY RESULT:\n{result}")

    return "\n\n".join(results)


def clean_response(text):
    text = re.sub(r"```sql\s*.*?\s*```", "", text, flags=re.DOTALL)
    text = re.sub(r"QUERY RESULT:.*?\n", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def user_requested_plan(user_input: str) -> bool:
    keywords = [
        "plan",
        "bulk-buy",
        "bulk buy",
        "recommend",
        "recommand",
        "forecast",
        "next order",
        "next purchase",
        "restock strategy",
        "replenish",
        "partner",
    ]
    lower = user_input.lower()
    return any(k in lower for k in keywords)


def run_agent(user_input):
    system_prompt = build_system_prompt()

    full_prompt = f"{system_prompt}\n\nUser request: {user_input}"

    print("\nAgent is thinking...")

    client = get_llm_client()
    response = client.models.generate_content(
        model="gemma-3-27b-it",
        contents=full_prompt,
    )

    ai_response = response.text

    sql_blocks = extract_sql_blocks(ai_response)

    if sql_blocks:
        sql_results = execute_agent_sql(sql_blocks)

        followup_prompt = f"""
{system_prompt}

User request: {user_input}

SQL executed with results: {sql_results}

Reply using the same INSTRUCTIONS. State exactly what changed. If the user asked for a plan/recommendation, include it (use the "Plan:" bullets format). No greetings.
"""
        client = get_llm_client()
        followup_response = client.models.generate_content(
            model="gemma-3-27b-it",
            contents=followup_prompt,
        )
        final_text = clean_response(followup_response.text)

        if user_requested_plan(user_input) and "plan:" not in final_text.lower():
            # Retry once with a stricter instruction.
            retry_prompt = f"""
{system_prompt}

User request: {user_input}

SQL executed with results: {sql_results}

You MUST include a short plan because the user asked for it.
Format:
1-3 short sentences summary of changes.
Plan:
- (max 6 bullets)
No greetings.
"""
            retry_response = client.models.generate_content(
                model="gemma-3-27b-it",
                contents=retry_prompt,
            )
            retried_text = clean_response(retry_response.text)
            if "plan:" in retried_text.lower():
                return retried_text

            # Fallback to the original model response (without SQL) if it contains a plan.
            fallback_text = clean_response(ai_response)
            if "plan:" in fallback_text.lower():
                return fallback_text

        return final_text

    return clean_response(ai_response)


if __name__ == "__main__":
    print("Testing AI Agent...")
    print("="*50)

    test_input = "I sold 10 units of Lapte Zuzu today. Update the stock and tell me the current inventory value."
    print(f"User: {test_input}")
    print("\nAgent response:")
    print(run_agent(test_input))

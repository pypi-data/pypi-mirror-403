#!/usr/bin/env python3
"""Interactive CLI for AISQL - Natural Language to SQL Generator"""

import os
import sys

# ANSI color codes
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
CYAN = "\033[36m"
WHITE = "\033[37m"
RED = "\033[31m"

DEFAULT_SCHEMA = """Table: customers
- id (int, primary key)
- name (varchar)
- email (varchar)
- created_at (timestamp)

Table: orders
- id (int, primary key)
- customer_id (int, foreign key -> customers.id)
- order_date (date)
- total (decimal)
- status (varchar)

Table: products
- id (int, primary key)
- name (varchar)
- price (decimal)
- category (varchar)

Table: order_items
- id (int, primary key)
- order_id (int, foreign key -> orders.id)
- product_id (int, foreign key -> products.id)
- quantity (int)
- unit_price (decimal)"""


def print_banner():
    print(
        f"""
{CYAN}    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║     █████╗ ██╗███████╗ ██████╗ ██╗                        ║
    ║    ██╔══██╗██║██╔════╝██╔═══██╗██║                        ║
    ║    ███████║██║███████╗██║   ██║██║                        ║
    ║    ██╔══██║██║╚════██║██║▄▄ ██║██║                        ║
    ║    ██║  ██║██║███████║╚██████╔╝███████╗                   ║
    ║    ╚═╝  ╚═╝╚═╝╚══════╝ ╚══▀▀═╝ ╚══════╝                   ║
    ║                                                           ║
    ║    Natural Language to SQL Generator                      ║
    ╚═══════════════════════════════════════════════════════════╝{RESET}
    """
    )


def print_help():
    print(
        f"""
{BOLD}Commands:{RESET}
  {GREEN}/help{RESET}          Show this help message
  {GREEN}/schema{RESET}        Show current schema
  {GREEN}/set schema{RESET}    Set a new schema (multi-line, end with empty line)
  {GREEN}/set key{RESET}       Set OpenAI API key
  {GREEN}/clear{RESET}         Clear screen
  {GREEN}/quit{RESET}          Exit the application

{DIM}Just type your question in natural language to generate SQL!{RESET}

{BOLD}Examples:{RESET}
  {CYAN}> Show me all customers who ordered in the last 30 days{RESET}
  {CYAN}> What are the top 5 products by total sales?{RESET}
  {CYAN}> Find customers who haven't placed any orders{RESET}
"""
    )


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def get_multiline_input(prompt: str) -> str:
    print(f"{BOLD}{prompt}{RESET}")
    print(f"{DIM}(Enter your schema, then press Enter twice to finish){RESET}")
    lines = []
    while True:
        line = input()
        if line == "":
            if lines:
                break
        else:
            lines.append(line)
    return "\n".join(lines)


def print_result(result):
    """Print query result with colors"""
    if result.error:
        print(f"\n{RED}Error: {result.error}{RESET}")
    else:
        print(f"\n{YELLOW}{'=' * 60}{RESET}")
        print(f"{BOLD}SQL Query:{RESET}")
        print(f"{DIM}{'-' * 60}{RESET}")
        print(f"{WHITE}{result.query}{RESET}")
        print(f"{DIM}{'-' * 60}{RESET}")
        print(f"\n{BOLD}Explanation:{RESET} {result.explanation.strip()}")
        valid_color = GREEN if result.is_valid else RED
        valid_text = "Yes" if result.is_valid else "No"
        print(f"{BOLD}Valid:{RESET} {valid_color}{valid_text}{RESET}")
        print(f"{YELLOW}{'=' * 60}{RESET}")


def print_schema(schema: str):
    """Print schema with colors"""
    print(f"\n{BOLD}Current Schema:{RESET}")
    print(f"{DIM}{'-' * 40}{RESET}")
    for line in schema.split("\n"):
        if line.startswith("Table:"):
            print(f"{CYAN}{line}{RESET}")
        else:
            print(line)
    print(f"{DIM}{'-' * 40}{RESET}")


def main():
    print_banner()

    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY", "")

    if not api_key:
        print(f"{YELLOW}OpenAI API key not found in environment.{RESET}")
        api_key = input("Enter your OpenAI API key: ").strip()
        if not api_key:
            print(f"{RED}Error: API key is required.{RESET}")
            sys.exit(1)
        os.environ["OPENAI_API_KEY"] = api_key
        print(f"{GREEN}API key set successfully!{RESET}\n")
    else:
        masked_key = api_key[:7] + "..." + api_key[-4:] if len(api_key) > 11 else "***"
        print(f"{GREEN}Using OPENAI_API_KEY from environment: {masked_key}{RESET}\n")

    schema = DEFAULT_SCHEMA
    generator = None

    print("Current schema loaded (use /schema to view, /set schema to change)")
    print(f"Type {GREEN}/help{RESET} for available commands\n")
    print(f"{DIM}{'-' * 60}{RESET}")

    while True:
        try:
            user_input = input(f"\n{BOLD}>{RESET} ").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() == "/quit" or user_input.lower() == "/exit":
                print(f"{CYAN}Goodbye!{RESET}")
                break

            elif user_input.lower() == "/help":
                print_help()

            elif user_input.lower() == "/schema":
                print_schema(schema)

            elif user_input.lower() == "/set schema":
                schema = get_multiline_input("\nEnter new schema:")
                generator = None  # Reset generator to use new schema
                print(f"\n{GREEN}Schema updated successfully!{RESET}")

            elif user_input.lower() == "/set key":
                new_key = input("Enter new OpenAI API key: ").strip()
                if new_key:
                    os.environ["OPENAI_API_KEY"] = new_key
                    generator = None  # Reset generator
                    print(f"{GREEN}API key updated successfully!{RESET}")
                else:
                    print(f"{YELLOW}API key not changed.{RESET}")

            elif user_input.lower() == "/clear":
                clear_screen()
                print_banner()

            elif user_input.startswith("/"):
                print(f"{RED}Unknown command: {user_input}{RESET}")
                print(f"Type {GREEN}/help{RESET} for available commands")

            else:
                # Generate SQL from natural language
                print(f"\n{DIM}Generating SQL...{RESET}")

                # Lazy load generator
                if generator is None:
                    try:
                        from aisql.lib import SQLGenerator

                        generator = SQLGenerator(schema=schema)
                    except Exception as e:
                        print(f"\n{RED}Error initializing generator: {e}{RESET}")
                        print("Make sure your API key is valid.")
                        continue

                try:
                    result = generator.generate(user_input)
                    print_result(result)

                except Exception as e:
                    print(f"\n{RED}Error generating SQL: {e}{RESET}")

        except KeyboardInterrupt:
            print(f"\n\n{YELLOW}Use /quit to exit{RESET}")
        except EOFError:
            print(f"\n{CYAN}Goodbye!{RESET}")
            break


if __name__ == "__main__":
    main()

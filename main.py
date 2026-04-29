from llm import chat
from database import create_tables, seed_data, search_products
from agent import run_agent

def display_results(results):
    if not results:
        print("\nNo products found.")
        return

    print(f"\n{'='*50}")
    print(f"{'ID':<5} {'Name':<25} {'Category':<15} {'Price':<10} {'Stock'}")
    print(f"{'='*50}")
    for product in results:
        print(f"{product['id']:<5} {product['nume']:<25} {product['categorie']:<15} {product['pret']:<10} {product['stoc']}")
    print(f"{'='*50}\n")

def database_menu():
    while True:
        print("\n--- Database Query ---")
        print("Enter product name or category")
        print("(or 'back' to return to main menu)")

        query = input("\nSearch: ").strip()

        if query.lower() == "back":
            break

        if not query:
            print("Please enter a search term.")
            continue

        results = search_products(query)
        display_results(results)

def assistant_menu():
    print("\n--- AI Assistant ---")
    print("(type 'back' to return to main menu)")

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() == "back":
            break

        if not user_input:
            continue

        print("\nAssistant: ", end="")
        response = chat(user_input)
        print(response)

def agent_menu():
    print("\n--- AI Store Manager ---")
    print("Tell me anything about your store I can update stock, show statistics and more!.")
    print("Examples:")
    print("  'I sold 10 units of Lapte Zuzu today'")
    print("  'Which products have low stock?'")
    print("  'Show me the total inventory value'")
    print("(type 'back' to return to main menu)")

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() == "back":
            break

        if not user_input:
            continue

        response = run_agent(user_input)
        print(f"\nAgent:\n{response}")

def main():
    create_tables()
    seed_data()

    print("\n" + "="*50)
    print("   Welcome to the Lidl Assistant!")
    print("="*50)

    while True:
        print("\n--- MAIN MENU ---")
        print("1. Talk to the assistant")
        print("2. Query the database")
        print("3. AI Store Manager")
        print("4. Exit")

        option = input("\nChoose an option (1-4): ").strip()

        if option == "1":
            assistant_menu()
        elif option == "2":
            database_menu()
        elif option == "3":
            agent_menu()
        elif option == "4":
            print("\nGoodbye!")
            break
        else:
            print("Invalid option. Please choose 1, 2, 3 or 4.")

if __name__ == "__main__":
    main()

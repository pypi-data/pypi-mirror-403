
def print_result(result):
    status = result.status.upper()

    print(f"\nRepoGuard Verdict: {status}\n")
    print("Reason:")
    print(f"  {result.explanation}\n")

    if result.violated_guidelines:
        print("Violated Guidelines:")
        for g in result.violated_guidelines:
            print(f"  - {g.authority} → {g.heading}")


import json
from pathlib import Path

from app.triage import triage_ticket


def main():
    dataset_path = Path("data/dhaba_tickets.json")

    with dataset_path.open(encoding="utf-8") as file:
        dataset = json.load(file)

    tickets = dataset["tickets"]
    results = []

    for ticket in tickets:
        result = triage_ticket(ticket)

        results.append({
            "ticket_id": result.ticket_id,
            "category": result.category.value,
            "severity": result.severity.value,
            "injection": result.prompt_injection_detected,
            "needs_human": result.needs_human,
            "refund_eligible": result.refund.eligible,
            "mode": result.processing_mode,
        })

    headers = [
        ("ticket_id", "TICKET"),
        ("category", "CATEGORY"),
        ("severity", "SEVERITY"),
        ("injection", "INJECTION"),
        ("needs_human", "HUMAN REVIEW"),
        ("refund_eligible", "REFUND"),
    ]

    widths = [12, 20, 10, 11, 14, 9]

    print(f"\nDhaba triage results: {len(results)} tickets\n")
    print(
        " | ".join(label.ljust(width) for (_, label), width in zip(headers, widths))
    )
    print("-" * (sum(widths) + 3 * (len(widths) - 1)))

    for result in results:
        values = [str(result[key]) for key, _ in headers]
        print(
            " | ".join(value.ljust(width) for value, width in zip(values, widths))
        )

    output_path = Path("data/triage_results.json")
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(results, file, indent=2, ensure_ascii=False)

    print(f"\nSaved results to: {output_path}")
    print(f"Tickets processed: {len(results)}")
    print(
        "Prompt-injection flags:",
        sum(result["injection"] for result in results),
    )
    print(
        "Human review required:",
        sum(result["needs_human"] for result in results),
    )
    print(
        "Automatic refund approvals:",
        sum(result["refund_eligible"] for result in results),
    )


if __name__ == "__main__":
    main()

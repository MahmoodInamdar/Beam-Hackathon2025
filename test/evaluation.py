import json
import os
from pathlib import Path
import uuid

# Configuration
EXTRACTED_JSON = "final.json"
AIRTABLE_JSON = "input.json"
OUTPUT_JSON = "evaluation_metricsss.json"
FLOAT_TOLERANCE = 0.01  # Tolerance for float comparisons
EXTRA_PENALTY = 0.01   # Penalty per extra field

def compare_values(val1, val2):
    """Compare two values, with tolerance for floats and string-number conversion."""
    # Handle string vs number (e.g., "54.75" vs 54.75)
    try:
        if isinstance(val1, str) and isinstance(val2, (int, float)):
            val1 = float(val1)
        elif isinstance(val2, str) and isinstance(val1, (int, float)):
            val2 = float(val2)
    except (ValueError, TypeError):
        pass

    if isinstance(val1, float) and isinstance(val2, float):
        return abs(val1 - val2) <= FLOAT_TOLERANCE
    return val1 == val2

def compare_arrays(arr1, arr2):
    """Compare arrays by matching most similar elements."""
    if not arr1 and not arr2:
        return 1.0, []
    if not arr1 or not arr2:
        return 0.0, [{"mismatch": f"Array length: {len(arr1)} vs {len(arr2)}"}]

    mismatches = []
    scores = []
    arr1, arr2 = arr1.copy(), arr2.copy()

    for item1 in arr1:
        best_score, best_mismatch = 0, []
        best_match = None
        for item2 in arr2:
            score, item_mismatches = compare_objects(item1, item2)
            if score > best_score:
                best_score, best_mismatch = score, item_mismatches
                best_match = item2
        if best_match is not None:
            scores.append(best_score)
            if best_score < 1:
                mismatches.append({"item": item1, "mismatches": best_mismatch})
            arr2.remove(best_match)

    len_penalty = min(len(arr1), len(arr2)) / max(len(arr1), len(arr2))
    avg_score = sum(scores) / len(scores) if scores else 0
    final_score = avg_score * len_penalty
    if len(arr1) != len(arr2):
        mismatches.append({"mismatch": f"Array length: {len(arr1)} vs {len(arr2)}"})
    return final_score, mismatches

def compare_objects(obj1, obj2):
    """Recursively compare JSON objects."""
    if not isinstance(obj1, dict) or not isinstance(obj2, dict):
        return (1.0, []) if compare_values(obj1, obj2) else (0.0, [{"mismatch": f"{obj1} != {obj2}"}])

    mismatches = []
    total_fields = 0
    matching_fields = 0

    for key in obj2:
        total_fields += 1
        if key not in obj1:
            mismatches.append({"field": key, "mismatch": "Missing"})
            continue
        val1, val2 = obj1[key], obj2[key]
        if isinstance(val2, dict):
            sub_score, sub_mismatches = compare_objects(val1, val2)
        elif isinstance(val2, list):
            sub_score, sub_mismatches = compare_arrays(val1, val2)
        else:
            sub_score = 1.0 if compare_values(val1, val2) else 0.0
            sub_mismatches = [{"field": key, "mismatch": f"{val1} != {val2}"}] if sub_score == 0 else []
        matching_fields += sub_score
        if sub_mismatches:
            mismatches.append({"field": key, "mismatches": sub_mismatches})

    extra_fields = sum(1 for key in obj1 if key not in obj2)
    for key in obj1:
        if key not in obj2:
            mismatches.append({"field": key, "mismatch": "Extra"})

    score = matching_fields / total_fields if total_fields > 0 else 0
    score *= (1 - EXTRA_PENALTY * extra_fields)
    return score, mismatches

def evaluate_json(extracted_data, airtable_data):
    """Evaluate extracted JSON against ground truth."""
    results = []
    airtable_dict = {item["record_id"]: item for item in airtable_data}

    for extracted_item in extracted_data:
        record_id = extracted_item["record_id"]
        if record_id not in airtable_dict:
            print(f"Warning: No ground truth for record_id: {record_id}")
            continue

        airtable_item = airtable_dict[record_id]
        extracted_output = extracted_item["expected_output"]
        airtable_output = airtable_item["expected_output"]

        # Normalize product/products key
        if "product" in extracted_output and "products" in airtable_output:
            extracted_output["products"] = extracted_output.pop("product")
        elif "products" in extracted_output and "product" in airtable_output:
            extracted_output["product"] = extracted_output.pop("products")

        score, mismatches = compare_objects(extracted_output, airtable_output)
        accuracy = max(0, score * 100)
        results.append({
            "record_id": record_id,
            "Type": extracted_item.get("type", "Unknown"),
            "Accuracy": round(accuracy, 2),
            "Mismatches": mismatches if accuracy < 100 else []
        })

    avg_accuracy = sum(r["Accuracy"] for r in results) / len(results) if results else 0
    return {"Files": results, "Average Accuracy": round(avg_accuracy, 2)}

def main():
    # Verify input files exist
    if not os.path.exists(EXTRACTED_JSON):
        print(f"Error: {EXTRACTED_JSON} not found")
        return
    if not os.path.exists(AIRTABLE_JSON):
        print(f"Error: {AIRTABLE_JSON} not found")
        return

    # Load JSON files
    try:
        with open(EXTRACTED_JSON, 'r', encoding='utf-8') as f:
            extracted_data = json.load(f)
        with open(AIRTABLE_JSON, 'r', encoding='utf-8') as f:
            airtable_data = json.load(f)
    except Exception as e:
        print(f"Error loading JSON files: {e}")
        return

    # Evaluate
    evaluation_results = evaluate_json(extracted_data, airtable_data)

    # Save results
    os.makedirs(os.path.dirname(OUTPUT_JSON) or '.', exist_ok=True)
    try:
        with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
            json.dump(evaluation_results, f, indent=2, ensure_ascii=False)
        print(f"Evaluation metrics saved to {OUTPUT_JSON}")
    except Exception as e:
        print(f"Error saving evaluation metrics: {e}")

if __name__ == "__main__":
    main()
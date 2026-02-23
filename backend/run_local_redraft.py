import os
import json
import sys
from local_llm_client import redraft_json

def main():
    if len(sys.argv) < 2:
        print("Usage: python run_local_redraft.py <session_id_or_json_path> [context_text_path]")
        sys.exit(1)

    input_arg = sys.argv[1]
    
    # Determine if it's a session ID or a direct path
    if os.path.exists(input_arg):
        json_path = input_arg
    else:
        # Assume session ID
        json_path = os.path.join(os.path.dirname(__file__), "uploads", "sessions", f"{input_arg}.json")
        if not os.path.exists(json_path):
            # Try uploads folder directly
            json_path = os.path.join(os.path.dirname(__file__), "uploads", f"{input_arg}")
    
    if not os.path.exists(json_path):
        print(f"Error: JSON file not found at {json_path}")
        sys.exit(1)

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Extract the actual data part (often nested under balance_sheet_data)
    draft_data = data.get("balance_sheet_data") or data
    
    context_text = ""
    if len(sys.argv) > 2 and os.path.exists(sys.argv[2]):
        with open(sys.argv[2], 'r', encoding='utf-8') as f:
            context_text = f.read()
    else:
        # Try to find associated content JSON if input_arg was session_id
        content_path = json_path.replace(".json", "_bs_content.json").replace("sessions/", "")
        if os.path.exists(content_path):
            with open(content_path, 'r', encoding='utf-8') as f:
                content_data = json.load(f)
                context_text = content_data.get("content", "")

    print(f"--- Redrafting Data for {os.path.basename(json_path)} ---")
    redrafted = redraft_json(draft_data, context_text)

    if redrafted:
        output_path = json_path.replace(".json", "_redrafted.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(redrafted, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Redraft Successful! Saved to: {output_path}")
        print("\n--- Redrafted JSON Output ---")
        print(json.dumps(redrafted, indent=2))
    else:
        print("❌ Redraft failed. Check local LLM status and balance sheet content.")

if __name__ == "__main__":
    main()

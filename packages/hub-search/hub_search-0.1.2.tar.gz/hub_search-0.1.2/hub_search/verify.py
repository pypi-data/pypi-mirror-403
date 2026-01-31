import concurrent.futures
from openai import OpenAI
import os
import sys

def verify_mt_plus(api_key, prompt_content="hi"):
    """
    Verifies a single DashScope API key.
    Only returns True if the API call is successful (HTTP 200).
    """
    client = OpenAI(
        api_key=api_key, 
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    try:
        # If this succeeds, the response was 200 OK.
        client.chat.completions.create(
            model="qwen-mt-plus",
            messages=[{'role': 'user', 'content': prompt_content}],
            max_tokens=1,
            timeout=10 # Set a timeout to avoid hanging
        )
        return (api_key, True, "Valid (200 OK)")
    except Exception as e:
        # Any exception (401, 402, 403, 404, 500, network error, etc.) is considered invalid.
        error_msg = str(e).replace("\n", " ") 
        return (api_key, False, f"Invalid: {error_msg}")


def verify_coder(api_key, prompt_content="请编写一个Python函数，返回Hello World"):
    """
    Verifies a single DashScope API key using qwen3-coder-plus model.
    Only returns True if the API call is successful (HTTP 200).
    """
    client = OpenAI(
        api_key=api_key, 
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    try:
        # If this succeeds, the response was 200 OK.
        client.chat.completions.create(
            model="qwen3-coder-plus",
            messages=[
                {'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': prompt_content}
            ],
            max_tokens=1,
            timeout=10
        )
        return (api_key, True, "Valid (200 OK) - Coder")
    except Exception as e:
        error_msg = str(e).replace("\n", " ") 
        return (api_key, False, f"Invalid: {error_msg}")


def run_verify(input_file, output_dir=None, threads=5, prompt_file=None):
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        sys.exit(1)
        
    prompt_content = "hi"
    if prompt_file:
        if not os.path.exists(prompt_file):
            print(f"Error: Prompt file '{prompt_file}' not found.")
            sys.exit(1)
        try:
            with open(prompt_file, "r", encoding="utf-8") as f:
                prompt_content = f.read()
            print(f"Using custom prompt from {prompt_file} ({len(prompt_content)} chars)")
        except Exception as e:
            print(f"Error reading prompt file: {e}")
            sys.exit(1)

    with open(input_file, 'r') as f:
        keys = [line.strip() for line in f if line.strip()]

    print(f"Loaded {len(keys)} keys from {input_file}. Verifying with {threads} threads...")

    valid_mt_keys = []
    valid_coder_keys = []
    
    # Helper function to verify a key with both methods
    def verify_both(key):
        mt_result = verify_mt_plus(key, prompt_content)
        coder_result = verify_coder(key)
        return (key, mt_result, coder_result)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as executor:
        future_to_key = {executor.submit(verify_both, key): key for key in keys}
        
        for i, future in enumerate(concurrent.futures.as_completed(future_to_key)):
            key, mt_result, coder_result = future.result()
            _, mt_valid, mt_msg = mt_result
            _, coder_valid, coder_msg = coder_result
            
            status_parts = []
            if mt_valid:
                valid_mt_keys.append(key)
                status_parts.append("MT✓")
            else:
                status_parts.append("MT✗")
            
            if coder_valid:
                valid_coder_keys.append(key)
                status_parts.append("Coder✓")
            else:
                status_parts.append("Coder✗")
            
            print(f"[{i+1}/{len(keys)}] {key[:10]}... : {' | '.join(status_parts)}")

    print(f"\nVerification complete.")
    print(f"  MT Plus valid: {len(valid_mt_keys)}")
    print(f"  Coder valid: {len(valid_coder_keys)}")
    
    # Determine output paths
    if output_dir:
        mt_output = os.path.join(output_dir, "valid_mt_keys.txt")
        coder_output = os.path.join(output_dir, "valid_coder_keys.txt")
    else:
        mt_output = "valid_mt_keys.txt"
        coder_output = "valid_coder_keys.txt"
    
    if valid_mt_keys:
        with open(mt_output, "w") as f:
            for key in valid_mt_keys:
                f.write(f"{key}\n")
        print(f"MT valid keys saved to: {mt_output}")
    
    if valid_coder_keys:
        with open(coder_output, "w") as f:
            for key in valid_coder_keys:
                f.write(f"{key}\n")
        print(f"Coder valid keys saved to: {coder_output}")
    
    if not valid_mt_keys and not valid_coder_keys:
        print("No valid keys found.")


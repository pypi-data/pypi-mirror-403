import os
import sys
import datetime
import json
import shutil
import time
from hub_search.search import run_search
from hub_search.clean import run_clean
from hub_search.verify import run_verify

def run_task(query, cwd=None, limit=30, threads=5):
    # 1. Setup paths
    base_dir = cwd if cwd else os.getcwd()
    hub_dir = os.path.join(base_dir, ".hub-search")
    current_dir = os.path.join(hub_dir, ".current")
    last_task_file = os.path.join(hub_dir, "last_task.json")
    
    start_time = datetime.datetime.now()
    start_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
    
    # 2. Create .hub-search and .current
    os.makedirs(hub_dir, exist_ok=True)
    
    # If .current exists (e.g., from a failed previous run), clean it up first
    if os.path.exists(current_dir):
        shutil.rmtree(current_dir)
    os.makedirs(current_dir, exist_ok=True)
    
    print(f"[{start_str}] Starting Task...")
    print(f"Working directory: {base_dir}")
    print(f"Task output dir: {current_dir}")
    print("=" * 50)
    
    try:
        # 3. Step 1: Search
        # We enforce enum mode for task as per context of "collecting"
        print("\n>>> Step 1: Searching GitHub...")
        run_search(query, limit=limit, enum=True, output_dir=current_dir)
        
        # 4. Step 2: Clean
        print("\n>>> Step 2: Cleaning results...")
        clean_keys_file = os.path.join(current_dir, "clean_keys.txt")
        run_clean(current_dir, clean_keys_file)
        
        # 5. Step 3: Verify
        print("\n>>> Step 3: Verifying keys...")
        # Check if clean_keys.txt exists and has content
        if os.path.exists(clean_keys_file) and os.path.getsize(clean_keys_file) > 0:
            run_verify(clean_keys_file, output_dir=current_dir, threads=threads)
        else:
            print("Skipping verification: No keys found in cleaning step.")
        
        # 6. Finalize
        end_time = datetime.datetime.now()
        end_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
        duration = (end_time - start_time).total_seconds()
        
        # Timestamp for the final directory name
        timestamp_name = start_time.strftime("%Y-%m-%d_%H:%M:%S")
        final_dir = os.path.join(hub_dir, timestamp_name)
        
        print("\n>>> Finalizing...")
        print(f"Moving results to: {final_dir}")
        shutil.move(current_dir, final_dir)
        
        # 7. Update last_task
        task_info = {
            "start_time": start_str,
            "end_time": end_str,
            "duration_seconds": duration,
            "query": query,
            "output_dir": final_dir
        }
        
        with open(last_task_file, "w", encoding="utf-8") as f:
            json.dump(task_info, f, indent=4)
            
        print("=" * 50)
        print(f"Task Complete in {duration:.2f} seconds.")
        print(f"Status saved to {last_task_file}")

    except Exception as e:
        print(f"\n[!] Task Failed: {e}")
        # Clean up .current if needed or leave it for debug?
        # Requirement says "When task execution finishes", assuming success.
        # But good to leave .current if failed for inspection.
        sys.exit(1)

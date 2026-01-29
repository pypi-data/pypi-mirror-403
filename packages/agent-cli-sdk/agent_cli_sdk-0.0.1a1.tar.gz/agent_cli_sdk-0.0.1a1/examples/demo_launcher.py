import os
import sys
import subprocess
import shutil

def check_env():
    print("\n[System] Detecting available CLI drivers...")
    gemini_path = shutil.which("gemini")
    copilot_path = shutil.which("copilot")
    
    status = {
        "gemini": {"installed": gemini_path is not None, "path": gemini_path},
        "copilot": {"installed": copilot_path is not None, "path": copilot_path},
        "mock": {"installed": True, "path": "Built-in Simulator"}
    }
    return status

def get_functional_demos(startpath):
    tasks_dir = os.path.join(startpath, 'tasks')
    demos = []
    if not os.path.exists(tasks_dir):
        return demos
        
    for f in sorted(os.listdir(tasks_dir)):
        if f.endswith('.py') and not f.startswith('__'):
            demos.append(os.path.join(tasks_dir, f))
    return demos

def main():
    print("========================================")
    print("   Agent CLI SDK - Universal Launcher")
    print("========================================")
    
    env_status = check_env()
    
    # Step 1: Choose Driver
    print("\nSTEP 1: Choose a Driver Engine:")
    drivers = ["gemini", "copilot", "mock"]
    for i, d in enumerate(drivers, 1):
        info = env_status[d]
        icon = "✅" if info["installed"] else "❌"
        status_text = "" if info["installed"] else " (Not installed)"
        print(f"  {i}. {d.upper():<8} {icon}{status_text}")
    
    d_choice = input("\nSelect driver number (1-3): ")
    try:
        driver_type = drivers[int(d_choice) - 1]
    except (ValueError, IndexError):
        print("Invalid choice. Exiting.")
        return

    # Step 2: Choose Demo Task
    script_dir = os.path.dirname(os.path.abspath(__file__))
    all_demo_paths = get_functional_demos(script_dir)
    
    print(f"\nSTEP 2: Choose a Task to run with [{driver_type.upper()}]:")
    for i, path in enumerate(all_demo_paths, 1):
        rel_path = os.path.relpath(path, script_dir)
        print(f"  {i:>2}. {rel_path}")
    
    t_choice = input("\nSelect task number (or 'q' to quit): ")
    if t_choice.lower() == 'q': return
    
    try:
        selected_task = all_demo_paths[int(t_choice) - 1]
        print(f"\n[System] Launching: {os.path.basename(selected_task)} using {driver_type}...\n")
        
        # Setup Environment
        root_dir = os.path.abspath(os.path.join(script_dir, ".."))
        env = os.environ.copy()
        env["PYTHONPATH"] = os.path.join(root_dir, "src") + os.pathsep + env.get("PYTHONPATH", "")
        
        # Pass the driver type as an argument to the demo script
        subprocess.run([sys.executable, selected_task, "--driver", driver_type], env=env)
        
    except (ValueError, IndexError):
        print("Invalid choice.")
    except KeyboardInterrupt:
        print("\nExit.")

if __name__ == "__main__":
    main()

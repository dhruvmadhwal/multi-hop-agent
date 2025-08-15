"""
Main entry point for the Multi-Hop Agent system.

This module provides the main entry point for running the agent from the command line.
"""
import sys
import argparse
from multi_hop_agent.runner import run_agent_on_prompt, batch_run

def main():
    """
    Main entry point for the Multi-Hop Agent system.
    """
    parser = argparse.ArgumentParser(description="Multi-Hop Agent System")
    
    # Define subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Run the agent on all examples in the dataset")
    
    # Single task command
    single_parser = subparsers.add_parser("single", help="Run the agent on a single task")
    single_parser.add_argument("task", help="The task/question to run the agent on")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run the appropriate command
    if args.command == "batch":
        print("Running batch processing...")
        batch_run()
    elif args.command == "single":
        print(f"Running agent on task: {args.task}")
        state = run_agent_on_prompt(args.task)
        print("\n=== Final Answer ===")
        print(state.get("reply", "No answer generated"))
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    # Fix for asyncio nested loops
    import nest_asyncio
    nest_asyncio.apply()
    
    main() 
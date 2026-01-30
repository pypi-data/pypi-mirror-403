
import argparse
import importlib.util
import sys
import os
import asyncio
from pathlib import Path
from ..logging import get_logger

def load_workflow_from_file(path: str):
    file_path = os.path.abspath(path)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Workflow file not found: {file_path}")

    spec = importlib.util.spec_from_file_location("devrpa_user_workflow", file_path)
    if spec is None or spec.loader is None:
         raise RuntimeError(f"Could not load specifications from file: {file_path}")
         
    module = importlib.util.module_from_spec(spec)
    sys.modules["devrpa_user_workflow"] = module
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        raise RuntimeError(f"Error executing workflow file: {e}")

    if not hasattr(module, "workflow"):
        raise RuntimeError("Workflow file must define a `workflow` variable")
    return module.workflow

async def run_workflow_async(wf, args, logger):
    logger.info("Executing workflow (Async)...")
    
    report = await wf.run(
        env_file=args.env_file, 
        config_file=args.config,
        artifacts_dir=args.artifacts_dir,
        resume_run_id=args.resume
    )
    
    # Save Report
    report_path = Path(args.artifacts_dir) / "run_report.json"
    report.save_json(report_path)
    logger.info(f"Run report saved to {report_path}")

    # Summary Table
    print("\n" + "="*80)
    print(f"{'Step Name':<40} | {'Status':<10} | {'Time (s)':<10}")
    print("-" * 80)
    for r in report.step_results:
        status = "✅ PASS" if r.success else "❌ FAIL"
        print(f"{r.name:<40} | {status:<10} | {r.duration:.2f}")
    print("="*80 + "\n")

    return report.success

def main():
    parser = argparse.ArgumentParser(prog="devrpa", description="Developer-first RPA Engine")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    run_parser = subparsers.add_parser("run", help="Run a workflow file")
    run_parser.add_argument("file", help="Path to workflow Python file")
    run_parser.add_argument("--env-file", help="Path to .env file")
    run_parser.add_argument("--config", help="Path to config file (.json/.yaml)")
    run_parser.add_argument("--artifacts-dir", help="Directory for artifacts", default="artifacts")
    run_parser.add_argument("--resume", help="Resume from run_id or 'last'", default=None)
    
    # Serve
    serve_parser = subparsers.add_parser("serve", help="Serve workflow as API")
    serve_parser.add_argument("file", help="Path to workflow Python file")
    serve_parser.add_argument("--port", help="Port to listen on", type=int, default=8000)

    # Create
    create_parser = subparsers.add_parser("create", help="Create a new workflow")
    create_parser.add_argument("--interactive", action="store_true", help="Launch interactive builder")

    # Cache
    cache_parser = subparsers.add_parser("cache", help="Manage cache")
    cache_sub = cache_parser.add_subparsers(dest="subcommand", required=True)
    cache_sub.add_parser("stats", help="Show statistics")
    cache_sub.add_parser("clear", help="Clear all cache")
    
    args = parser.parse_args()
    logger = get_logger()

    if args.command == "run":
        try:
            logger.info("Loading workflow...")
            wf = load_workflow_from_file(args.file)
            
            success = asyncio.run(run_workflow_async(wf, args, logger))

            if success:
                logger.info("Workflow completed successfully")
                sys.exit(0)
            else:
                logger.error("Workflow failed")
                sys.exit(1)
        except Exception as e:
            logger.error(f"Fatal error: {e}")
            sys.exit(1)

    elif args.command == "serve":
        logger.info(f"Serving workflow from {args.file} on port {args.port}...")
        try:
            wf = load_workflow_from_file(args.file)
            wf.serve(port=args.port)
        except Exception as e:
            logger.error(f"Failed to serve: {e}")
            sys.exit(1)

    elif args.command == "create":
        if args.interactive:
            try:
                from .interactive import run_interactive_builder
                run_interactive_builder()
            except ImportError as e:
                logger.error(f"Failed to launch interactive builder: {e}")
                print("Make sure 'textual' is installed: pip install textual")
                sys.exit(1)
        else:
            print("Non-interactive creation not yet implemented. Use --interactive")

    elif args.command == "cache":
        from ..cache import get_cache_backend
        backend = get_cache_backend("file") # CLI manages file cache by default
        
        if args.subcommand == "stats":
            stats = backend.stats()
            print("Cache Stats:")
            print(f"  Items: {stats.get('size')}")
            print(f"  Hits:  {stats.get('hits')}")
            print(f"  Misses:{stats.get('misses')}")
        
        elif args.subcommand == "clear":
            backend.clear()
            print("Cache cleared.")

if __name__ == "__main__":
    main()

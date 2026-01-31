# melage/core/headless.py
import sys
from melage.core.io import load_image_core
# Import dynamic plugin loader if you moved it to utils
from melage.utils.headless_utils import list_available_tools, get_plugin_runner


def run_headless_mode(args):
    """
    Main entry point for headless execution.
    """
    print(f"--- MELAGE Headless: {args.tool} ---")

    # 1. Validation
    if not args.input or not args.output:
        print("Error: Input and Output paths are required.")
        sys.exit(1)

    # 2. Load Data (Using the shared core loader we discussed)
    readIM, info, fmt = load_image_core(args.input)
    if not info[1]:
        print(f"Error loading file: {info[2]}")
        sys.exit(1)

    # 3. Resolve Plugin
    # This logic delegates the "finding" to utils, keeping this file clean
    plugin_func = get_plugin_runner(args.tool)

    if not plugin_func:
        print(f"Error: Could not find runner for tool '{args.tool}'")
        sys.exit(1)

    # 4. Execute
    try:
        # Assuming all plugins now conform to a standard headless signature
        # e.g., run(data, affine, **kwargs)
        result = plugin_func(readIM.image, readIM.get_affine(), args)

        # 5. Save (or delegate saving to a core.io function)
        save_result(result, args.output, readIM.header)

    except Exception as e:
        print(f"CRITICAL FAILURE during processing: {e}")
        sys.exit(1)
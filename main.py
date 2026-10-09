"""
Wealth Advisor Assistant — Multi-Agent System

Entry point that configures logging and launches the orchestrator pipeline.
"""

import argparse
import logging
import sys
from pathlib import Path

from config import LOG_LEVEL, LOG_FORMAT, LOGS_DIR, DATA_DIR
from agents import OrchestratorAgent


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else getattr(logging, LOG_LEVEL, logging.INFO)
    log_file = LOGS_DIR / "execution.log"

    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, mode="a"),
    ]

    logging.basicConfig(level=level, format=LOG_FORMAT, handlers=handlers)
    logging.getLogger().info("Logging initialised — level: %s, file: %s", level, log_file)


def main():
    parser = argparse.ArgumentParser(description="Wealth Advisor Assistant — Multi-Agent System")
    parser.add_argument(
        "--input",
        type=str,
        default=str(DATA_DIR / "sample_client.json"),
        help="Path to the client financial data JSON file",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug-level logging")
    parser.add_argument(
        "--no-human-review",
        action="store_true",
        help="Skip the human-in-the-loop checkpoint",
    )
    args = parser.parse_args()

    if args.no_human_review:
        import config
        config.HUMAN_IN_LOOP_ENABLED = False

    setup_logging(args.verbose)
    logger = logging.getLogger("main")

    input_path = Path(args.input)
    if not input_path.exists():
        logger.error("Input file not found: %s", input_path)
        sys.exit(1)

    logger.info("Starting Wealth Advisor pipeline with input: %s", input_path)

    orchestrator = OrchestratorAgent()
    result = orchestrator.run({"file_path": str(input_path)})

    if result.success:
        report = result.data.get("report")
        output_path = result.data.get("output_path")

        print("\n" + "=" * 60)
        print("  ADVISORY REPORT SUMMARY")
        print("=" * 60)
        print(f"  Client:     {report.client_name} ({report.client_id})")
        print(f"  Risk:       {report.risk_assessment}")
        print(f"  Anomalies:  {len(report.anomalies)}")
        print(f"  Saved to:   {output_path}")
        print()

        if report.recommendations:
            print("  Recommendations:")
            for i, rec in enumerate(report.recommendations, 1):
                print(f"    {i}. {rec}")
            print()

        if report.next_steps:
            print("  Next Steps:")
            for step in report.next_steps:
                print(f"    • {step}")
            print()

        logger.info("Pipeline completed successfully")
    else:
        logger.error("Pipeline failed: %s", result.error)
        sys.exit(1)


if __name__ == "__main__":
    main()

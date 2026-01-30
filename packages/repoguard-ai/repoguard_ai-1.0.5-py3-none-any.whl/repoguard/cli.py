import argparse
import sys

from repoguard.gitdiff import get_diff
from repoguard.format import print_result
from repoguard.run import validate_remote,analyze_remote

EXIT_CODES={
   "OK":0,
   "Warning":10,
   "Violation":20
}

def main():
    parser=argparse.ArgumentParser(prog="repoguard")
    subparser=parser.add_subparsers(dest="command")

    subparser.add_parser("analyze")
    subparser.add_parser("validate")

    args=parser.parse_args()

    if args.command == "analyze":
      try:
          analyze_remote()
          print("RepoGuard analysis complete.")
          sys.exit(0)
      except Exception as e:
        print("RepoGuard analyze error:", e)
        sys.exit(30)

    if args.command=="validate":
        try:
          diff = get_diff()
          if not diff.strip():
            print("No changes detected.")
            sys.exit(0)

          result = validate_remote(diff)

          print_result(result)
          sys.exit(EXIT_CODES.get(result.status, 30))

        except Exception as e:
          print("RepoGuard error:", e)
          sys.exit(30)
    else:
        parser.print_help()
        sys.exit(30)
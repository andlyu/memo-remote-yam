import argparse
from pathlib import Path
from .manager import Settings
from .web import App


def main():
    parser = argparse.ArgumentParser(description="Agent as Policy on Remote YAM")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8797)
    parser.add_argument("--data", type=Path, default=Path("data"))
    parser.add_argument("--api", default=Settings.origin)
    parser.add_argument("--robot-id", default="yam-1")
    parser.add_argument("--model", default="gpt-6-astra")
    parser.add_argument("--agent", choices=("codex", "docker"), default="codex")
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--demo", action="store_true", help="Offline mock station and scripted agent; no network, model or physical robot")
    parser.add_argument("--mock-robot", action="store_true", help="Use the real coding agent with an offline mock station; model usage, no physical robot")
    parser.add_argument("--public-origin", help="Canonical HTTPS origin when serving a public website")
    args = parser.parse_args()
    if args.host not in ("127.0.0.1", "localhost", "::1") and not args.demo:
        if args.agent != "docker" or not args.public_origin or not args.public_origin.startswith("https://"):
            parser.error("Public hosting requires --agent docker and --public-origin https://...; local Codex runs as your user")
    settings = Settings(data=args.data, origin=args.api, robot_id=args.robot_id, model=args.model,
                        agent_mode=args.agent, demo=args.demo, mock_robot=args.mock_robot, codex=args.codex)
    app = App(settings, public_origin=args.public_origin)
    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()

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
    parser.add_argument("--agent", choices=("codex", "docker", "remote"), default="codex")
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--demo", action="store_true", help="Mock station and scripted agent; live public cameras, no model or physical control")
    parser.add_argument("--synthetic-cameras", action="store_true", help="Explicit offline camera fixtures for tests; default cameras are the public API feeds")
    parser.add_argument("--mock-robot", action="store_true", help="Use the real coding agent with an offline mock station; model usage, no physical robot")
    parser.add_argument("--public-origin", help="Canonical HTTPS origin when serving a public website")
    parser.add_argument("--memory-encoder", choices=("semantic", "lexical"), default="semantic",
                        help="Semantic MiniLM retrieval by default; lexical hashing is for explicit offline fixtures")
    parser.add_argument("--worker", action="store_true", help="Serve the authenticated Playground packet worker; no robot session is created")
    parser.add_argument("--service-token-file", type=Path, help="Private file containing the Playground-to-worker authentication token")
    args = parser.parse_args()
    if args.host not in ("127.0.0.1", "localhost", "::1") and not args.demo:
        if args.agent != "docker" or not args.public_origin or not args.public_origin.startswith("https://"):
            parser.error("Public hosting requires --agent docker and --public-origin https://...; local Codex runs as your user")
    settings = Settings(data=args.data, origin=args.api, robot_id=args.robot_id, model=args.model,
                        agent_mode=args.agent, demo=args.demo, mock_robot=args.mock_robot, codex=args.codex,
                        camera_source="synthetic" if args.synthetic_cameras else "api", memory_encoder=args.memory_encoder)
    if args.worker:
        if not args.service_token_file:
            parser.error("--worker requires --service-token-file")
        from .service import WorkerApp
        app = WorkerApp(settings, args.service_token_file.read_text().strip())
    else:
        app = App(settings, public_origin=args.public_origin)
    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()

import sys

from hypergolic.analytics import save_crash_log
from hypergolic.app import App
from hypergolic.lifespan import HypergolicLifespan
from hypergolic.session_context import build_session_context


def main():
    try:
        session_context = build_session_context()

        with HypergolicLifespan(session_context):
            App(session_context).run()
    except KeyboardInterrupt:
        # Normal exit via Ctrl+C, don't log as crash
        sys.exit(0)
    except Exception:
        # Log the crash (but don't let logging failures mask the original error)
        try:
            save_crash_log(*sys.exc_info())
        except Exception:
            pass  # Silently ignore logging failures

        raise


if __name__ == "__main__":
    main()

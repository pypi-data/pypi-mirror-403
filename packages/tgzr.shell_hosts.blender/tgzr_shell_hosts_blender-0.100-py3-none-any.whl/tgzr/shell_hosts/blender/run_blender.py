if __name__ == "__main__":
    from .app import blender
    from tgzr.shell.session import get_default_session

    session = get_default_session(ensure_set=True)
    blender.run_app(session=session, version=None)

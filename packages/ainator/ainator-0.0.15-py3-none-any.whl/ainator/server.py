from .configuration import configuration

agent_os = configuration.agent_os()

# This returns a FastAPI app
app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app="ainator.server:app", reload=True)

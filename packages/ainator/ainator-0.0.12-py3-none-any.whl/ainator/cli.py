# hide warnings from CLI
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=Warning)
warnings.filterwarnings("ignore", category=UserWarning)

import cli2
from pathlib import Path
import os
import sys

from ainator.configuration import configuration
from ainator.renderer import StreamingMarkdownPrinter

from agno.db.base import SessionType


class Group(cli2.Group):
    def help(self, *args, short=False, **kwargs):
        if short:
            return super().help(short=short)

        print(cli2.t.o.b('AINATOR CONFIGURATION'))
        print(cli2.t.y.b(configuration.path_config))
        cli2.print(dict(configuration))

        return super().help(*args, **kwargs)


class ClosingDbCommand(cli2.Command):
    async def post_call(self):
        cli2.log.debug('closing db')
        await configuration.db.close()
        cli2.log.info('closed db')


cli = Group(__doc__, cmdclass=ClosingDbCommand)


@cli.cmd(color='yellow')
def chat():
    """ Interactive chat in terminal """
    configuration.agent().cli_app(stream=True)


class AgentRunner:
    def __init__(self):
        self.configuration = configuration

    async def run_agent(self, agent, *prompt, **kwargs):
        prompt = self.prompt_assemble(*prompt)

        response_stream = agent.arun(
            prompt,
            stream=True,
            stream_events=True,
            stream_intermediate_steps=True,
            **kwargs,
        )

        printer = StreamingMarkdownPrinter()
        async for event in response_stream:
            await self.handle_event(event, printer)

        session_id = kwargs.get('session_id', agent.session_id)
        session = await agent.aget_or_create_session_name(session_id)
        print(
            cli2.t.o.b('SESSION:'),
            session.session_data.get('session_name', session_id),
        )
        with self.configuration:
            self.configuration['session_id'] = session_id
            self.configuration['session_name'] = session.session_data.get(
                'session_name',
                'Un-named',
            )

    async def handle_event(self, event, printer):
        if event.event == "ToolCallStarted":
            if event.tool.tool_name == 'think':
                return  # handled by ReasoningStep
            cli2.print(dict( event=event.event,
                tool_name=event.tool.tool_name,
                tool_args=event.tool.tool_args,
            ))
            print(cli2.t.reset)
            # we also have all these attributes
            # tool_call_error=None, result=None, metrics=None, child_run_id=None, stop_after_tool_call=False, created_at=1768818745, requires_confirmation=None, confirmed=None, confirmation_note=None, requires_user_input=None, user_input_schema=None, answered=None, external_execution_required=None)
        elif event.event == "ToolCallCompleted":
            if event.tool.tool_name == 'think':
                return # handled by ReasoningStep
            cli2.print(
                dict(
                    event=event.event,
                    tool_name=event.tool.tool_name,
                    tool_args=event.tool.tool_args,
                    duration=event.tool.metrics.duration,
                ),
                f'result:\n{event.tool.result}',
            )
            print(cli2.t.reset)
        elif event.event == "ReasoningStep":
            printer.add_reasoning(event.content.title)
            print()
            printer.add_reasoning(event.content.reasoning)
            printer.add_reasoning(event.content.action)
            printer.add_reasoning(event.content.result)
            print()
            print()
        elif event.event == 'RunContent':
            printer.add_content(event.content)

    def prompt_assemble(self, *prompt):
        if prompt:
            prompt = ' '.join(prompt)
        else:
            print(cli2.t.o.b('Waiting for prompt in stdin ...'))
            prompt = sys.stdin.read()
            print(cli2.t.o.b('STDIN RECEIVED PROMPT:'))
            print(prompt)
            print(cli2.t.o.b('END STDIN RECEIVED PROMPT'))
        return prompt


@cli.cmd(color='yellow')
async def hi(*prompt):
    """
    Create a new session with a given prompt

    Ie.:

        ainator hi fix the error in foo.py

    To add a new message in the same session, use the but command:

        artinator but also add a test
    """
    await AgentRunner().run_agent(configuration.agent(), *prompt)


@cli.cmd(color='yellow')
async def but(*prompt):
    """
    Prompt in the current session
    """
    await AgentRunner().run_agent(
        configuration.agent(),
        *prompt,
        session_id=configuration.get('session_id', None),
    )


@cli.cmd(color='yellow')
async def fix(*command):
    """
    Run a command, and iterate to fix it until it exits with 0 return code.

    :param command: Shell command to iterate on.
    """
    agent = configuration.agent()
    agent.instructions.append(
        'You are running in a loop where you are fed with the'
        ' output of this command: {" ".join(proc.args)}.'
        ' Use the file tools to edit that code until the commnand exits'
        ' succesfully, fix any reported problem'
    )

    rc = 1
    while rc != 0:
        proc = cli2.Proc(*command)
        await proc.wait()
        await AgentRunner().run_agent(
            agent,
            proc.out,
            session_id=configuration.get('session_id', None),
        )
        rc = proc.rc


@cli.cmd(color='green')
async def sessions():
    """ List saved sessions """
    from datetime import datetime
    sessions = configuration.db.get_sessions(session_type=SessionType.AGENT)
    for session in await sessions:
        dt = datetime.fromtimestamp(session.created_at)
        iso_string = dt.isoformat()
        name = session.session_data.get('session_name', 'Unamed (web, chat)')
        print(session.session_id, iso_string, name)


@cli.cmd
async def switch(session_id=None):
    """
    Change context by switching to another session.

    If session_id is omitted, then current context switches to a new, empty
    session.

    :param session_id: A session uuid to switch to a given session
    """
    with configuration:
        if session_id:
            configuration['session_id'] = session_id
        else:
            del configuration['session_id']


@cli.cmd(color='green')
async def show(session_id=None):
    """
    Show messages in session
    """
    session_id = session_id or configuration.get('session_id', None)
    if not session_id:
        return 'No session to show, start prompting and call me again'

    session = await configuration.db.get_session(
        session_id,
        session_type=SessionType.AGENT,
        deserialize=True,
    )
    messages = session.get_messages()
    for message in messages:
        if message.role == 'system':
            continue
        if message.tool_calls:
            continue
        cli2.print(cli2.t.g(message.role.upper()))
        print(cli2.highlight(message.content, 'Markdown'))


class RagGroup(cli2.Group):
    """ Local RAG management """

    def help(self, *args, short=False, **kwargs):
        if short:
            return super().help(short=short)

        print(cli2.t.o.b('AINATOR RAGs'))
        print(cli2.t.y.b(configuration.path_config))
        cli2.print(dict(configuration['knowledge']))

        self.load_entrypoints(args)
        return super().help(*args, **kwargs)

    def load_entrypoints(self, argv):
        from importlib.metadata import entry_points
        eps = entry_points(group="ainator.knowledge")
        if argv and argv[0] != 'help':
            eps = eps.select(name=argv[0])

        for ep in eps:
            cls = ep.load()
            self.group(ep.name, doc=cls.__doc__).load(cls(configuration))

    def __call__(self, *argv):
        self.load_entrypoints(argv)
        return super().__call__(*argv)

rag = cli.group('rag', grpclass=RagGroup)


@rag.cmd(color='yellow')
async def search(name, string):
    """ Search for a string in knowledge base """
    return await configuration.knowledges[name].async_search(string)


@rag.cmd(color='red')
async def delete(name):
    """ Remove a knowledge base """
    with configuration:
        del configuration['knowledge'][name]


@rag.cmd
async def update(*names):
    """
    Update knowledge bases

    :param names: Names of the knowledge base to update, if not provided then
                  all are updated
    """
    configurations = {
        name: cfg
        for name, cfg in configuration['knowledge'].items()
        if not names or name in names
    }

    from importlib.metadata import entry_points, EntryPoint
    eps = {ep.name: ep for ep in entry_points(group="ainator.knowledge")}

    tasks = []
    for name, knowledge_configuration in configurations.items():
        plugin_name = knowledge_configuration.pop('plugin')
        plugin = eps[plugin_name].load()(configuration)
        tasks.append(plugin.add(**knowledge_configuration))

    await cli2.Queue().run(*tasks)


@cli.cmd(color='green')
async def server():
    """
    Run AgentOS server

    It's the backend for: https://github.com/agno-agi/agent-ui
    """
    agent_os = configuration.agent_os()
    agent_os.serve(app="ainator.server:app", reload=True)


@cli.cmd(color='green')
def skills():
    """
    List skills discovered from ./.ainator/skills and skills configuration.
    """
    for skill in configuration.skills.get_all_skills():
        print(cli2.t.o(skill.source_path))
        print(cli2.t.m(skill.description))

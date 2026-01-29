import click
from click import Group
from litestar.plugins import CLIPlugin

from core.cli import coro
from core.database import session_maker
from core.mail import MailClient
from core.settings import settings
from core.storage import provide_storage

from .loaders import AuthLoader
from .services import (
    provide_auth_service,
    provide_permission_service,
    provide_role_service,
    provide_user_service,
)


class AuthPlugin(CLIPlugin):
    def on_cli_init(self, cli: Group) -> None:
        @cli.group(help="Manage auth, load data with ``load`` command")
        @click.version_option(prog_name="auth")
        def auth(): ...

        @auth.command(help="load auth data")
        @coro
        async def load():
            async with session_maker() as session:
                click.echo("Loading auth data... ")
                loader = AuthLoader(
                    user_service=await provide_user_service(session),
                    role_service=await provide_role_service(session),
                    permission_service=await provide_permission_service(session),
                )

                await loader.clear()
                await loader.load()

        @auth.command(help="load auth data")
        @coro
        async def clear():
            async with session_maker() as session:
                user_service = await provide_user_service(session)
                await user_service.delete_where()
                click.echo("Clear auth data")

        @auth.command(help="Send test mail")
        @click.argument("recipient")
        def send_mail(recipient):
            mail_controller = MailClient(settings.mail_config)
            mail_controller.send([recipient], "test", "test")

        @auth.command(help="Set user password")
        @coro
        @click.argument("email")
        @click.argument("password")
        async def set_user_password(email, password):
            async with session_maker() as session:
                mail_controller = MailClient(settings.mail_config)
                async for auth_service in provide_auth_service(
                    db_session=session,
                    mail_client=mail_controller,
                    storage=await provide_storage(),
                    user_service=await provide_user_service(session),
                ):
                    await auth_service.set_user_password(email, password)

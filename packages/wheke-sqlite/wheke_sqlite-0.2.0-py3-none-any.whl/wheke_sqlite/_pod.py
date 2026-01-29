from wheke import Pod, ServiceConfig

from ._cli import cli
from ._service import DatabaseService, database_service_factory

database_pod = Pod(
    "database",
    services=[
        ServiceConfig(
            DatabaseService,
            database_service_factory,
            is_singleton=True,
            singleton_cleanup_method="dispose",
        ),
    ],
    cli=cli,
)

from manage_django_project.management.commands.run_dev_server import Command as RunServerCommand


class Command(RunServerCommand):
    default_addr = '0.0.0.0'  # Change "127.0.0.1", so it's useable by other devices on the network

    def execute(self, *args, **options):
        if not options['addrport']:
            options['addrport'] = f'{self.default_addr}:{self.default_port}'
        super().execute(*args, **options)

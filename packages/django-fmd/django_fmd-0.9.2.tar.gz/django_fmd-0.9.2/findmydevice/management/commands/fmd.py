from getpass import getpass

from manage_django_project.management.base import BaseManageCommand
from rich.panel import Panel

from findmydevice.client.client import FmdClient
from findmydevice.client.data_classes import ClientDeviceData


class Command(BaseManageCommand):
    help = 'Find My Device - Client CLI'

    def add_arguments(self, parser):
        parser.add_argument(
            '--server',
            default='http://localhost:8000',
            help='FMD server url',
        )
        parser.add_argument(
            '--ssl-verify',
            action='store_true',
            help='Verify SSL certificates?',
        )

        parser.add_argument(
            '--device-id',
            default=None,
            help='The device ID',
        )
        parser.add_argument(
            '--get-location',
            action='store_true',
            help='Fetch and display last device location (Needs ID and Password)',
        )

    def handle(self, *args, **options):
        connection_kwargs = dict(
            fmd_server_url=options['server'],
            ssl_verify=options['ssl_verify'],
        )
        self.console.print(f'Connect with: {connection_kwargs}')
        fmd_client = FmdClient(**connection_kwargs)

        version = fmd_client.get_version()
        self.console.print(Panel(f'Server version: [bold]{version}'))

        plaintext_password = getpass(prompt='Device Password: ')

        client_device_data = ClientDeviceData(
            plaintext_password=plaintext_password,
            short_id=options.get('device_id'),
        )

        location_data_size = fmd_client.get_location_data_size(client_device_data=client_device_data)
        location_count = location_data_size.length + 1
        self.console.print(Panel(f'location count: [bold]{location_count}'))

        if options['get_location']:
            location = fmd_client.get_location(client_device_data=client_device_data)
            self.console.print(Panel(f'location: [bold]{location}'))

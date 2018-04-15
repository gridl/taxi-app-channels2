from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from nose.tools import assert_true
import pytest

from example_taxi.routing import application


@database_sync_to_async
def create_user(
    *,
    username='rider@example.com',
    password='pAssw0rd!',
    group='rider'
):
    # Create user.
    user = get_user_model().objects.create_user(
        username=username,
        password=password
    )

    # Create user group.
    user_group, _ = Group.objects.get_or_create(name=group)
    user.groups.add(user_group)
    user.save()
    return user


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestWebsockets:

    async def test_authorized_user_can_connect(self):
        # Force authentication to get session ID.
        client = Client()
        user = await create_user()
        client.force_login(user=user)

        # Pass session ID in headers to authenticate.
        communicator = WebsocketCommunicator(
            application=application,
            path='/taxi/',
            headers=[(
                b'cookie',
                f'sessionid={client.cookies["sessionid"].value}'.encode('ascii')
            )]
        )
        connected, _ = await communicator.connect()
        assert_true(connected)
        return communicator

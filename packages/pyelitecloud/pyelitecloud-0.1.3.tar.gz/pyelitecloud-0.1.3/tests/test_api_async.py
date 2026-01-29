import asyncio
import copy
from datetime import datetime
import logging
import pytest
import pytest_asyncio

from src.pyelitecloud import (
    AsyncEliteCloudApi,
    EliteCloudApi,
    EliteCloudApiFlag,
    EliteCloudSite,
    EliteCloudError,
    EliteCloudAuthError,
    EliteCloudConnectError,
    EliteCloudDataError,
    LoginMethod,
)

from . import TEST_USERNAME, TEST_PASSWORD

_LOGGER = logging.getLogger(__name__)

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


class TestContext:
    def __init__(self):
        self.api = None

    async def cleanup(self):
        if self.api:
            await self.api.logout()
            await self.api.close()
            assert self.api.closed == True


@pytest_asyncio.fixture
async def context():
    # Prepare
    ctx = TestContext()

    # pass objects to tests
    yield ctx

    # cleanup
    await ctx.cleanup()


@pytest.mark.asyncio
@pytest.mark.usefixtures("context")
@pytest.mark.parametrize(
    "name, method, usr, pwd, exp_except",
    [
        ("ok",   'Any',        TEST_USERNAME, TEST_PASSWORD, None),
        ("ok",   'Auth-Api',   TEST_USERNAME, TEST_PASSWORD, None),
        ("fail", 'Any',        "dummy_usr",   "wrong_pwd",   EliteCloudConnectError),
        ("fail", 'Auth-Api',   "dummy_usr",   "wrong_pwd",   EliteCloudConnectError),
    ]
)
async def test_login(name, method, usr, pwd, exp_except, request):
    context = request.getfixturevalue("context")
    assert context.api is None

    context.api = AsyncEliteCloudApi(usr, pwd)
    assert context.api.closed == False

    if exp_except is None:
        assert context.api._login_method is None
        assert context.api._user_uuid is None

        match method:
            case 'Any':      await context.api.login()
            case 'Auth-Api': await context.api._login_auth_api()

        assert context.api._login_method is not None
        assert context.api._access_token is not None
        assert context.api._access_exp_ts > 0
        assert context.api._device_token is not None
        assert context.api._device_exp_ts > 0

        assert context.api._user_uuid is not None
        assert context.api._device_uuid is not None
        assert context.api._device_id is not None

    else:
        with pytest.raises(exp_except):
            match method:
                case 'Any':         await context.api.login()
                case 'Auth-Api':    await context.api._login_auth_api()


@pytest.mark.asyncio
@pytest.mark.usefixtures("context")
@pytest.mark.parametrize(
    "name, usr, pwd, exp_except",
    [
        ("login multi", TEST_USERNAME, TEST_PASSWORD, None),
    ]
)
async def test_login_seq(name, usr, pwd, exp_except, request):
    context = request.getfixturevalue("context")
    assert context.api is None

    # First call with wrong pwd
    context.api = AsyncEliteCloudApi(usr, "wrong_pwd")
    assert context.api.closed == False
    assert context.api._login_method is None

    with pytest.raises(EliteCloudConnectError):
        await context.api.login()

    # Next call with correct pwd
    context.api = AsyncEliteCloudApi(usr, pwd)
    assert context.api.closed == False
    assert context.api._login_method is None

    if exp_except is None:
        await context.api.login()

        assert context.api._login_method is not None

    else:
        with pytest.raises(exp_except):
            await context.api.login()


@pytest.mark.asyncio
@pytest.mark.usefixtures("context")
@pytest.mark.parametrize(
    "name, method, loop, exp_except",
    [
        ("ok",  'Auto',               0, None),
        ("ok",  LoginMethod.AUTH_API, 0, None),
        #("24h", "Auto",               24*60, None),    # Run 1 full day
        #("24h", LoginMethod.AUTH_API, 24*60, None),    # Run 1 full day
    ]
)
async def test_fetch_status(name, method, loop, exp_except, request):
    context = request.getfixturevalue("context")
    context.api = AsyncEliteCloudApi(TEST_USERNAME, TEST_PASSWORD)
    assert context.api.closed == False

    # Login
    match method:
        case 'Auto':                 await context.api.login()
        case LoginMethod.AUTH_API:   await context.api._login_auth_api()

    login_method_org = context.api._login_method

    # Get profile
    sites = await context.api.fetch_sites()

    assert sites is not None
    assert type(sites) is list
    assert len(sites) > 0

    # Get resources and status for each site
    for site in sites:
        site_uuid = site.get('uuid')
        assert site_uuid is not None

        resources = await context.api.fetch_site_resources(site_uuid)

        assert resources is not None
        assert type(resources) is dict
        assert len(resources) > 0
        assert 'area' in resources
        assert 'input' in resources
        assert 'output' in resources
        
        status = await context.api.fetch_site_status(site_uuid)

        assert status is not None
        assert type(status) is dict
        assert len(status) > 0
        assert 'area' in status
        assert 'input' in status
        assert 'output' in status

    counter_success: int = 0
    counter_fail: int = 0
    reason_fail: dict[str,int] = {}
    for idx in range(0,loop+1):
        # Get fresh site statuses
        try:
            # Check access-token and refresh or re-login if needed
            await context.api.login()
            assert login_method_org == context.api._login_method

            # Get all sites
            sites = await context.api.fetch_sites()

            assert sites is not None
            assert type(sites) is list
            assert len(sites) > 0
                
            # Get status for a site
            status = await context.api.fetch_site_status(site_uuid)

            assert status is not None
            assert type(status) is dict
            assert len(status) > 0

            counter_success += 1
        
        except Exception as ex:
            counter_fail += 1
            reason = str(ex)
            reason_fail[reason] = reason_fail[reason]+1 if reason in reason_fail else 1
            _LOGGER.warning(f"Fail: {ex}")

        if loop:
            # Simulate failure to recover from
            #if idx % 6 == 0:
            #    await context.api._async_logout("simulate failure")
            #elif idx % 3 == 0:
            #    await context.api._async_logout("login force refresh", EliteCloudLogin.ACCESS_TOKEN)

            if method != "Auto":
                context.api._login_method = method

            _LOGGER.debug(f"Loop test, {idx} of {loop} (success={counter_success}, fail={counter_fail})")
            await asyncio.sleep(60)

    _LOGGER.info(f"Fail summary after {loop} loops:")
    for reason,count in reason_fail.items():
        _LOGGER.info(f"  {count}x {reason}")

    assert counter_fail == 0


@pytest.mark.asyncio
@pytest.mark.usefixtures("context")
@pytest.mark.parametrize(
    "name, method, loop, exp_except",
    [
        ("ok",  'Auto',               0, None),
        ("ok",  LoginMethod.AUTH_API, 0, None),
        #("24h", "Auto",               24*60, None),    # Run 1 full day
        #("24h", LoginMethod.AUTH_API, 24*60, None),    # Run 1 full day
    ]
)
async def test_subscribe_status(name, method, loop, exp_except, request):
    context = request.getfixturevalue("context")
    flags = {
        EliteCloudApiFlag.RESPONSE_DIVERT: True     # Also pass overal status messages as individual updates
    }
    context.api = AsyncEliteCloudApi(TEST_USERNAME, TEST_PASSWORD, flags=flags)
    assert context.api.closed == False

    # Login
    match method:
        case 'Auto':                 await context.api.login()
        case LoginMethod.AUTH_API:   await context.api._login_auth_api()

    login_method_org = context.api._login_method

    # Get profile
    sites = await context.api.fetch_sites()

    assert sites is not None
    assert type(sites) is list
    assert len(sites) > 0

    # Declare counters to track callbacks received
    counters_sites = {}
    counters_sections = {}

    # Define inline callback function
    async def on_status(site: EliteCloudSite, section:str, id:str, status: dict):
        if site.uuid in counters_sites:
            counters_sites[site.uuid] += 1
        else:
            counters_sites[site.uuid] = 1

        if section in counters_sections:
            counters_sections[section] += 1
        else:
            counters_sections[section] = 1

    # Subscribe to status updates for each site
    for site in sites:
        site_uuid = site.get('uuid')
        assert site_uuid is not None

        await context.api.subscribe_site_status(site_uuid, on_status)

    # Wait a moment for statusses to come in
    await asyncio.sleep(2)

    # Check that status updates were received
    for site in sites:
        site_uuid = site.get('uuid')

        assert site_uuid in counters_sites
        assert counters_sites[site_uuid] > 0

        for section in ["status", "area", "input", "output", "tamper", "system"]:
            assert section in counters_sections
            assert counters_sections[section] >= len(sites)


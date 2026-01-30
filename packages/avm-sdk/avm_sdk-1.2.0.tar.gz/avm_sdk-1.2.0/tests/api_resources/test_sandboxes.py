# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import httpx
import pytest
from respx import MockRouter

from sandbox_sdk import SandboxSDK, AsyncSandboxSDK
from tests.utils import assert_matches_type
from sandbox_sdk.types import (
    SandboxListResponse,
    SandboxCreateResponse,
    SandboxDeleteResponse,
    SandboxUploadResponse,
    SandboxExecuteResponse,
    SandboxDeleteAllResponse,
)
from sandbox_sdk._response import (
    BinaryAPIResponse,
    AsyncBinaryAPIResponse,
    StreamedBinaryAPIResponse,
    AsyncStreamedBinaryAPIResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestSandboxes:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: SandboxSDK) -> None:
        sandbox = client.sandboxes.create()
        assert_matches_type(SandboxCreateResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: SandboxSDK) -> None:
        sandbox = client.sandboxes.create(
            env_vars={"foo": "string"},
            image="avmcodes/avm-default-sandbox",
            name="my-project",
            resources={
                "cpus": 1,
                "memory": 512,
                "storage": 10,
            },
            wait_for_ready=True,
        )
        assert_matches_type(SandboxCreateResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: SandboxSDK) -> None:
        response = client.sandboxes.with_raw_response.create()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sandbox = response.parse()
        assert_matches_type(SandboxCreateResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: SandboxSDK) -> None:
        with client.sandboxes.with_streaming_response.create() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sandbox = response.parse()
            assert_matches_type(SandboxCreateResponse, sandbox, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: SandboxSDK) -> None:
        sandbox = client.sandboxes.list()
        assert_matches_type(SandboxListResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: SandboxSDK) -> None:
        sandbox = client.sandboxes.list(
            page=1,
            page_size=20,
        )
        assert_matches_type(SandboxListResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: SandboxSDK) -> None:
        response = client.sandboxes.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sandbox = response.parse()
        assert_matches_type(SandboxListResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: SandboxSDK) -> None:
        with client.sandboxes.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sandbox = response.parse()
            assert_matches_type(SandboxListResponse, sandbox, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: SandboxSDK) -> None:
        sandbox = client.sandboxes.delete(
            id="id",
        )
        assert_matches_type(SandboxDeleteResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete_with_all_params(self, client: SandboxSDK) -> None:
        sandbox = client.sandboxes.delete(
            id="id",
            create_snapshot=True,
            keep_storage=False,
            snapshot_name="final-backup",
        )
        assert_matches_type(SandboxDeleteResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: SandboxSDK) -> None:
        response = client.sandboxes.with_raw_response.delete(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sandbox = response.parse()
        assert_matches_type(SandboxDeleteResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: SandboxSDK) -> None:
        with client.sandboxes.with_streaming_response.delete(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sandbox = response.parse()
            assert_matches_type(SandboxDeleteResponse, sandbox, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: SandboxSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.sandboxes.with_raw_response.delete(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete_all(self, client: SandboxSDK) -> None:
        sandbox = client.sandboxes.delete_all()
        assert_matches_type(SandboxDeleteAllResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete_all(self, client: SandboxSDK) -> None:
        response = client.sandboxes.with_raw_response.delete_all()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sandbox = response.parse()
        assert_matches_type(SandboxDeleteAllResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete_all(self, client: SandboxSDK) -> None:
        with client.sandboxes.with_streaming_response.delete_all() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sandbox = response.parse()
            assert_matches_type(SandboxDeleteAllResponse, sandbox, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_method_download(self, client: SandboxSDK, respx_mock: MockRouter) -> None:
        respx_mock.get("/v1/sandboxes/id/download").mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        sandbox = client.sandboxes.download(
            id="id",
            path="path",
        )
        assert sandbox.is_closed
        assert sandbox.json() == {"foo": "bar"}
        assert cast(Any, sandbox.is_closed) is True
        assert isinstance(sandbox, BinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_raw_response_download(self, client: SandboxSDK, respx_mock: MockRouter) -> None:
        respx_mock.get("/v1/sandboxes/id/download").mock(return_value=httpx.Response(200, json={"foo": "bar"}))

        sandbox = client.sandboxes.with_raw_response.download(
            id="id",
            path="path",
        )

        assert sandbox.is_closed is True
        assert sandbox.http_request.headers.get("X-Stainless-Lang") == "python"
        assert sandbox.json() == {"foo": "bar"}
        assert isinstance(sandbox, BinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_streaming_response_download(self, client: SandboxSDK, respx_mock: MockRouter) -> None:
        respx_mock.get("/v1/sandboxes/id/download").mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        with client.sandboxes.with_streaming_response.download(
            id="id",
            path="path",
        ) as sandbox:
            assert not sandbox.is_closed
            assert sandbox.http_request.headers.get("X-Stainless-Lang") == "python"

            assert sandbox.json() == {"foo": "bar"}
            assert cast(Any, sandbox.is_closed) is True
            assert isinstance(sandbox, StreamedBinaryAPIResponse)

        assert cast(Any, sandbox.is_closed) is True

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    def test_path_params_download(self, client: SandboxSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.sandboxes.with_raw_response.download(
                id="",
                path="path",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_execute(self, client: SandboxSDK) -> None:
        sandbox = client.sandboxes.execute(
            id="id",
            command="python -c \"print('Hello, World!')\"",
        )
        assert_matches_type(SandboxExecuteResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_execute_with_all_params(self, client: SandboxSDK) -> None:
        sandbox = client.sandboxes.execute(
            id="id",
            command="python -c \"print('Hello, World!')\"",
            env={"foo": "string"},
            api_timeout=5,
            working_dir="working_dir",
        )
        assert_matches_type(SandboxExecuteResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_execute(self, client: SandboxSDK) -> None:
        response = client.sandboxes.with_raw_response.execute(
            id="id",
            command="python -c \"print('Hello, World!')\"",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sandbox = response.parse()
        assert_matches_type(SandboxExecuteResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_execute(self, client: SandboxSDK) -> None:
        with client.sandboxes.with_streaming_response.execute(
            id="id",
            command="python -c \"print('Hello, World!')\"",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sandbox = response.parse()
            assert_matches_type(SandboxExecuteResponse, sandbox, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_execute(self, client: SandboxSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.sandboxes.with_raw_response.execute(
                id="",
                command="python -c \"print('Hello, World!')\"",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_upload(self, client: SandboxSDK) -> None:
        sandbox = client.sandboxes.upload(
            id="id",
            path="path",
        )
        assert_matches_type(SandboxUploadResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_upload_with_all_params(self, client: SandboxSDK) -> None:
        sandbox = client.sandboxes.upload(
            id="id",
            path="path",
            file={},
        )
        assert_matches_type(SandboxUploadResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_upload(self, client: SandboxSDK) -> None:
        response = client.sandboxes.with_raw_response.upload(
            id="id",
            path="path",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sandbox = response.parse()
        assert_matches_type(SandboxUploadResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_upload(self, client: SandboxSDK) -> None:
        with client.sandboxes.with_streaming_response.upload(
            id="id",
            path="path",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sandbox = response.parse()
            assert_matches_type(SandboxUploadResponse, sandbox, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_upload(self, client: SandboxSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            client.sandboxes.with_raw_response.upload(
                id="",
                path="path",
            )


class TestAsyncSandboxes:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncSandboxSDK) -> None:
        sandbox = await async_client.sandboxes.create()
        assert_matches_type(SandboxCreateResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncSandboxSDK) -> None:
        sandbox = await async_client.sandboxes.create(
            env_vars={"foo": "string"},
            image="avmcodes/avm-default-sandbox",
            name="my-project",
            resources={
                "cpus": 1,
                "memory": 512,
                "storage": 10,
            },
            wait_for_ready=True,
        )
        assert_matches_type(SandboxCreateResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncSandboxSDK) -> None:
        response = await async_client.sandboxes.with_raw_response.create()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sandbox = await response.parse()
        assert_matches_type(SandboxCreateResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncSandboxSDK) -> None:
        async with async_client.sandboxes.with_streaming_response.create() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sandbox = await response.parse()
            assert_matches_type(SandboxCreateResponse, sandbox, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncSandboxSDK) -> None:
        sandbox = await async_client.sandboxes.list()
        assert_matches_type(SandboxListResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncSandboxSDK) -> None:
        sandbox = await async_client.sandboxes.list(
            page=1,
            page_size=20,
        )
        assert_matches_type(SandboxListResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncSandboxSDK) -> None:
        response = await async_client.sandboxes.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sandbox = await response.parse()
        assert_matches_type(SandboxListResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncSandboxSDK) -> None:
        async with async_client.sandboxes.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sandbox = await response.parse()
            assert_matches_type(SandboxListResponse, sandbox, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncSandboxSDK) -> None:
        sandbox = await async_client.sandboxes.delete(
            id="id",
        )
        assert_matches_type(SandboxDeleteResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete_with_all_params(self, async_client: AsyncSandboxSDK) -> None:
        sandbox = await async_client.sandboxes.delete(
            id="id",
            create_snapshot=True,
            keep_storage=False,
            snapshot_name="final-backup",
        )
        assert_matches_type(SandboxDeleteResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncSandboxSDK) -> None:
        response = await async_client.sandboxes.with_raw_response.delete(
            id="id",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sandbox = await response.parse()
        assert_matches_type(SandboxDeleteResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncSandboxSDK) -> None:
        async with async_client.sandboxes.with_streaming_response.delete(
            id="id",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sandbox = await response.parse()
            assert_matches_type(SandboxDeleteResponse, sandbox, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncSandboxSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.sandboxes.with_raw_response.delete(
                id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete_all(self, async_client: AsyncSandboxSDK) -> None:
        sandbox = await async_client.sandboxes.delete_all()
        assert_matches_type(SandboxDeleteAllResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete_all(self, async_client: AsyncSandboxSDK) -> None:
        response = await async_client.sandboxes.with_raw_response.delete_all()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sandbox = await response.parse()
        assert_matches_type(SandboxDeleteAllResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete_all(self, async_client: AsyncSandboxSDK) -> None:
        async with async_client.sandboxes.with_streaming_response.delete_all() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sandbox = await response.parse()
            assert_matches_type(SandboxDeleteAllResponse, sandbox, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_method_download(self, async_client: AsyncSandboxSDK, respx_mock: MockRouter) -> None:
        respx_mock.get("/v1/sandboxes/id/download").mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        sandbox = await async_client.sandboxes.download(
            id="id",
            path="path",
        )
        assert sandbox.is_closed
        assert await sandbox.json() == {"foo": "bar"}
        assert cast(Any, sandbox.is_closed) is True
        assert isinstance(sandbox, AsyncBinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_raw_response_download(self, async_client: AsyncSandboxSDK, respx_mock: MockRouter) -> None:
        respx_mock.get("/v1/sandboxes/id/download").mock(return_value=httpx.Response(200, json={"foo": "bar"}))

        sandbox = await async_client.sandboxes.with_raw_response.download(
            id="id",
            path="path",
        )

        assert sandbox.is_closed is True
        assert sandbox.http_request.headers.get("X-Stainless-Lang") == "python"
        assert await sandbox.json() == {"foo": "bar"}
        assert isinstance(sandbox, AsyncBinaryAPIResponse)

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_streaming_response_download(self, async_client: AsyncSandboxSDK, respx_mock: MockRouter) -> None:
        respx_mock.get("/v1/sandboxes/id/download").mock(return_value=httpx.Response(200, json={"foo": "bar"}))
        async with async_client.sandboxes.with_streaming_response.download(
            id="id",
            path="path",
        ) as sandbox:
            assert not sandbox.is_closed
            assert sandbox.http_request.headers.get("X-Stainless-Lang") == "python"

            assert await sandbox.json() == {"foo": "bar"}
            assert cast(Any, sandbox.is_closed) is True
            assert isinstance(sandbox, AsyncStreamedBinaryAPIResponse)

        assert cast(Any, sandbox.is_closed) is True

    @parametrize
    @pytest.mark.respx(base_url=base_url)
    async def test_path_params_download(self, async_client: AsyncSandboxSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.sandboxes.with_raw_response.download(
                id="",
                path="path",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_execute(self, async_client: AsyncSandboxSDK) -> None:
        sandbox = await async_client.sandboxes.execute(
            id="id",
            command="python -c \"print('Hello, World!')\"",
        )
        assert_matches_type(SandboxExecuteResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_execute_with_all_params(self, async_client: AsyncSandboxSDK) -> None:
        sandbox = await async_client.sandboxes.execute(
            id="id",
            command="python -c \"print('Hello, World!')\"",
            env={"foo": "string"},
            api_timeout=5,
            working_dir="working_dir",
        )
        assert_matches_type(SandboxExecuteResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_execute(self, async_client: AsyncSandboxSDK) -> None:
        response = await async_client.sandboxes.with_raw_response.execute(
            id="id",
            command="python -c \"print('Hello, World!')\"",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sandbox = await response.parse()
        assert_matches_type(SandboxExecuteResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_execute(self, async_client: AsyncSandboxSDK) -> None:
        async with async_client.sandboxes.with_streaming_response.execute(
            id="id",
            command="python -c \"print('Hello, World!')\"",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sandbox = await response.parse()
            assert_matches_type(SandboxExecuteResponse, sandbox, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_execute(self, async_client: AsyncSandboxSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.sandboxes.with_raw_response.execute(
                id="",
                command="python -c \"print('Hello, World!')\"",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_upload(self, async_client: AsyncSandboxSDK) -> None:
        sandbox = await async_client.sandboxes.upload(
            id="id",
            path="path",
        )
        assert_matches_type(SandboxUploadResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_upload_with_all_params(self, async_client: AsyncSandboxSDK) -> None:
        sandbox = await async_client.sandboxes.upload(
            id="id",
            path="path",
            file={},
        )
        assert_matches_type(SandboxUploadResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_upload(self, async_client: AsyncSandboxSDK) -> None:
        response = await async_client.sandboxes.with_raw_response.upload(
            id="id",
            path="path",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sandbox = await response.parse()
        assert_matches_type(SandboxUploadResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_upload(self, async_client: AsyncSandboxSDK) -> None:
        async with async_client.sandboxes.with_streaming_response.upload(
            id="id",
            path="path",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sandbox = await response.parse()
            assert_matches_type(SandboxUploadResponse, sandbox, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_upload(self, async_client: AsyncSandboxSDK) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `id` but received ''"):
            await async_client.sandboxes.with_raw_response.upload(
                id="",
                path="path",
            )

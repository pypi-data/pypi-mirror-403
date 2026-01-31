from __future__ import annotations

import base64
import contextlib
import io
import uuid
from typing import Any, Callable, Iterable, Optional

import httpx


class EdgeMLClientError(RuntimeError):
    pass


class _ApiClient:
    def __init__(self, api_key: str, api_base: str, timeout: float = 20.0):
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}"}

    def get(self, path: str, params: Optional[dict[str, Any]] = None) -> Any:
        with httpx.Client(timeout=self.timeout) as client:
            res = client.get(f"{self.api_base}{path}", params=params, headers=self._headers())
        if res.status_code >= 400:
            raise EdgeMLClientError(res.text)
        return res.json()

    def post(self, path: str, payload: dict[str, Any]) -> Any:
        with httpx.Client(timeout=self.timeout) as client:
            res = client.post(f"{self.api_base}{path}", json=payload, headers=self._headers())
        if res.status_code >= 400:
            raise EdgeMLClientError(res.text)
        return res.json()

    def get_bytes(self, path: str, params: Optional[dict[str, Any]] = None) -> bytes:
        with httpx.Client(timeout=self.timeout) as client:
            res = client.get(f"{self.api_base}{path}", params=params, headers=self._headers())
        if res.status_code >= 400:
            raise EdgeMLClientError(res.text)
        return res.content


class Federation:
    def __init__(
        self,
        api_key: str,
        name: str | None = None,
        org_id: str = "default",
        api_base: str = "https://api.edgeml.io/api/v1",
    ):
        self.api = _ApiClient(api_key=api_key, api_base=api_base)
        self.org_id = org_id
        self.name = name or "default"
        self.last_model_id: Optional[str] = None
        self.last_version: Optional[str] = None
        self.federation_id = self._resolve_or_create_federation()

    def _resolve_or_create_federation(self) -> str:
        existing = self.api.get(
            "/federations",
            params={"org_id": self.org_id, "name": self.name},
        )
        if existing:
            return existing[0]["id"]
        created = self.api.post(
            "/federations",
            {"org_id": self.org_id, "name": self.name},
        )
        return created["id"]

    def invite(self, org_ids: Iterable[str]) -> list[dict[str, Any]]:
        payload = {"org_ids": list(org_ids)}
        return self.api.post(f"/federations/{self.federation_id}/invite", payload)

    def _resolve_model_id(self, model: str) -> str:
        # Try name lookup first; if not found, assume it's an ID
        data = self.api.get("/models", params={"org_id": self.org_id})
        for item in data.get("models", []):
            if item.get("name") == model:
                return item["id"]
        return model

    def train(
        self,
        model: str,
        algorithm: str = "fedavg",
        rounds: int = 1,
        min_updates: int = 1,
        base_version: Optional[str] = None,
        new_version: Optional[str] = None,
        publish: bool = True,
        strategy: str = "metrics",
        update_format: str = "delta",
        architecture: Optional[str] = None,
        input_dim: int = 16,
        hidden_dim: int = 8,
        output_dim: int = 4,
    ) -> dict[str, Any]:
        if algorithm.lower() != "fedavg":
            raise EdgeMLClientError(f"Unsupported algorithm: {algorithm}")

        model_id = self._resolve_model_id(model)
        self.last_model_id = model_id
        result: Optional[dict[str, Any]] = None
        current_base = base_version

        for _ in range(rounds):
            payload = {
                "model_id": model_id,
                "base_version": current_base,
                "new_version": new_version,
                "min_updates": min_updates,
                "publish": publish,
                "strategy": strategy,
                "update_format": update_format,
                "architecture": architecture,
                "input_dim": input_dim,
                "hidden_dim": hidden_dim,
                "output_dim": output_dim,
            }
            result = self.api.post("/training/aggregate", payload)
            current_base = result.get("new_version")
            self.last_version = current_base
            new_version = None

        return result or {}

    def deploy(
        self,
        model_id: Optional[str] = None,
        version: Optional[str] = None,
        rollout_percentage: int = 10,
        target_percentage: int = 100,
        increment_step: int = 10,
        start_immediately: bool = True,
    ) -> dict[str, Any]:
        model_id = model_id or self.last_model_id
        if not model_id:
            raise EdgeMLClientError("model_id is required for deploy()")

        if not version:
            if self.last_version:
                version = self.last_version
            else:
                latest = self.api.get(f"/models/{model_id}/versions/latest")
                version = latest.get("version")
        if not version:
            raise EdgeMLClientError("version is required for deploy()")

        payload = {
            "version": version,
            "rollout_percentage": rollout_percentage,
            "target_percentage": target_percentage,
            "increment_step": increment_step,
            "start_immediately": start_immediately,
        }
        return self.api.post(f"/models/{model_id}/rollouts", payload)


class FederatedClient:
    def __init__(
        self,
        api_key: str,
        org_id: str = "default",
        api_base: str = "https://api.edgeml.io/api/v1",
        device_identifier: Optional[str] = None,
        platform: str = "python",
    ):
        self.api = _ApiClient(api_key=api_key, api_base=api_base)
        self.org_id = org_id
        self.device_identifier = device_identifier or f"client-{uuid.uuid4().hex[:10]}"
        self.platform = platform
        self.device_id: Optional[str] = None

    def register(self) -> str:
        if self.device_id:
            return self.device_id
        payload = {
            "device_identifier": self.device_identifier,
            "org_id": self.org_id,
            "platform": self.platform,
            "os_version": "macos",
            "sdk_version": "0.1.0",
            "app_version": "0.1.0",
            "metadata": {"client": "python-sdk"},
            "capabilities": {"training": True},
        }
        response = self.api.post("/devices/register", payload)
        self.device_id = response.get("id")
        if not self.device_id:
            raise EdgeMLClientError("Device registration failed: missing device ID")
        return self.device_id

    def join_federation(self, federation_name: str) -> dict[str, Any]:
        self.register()
        existing = self.api.get("/federations", params={"name": federation_name})
        if existing:
            federation_id = existing[0]["id"]
        else:
            created = self.api.post(
                "/federations",
                {"org_id": self.org_id, "name": federation_name},
            )
            federation_id = created["id"]
        return self.api.post(
            f"/federations/{federation_id}/join",
            {"org_id": self.org_id},
        )

    def train(
        self,
        model: str,
        local_data: Any,
        rounds: int = 1,
        version: Optional[str] = None,
        sample_count: int = 0,
        metrics: Optional[dict[str, float]] = None,
        update_format: str = "delta",
    ) -> list[dict[str, Any]]:
        self.register()
        results = []

        model_id = self._resolve_model_id(model)
        if not version:
            latest = self.api.get(f"/models/{model_id}/versions/latest")
            version = latest.get("version")
        if not version:
            raise EdgeMLClientError("Failed to resolve model version")

        for _ in range(rounds):
            if callable(local_data):
                weights_data, sample_count, metrics = local_data()
            else:
                weights_data = local_data

            weights_data = self._serialize_weights(weights_data)

            weights_b64 = base64.b64encode(weights_data).decode("ascii")
            payload = {
                "model_id": model_id,
                "version": version,
                "device_id": self.device_id,
                "sample_count": sample_count or 0,
                "metrics": metrics or {},
                "update_format": update_format,
                "weights_data": weights_b64,
            }
            results.append(self.api.post("/training/weights", payload))

        return results

    def pull_model(
        self,
        model: str,
        version: Optional[str] = None,
        format: str = "pytorch",
    ) -> bytes:
        model_id = self._resolve_model_id(model)
        if not version:
            latest = self.api.get(f"/models/{model_id}/versions/latest")
            version = latest.get("version")
        if not version:
            raise EdgeMLClientError("Failed to resolve model version")
        return self.api.get_bytes(
            f"/models/{model_id}/versions/{version}/download",
            params={"format": format},
        )

    def train_from_remote(
        self,
        model: str,
        local_train_fn: Any,
        rounds: int = 1,
        version: Optional[str] = None,
        update_format: str = "weights",
        format: str = "pytorch",
    ) -> list[dict[str, Any]]:
        self.register()
        model_id = self._resolve_model_id(model)
        if not version:
            latest = self.api.get(f"/models/{model_id}/versions/latest")
            version = latest.get("version")
        if not version:
            raise EdgeMLClientError("Failed to resolve model version")

        results = []
        for _ in range(rounds):
            base_bytes = self.pull_model(model_id, version=version, format=format)
            base_state = self._deserialize_weights(base_bytes)
            updated_state, sample_count, metrics = local_train_fn(base_state)
            if update_format == "delta":
                updated_state = compute_state_dict_delta(base_state, updated_state)
            weights_data = self._serialize_weights(updated_state)
            payload = {
                "model_id": model_id,
                "version": version,
                "device_id": self.device_id,
                "sample_count": sample_count or 0,
                "metrics": metrics or {},
                "update_format": update_format,
                "weights_data": base64.b64encode(weights_data).decode("ascii"),
            }
            results.append(self.api.post("/training/weights", payload))
        return results

    def _resolve_model_id(self, model: str) -> str:
        data = self.api.get("/models", params={"org_id": self.org_id})
        for item in data.get("models", []):
            if item.get("name") == model:
                return item["id"]
        return model

    def _serialize_weights(self, weights: Any) -> bytes:
        if isinstance(weights, (bytes, bytearray)):
            return bytes(weights)

        try:
            import torch  # type: ignore
        except Exception:
            torch = None

        if torch is not None:
            if isinstance(weights, torch.nn.Module):
                import io
                buffer = io.BytesIO()
                torch.save(weights.state_dict(), buffer)
                return buffer.getvalue()
            if isinstance(weights, dict):
                import io
                buffer = io.BytesIO()
                torch.save(weights, buffer)
                return buffer.getvalue()

        raise EdgeMLClientError(
            "local_data must be bytes, a torch.nn.Module, a state_dict dict, "
            "or a callable returning (weights, sample_count, metrics)"
        )

    def _deserialize_weights(self, payload: bytes) -> dict:
        try:
            import torch  # type: ignore
        except Exception as exc:
            raise EdgeMLClientError("torch is required to load remote weights") from exc
        buffer = io.BytesIO(payload)
        state = torch.load(buffer, map_location="cpu")
        if not isinstance(state, dict):
            raise EdgeMLClientError("Remote payload was not a state_dict")
        return state


def compute_state_dict_delta(base_state: dict, updated_state: dict) -> dict:
    """
    Compute a delta state_dict = updated - base.

    Intended for small demo models (fits in memory).
    """
    try:
        import torch  # type: ignore
    except Exception as exc:
        raise EdgeMLClientError("torch is required to compute state_dict deltas") from exc

    delta: dict = {}
    for key, base_tensor in base_state.items():
        updated_tensor = updated_state.get(key)
        if updated_tensor is None:
            continue
        if torch.is_tensor(base_tensor) and torch.is_tensor(updated_tensor):
            delta[key] = updated_tensor.detach().cpu() - base_tensor.detach().cpu()
    return delta

    def deploy(
        self,
        model_id: str,
        version: Optional[str] = None,
        rollout_percentage: int = 10,
        target_percentage: int = 100,
        increment_step: int = 10,
        start_immediately: bool = True,
    ) -> dict[str, Any]:
        if not version:
            latest = self.api.get(f"/models/{model_id}/versions/latest")
            version = latest.get("version")
        if not version:
            raise EdgeMLClientError("Failed to resolve model version")

        payload = {
            "version": version,
            "rollout_percentage": rollout_percentage,
            "target_percentage": target_percentage,
            "increment_step": increment_step,
            "start_immediately": start_immediately,
        }
        return self.api.post(f"/models/{model_id}/rollouts", payload)


class ModelRegistry:
    def __init__(
        self,
        api_key: str,
        org_id: str = "default",
        api_base: str = "https://api.edgeml.io/api/v1",
        timeout: float = 60.0,
    ):
        self.api = _ApiClient(api_key=api_key, api_base=api_base, timeout=timeout)
        self.org_id = org_id

    def resolve_model_id(self, model: str) -> str:
        data = self.api.get("/models", params={"org_id": self.org_id})
        for item in data.get("models", []):
            if item.get("name") == model:
                return item["id"]
        return model

    def ensure_model(
        self,
        name: str,
        framework: str,
        use_case: str,
        description: str | None = None,
    ) -> dict[str, Any]:
        data = self.api.get("/models", params={"org_id": self.org_id})
        for item in data.get("models", []):
            if item.get("name") == name:
                return item
        payload = {
            "name": name,
            "description": description or "",
            "framework": framework,
            "use_case": use_case,
            "org_id": self.org_id,
        }
        return self.api.post("/models", payload)

    def upload_version_from_path(
        self,
        model_id: str,
        file_path: str,
        version: str,
        description: str | None = None,
        formats: str | None = None,
        onnx_data_path: str | None = None,
        architecture: str | None = None,
        input_dim: int | None = None,
        hidden_dim: int | None = None,
        output_dim: int | None = None,
    ) -> dict[str, Any]:
        data: dict[str, Any] = {"version": version}
        if description:
            data["description"] = description
        if formats:
            data["formats"] = formats
        if architecture:
            data["architecture"] = architecture
        if input_dim is not None:
            data["input_dim"] = str(input_dim)
        if hidden_dim is not None:
            data["hidden_dim"] = str(hidden_dim)
        if output_dim is not None:
            data["output_dim"] = str(output_dim)

        with contextlib.ExitStack() as stack:
            files: dict[str, Any] = {"file": stack.enter_context(open(file_path, "rb"))}
            if onnx_data_path:
                files["onnx_data"] = stack.enter_context(open(onnx_data_path, "rb"))
            with httpx.Client(timeout=self.api.timeout) as client:
                res = client.post(
                    f"{self.api.api_base}/models/{model_id}/versions/upload",
                    data=data,
                    files=files,
                    headers=self.api._headers(),
                )
        if res.status_code >= 400:
            raise EdgeMLClientError(res.text)
        return res.json()

    def publish_version(self, model_id: str, version: str) -> dict[str, Any]:
        return self.api.post(f"/models/{model_id}/versions/{version}/publish", {})

    def create_rollout(
        self,
        model_id: str,
        version: str,
        rollout_percentage: int = 10,
        target_percentage: int = 100,
        increment_step: int = 10,
        start_immediately: bool = True,
    ) -> dict[str, Any]:
        payload = {
            "version": version,
            "rollout_percentage": rollout_percentage,
            "target_percentage": target_percentage,
            "increment_step": increment_step,
            "start_immediately": start_immediately,
        }
        return self.api.post(f"/models/{model_id}/rollouts", payload)

"""Container object."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import Field

from ocsf._base import OCSFBaseModel

if TYPE_CHECKING:
    from ocsf.v1_2_0.objects.fingerprint import Fingerprint
    from ocsf.v1_2_0.objects.image import Image


class Container(OCSFBaseModel):
    """The Container object describes an instance of a specific container. A container is a prepackaged, portable system image that runs isolated on an existing system using a container runtime like containerd.

    See: https://schema.ocsf.io/1.2.0/objects/container
    """

    hash: Fingerprint | None = Field(
        default=None,
        description="Commit hash of image created for docker or the SHA256 hash of the container. For example: <code>13550340a8681c84c861aac2e5b440161c2b33a3e4f302ac680ca5b686de48de</code>. [Recommended]",
    )
    image: Image | None = Field(
        default=None,
        description="The container image used as a template to run the container. [Recommended]",
    )
    name: str | None = Field(default=None, description="The container name. [Recommended]")
    network_driver: str | None = Field(
        default=None,
        description="The network driver used by the container. For example, bridge, overlay, host, none, etc.",
    )
    orchestrator: str | None = Field(
        default=None,
        description="The orchestrator managing the container, such as ECS, EKS, K8s, or OpenShift.",
    )
    pod_uuid: Any | None = Field(
        default=None,
        description="The unique identifier of the pod (or equivalent) that the container is executing on.",
    )
    runtime: str | None = Field(
        default=None, description="The backend running the container, such as containerd or cri-o."
    )
    size: int | None = Field(
        default=None, description="The size of the container image. [Recommended]"
    )
    tag: str | None = Field(
        default=None,
        description="The tag used by the container. It can indicate version, format, OS.",
    )
    uid: str | None = Field(
        default=None,
        description="The full container unique identifier for this instantiation of the container. For example: <code>ac2ea168264a08f9aaca0dfc82ff3551418dfd22d02b713142a6843caa2f61bf</code>. [Recommended]",
    )

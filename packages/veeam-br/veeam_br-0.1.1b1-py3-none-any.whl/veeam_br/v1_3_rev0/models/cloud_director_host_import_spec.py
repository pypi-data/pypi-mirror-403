from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.e_managed_server_type import EManagedServerType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.cloud_director_vi_host_import_spec import CloudDirectorViHostImportSpec
    from ..models.credentials_import_model import CredentialsImportModel


T = TypeVar("T", bound="CloudDirectorHostImportSpec")


@_attrs_define
class CloudDirectorHostImportSpec:
    """Import settings for VMware Cloud Director server.

    Attributes:
        name (str): Full DNS name or IP address of the server.
        description (str): Description of the server.
        type_ (EManagedServerType): Type of the server.
        credentials (CredentialsImportModel): Credentials used for connection.
        certificate_thumbprint (Union[Unset, str]): Certificate thumbprint used to verify the server identity.
        url (Union[Unset, str]): URL of the VMware Cloud Director server.
        vi_servers (Union[Unset, list['CloudDirectorViHostImportSpec']]): Array of vCenter Servers added to the VMware
            Cloud Director.
    """

    name: str
    description: str
    type_: EManagedServerType
    credentials: "CredentialsImportModel"
    certificate_thumbprint: Union[Unset, str] = UNSET
    url: Union[Unset, str] = UNSET
    vi_servers: Union[Unset, list["CloudDirectorViHostImportSpec"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        description = self.description

        type_ = self.type_.value

        credentials = self.credentials.to_dict()

        certificate_thumbprint = self.certificate_thumbprint

        url = self.url

        vi_servers: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.vi_servers, Unset):
            vi_servers = []
            for vi_servers_item_data in self.vi_servers:
                vi_servers_item = vi_servers_item_data.to_dict()
                vi_servers.append(vi_servers_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "description": description,
                "type": type_,
                "credentials": credentials,
            }
        )
        if certificate_thumbprint is not UNSET:
            field_dict["certificateThumbprint"] = certificate_thumbprint
        if url is not UNSET:
            field_dict["url"] = url
        if vi_servers is not UNSET:
            field_dict["viServers"] = vi_servers

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.cloud_director_vi_host_import_spec import CloudDirectorViHostImportSpec
        from ..models.credentials_import_model import CredentialsImportModel

        d = dict(src_dict)
        name = d.pop("name")

        description = d.pop("description")

        type_ = EManagedServerType(d.pop("type"))

        credentials = CredentialsImportModel.from_dict(d.pop("credentials"))

        certificate_thumbprint = d.pop("certificateThumbprint", UNSET)

        url = d.pop("url", UNSET)

        vi_servers = []
        _vi_servers = d.pop("viServers", UNSET)
        for vi_servers_item_data in _vi_servers or []:
            vi_servers_item = CloudDirectorViHostImportSpec.from_dict(vi_servers_item_data)

            vi_servers.append(vi_servers_item)

        cloud_director_host_import_spec = cls(
            name=name,
            description=description,
            type_=type_,
            credentials=credentials,
            certificate_thumbprint=certificate_thumbprint,
            url=url,
            vi_servers=vi_servers,
        )

        cloud_director_host_import_spec.additional_properties = d
        return cloud_director_host_import_spec

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties

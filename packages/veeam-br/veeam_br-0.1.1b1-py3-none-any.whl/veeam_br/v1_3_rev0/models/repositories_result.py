from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.amazon_s3_glacier_storage_model import AmazonS3GlacierStorageModel
    from ..models.amazon_s3_storage_model import AmazonS3StorageModel
    from ..models.amazon_snowball_edge_storage_model import AmazonSnowballEdgeStorageModel
    from ..models.azure_archive_storage_model import AzureArchiveStorageModel
    from ..models.azure_blob_storage_model import AzureBlobStorageModel
    from ..models.azure_data_box_storage_model import AzureDataBoxStorageModel
    from ..models.google_cloud_storage_model import GoogleCloudStorageModel
    from ..models.ibm_cloud_storage_model import IBMCloudStorageModel
    from ..models.linux_hardened_storage_model import LinuxHardenedStorageModel
    from ..models.linux_local_storage_model import LinuxLocalStorageModel
    from ..models.nfs_storage_model import NfsStorageModel
    from ..models.pagination_result import PaginationResult
    from ..models.s3_compatible_storage_model import S3CompatibleStorageModel
    from ..models.smb_storage_model import SmbStorageModel
    from ..models.veeam_data_cloud_vault_storage_model import VeeamDataCloudVaultStorageModel
    from ..models.wasabi_cloud_storage_model import WasabiCloudStorageModel
    from ..models.windows_local_storage_model import WindowsLocalStorageModel


T = TypeVar("T", bound="RepositoriesResult")


@_attrs_define
class RepositoriesResult:
    """Backup repository details.

    Attributes:
        data (list[Union['AmazonS3GlacierStorageModel', 'AmazonS3StorageModel', 'AmazonSnowballEdgeStorageModel',
            'AzureArchiveStorageModel', 'AzureBlobStorageModel', 'AzureDataBoxStorageModel', 'GoogleCloudStorageModel',
            'IBMCloudStorageModel', 'LinuxHardenedStorageModel', 'LinuxLocalStorageModel', 'NfsStorageModel',
            'S3CompatibleStorageModel', 'SmbStorageModel', 'VeeamDataCloudVaultStorageModel', 'WasabiCloudStorageModel',
            'WindowsLocalStorageModel']]): Array of backup repositories.
        pagination (PaginationResult): Pagination settings.
    """

    data: list[
        Union[
            "AmazonS3GlacierStorageModel",
            "AmazonS3StorageModel",
            "AmazonSnowballEdgeStorageModel",
            "AzureArchiveStorageModel",
            "AzureBlobStorageModel",
            "AzureDataBoxStorageModel",
            "GoogleCloudStorageModel",
            "IBMCloudStorageModel",
            "LinuxHardenedStorageModel",
            "LinuxLocalStorageModel",
            "NfsStorageModel",
            "S3CompatibleStorageModel",
            "SmbStorageModel",
            "VeeamDataCloudVaultStorageModel",
            "WasabiCloudStorageModel",
            "WindowsLocalStorageModel",
        ]
    ]
    pagination: "PaginationResult"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.amazon_s3_glacier_storage_model import AmazonS3GlacierStorageModel
        from ..models.amazon_s3_storage_model import AmazonS3StorageModel
        from ..models.amazon_snowball_edge_storage_model import AmazonSnowballEdgeStorageModel
        from ..models.azure_archive_storage_model import AzureArchiveStorageModel
        from ..models.azure_blob_storage_model import AzureBlobStorageModel
        from ..models.azure_data_box_storage_model import AzureDataBoxStorageModel
        from ..models.google_cloud_storage_model import GoogleCloudStorageModel
        from ..models.ibm_cloud_storage_model import IBMCloudStorageModel
        from ..models.linux_hardened_storage_model import LinuxHardenedStorageModel
        from ..models.linux_local_storage_model import LinuxLocalStorageModel
        from ..models.nfs_storage_model import NfsStorageModel
        from ..models.s3_compatible_storage_model import S3CompatibleStorageModel
        from ..models.smb_storage_model import SmbStorageModel
        from ..models.wasabi_cloud_storage_model import WasabiCloudStorageModel
        from ..models.windows_local_storage_model import WindowsLocalStorageModel

        data = []
        for data_item_data in self.data:
            data_item: dict[str, Any]
            if isinstance(data_item_data, WindowsLocalStorageModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, LinuxLocalStorageModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, NfsStorageModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, SmbStorageModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, AzureBlobStorageModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, AzureDataBoxStorageModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, AmazonS3StorageModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, AmazonSnowballEdgeStorageModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, S3CompatibleStorageModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, GoogleCloudStorageModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, IBMCloudStorageModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, AmazonS3GlacierStorageModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, AzureArchiveStorageModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, WasabiCloudStorageModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, LinuxHardenedStorageModel):
                data_item = data_item_data.to_dict()
            else:
                data_item = data_item_data.to_dict()

            data.append(data_item)

        pagination = self.pagination.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "data": data,
                "pagination": pagination,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.amazon_s3_glacier_storage_model import AmazonS3GlacierStorageModel
        from ..models.amazon_s3_storage_model import AmazonS3StorageModel
        from ..models.amazon_snowball_edge_storage_model import AmazonSnowballEdgeStorageModel
        from ..models.azure_archive_storage_model import AzureArchiveStorageModel
        from ..models.azure_blob_storage_model import AzureBlobStorageModel
        from ..models.azure_data_box_storage_model import AzureDataBoxStorageModel
        from ..models.google_cloud_storage_model import GoogleCloudStorageModel
        from ..models.ibm_cloud_storage_model import IBMCloudStorageModel
        from ..models.linux_hardened_storage_model import LinuxHardenedStorageModel
        from ..models.linux_local_storage_model import LinuxLocalStorageModel
        from ..models.nfs_storage_model import NfsStorageModel
        from ..models.pagination_result import PaginationResult
        from ..models.s3_compatible_storage_model import S3CompatibleStorageModel
        from ..models.smb_storage_model import SmbStorageModel
        from ..models.veeam_data_cloud_vault_storage_model import VeeamDataCloudVaultStorageModel
        from ..models.wasabi_cloud_storage_model import WasabiCloudStorageModel
        from ..models.windows_local_storage_model import WindowsLocalStorageModel

        d = dict(src_dict)
        data = []
        _data = d.pop("data")
        for data_item_data in _data:

            def _parse_data_item(
                data: object,
            ) -> Union[
                "AmazonS3GlacierStorageModel",
                "AmazonS3StorageModel",
                "AmazonSnowballEdgeStorageModel",
                "AzureArchiveStorageModel",
                "AzureBlobStorageModel",
                "AzureDataBoxStorageModel",
                "GoogleCloudStorageModel",
                "IBMCloudStorageModel",
                "LinuxHardenedStorageModel",
                "LinuxLocalStorageModel",
                "NfsStorageModel",
                "S3CompatibleStorageModel",
                "SmbStorageModel",
                "VeeamDataCloudVaultStorageModel",
                "WasabiCloudStorageModel",
                "WindowsLocalStorageModel",
            ]:
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_repository_model_type_0 = WindowsLocalStorageModel.from_dict(data)

                    return componentsschemas_repository_model_type_0
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_repository_model_type_1 = LinuxLocalStorageModel.from_dict(data)

                    return componentsschemas_repository_model_type_1
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_repository_model_type_2 = NfsStorageModel.from_dict(data)

                    return componentsschemas_repository_model_type_2
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_repository_model_type_3 = SmbStorageModel.from_dict(data)

                    return componentsschemas_repository_model_type_3
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_repository_model_type_4 = AzureBlobStorageModel.from_dict(data)

                    return componentsschemas_repository_model_type_4
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_repository_model_type_5 = AzureDataBoxStorageModel.from_dict(data)

                    return componentsschemas_repository_model_type_5
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_repository_model_type_6 = AmazonS3StorageModel.from_dict(data)

                    return componentsschemas_repository_model_type_6
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_repository_model_type_7 = AmazonSnowballEdgeStorageModel.from_dict(data)

                    return componentsschemas_repository_model_type_7
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_repository_model_type_8 = S3CompatibleStorageModel.from_dict(data)

                    return componentsschemas_repository_model_type_8
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_repository_model_type_9 = GoogleCloudStorageModel.from_dict(data)

                    return componentsschemas_repository_model_type_9
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_repository_model_type_10 = IBMCloudStorageModel.from_dict(data)

                    return componentsschemas_repository_model_type_10
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_repository_model_type_11 = AmazonS3GlacierStorageModel.from_dict(data)

                    return componentsschemas_repository_model_type_11
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_repository_model_type_12 = AzureArchiveStorageModel.from_dict(data)

                    return componentsschemas_repository_model_type_12
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_repository_model_type_13 = WasabiCloudStorageModel.from_dict(data)

                    return componentsschemas_repository_model_type_13
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_repository_model_type_14 = LinuxHardenedStorageModel.from_dict(data)

                    return componentsschemas_repository_model_type_14
                except:  # noqa: E722
                    pass
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_repository_model_type_15 = VeeamDataCloudVaultStorageModel.from_dict(data)

                return componentsschemas_repository_model_type_15

            data_item = _parse_data_item(data_item_data)

            data.append(data_item)

        pagination = PaginationResult.from_dict(d.pop("pagination"))

        repositories_result = cls(
            data=data,
            pagination=pagination,
        )

        repositories_result.additional_properties = d
        return repositories_result

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

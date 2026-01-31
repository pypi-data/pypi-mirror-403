from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.amazon_s3_server_model import AmazonS3ServerModel
    from ..models.azure_blob_server_model import AzureBlobServerModel
    from ..models.file_server_model import FileServerModel
    from ..models.nas_filer_server_model import NASFilerServerModel
    from ..models.nfs_share_server_model import NFSShareServerModel
    from ..models.pagination_result import PaginationResult
    from ..models.s3_compatible_server_model import S3CompatibleServerModel
    from ..models.smb_share_server_model import SMBShareServerModel


T = TypeVar("T", bound="UnstructuredDataServersResult")


@_attrs_define
class UnstructuredDataServersResult:
    """Details on unstructured data servers.

    Attributes:
        data (list[Union['AmazonS3ServerModel', 'AzureBlobServerModel', 'FileServerModel', 'NASFilerServerModel',
            'NFSShareServerModel', 'S3CompatibleServerModel', 'SMBShareServerModel']]): Array of unstructured data servers.
        pagination (PaginationResult): Pagination settings.
    """

    data: list[
        Union[
            "AmazonS3ServerModel",
            "AzureBlobServerModel",
            "FileServerModel",
            "NASFilerServerModel",
            "NFSShareServerModel",
            "S3CompatibleServerModel",
            "SMBShareServerModel",
        ]
    ]
    pagination: "PaginationResult"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.amazon_s3_server_model import AmazonS3ServerModel
        from ..models.file_server_model import FileServerModel
        from ..models.nas_filer_server_model import NASFilerServerModel
        from ..models.nfs_share_server_model import NFSShareServerModel
        from ..models.s3_compatible_server_model import S3CompatibleServerModel
        from ..models.smb_share_server_model import SMBShareServerModel

        data = []
        for data_item_data in self.data:
            data_item: dict[str, Any]
            if isinstance(data_item_data, FileServerModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, SMBShareServerModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, NFSShareServerModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, NASFilerServerModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, S3CompatibleServerModel):
                data_item = data_item_data.to_dict()
            elif isinstance(data_item_data, AmazonS3ServerModel):
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
        from ..models.amazon_s3_server_model import AmazonS3ServerModel
        from ..models.azure_blob_server_model import AzureBlobServerModel
        from ..models.file_server_model import FileServerModel
        from ..models.nas_filer_server_model import NASFilerServerModel
        from ..models.nfs_share_server_model import NFSShareServerModel
        from ..models.pagination_result import PaginationResult
        from ..models.s3_compatible_server_model import S3CompatibleServerModel
        from ..models.smb_share_server_model import SMBShareServerModel

        d = dict(src_dict)
        data = []
        _data = d.pop("data")
        for data_item_data in _data:

            def _parse_data_item(
                data: object,
            ) -> Union[
                "AmazonS3ServerModel",
                "AzureBlobServerModel",
                "FileServerModel",
                "NASFilerServerModel",
                "NFSShareServerModel",
                "S3CompatibleServerModel",
                "SMBShareServerModel",
            ]:
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_unstructured_data_server_model_type_0 = FileServerModel.from_dict(data)

                    return componentsschemas_unstructured_data_server_model_type_0
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_unstructured_data_server_model_type_1 = SMBShareServerModel.from_dict(data)

                    return componentsschemas_unstructured_data_server_model_type_1
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_unstructured_data_server_model_type_2 = NFSShareServerModel.from_dict(data)

                    return componentsschemas_unstructured_data_server_model_type_2
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_unstructured_data_server_model_type_3 = NASFilerServerModel.from_dict(data)

                    return componentsschemas_unstructured_data_server_model_type_3
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_unstructured_data_server_model_type_4 = S3CompatibleServerModel.from_dict(data)

                    return componentsschemas_unstructured_data_server_model_type_4
                except:  # noqa: E722
                    pass
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    componentsschemas_unstructured_data_server_model_type_5 = AmazonS3ServerModel.from_dict(data)

                    return componentsschemas_unstructured_data_server_model_type_5
                except:  # noqa: E722
                    pass
                if not isinstance(data, dict):
                    raise TypeError()
                componentsschemas_unstructured_data_server_model_type_6 = AzureBlobServerModel.from_dict(data)

                return componentsschemas_unstructured_data_server_model_type_6

            data_item = _parse_data_item(data_item_data)

            data.append(data_item)

        pagination = PaginationResult.from_dict(d.pop("pagination"))

        unstructured_data_servers_result = cls(
            data=data,
            pagination=pagination,
        )

        unstructured_data_servers_result.additional_properties = d
        return unstructured_data_servers_result

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

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.amazon_s3_glacier_storage_import_spec import AmazonS3GlacierStorageImportSpec
    from ..models.amazon_s3_storage_import_spec import AmazonS3StorageImportSpec
    from ..models.amazon_snowball_edge_storage_import_spec import AmazonSnowballEdgeStorageImportSpec
    from ..models.azure_archive_storage_import_spec import AzureArchiveStorageImportSpec
    from ..models.azure_blob_storage_import_spec import AzureBlobStorageImportSpec
    from ..models.azure_data_box_storage_import_spec import AzureDataBoxStorageImportSpec
    from ..models.google_cloud_storage_import_spec import GoogleCloudStorageImportSpec
    from ..models.ibm_cloud_storage_import_spec import IBMCloudStorageImportSpec
    from ..models.linux_hardened_storage_import_spec import LinuxHardenedStorageImportSpec
    from ..models.linux_local_storage_import_spec import LinuxLocalStorageImportSpec
    from ..models.nfs_storage_import_spec import NfsStorageImportSpec
    from ..models.s3_compatible_storage_import_spec import S3CompatibleStorageImportSpec
    from ..models.smb_storage_import_spec import SmbStorageImportSpec
    from ..models.wasabi_cloud_storage_import_spec import WasabiCloudStorageImportSpec
    from ..models.windows_local_storage_import_spec import WindowsLocalStorageImportSpec


T = TypeVar("T", bound="RepositoryImportSpecCollection")


@_attrs_define
class RepositoryImportSpecCollection:
    """
    Attributes:
        windows_local_repositories (Union[Unset, list['WindowsLocalStorageImportSpec']]): Array of Microsoft Windows-
            based repositories.
        linux_local_repositories (Union[Unset, list['LinuxLocalStorageImportSpec']]): Array of Linux-based repositories.
        smb_repositories (Union[Unset, list['SmbStorageImportSpec']]): Array of SMB backup repositories.
        nfs_repositories (Union[Unset, list['NfsStorageImportSpec']]): Array of NFS backup repositories.
        azure_blob_storages (Union[Unset, list['AzureBlobStorageImportSpec']]): Array of Microsoft Azure Blob storages.
        azure_data_box_storages (Union[Unset, list['AzureDataBoxStorageImportSpec']]): Array of Microsoft Azure Data Box
            storages.
        amazon_s3_storages (Union[Unset, list['AmazonS3StorageImportSpec']]): Array of Amazon S3 storages.
        amazon_snowball_edge_storages (Union[Unset, list['AmazonSnowballEdgeStorageImportSpec']]): Array of AWS Snowball
            Edge storages.
        s3_compatible_storages (Union[Unset, list['S3CompatibleStorageImportSpec']]): Array of S3 compatible storages.
        google_cloud_storages (Union[Unset, list['GoogleCloudStorageImportSpec']]): Array of Google Cloud storages.
        ibm_cloud_storages (Union[Unset, list['IBMCloudStorageImportSpec']]): Array of IBM Cloud storages.
        amazon_s3_glacier_storages (Union[Unset, list['AmazonS3GlacierStorageImportSpec']]): Array of Amazon S3 Glacier
            storages.
        azure_archive_storages (Union[Unset, list['AzureArchiveStorageImportSpec']]): Array of Microsoft Azure Archive
            storages.
        wasabi_cloud_storages (Union[Unset, list['WasabiCloudStorageImportSpec']]): Array of Wasabi Cloud storages.
        linux_hardened_repositories (Union[Unset, list['LinuxHardenedStorageImportSpec']]): Array of Linux hardened
            repositories.
    """

    windows_local_repositories: Union[Unset, list["WindowsLocalStorageImportSpec"]] = UNSET
    linux_local_repositories: Union[Unset, list["LinuxLocalStorageImportSpec"]] = UNSET
    smb_repositories: Union[Unset, list["SmbStorageImportSpec"]] = UNSET
    nfs_repositories: Union[Unset, list["NfsStorageImportSpec"]] = UNSET
    azure_blob_storages: Union[Unset, list["AzureBlobStorageImportSpec"]] = UNSET
    azure_data_box_storages: Union[Unset, list["AzureDataBoxStorageImportSpec"]] = UNSET
    amazon_s3_storages: Union[Unset, list["AmazonS3StorageImportSpec"]] = UNSET
    amazon_snowball_edge_storages: Union[Unset, list["AmazonSnowballEdgeStorageImportSpec"]] = UNSET
    s3_compatible_storages: Union[Unset, list["S3CompatibleStorageImportSpec"]] = UNSET
    google_cloud_storages: Union[Unset, list["GoogleCloudStorageImportSpec"]] = UNSET
    ibm_cloud_storages: Union[Unset, list["IBMCloudStorageImportSpec"]] = UNSET
    amazon_s3_glacier_storages: Union[Unset, list["AmazonS3GlacierStorageImportSpec"]] = UNSET
    azure_archive_storages: Union[Unset, list["AzureArchiveStorageImportSpec"]] = UNSET
    wasabi_cloud_storages: Union[Unset, list["WasabiCloudStorageImportSpec"]] = UNSET
    linux_hardened_repositories: Union[Unset, list["LinuxHardenedStorageImportSpec"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        windows_local_repositories: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.windows_local_repositories, Unset):
            windows_local_repositories = []
            for windows_local_repositories_item_data in self.windows_local_repositories:
                windows_local_repositories_item = windows_local_repositories_item_data.to_dict()
                windows_local_repositories.append(windows_local_repositories_item)

        linux_local_repositories: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.linux_local_repositories, Unset):
            linux_local_repositories = []
            for linux_local_repositories_item_data in self.linux_local_repositories:
                linux_local_repositories_item = linux_local_repositories_item_data.to_dict()
                linux_local_repositories.append(linux_local_repositories_item)

        smb_repositories: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.smb_repositories, Unset):
            smb_repositories = []
            for smb_repositories_item_data in self.smb_repositories:
                smb_repositories_item = smb_repositories_item_data.to_dict()
                smb_repositories.append(smb_repositories_item)

        nfs_repositories: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.nfs_repositories, Unset):
            nfs_repositories = []
            for nfs_repositories_item_data in self.nfs_repositories:
                nfs_repositories_item = nfs_repositories_item_data.to_dict()
                nfs_repositories.append(nfs_repositories_item)

        azure_blob_storages: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.azure_blob_storages, Unset):
            azure_blob_storages = []
            for azure_blob_storages_item_data in self.azure_blob_storages:
                azure_blob_storages_item = azure_blob_storages_item_data.to_dict()
                azure_blob_storages.append(azure_blob_storages_item)

        azure_data_box_storages: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.azure_data_box_storages, Unset):
            azure_data_box_storages = []
            for azure_data_box_storages_item_data in self.azure_data_box_storages:
                azure_data_box_storages_item = azure_data_box_storages_item_data.to_dict()
                azure_data_box_storages.append(azure_data_box_storages_item)

        amazon_s3_storages: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.amazon_s3_storages, Unset):
            amazon_s3_storages = []
            for amazon_s3_storages_item_data in self.amazon_s3_storages:
                amazon_s3_storages_item = amazon_s3_storages_item_data.to_dict()
                amazon_s3_storages.append(amazon_s3_storages_item)

        amazon_snowball_edge_storages: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.amazon_snowball_edge_storages, Unset):
            amazon_snowball_edge_storages = []
            for amazon_snowball_edge_storages_item_data in self.amazon_snowball_edge_storages:
                amazon_snowball_edge_storages_item = amazon_snowball_edge_storages_item_data.to_dict()
                amazon_snowball_edge_storages.append(amazon_snowball_edge_storages_item)

        s3_compatible_storages: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.s3_compatible_storages, Unset):
            s3_compatible_storages = []
            for s3_compatible_storages_item_data in self.s3_compatible_storages:
                s3_compatible_storages_item = s3_compatible_storages_item_data.to_dict()
                s3_compatible_storages.append(s3_compatible_storages_item)

        google_cloud_storages: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.google_cloud_storages, Unset):
            google_cloud_storages = []
            for google_cloud_storages_item_data in self.google_cloud_storages:
                google_cloud_storages_item = google_cloud_storages_item_data.to_dict()
                google_cloud_storages.append(google_cloud_storages_item)

        ibm_cloud_storages: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.ibm_cloud_storages, Unset):
            ibm_cloud_storages = []
            for ibm_cloud_storages_item_data in self.ibm_cloud_storages:
                ibm_cloud_storages_item = ibm_cloud_storages_item_data.to_dict()
                ibm_cloud_storages.append(ibm_cloud_storages_item)

        amazon_s3_glacier_storages: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.amazon_s3_glacier_storages, Unset):
            amazon_s3_glacier_storages = []
            for amazon_s3_glacier_storages_item_data in self.amazon_s3_glacier_storages:
                amazon_s3_glacier_storages_item = amazon_s3_glacier_storages_item_data.to_dict()
                amazon_s3_glacier_storages.append(amazon_s3_glacier_storages_item)

        azure_archive_storages: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.azure_archive_storages, Unset):
            azure_archive_storages = []
            for azure_archive_storages_item_data in self.azure_archive_storages:
                azure_archive_storages_item = azure_archive_storages_item_data.to_dict()
                azure_archive_storages.append(azure_archive_storages_item)

        wasabi_cloud_storages: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.wasabi_cloud_storages, Unset):
            wasabi_cloud_storages = []
            for wasabi_cloud_storages_item_data in self.wasabi_cloud_storages:
                wasabi_cloud_storages_item = wasabi_cloud_storages_item_data.to_dict()
                wasabi_cloud_storages.append(wasabi_cloud_storages_item)

        linux_hardened_repositories: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.linux_hardened_repositories, Unset):
            linux_hardened_repositories = []
            for linux_hardened_repositories_item_data in self.linux_hardened_repositories:
                linux_hardened_repositories_item = linux_hardened_repositories_item_data.to_dict()
                linux_hardened_repositories.append(linux_hardened_repositories_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if windows_local_repositories is not UNSET:
            field_dict["WindowsLocalRepositories"] = windows_local_repositories
        if linux_local_repositories is not UNSET:
            field_dict["LinuxLocalRepositories"] = linux_local_repositories
        if smb_repositories is not UNSET:
            field_dict["SmbRepositories"] = smb_repositories
        if nfs_repositories is not UNSET:
            field_dict["NfsRepositories"] = nfs_repositories
        if azure_blob_storages is not UNSET:
            field_dict["AzureBlobStorages"] = azure_blob_storages
        if azure_data_box_storages is not UNSET:
            field_dict["AzureDataBoxStorages"] = azure_data_box_storages
        if amazon_s3_storages is not UNSET:
            field_dict["AmazonS3Storages"] = amazon_s3_storages
        if amazon_snowball_edge_storages is not UNSET:
            field_dict["AmazonSnowballEdgeStorages"] = amazon_snowball_edge_storages
        if s3_compatible_storages is not UNSET:
            field_dict["S3CompatibleStorages"] = s3_compatible_storages
        if google_cloud_storages is not UNSET:
            field_dict["GoogleCloudStorages"] = google_cloud_storages
        if ibm_cloud_storages is not UNSET:
            field_dict["IBMCloudStorages"] = ibm_cloud_storages
        if amazon_s3_glacier_storages is not UNSET:
            field_dict["AmazonS3GlacierStorages"] = amazon_s3_glacier_storages
        if azure_archive_storages is not UNSET:
            field_dict["AzureArchiveStorages"] = azure_archive_storages
        if wasabi_cloud_storages is not UNSET:
            field_dict["WasabiCloudStorages"] = wasabi_cloud_storages
        if linux_hardened_repositories is not UNSET:
            field_dict["LinuxHardenedRepositories"] = linux_hardened_repositories

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.amazon_s3_glacier_storage_import_spec import AmazonS3GlacierStorageImportSpec
        from ..models.amazon_s3_storage_import_spec import AmazonS3StorageImportSpec
        from ..models.amazon_snowball_edge_storage_import_spec import AmazonSnowballEdgeStorageImportSpec
        from ..models.azure_archive_storage_import_spec import AzureArchiveStorageImportSpec
        from ..models.azure_blob_storage_import_spec import AzureBlobStorageImportSpec
        from ..models.azure_data_box_storage_import_spec import AzureDataBoxStorageImportSpec
        from ..models.google_cloud_storage_import_spec import GoogleCloudStorageImportSpec
        from ..models.ibm_cloud_storage_import_spec import IBMCloudStorageImportSpec
        from ..models.linux_hardened_storage_import_spec import LinuxHardenedStorageImportSpec
        from ..models.linux_local_storage_import_spec import LinuxLocalStorageImportSpec
        from ..models.nfs_storage_import_spec import NfsStorageImportSpec
        from ..models.s3_compatible_storage_import_spec import S3CompatibleStorageImportSpec
        from ..models.smb_storage_import_spec import SmbStorageImportSpec
        from ..models.wasabi_cloud_storage_import_spec import WasabiCloudStorageImportSpec
        from ..models.windows_local_storage_import_spec import WindowsLocalStorageImportSpec

        d = dict(src_dict)
        windows_local_repositories = []
        _windows_local_repositories = d.pop("WindowsLocalRepositories", UNSET)
        for windows_local_repositories_item_data in _windows_local_repositories or []:
            windows_local_repositories_item = WindowsLocalStorageImportSpec.from_dict(
                windows_local_repositories_item_data
            )

            windows_local_repositories.append(windows_local_repositories_item)

        linux_local_repositories = []
        _linux_local_repositories = d.pop("LinuxLocalRepositories", UNSET)
        for linux_local_repositories_item_data in _linux_local_repositories or []:
            linux_local_repositories_item = LinuxLocalStorageImportSpec.from_dict(linux_local_repositories_item_data)

            linux_local_repositories.append(linux_local_repositories_item)

        smb_repositories = []
        _smb_repositories = d.pop("SmbRepositories", UNSET)
        for smb_repositories_item_data in _smb_repositories or []:
            smb_repositories_item = SmbStorageImportSpec.from_dict(smb_repositories_item_data)

            smb_repositories.append(smb_repositories_item)

        nfs_repositories = []
        _nfs_repositories = d.pop("NfsRepositories", UNSET)
        for nfs_repositories_item_data in _nfs_repositories or []:
            nfs_repositories_item = NfsStorageImportSpec.from_dict(nfs_repositories_item_data)

            nfs_repositories.append(nfs_repositories_item)

        azure_blob_storages = []
        _azure_blob_storages = d.pop("AzureBlobStorages", UNSET)
        for azure_blob_storages_item_data in _azure_blob_storages or []:
            azure_blob_storages_item = AzureBlobStorageImportSpec.from_dict(azure_blob_storages_item_data)

            azure_blob_storages.append(azure_blob_storages_item)

        azure_data_box_storages = []
        _azure_data_box_storages = d.pop("AzureDataBoxStorages", UNSET)
        for azure_data_box_storages_item_data in _azure_data_box_storages or []:
            azure_data_box_storages_item = AzureDataBoxStorageImportSpec.from_dict(azure_data_box_storages_item_data)

            azure_data_box_storages.append(azure_data_box_storages_item)

        amazon_s3_storages = []
        _amazon_s3_storages = d.pop("AmazonS3Storages", UNSET)
        for amazon_s3_storages_item_data in _amazon_s3_storages or []:
            amazon_s3_storages_item = AmazonS3StorageImportSpec.from_dict(amazon_s3_storages_item_data)

            amazon_s3_storages.append(amazon_s3_storages_item)

        amazon_snowball_edge_storages = []
        _amazon_snowball_edge_storages = d.pop("AmazonSnowballEdgeStorages", UNSET)
        for amazon_snowball_edge_storages_item_data in _amazon_snowball_edge_storages or []:
            amazon_snowball_edge_storages_item = AmazonSnowballEdgeStorageImportSpec.from_dict(
                amazon_snowball_edge_storages_item_data
            )

            amazon_snowball_edge_storages.append(amazon_snowball_edge_storages_item)

        s3_compatible_storages = []
        _s3_compatible_storages = d.pop("S3CompatibleStorages", UNSET)
        for s3_compatible_storages_item_data in _s3_compatible_storages or []:
            s3_compatible_storages_item = S3CompatibleStorageImportSpec.from_dict(s3_compatible_storages_item_data)

            s3_compatible_storages.append(s3_compatible_storages_item)

        google_cloud_storages = []
        _google_cloud_storages = d.pop("GoogleCloudStorages", UNSET)
        for google_cloud_storages_item_data in _google_cloud_storages or []:
            google_cloud_storages_item = GoogleCloudStorageImportSpec.from_dict(google_cloud_storages_item_data)

            google_cloud_storages.append(google_cloud_storages_item)

        ibm_cloud_storages = []
        _ibm_cloud_storages = d.pop("IBMCloudStorages", UNSET)
        for ibm_cloud_storages_item_data in _ibm_cloud_storages or []:
            ibm_cloud_storages_item = IBMCloudStorageImportSpec.from_dict(ibm_cloud_storages_item_data)

            ibm_cloud_storages.append(ibm_cloud_storages_item)

        amazon_s3_glacier_storages = []
        _amazon_s3_glacier_storages = d.pop("AmazonS3GlacierStorages", UNSET)
        for amazon_s3_glacier_storages_item_data in _amazon_s3_glacier_storages or []:
            amazon_s3_glacier_storages_item = AmazonS3GlacierStorageImportSpec.from_dict(
                amazon_s3_glacier_storages_item_data
            )

            amazon_s3_glacier_storages.append(amazon_s3_glacier_storages_item)

        azure_archive_storages = []
        _azure_archive_storages = d.pop("AzureArchiveStorages", UNSET)
        for azure_archive_storages_item_data in _azure_archive_storages or []:
            azure_archive_storages_item = AzureArchiveStorageImportSpec.from_dict(azure_archive_storages_item_data)

            azure_archive_storages.append(azure_archive_storages_item)

        wasabi_cloud_storages = []
        _wasabi_cloud_storages = d.pop("WasabiCloudStorages", UNSET)
        for wasabi_cloud_storages_item_data in _wasabi_cloud_storages or []:
            wasabi_cloud_storages_item = WasabiCloudStorageImportSpec.from_dict(wasabi_cloud_storages_item_data)

            wasabi_cloud_storages.append(wasabi_cloud_storages_item)

        linux_hardened_repositories = []
        _linux_hardened_repositories = d.pop("LinuxHardenedRepositories", UNSET)
        for linux_hardened_repositories_item_data in _linux_hardened_repositories or []:
            linux_hardened_repositories_item = LinuxHardenedStorageImportSpec.from_dict(
                linux_hardened_repositories_item_data
            )

            linux_hardened_repositories.append(linux_hardened_repositories_item)

        repository_import_spec_collection = cls(
            windows_local_repositories=windows_local_repositories,
            linux_local_repositories=linux_local_repositories,
            smb_repositories=smb_repositories,
            nfs_repositories=nfs_repositories,
            azure_blob_storages=azure_blob_storages,
            azure_data_box_storages=azure_data_box_storages,
            amazon_s3_storages=amazon_s3_storages,
            amazon_snowball_edge_storages=amazon_snowball_edge_storages,
            s3_compatible_storages=s3_compatible_storages,
            google_cloud_storages=google_cloud_storages,
            ibm_cloud_storages=ibm_cloud_storages,
            amazon_s3_glacier_storages=amazon_s3_glacier_storages,
            azure_archive_storages=azure_archive_storages,
            wasabi_cloud_storages=wasabi_cloud_storages,
            linux_hardened_repositories=linux_hardened_repositories,
        )

        repository_import_spec_collection.additional_properties = d
        return repository_import_spec_collection

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

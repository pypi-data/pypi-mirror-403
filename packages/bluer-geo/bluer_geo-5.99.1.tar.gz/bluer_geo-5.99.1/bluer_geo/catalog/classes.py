from typing import List, Type

from bluer_options.env import BLUER_AI_WEB_STATUS

from bluer_geo import env
from bluer_geo.catalog.generic import (
    GenericCatalog,
    VoidCatalog,
    GenericDatacube,
    VoidDatacube,
)

if env.BLUER_GEO_DISABLE_ALL_CATALOGS == 0:
    from bluer_geo.catalog.copernicus import (
        CopernicusCatalog,
        CopernicusSentinel2Datacube,
    )
    from bluer_geo.catalog.firms import FirmsCatalog
    from bluer_geo.catalog.firms.area import FirmsAreaDatacube

    if BLUER_AI_WEB_STATUS == "online":
        from bluer_geo.catalog.maxar_open_data import (
            MaxarOpenDataCatalog,
            MaxarOpenDataDatacube,
        )
        from bluer_geo.catalog.ukraine_timemap import (
            UkraineTimemapCatalog,
            UkraineTimemapDatacube,
        )

list_of_catalog_classes: List[Type[GenericCatalog]] = [
    GenericCatalog,
] + (
    (
        (
            [
                FirmsCatalog,
            ]
            + (
                [
                    CopernicusCatalog,
                    MaxarOpenDataCatalog,
                    UkraineTimemapCatalog,
                ]
                if BLUER_AI_WEB_STATUS == "online"
                else []
            )
        )
        if env.BLUER_GEO_DISABLE_ALL_CATALOGS == 0
        else []
    )
)

list_of_catalogs: List[str] = sorted(
    [
        catalog_name
        for catalog_name in [
            catalog_class.name for catalog_class in list_of_catalog_classes
        ]
        if catalog_name not in env.BLUE_GEO_DISABLED_CATALOGS.split(",")
    ]
)

list_of_datacube_classes: List[Type[GenericDatacube]] = [
    GenericDatacube,
] + (
    (
        (
            [
                FirmsAreaDatacube,
            ]
            + (
                [
                    UkraineTimemapDatacube,
                    CopernicusSentinel2Datacube,
                    MaxarOpenDataDatacube,
                ]
                if BLUER_AI_WEB_STATUS == "online"
                else []
            )
        )
        if env.BLUER_GEO_DISABLE_ALL_CATALOGS == 0
        else []
    )
)

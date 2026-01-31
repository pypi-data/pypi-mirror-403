from enum import Enum


class WorkOrderStatus(Enum):
    OPEN = 1
    COMPLETE = 2
    CLOSED = 3
    REQUESTED = 4
    CANCELLED = 5
    EXPIRED = 6
    IN_PROGRESS = 7

    def __str__(self):
        return str(self.value)


class WorkOrderPriority(Enum):
    MINOR = 1291
    MAJOR = 1292
    CRITICAL = 1293
    EMERGENCY = 1294

    def __str__(self):
        return str(self.value)


class WorkOrderType(Enum):
    PM = 1222
    REPAIR = 1223
    INSTALLATION = 1224

    def __str__(self):
        return str(self.value)


class FacetSearchKeys(Enum):
    ASSETTAG_KEY = 'ASSETTAG'
    DESCRIPTION_KEY = 'DESCRIPTION'
    CREATEDDATE_KEY = 'CREATEDDATE'
    CLIENT_ID_KEY = "ClientID"
    ASSET_CLASS_ID_KEY = "AssetClassID"
    WO_TYPE_KEY = "TYPE"
    WO_PRIORITY_KEY = "PRIORITY"
    WO_STATUS_KEY = "STATUS"

    def __str__(self):
        return self.value


if __name__ == '__main__':
    print(WorkOrderPriority.MINOR)
    print(WorkOrderType.PM)
    print(FacetSearchKeys.CLIENT_ID_KEY)
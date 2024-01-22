CREATE TABLE Workspaces (
    WorkspaceId STRING(36) NOT NULL DEFAULT (GENERATE_UUID())
) PRIMARY KEY (WorkspaceId);

CREATE TABLE Users (
    UserId STRING(36) NOT NULL DEFAULT (GENERATE_UUID())
) PRIMARY KEY (UserId);

CREATE TABLE MonitoredServices (
    ServiceId STRING(36) NOT NULL DEFAULT (GENERATE_UUID()),
    Url STRING(1024) NOT NULL,
    Frequency INT64 NOT NULL,
    AlertingWindow INT64 NOT NULL,
    AllowedResponseTime INT64 NOT NULL,
    WorkspaceId STRING(36) NOT NULL
) PRIMARY KEY (ServiceId);

CREATE NULL_FILTERED INDEX MonitoredServicesByWorkspaceId ON MonitoredServices(WorkspaceId, ServiceId);

CREATE TABLE ContactMethods (
    ServiceId STRING(36) NOT NULL,
    MethodOrder INT64 NOT NULL,
    Email STRING(128) NOT NULL,
) PRIMARY KEY (ServiceId, MethodOrder), INTERLEAVE IN PARENT MonitoredServices ON DELETE CASCADE;

CREATE TABLE MonitoredServicesLease (
    ServiceId STRING(36) NOT NULL,
    MonitorId STRING(36) NOT NULL,
    LeasedAt TIMESTAMP NOT NULL,
    LeaseDurationMs INT64 NOT NULL,
    LeasedTo TIMESTAMP NOT NULL AS (TIMESTAMP_MILLIS(UNIX_MILLIS(LeasedAt) + LeaseDurationMs)) STORED
) PRIMARY KEY (ServiceId, MonitorId);

CREATE NULL_FILTERED INDEX LeaseByMonitorId ON MonitoredServicesLease(MonitorId, ServiceId);

CREATE TABLE Alerts (
    ShardId INT64 NOT NULL AS (MOD(FARM_FINGERPRINT(ServiceId), 32) + 31) STORED,
    AlertId STRING(36) NOT NULL DEFAULT (GENERATE_UUID()),
    ServiceId STRING(36) NOT NULL,
    MonitorId STRING(36) NOT NULL,
    DetectionTimestamp TIMESTAMP NOT NULL,
    StatusExpirationTimestamp TIMESTAMP,
    AlertStatus INT64 NOT NULL

) PRIMARY KEY (ShardId, ServiceId, DetectionTimestamp DESC);

CREATE NULL_FILTERED INDEX AlertsById ON Alerts(AlertId);

CREATE NULL_FILTERED INDEX AlertsByStatus ON Alerts(AlertStatus, AlertId)
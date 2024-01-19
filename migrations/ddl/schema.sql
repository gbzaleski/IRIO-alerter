CREATE TABLE MonitoredServices (
    ServiceId STRING(36) DEFAULT (GENERATE_UUID()),
    Url STRING(1024),
    Frequency INT64 NOT NULL,
    AlertingWindow INT64 NOT NULL,
    AllowedResponseTime INT64 NOT NULL
) PRIMARY KEY (ServiceId)

CREATE TABLE MonitoredServicesLease (
    ServiceId STRING(36),
    MonitorId STRING(36),
    leasedAt TIMESTAMP NOT NULL,
    leaseDurationMs INT64 NOT NULL
) PRIMARY KEY (ServiceId, MonitorId)

CREATE TABLE Detections (
    ServiceId STRING(36),
    lastDetectionTime TIMESTAMP
) PRIMARY KEY (ServiceId)

CREATE TABLE Alerts (
    AlertId STRING(36) DEFAULT (GENERATE_UUID()),
    ServiceId STRING(36),
    MonitorId STRING(36),
    detectionTimestamp TIMESTAMP NOT NULL

) PRIMARY KEY (ServiceId, AlertId),
INTERLEAVE IN PARENT MonitoredServices ON DELETE CASCADE
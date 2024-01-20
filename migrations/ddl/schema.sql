CREATE TABLE MonitoredServices (
    ServiceId STRING(36) DEFAULT (GENERATE_UUID()),
    Url STRING(1024),
    Frequency INT64 NOT NULL,
    AlertingWindow INT64 NOT NULL,
    AllowedResponseTime INT64 NOT NULL
) PRIMARY KEY (ServiceId);

CREATE TABLE MonitoredServicesLease (
    ServiceId STRING(36),
    MonitorId STRING(36),
    LeasedAt TIMESTAMP NOT NULL,
    LeaseDurationMs INT64 NOT NULL
    LeasedTo TIMESTAMP NOT NULL AS (TIMESTAMP_MILLIS(UNIX_MILLIS(LeasedAt) + LeaseDurationMs)) STORED
) PRIMARY KEY (ServiceId, MonitorId);

CREATE TABLE Detections (
    ServiceId STRING(36),
    LastDetectionTime TIMESTAMP
) PRIMARY KEY (ServiceId);

CREATE TABLE Alerts (
    AlertId STRING(36) DEFAULT (GENERATE_UUID()),
    ServiceId STRING(36),
    MonitorId STRING(36),
    DetectionTimestamp TIMESTAMP NOT NULL,
    AlertStatus INT64 NOT NULL

) PRIMARY KEY (ServiceId, DetectionTimestamp DESC);

CREATE NULL_FILTERED INDEX AlertsById ON Alerts(AlertId)
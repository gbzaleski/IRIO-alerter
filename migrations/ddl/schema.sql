CREATE TABLE MonitoredServices (
    ServiceId INT64 NOT NULL,
    Url STRING(1024),
    Frequency INT64 NOT NULL,
    AlertingWindow INT64 NOT NULL,
    AllowedResponseTime INT64 NOT NULL
) PRIMARY KEY (ServiceId)

CREATE TABLE Alerts (
    AlertId STRING(36) DEFAULT (GENERATE_UUID()),
    MonitorId INT64 NOT NULL,
    detectionTimestamp TIMESTAMP NOT NULL

) PRIMARY KEY (AlertId)
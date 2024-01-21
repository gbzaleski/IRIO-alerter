INSERT INTO MonitoredServices (ServiceId, Url, Frequency, AlertingWindow, AllowedResponseTime)
VALUES ('6839b274-f5ab-42f5-a3f8-ea10bbf2b599', "http://localhost:8000/", 10000, 5000, 120000)
THEN RETURN ServiceId
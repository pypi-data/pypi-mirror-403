SELECT typeId, timestamp, group_concat((metricId + 9400),';') as metricId, group_concat(value,';') as metric_values FROM GPU_METRICS
GROUP BY typeId, timestamp
ORDER BY timestamp ASC
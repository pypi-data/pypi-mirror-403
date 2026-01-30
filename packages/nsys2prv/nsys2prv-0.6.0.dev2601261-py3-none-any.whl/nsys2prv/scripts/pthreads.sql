SELECT 
    os.start,
    os.end,
    os.eventClass,
    (os.globalTid / 0x1000000 % 0x1000000) as Pid,
    (os.globalTid % 0x1000000) as Tid,
    sid.value as "Event"
FROM OSRT_API as os
LEFT JOIN ENUM_NSYS_EVENT_CLASS as et ON os.eventClass = et.id
LEFT OUTER JOIN StringIds as sid ON os.nameId = sid.id
WHERE os.eventClass = 27 
  AND sid.value LIKE '%pthread%';
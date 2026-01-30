WITH
    domains AS (
        SELECT
            min(start),
            domainId AS id,
            globalTid AS globalTid,
            text AS name
        FROM
            NVTX_EVENTS
        WHERE
            eventType == 75
        GROUP BY 2, 3
    ),
	category AS (
    SELECT
      category,
      domainId,
	  globalTid AS globalTid,
      text AS categoryName
    FROM NVTX_EVENTS
    WHERE eventType == 33 -- category definition events
  ),
    maxts AS(
        SELECT max(max(start), max(end)) AS m
        FROM   NVTX_EVENTS
    ),
    nvtx AS (
        SELECT
			ne.start AS "Start:ts_ns",
            coalesce(ne.end, ne.start) AS "End:ts_ns",
            CASE 
                WHEN ne.eventType IS 34
                    THEN 0
                ELSE
                    coalesce(ne.end, (SELECT m FROM maxts)) - ne.start 
            END AS "Duration:dur_ns",
            CASE
                WHEN sid.value IS NOT NULL
                    THEN sid.value
                WHEN sid.value IS NULL
                    THEN ne.text
                ELSE ne.text
            END AS "Name",
			d.name as "domain",
			ne.jsonText,
			ne.eventType,
			category.categoryName as "category",
			(ne.globalTid / 0x1000000 % 0x1000000) as PID,
			(ne.globalTid % 0x1000000) as TID
        FROM
            NVTX_EVENTS AS ne
        LEFT JOIN
            domains AS d
            ON ne.domainId == d.id
                AND (ne.globalTid & 0x0000FFFFFF000000) == (d.globalTid & 0x0000FFFFFF000000)
        LEFT OUTER JOIN
            StringIds AS sid
            ON ne.textId == sid.id
		LEFT JOIN category 
		ON category.category == ne.category AND category.domainId == ne.domainId AND (ne.globalTid & 0x0000FFFFFF000000) == (category.globalTid & 0x0000FFFFFF000000)
        WHERE
            ne.eventType IN (34, 59, 60)
    )
SELECT
	*
	FROM
	nvtx
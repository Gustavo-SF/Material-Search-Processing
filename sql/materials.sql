SELECT TOP 5000
    material_id,
    material_description
FROM
    proc_db.zmm001
WHERE
    material_type = 'ZMAT'
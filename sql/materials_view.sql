SELECT 
    zmm001.Material, 
    CAST(zmm001.MaterialDescription AS VARCHAR(MAX)) AS MaterialDescription, 
    zmm001.MaterialGroup, 
    CAST(zmm001.MaterialGroupDescription AS VARCHAR(MAX)) AS MaterialGroupDescription, 
    zmm001.Unit, 
    zmm001.MaterialType, 
    zmm001.Created, 
    zmm001.LastChange, 
    ISNULL(AVG(mb51view.ValuePerUnit), '0') as AveragePrice,
    ISNULL(STDEV(mb51view.ValuePerUnit), '0') as STDPrice,
    ISNULL(COUNT(mb51view.ValuePerUnit), '0') as CountMovements
FROM [PPP].[ZMM001] as zmm001
LEFT JOIN (
    SELECT Material, MovementValueEuro / Quantity AS ValuePerUnit
    FROM [PPP].[MB51view]
    WHERE Quantity > 0
) as mb51view
ON mb51view.Material=zmm001.Material
GROUP BY
    zmm001.Material,
    CAST(zmm001.MaterialDescription AS VARCHAR(MAX)),
    zmm001.MaterialGroup,
    CAST(zmm001.MaterialGroupDescription AS VARCHAR(MAX)),
    zmm001.Unit,
    zmm001.MaterialType,
    zmm001.Created,
    zmm001.LastChange
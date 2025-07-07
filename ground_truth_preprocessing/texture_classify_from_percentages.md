## Calculate the texture of the soil when sand%, slit%, and clay% are provided

Imagine percentages for sand%, clay%, and slit% are in D, E, and F columns respectively.

To calculate the texture in 56th row
`=IF(E56>=40,IF(F56>=40,"silty clay",IF(D56>=45,"sandy clay","clay")),IF(E56>=27,IF(F56>=28,"silty clay loam",IF(D56>=20,"sandy clay loam","clay loam")),IF(E56>=20,IF(D56>=52,"sandy loam",IF(F56>=50,"silt loam","loam")),IF(E56<7,IF(D56>=85,"sand",IF(D56>=70,"loamy sand","sandy loam")),IF(F56>=80,"silt",IF(F56>=50,"silt loam","loam"))))))
`
